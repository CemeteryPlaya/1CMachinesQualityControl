# -*- coding: utf-8 -*-
"""
Админ-панель: /admin

Вход по логину/паролю (сессии Flask). Права администраторов (таблица admins):
- can_view_reports  — видеть отчеты за сегодня и кто их отправил (дашборд, детали);
- can_view_history  — просматривать историю отчетов с фильтрами;
- receive_instant_notifications — мгновенные push в Telegram о каждом отчете;
- receive_daily_digest — дневная сводка «кто и сколько отправил сегодня»;
- is_superadmin     — управление администраторами.
"""
import re
import logging
import secrets
from datetime import date, datetime, timedelta
from functools import wraps
from importlib import import_module

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, abort, g, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash

from telegram_auth import validate_init_data
from time_utils import today_local
from translations import get_bot_message
from database import (get_admin_by_username, get_admin_by_id, get_all_admins,
                      get_admin_by_telegram_id, create_admin, update_admin,
                      get_daily_inspections, get_daily_inspection_by_id,
                      get_inspections_history, get_inspection_by_id,
                      get_maintenance_history, get_maintenance_report_by_id,
                      get_submission_stats_for_date,
                      get_daily_dates_by_machine, get_weekly_dates_by_machine,
                      get_maintenance_for_analytics,
                      get_filter_options, FILTER_SCHEMES)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)

# Человекочитаемые названия проверок ежедневного чек-листа
DAILY_CHECKS = [
    ('engine_oil', 'Состояние и уровень моторного масла'),
    ('antifreeze', 'Состояние и уровень антифриза'),
    ('air_filter', 'Состояние воздушного фильтра'),
]

ADMIN_FLAGS = [
    ('can_view_reports', 'Просмотр отчетов'),
    ('can_view_history', 'История отчетов'),
    ('receive_instant_notifications', 'Мгновенные уведомления'),
    ('receive_daily_digest', 'Дневная сводка'),
    ('is_superadmin', 'Суперадмин'),
]

# Значения radio-полей для цветовой подсветки (все 4 языка форм).
# Только для полей, отмечавшихся в формах как radio; прочие значения — нейтральные.
_GOOD_VALUES = {'Нормальное', 'Нормально', 'Normal', 'Қалыпты',
                'Имеется', 'Present', 'Бар', 'Bor'}
_BAD_VALUES = {'Не нормальное', 'Не нормально', 'Not normal', 'Қалыпсыз', 'Normal emas',
               'Отсутствует', 'Absent', 'Жоқ', "Yo'q"}

# Реверсивные поля: «Имеется» здесь — плохо, «Отсутствует» — хорошо
# («Какое либо повреждение», «Наличие какой-либо течи в системе»)
_REVERSED_FIELD_IDS = {'body_defects', 'hydro_oil_system_leakages'}


def _value_status(value, reversed_field: bool = False) -> str:
    """'good' | 'bad' | None для значения radio-поля.

    reversed_field=True инвертирует оценку (поля про повреждения/течи,
    где «Имеется» — плохо, а «Отсутствует» — хорошо).
    """
    if not isinstance(value, str):
        return None
    v = value.strip()
    if v in _GOOD_VALUES:
        return 'bad' if reversed_field else 'good'
    if v in _BAD_VALUES:
        return 'good' if reversed_field else 'bad'
    return None


# Названия типов форм — те же, что на кнопках выбора в боте
WEEKLY_FORM_NAMES = {
    'lv': get_bot_message('vehicle_lv', 'ru'),
    'lv_oa': get_bot_message('vehicle_lv_oa', 'ru'),
    'sv': get_bot_message('vehicle_sv', 'ru'),
    'sv_oa': get_bot_message('vehicle_sv_oa', 'ru'),
    'gsheets': 'Google Forms Общая - выезд',
}

# Модули конфигов еженедельных форм (как в app_routes.FORM_CONFIG_MODULES).
# gsheets — Google Form с той же структурой, что «Спецтехника — выезд».
_WEEKLY_CONFIG_MODULES = {
    'lv': 'lv_form_config',
    'lv_oa': 'lv_oa_form_config',
    'sv': 'sv_form_config',
    'sv_oa': 'sv_oa_form_config',
    'gsheets': 'sv_oa_form_config',
}

# У gsheets-отчётов ключи results — русские заголовки вопросов Google Form
# (AppsScript шлёт title как ключ), поэтому сопоставляем по подписи, а не по id.
_MATCH_BY_LABEL = {'gsheets'}


def _norm_label(text) -> str:
    """Нормализация подписи для матчинга gsheets: регистр, пробелы, ё→е.

    Небольшие расхождения формулировок вопроса в Google Form и подписи
    в конфиге (лишний пробел, буква ё) не должны уводить поле в «Итог»."""
    if not isinstance(text, str):
        return ''
    return re.sub(r'\s+', ' ', text.strip().lower().replace('ё', 'е'))


def _build_weekly_groups(form_type: str, results: dict):
    """Собирает результаты еженедельного чек-листа в группы по секциям формы.

    Использует конфиг формы (get_form_config('ru')): порядок полей, русские
    подписи и заголовки секций — как в самой форме. Возвращает (groups, leftovers):
    groups = [{'header': str|None, 'items': [{'label','value'}]}],
    leftovers — значения results, которых нет в конфиге (показываются отдельно).
    Если конфиг не найден (например, gsheets) — (None, results).
    """
    module_name = _WEEKLY_CONFIG_MODULES.get(form_type)
    if not module_name:
        return None, dict(results)
    try:
        config = import_module(module_name).get_form_config('ru')
    except Exception as e:
        logger.warning(f"Failed to load form config for {form_type}: {e}")
        return None, dict(results)

    match_by_label = form_type in _MATCH_BY_LABEL

    # Для матчинга по подписи строим нормализованный индекс ключей results
    norm_index = {}
    if match_by_label:
        for k in results:
            norm_index.setdefault(_norm_label(k), k)

    def find_key(item_key):
        """Ключ results для поля конфига (с нормализацией для gsheets)."""
        if not match_by_label:
            return item_key if item_key in results else None
        return norm_index.get(_norm_label(item_key))

    groups = []
    current = {'header': None, 'items': []}
    used = set()

    for item in config:
        itype = item.get('type')
        if itype == 'header':
            if current['items']:
                groups.append(current)
            current = {'header': item.get('label'), 'items': []}
            continue
        if itype in ('hidden', 'readonly'):
            continue
        if itype == 'odometer_group':
            for sub in item.get('fields', []):
                sub_key = find_key(sub.get('label') if match_by_label else sub.get('id'))
                if sub_key is not None:
                    current['items'].append({'label': sub.get('label', sub.get('id')),
                                             'value': results[sub_key],
                                             'status': None})
                    used.add(sub_key)
            continue
        fid = item.get('id')
        key = find_key(item.get('label') if match_by_label else fid)
        if key is not None:
            # Подсветка хорошо/плохо — только для radio-полей формы;
            # для полей про повреждения/течи оценка инвертируется
            status = None
            if itype == 'radio':
                status = _value_status(results[key],
                                       reversed_field=fid in _REVERSED_FIELD_IDS)
            current['items'].append({'label': item.get('label', fid),
                                     'value': results[key],
                                     'status': status})
            used.add(key)

    if current['items']:
        groups.append(current)

    # Не вошедшие в конфиг ключи: для gsheets это финальные вопросы формы
    # («Итог») — подсвечиваем их значения; для остальных форм — нейтрально.
    leftovers = []
    for k, v in results.items():
        if k in used or k == 'photos' or not isinstance(v, (str, int, float)):
            continue
        leftovers.append({'label': k, 'value': v,
                          'status': _value_status(v) if match_by_label else None})
    return groups, leftovers


def login_required(permission: str = None):
    """Требует входа; при указании permission — соответствующего права
    (суперадмин проходит любую проверку)."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            admin_id = session.get('admin_id')
            if not admin_id:
                return redirect(url_for('admin.login', next=request.path))
            admin = get_admin_by_id(admin_id)
            if not admin or not admin.get('is_active'):
                session.pop('admin_id', None)
                return redirect(url_for('admin.login'))
            if permission and not (admin.get(permission) or admin.get('is_superadmin')):
                abort(403)
            g.admin = admin
            return f(*args, **kwargs)
        return wrapper
    return decorator


def _parse_date(raw):
    if not raw:
        return None
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date()
    except ValueError:
        return None


def _read_filters(rtype: str) -> tuple:
    """Считывает фильтры machine/sender/person/project из query-параметров.

    Возвращает (filters_для_SQL {колонка: значение}, selected {роль: значение}).
    Колонки берутся из FILTER_SCHEMES — от типа отчёта зависит, что есть.
    """
    scheme = FILTER_SCHEMES.get(rtype, {})
    selected, filters = {}, {}
    for role in ('machine', 'sender', 'person', 'project'):
        val = request.args.get(role, '').strip()
        selected[role] = val
        if val and scheme.get(role):
            filters[scheme[role]] = val
    return filters, selected


# ============================================================
# Аутентификация
# ============================================================

def _get_csrf_token() -> str:
    if '_csrf' not in session:
        session['_csrf'] = secrets.token_hex(16)
    return session['_csrf']


@admin_bp.app_context_processor
def _inject_csrf():
    return {'csrf_token': _get_csrf_token}


def _check_csrf():
    token = request.form.get('_csrf', '')
    if not token or not secrets.compare_digest(token, session.get('_csrf', '')):
        abort(400, 'CSRF token mismatch')


@admin_bp.route('/auth_telegram', methods=['POST'])
def auth_telegram():
    """Вход из Telegram Mini App: по подписанному initData, доступ — если
    Telegram ID пользователя есть среди активных администраторов."""
    init_data = (request.json or {}).get('init_data', '') if request.is_json \
        else request.form.get('init_data', '')
    if not init_data:
        return jsonify({"success": False, "error": "no init_data"}), 400

    user = validate_init_data(init_data)
    if not user or not user.get('id'):
        return jsonify({"success": False, "error": "invalid signature"}), 403

    admin = get_admin_by_telegram_id(str(user['id']))
    if not admin:
        logger.info(f"Admin access denied for telegram id {user.get('id')}")
        return jsonify({"success": False, "error": "access_denied"}), 403

    session['admin_id'] = admin['id']
    logger.info(f"Admin '{admin['username']}' logged in via Telegram (id={user['id']})")
    return jsonify({"success": True, "redirect": url_for('admin.dashboard')})


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        _check_csrf()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = get_admin_by_username(username)
        if admin and admin.get('is_active') and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            logger.info(f"Admin '{username}' logged in")
            next_url = request.args.get('next') or url_for('admin.dashboard')
            return redirect(next_url)
        flash('Неверный логин или пароль', 'error')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin.login'))


# ============================================================
# Дашборд — отчеты за сегодня и кто их отправил
# ============================================================

@admin_bp.route('/')
@login_required('can_view_reports')
def dashboard():
    today = today_local()
    stats = get_submission_stats_for_date(today)
    latest_daily = get_daily_inspections(date_from=today, date_to=today, limit=50)
    return render_template('admin/dashboard.html',
                           admin=g.admin, stats=stats, today=today,
                           latest_daily=latest_daily)


# ============================================================
# История отчетов
# ============================================================

@admin_bp.route('/reports')
@login_required('can_view_history')
def reports():
    rtype = request.args.get('type', 'daily')
    if rtype not in ('daily', 'weekly', 'to'):
        rtype = 'daily'
    date_from = _parse_date(request.args.get('date_from'))
    date_to = _parse_date(request.args.get('date_to'))
    filters, selected = _read_filters(rtype)

    if rtype == 'daily':
        rows = get_daily_inspections(date_from, date_to, limit=300, filters=filters)
    elif rtype == 'weekly':
        rows = get_inspections_history(date_from, date_to, limit=300, filters=filters)
        for r in rows:
            r['form_type_name'] = WEEKLY_FORM_NAMES.get(r.get('form_type'), r.get('form_type'))
    else:
        rows = get_maintenance_history(date_from, date_to, limit=300, filters=filters)

    return render_template('admin/reports.html',
                           admin=g.admin, rtype=rtype, rows=rows,
                           date_from=request.args.get('date_from', ''),
                           date_to=request.args.get('date_to', ''),
                           options=get_filter_options(rtype), selected=selected,
                           scheme=FILTER_SCHEMES[rtype])


@admin_bp.route('/reports/<rtype>/<int:report_id>')
@login_required('can_view_reports')
def report_detail(rtype, report_id):
    if rtype == 'daily':
        report = get_daily_inspection_by_id(report_id)
    elif rtype == 'weekly':
        report = get_inspection_by_id(report_id)
    elif rtype == 'to':
        report = get_maintenance_report_by_id(report_id)
    else:
        abort(404)
    if not report:
        abort(404)

    results = report.get('results') or {}
    photos = results.get('photos') or {}
    if rtype == 'to':
        # У отчетов ТО фото лежат в отдельной JSONB-колонке photos
        photos = report.get('photos') or {}

    # Для ежедневных: собираем проверки (значение + комментарий)
    checks = []
    if rtype == 'daily':
        for key, label in DAILY_CHECKS:
            checks.append({
                'label': label,
                'value': results.get(key, '—'),
                'status': _value_status(results.get(key)),
                'comment': results.get(f'{key}_comment', ''),
                'photos': photos.get(f'{key}_photos', []),
            })

    # Для еженедельных: результаты группами по секциям формы, с подписями полей
    result_groups, leftovers, form_name = None, [], None
    leftover_title = 'Прочее'
    if rtype == 'weekly':
        form_type = report.get('form_type')
        form_name = WEEKLY_FORM_NAMES.get(form_type, form_type)
        result_groups, leftovers = _build_weekly_groups(form_type, results)
        # В Google-форме несопоставленные вопросы — финальный блок «Итог»
        if form_type == 'gsheets':
            leftover_title = 'Итог'

    return render_template('admin/report_detail.html',
                           admin=g.admin, rtype=rtype, report=report,
                           results=results, photos=photos, checks=checks,
                           result_groups=result_groups, leftovers=leftovers,
                           leftover_title=leftover_title, form_name=form_name)


# ============================================================
# Аналитика: пропуски отчётов и поломки
# ============================================================

def _compute_day_coverage(dates, window_days: int, today: date) -> dict:
    """Покрытие ежедневными отчётами за окно (от первого отчёта, но не глубже
    window_days). Возвращает expected/reported/missed_count/missed_recent/pct."""
    if not dates:
        return None
    first = min(dates)
    window_start = max(first, today - timedelta(days=window_days - 1))
    expected = (today - window_start).days + 1
    reported_days = {d for d in dates if d >= window_start}
    all_days = {window_start + timedelta(days=i) for i in range(expected)}
    missed = sorted(all_days - reported_days, reverse=True)
    pct = round(100 * len(reported_days) / expected) if expected else 100
    return {
        'window_start': window_start, 'expected': expected,
        'reported': len(reported_days), 'missed_count': len(missed),
        'missed_recent': missed[:7], 'pct': pct,
        'last_report': max(dates),
    }


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _compute_week_coverage(dates, window_weeks: int, today: date) -> dict:
    """Покрытие еженедельными отчётами: неделя закрыта, если в ней был отчёт."""
    if not dates:
        return None
    first_monday = _monday(min(dates))
    window_start = max(first_monday, _monday(today) - timedelta(weeks=window_weeks - 1))
    reported_weeks = {_monday(d) for d in dates}
    missed, expected = [], 0
    m = window_start
    while m <= today:
        expected += 1
        if m not in reported_weeks:
            missed.append(m)
        m += timedelta(weeks=1)
    missed.sort(reverse=True)
    pct = round(100 * (expected - len(missed)) / expected) if expected else 100
    return {
        'window_start': window_start, 'expected': expected,
        'reported': expected - len(missed), 'missed_count': len(missed),
        'missed_recent': missed[:7], 'pct': pct,
        'last_report': max(dates),
    }


def _coverage_status(pct: int) -> str:
    if pct >= 90:
        return 'good'
    if pct >= 70:
        return 'warn'
    return 'bad'


def _build_missed_rows(rows, kind: str, window: int, today: date) -> list:
    """Строки таблицы пропусков: одна на машину, худшее покрытие сверху."""
    out = []
    for r in rows:
        cov = (_compute_day_coverage(r['dates'], window, today) if kind == 'daily'
               else _compute_week_coverage(r['dates'], window, today))
        if not cov:
            continue
        out.append({
            'machine_model': r['machine_model'],
            'machine_plate': r['machine_plate'],
            'machine_inventory': r['machine_inventory'],
            'total': r['total'],
            'status': _coverage_status(cov['pct']),
            **cov,
        })
    out.sort(key=lambda x: (x['pct'], -x['missed_count']))
    return out


def _fmt_downtime(total_hours: int) -> str:
    days, hours = divmod(int(total_hours), 24)
    if days and hours:
        return f"{days} дн. {hours} ч."
    if days:
        return f"{days} дн."
    return f"{hours} ч."


def _build_breakdown_rows(reports) -> list:
    """Аналитика поломок по машинам с отчётами о ТО."""
    by_machine = {}
    for r in reports:
        key = (r.get('machine_inventory') or '—',
               r.get('machine_model') or 'Неизвестно',
               r.get('machine_plate') or '')
        m = by_machine.setdefault(key, {
            'machine_inventory': key[0], 'machine_model': key[1], 'machine_plate': key[2],
            'total': 0, 'unplanned': 0, 'downtime_hours': 0,
            'last_repair': None, 'last_unplanned': None, 'reasons': [],
        })
        m['total'] += 1
        rd = r.get('to_date') or (r['created_at'].date() if r.get('created_at') else None)
        if rd and (m['last_repair'] is None or rd > m['last_repair']):
            m['last_repair'] = rd
        is_unplanned = 'внеплан' in (r.get('repair_type') or '').lower()
        if is_unplanned:
            m['unplanned'] += 1
            if rd and (m['last_unplanned'] is None or rd > m['last_unplanned']):
                m['last_unplanned'] = rd
        m['downtime_hours'] += (r.get('downtime_days') or 0) * 24 + (r.get('downtime_hours') or 0)
        reason = (r.get('breakdown_reason') or '').strip()
        if reason:
            m['reasons'].append((rd, reason))

    out = []
    for m in by_machine.values():
        m['unplanned_pct'] = round(100 * m['unplanned'] / m['total']) if m['total'] else 0
        m['downtime_str'] = _fmt_downtime(m['downtime_hours'])
        m['reasons'] = [
            {'date': d, 'text': (t[:120] + '…') if len(t) > 120 else t}
            for d, t in sorted(m['reasons'], key=lambda x: (x[0] is None, x[0]), reverse=True)[:3]
        ]
        m['status'] = 'bad' if m['unplanned_pct'] >= 50 and m['unplanned'] >= 2 else (
            'warn' if m['unplanned'] >= 1 else 'good')
        out.append(m)
    out.sort(key=lambda x: (-x['unplanned'], -x['downtime_hours']))
    return out


@admin_bp.route('/analytics')
@login_required('can_view_history')
def analytics():
    tab = request.args.get('tab', 'daily')
    if tab not in ('daily', 'weekly', 'breakdowns'):
        tab = 'daily'
    today = today_local()

    # Схемы фильтров совпадают с историей: breakdowns — это отчёты о ТО
    ftype = 'to' if tab == 'breakdowns' else tab
    filters, selected = _read_filters(ftype)

    rows, window = [], None
    if tab == 'daily':
        window = request.args.get('days', type=int) or 30
        window = window if window in (7, 30, 90) else 30
        rows = _build_missed_rows(get_daily_dates_by_machine(filters), 'daily', window, today)
    elif tab == 'weekly':
        window = request.args.get('weeks', type=int) or 12
        window = window if window in (4, 12, 26) else 12
        rows = _build_missed_rows(get_weekly_dates_by_machine(filters), 'weekly', window, today)
    else:
        rows = _build_breakdown_rows(get_maintenance_for_analytics(filters))

    return render_template('admin/analytics.html',
                           admin=g.admin, tab=tab, rows=rows,
                           window=window, today=today,
                           options=get_filter_options(ftype), selected=selected,
                           scheme=FILTER_SCHEMES[ftype])


# ============================================================
# Управление администраторами (только суперадмин)
# ============================================================

@admin_bp.route('/admins')
@login_required('is_superadmin')
def admins_list():
    return render_template('admin/admins.html',
                           admin=g.admin, admins=get_all_admins(),
                           admin_flags=ADMIN_FLAGS)


@admin_bp.route('/admins/create', methods=['POST'])
@login_required('is_superadmin')
def admins_create():
    _check_csrf()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        flash('Логин и пароль обязательны', 'error')
        return redirect(url_for('admin.admins_list'))
    if get_admin_by_username(username):
        flash(f'Администратор «{username}» уже существует', 'error')
        return redirect(url_for('admin.admins_list'))

    flags = {flag: bool(request.form.get(flag)) for flag, _ in ADMIN_FLAGS}
    new_id = create_admin(
        username=username,
        password_hash=generate_password_hash(password),
        full_name=request.form.get('full_name', '').strip() or None,
        telegram_user_id=request.form.get('telegram_user_id', '').strip() or None,
        **flags,
    )
    flash('Администратор создан' if new_id else 'Ошибка создания администратора',
          'success' if new_id else 'error')
    return redirect(url_for('admin.admins_list'))


@admin_bp.route('/admins/<int:admin_id>/update', methods=['POST'])
@login_required('is_superadmin')
def admins_update(admin_id):
    _check_csrf()
    target = get_admin_by_id(admin_id)
    if not target:
        abort(404)

    fields = {
        'full_name': request.form.get('full_name', '').strip() or None,
        'telegram_user_id': request.form.get('telegram_user_id', '').strip() or None,
    }
    for flag, _ in ADMIN_FLAGS:
        fields[flag] = bool(request.form.get(flag))

    # Нельзя снять права суперадмина/деактивировать самого себя
    if admin_id == g.admin['id']:
        fields['is_superadmin'] = True
        fields['is_active'] = True
    else:
        fields['is_active'] = bool(request.form.get('is_active'))

    new_password = request.form.get('new_password', '')
    if new_password:
        fields['password_hash'] = generate_password_hash(new_password)

    ok = update_admin(admin_id, fields)
    flash('Сохранено' if ok else 'Ошибка сохранения', 'success' if ok else 'error')
    return redirect(url_for('admin.admins_list'))
