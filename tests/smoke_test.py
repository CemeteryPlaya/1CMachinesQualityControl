# -*- coding: utf-8 -*-
"""
Смоук-тесты без БД: конфиги форм, переводы, классификация значений,
группировка результатов, валидация initData, рендер шаблонов.

Запуск из корня проекта:  python tests/smoke_test.py
"""
import os
import sys
import hmac
import json
import hashlib
from datetime import datetime, date
from urllib.parse import urlencode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASSED = 0


def check(name, condition):
    global PASSED
    assert condition, f"FAILED: {name}"
    PASSED += 1
    print(f"  ok: {name}")


def test_form_configs():
    """Все 6 конфигов форм собираются на 4 языках, у всех полей есть label."""
    from importlib import import_module
    modules = ['lv_form_config', 'lv_oa_form_config', 'sv_form_config',
               'sv_oa_form_config', 'to_form_config', 'daily_form_config']
    for m in modules:
        for lang in ('ru', 'en', 'kk', 'uz'):
            cfg = import_module(m).get_form_config(lang)
            check(f"{m}/{lang}: не пустой", len(cfg) > 0)
            for item in cfg:
                # У hidden и repeater подписи нет по конструкции
                if item.get('type') not in ('hidden', 'repeater'):
                    assert item.get('label'), f"{m}/{lang}: {item.get('id')} без label"
    # Ключевые поля ежедневной формы
    ids = [i['id'] for i in import_module('daily_form_config').get_form_config('ru')]
    check("daily: проект+оператор присутствуют",
          'department_uid' in ids and 'driver_uid' in ids and 'mechanic_uid' not in ids)
    # Фото внепланового ремонта в ТО
    to_cfg = import_module('to_form_config').get_form_config('ru')
    ph = next(i for i in to_cfg if i['id'] == 'repair_photos')
    check("to: repair_photos max=10, скрыто", ph['max'] == 10 and ph['initially_hidden'])


def test_translations():
    from translations import get_bot_message, get_webapp_strings, BOT_MESSAGES
    for lang in ('ru', 'en', 'kk', 'uz'):
        for key in ('welcome', 'checklist_daily', 'checklist_weekly',
                    'fill_daily_form_button', 'daily_submission_confirmed',
                    'enter_full_name', 'full_name_saved', 'full_name_invalid'):
            v = get_bot_message(key, lang)
            assert v and v != key, (lang, key)
        ui = get_webapp_strings(lang)
        assert ui['submit_button'] and ui['field_required'] and ui['take_photo']
    check("bot messages: все ключи на 4 языках", True)
    # ru-фолбэк для отсутствующего в языке ключа
    BOT_MESSAGES['en'].pop('_test_key', None)
    BOT_MESSAGES['ru']['_test_key'] = 'значение'
    check("get_bot_message: фолбэк на ru", get_bot_message('_test_key', 'en') == 'значение')
    del BOT_MESSAGES['ru']['_test_key']


def test_value_status():
    from admin_routes import _value_status
    check("Нормальное=good", _value_status('Нормальное') == 'good')
    check("Нормально=good", _value_status('Нормально') == 'good')
    check("Present=good", _value_status('Present') == 'good')
    check("Не нормальное=bad", _value_status('Не нормальное') == 'bad')
    check("Yo'q=bad", _value_status("Yo'q") == 'bad')
    check("Дизель=нейтрально", _value_status('Дизель') is None)
    check("число=нейтрально", _value_status(5) is None)
    check("реверс: Имеется=bad", _value_status('Имеется', reversed_field=True) == 'bad')
    check("реверс: Отсутствует=good", _value_status('Отсутствует', reversed_field=True) == 'good')


def test_weekly_groups():
    from admin_routes import _build_weekly_groups
    results = {'body_state': 'Нормальное', 'body_defects': 'Имеется',
               'hydro_oil_system_leakages': 'Отсутствует', 'legacy_key': 'x'}
    groups, leftovers = _build_weekly_groups('lv', results)
    st = {it['label']: it['status'] for gr in groups for it in gr['items']}
    check("lv: Состояние кузова=good", st.get('Состояние кузова') == 'good')
    check("lv: повреждение реверс=bad", st.get('Какое либо повреждение') == 'bad')
    check("lv: течь реверс=good", st.get('Наличие какой-либо течи в системе') == 'good')
    check("lv: legacy в остатке без подсветки",
          any(l['label'] == 'legacy_key' and l['status'] is None for l in leftovers))

    # gsheets: матчинг по подписи с нормализацией (регистр/пробелы/ё)
    gs = {'состояние  кузова': 'Нормальное', 'Какое либо повреждение': 'Имеется',
          'Итоговая оценка': 'Не нормально'}
    groups2, leftovers2 = _build_weekly_groups('gsheets', gs)
    st2 = {it['label']: it['status'] for gr in groups2 for it in gr['items']}
    check("gsheets: нормализация подписи", st2.get('Состояние кузова') == 'good')
    check("gsheets: реверс работает", st2.get('Какое либо повреждение') == 'bad')
    check("gsheets: Итог подсвечен",
          any(l['label'] == 'Итоговая оценка' and l['status'] == 'bad' for l in leftovers2))

    # Нет конфига — фолбэк
    g3, l3 = _build_weekly_groups('unknown_type', {'a': 'b'})
    check("нет конфига: сырой фолбэк", g3 is None and l3 == {'a': 'b'})


def test_init_data_validation():
    from telegram_auth import validate_init_data, resolve_submit_user
    from bot_instance import BOT_TOKEN

    user = json.dumps({'id': 777, 'first_name': 'T'})
    fields = {'auth_date': '1700000000', 'query_id': 'q', 'user': user}
    dcs = '\n'.join(f'{k}={v}' for k, v in sorted(fields.items()))
    secret = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
    h = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    good = urlencode({**fields, 'hash': h})

    check("валидная подпись принята", validate_init_data(good)['id'] == 777)
    check("подделка отклонена", validate_init_data(good.replace(h, '0' * 64)) is None)
    check("пустой initData отклонён", validate_init_data('') is None)

    data = {'init_data': good, 'telegram_user_id': 'spoofed'}
    ok, _ = resolve_submit_user(data)
    check("resolve: id заменён проверенным", ok and data['telegram_user_id'] == 777)
    check("resolve: init_data удалён из payload", 'init_data' not in data)


def test_templates_render():
    from flask import Flask, render_template
    from app_routes import app_bp
    from admin_routes import admin_bp, ADMIN_FLAGS
    from translations import get_webapp_strings
    from importlib import import_module

    app = Flask(__name__,
                template_folder=os.path.join(ROOT, 'templates'),
                static_folder=os.path.join(ROOT, 'static'))
    app.secret_key = 't'
    app.register_blueprint(app_bp)
    app.register_blueprint(admin_bp)

    # Формы: все 6 типов, ru
    with app.test_request_context('/'):
        for form_type, module in [('lv', 'lv_form_config'), ('sv_oa', 'sv_oa_form_config'),
                                  ('to', 'to_form_config'), ('daily', 'daily_form_config')]:
            html = render_template('index.html', title='T',
                                   questions=import_module(module).get_form_config('ru'),
                                   lang='ru', form_type=form_type,
                                   ui=get_webapp_strings('ru'))
            assert 'inspectionForm' in html
        check("index.html: 4 типа форм рендерятся", True)

    # Админка
    admin = {'id': 1, 'username': 'a', 'full_name': 'Тест', 'telegram_user_id': '1',
             'is_superadmin': True, 'can_view_reports': True, 'can_view_history': True,
             'receive_instant_notifications': True, 'receive_daily_digest': True,
             'is_active': True}
    stats = {'daily': [], 'weekly': [], 'to': [],
             'daily_total': 0, 'weekly_total': 0, 'to_total': 0}
    from database import FILTER_SCHEMES
    options = {'machines': [{'machine_inventory': '01', 'machine_model': 'КамАЗ',
                             'machine_plate': 'A1'}],
               'senders': ['Тестов Тест'], 'persons': ['Иванов'], 'projects': ['Проект А']}
    selected = {'machine': '', 'sender': '', 'person': '', 'project': ''}
    with app.test_request_context('/admin/'):
        render_template('admin/login.html')
        render_template('admin/dashboard.html', admin=admin, stats=stats,
                        today=date.today(), latest_daily=[])
        render_template('admin/admins.html', admin=admin, admins=[admin],
                        admin_flags=ADMIN_FLAGS)
        html = render_template('admin/reports.html', admin=admin, rtype='daily',
                               rows=[], date_from='', date_to='',
                               options=options, selected=selected,
                               scheme=FILTER_SCHEMES['daily'])
        check("шаблоны админки рендерятся", 'История' in html)
        check("фильтры в истории: машина/отправитель/оператор/проект",
              'КамАЗ' in html and 'Тестов Тест' in html and
              'Оператор' in html and 'Проект' in html)
        html_a = render_template('admin/analytics.html', admin=admin, tab='breakdowns',
                                 rows=[], window=None, today=date.today(),
                                 options=options, selected=selected,
                                 scheme=FILTER_SCHEMES['to'])
        check("фильтры в аналитике поломок", 'Ответственный' in html_a and 'Подразделение' in html_a)

    # CSRF-токен присутствует в формах админов
    with app.test_request_context('/admin/admins'):
        html = render_template('admin/admins.html', admin=admin, admins=[admin],
                               admin_flags=ADMIN_FLAGS)
        check("CSRF-токен в формах", '_csrf' in html)


def test_full_name_validation():
    from bot_handlers import _is_valid_full_name
    check("Иванов Иван — валидно", _is_valid_full_name('Иванов Иван'))
    check("Иванов Иван Иванович — валидно", _is_valid_full_name('Иванов Иван Иванович'))
    check("O'rinboyev Anvar — валидно (апостроф)", _is_valid_full_name("O'rinboyev Anvar"))
    check("Мамедов-оглы Али — валидно (дефис)", _is_valid_full_name('Мамедов-оглы Али'))
    check("одно слово — невалидно", not _is_valid_full_name('Иванов'))
    check("кнопка с эмодзи — невалидно", not _is_valid_full_name('🔄 Изменить язык'))
    check("команда — невалидно", not _is_valid_full_name('/start test'))
    check("цифры — невалидно", not _is_valid_full_name('Иванов 123'))
    check("пусто — невалидно", not _is_valid_full_name(''))


def test_analytics_computations():
    from datetime import timedelta
    from admin_routes import (_compute_day_coverage, _compute_week_coverage,
                              _build_breakdown_rows, _fmt_downtime, _coverage_status)
    today = date(2026, 7, 2)  # четверг

    # Ежедневное покрытие: отчёты 3 дня из последних 5, первый отчёт 5 дней назад
    dates = [today, today - timedelta(days=2), today - timedelta(days=4)]
    cov = _compute_day_coverage(dates, 30, today)
    check("день: окно от первого отчета", cov['window_start'] == today - timedelta(days=4))
    check("день: 3 из 5", cov['reported'] == 3 and cov['expected'] == 5)
    check("день: 2 пропуска", cov['missed_count'] == 2)
    check("день: pct=60", cov['pct'] == 60)
    check("день: пропуски свежие сверху", cov['missed_recent'][0] == today - timedelta(days=1))

    # Окно ограничивает глубину
    old = [today - timedelta(days=100), today]
    cov2 = _compute_day_coverage(old, 7, today)
    check("день: окно 7 дней", cov2['expected'] == 7 and cov2['reported'] == 1)

    # Недельное покрытие: отчёты в этой неделе и 2 недели назад → пропущена 1 неделя
    wdates = [today, today - timedelta(weeks=2)]
    wcov = _compute_week_coverage(wdates, 12, today)
    check("неделя: 2 из 3", wcov['reported'] == 2 and wcov['expected'] == 3)
    check("неделя: 1 пропуск", wcov['missed_count'] == 1)

    check("статусы покрытия", _coverage_status(95) == 'good' and
          _coverage_status(75) == 'warn' and _coverage_status(50) == 'bad')
    check("формат простоя", _fmt_downtime(50) == '2 дн. 2 ч.' and _fmt_downtime(24) == '1 дн.'
          and _fmt_downtime(5) == '5 ч.')

    # Поломки: 2 внеплановых из 3 → status bad, простой суммируется
    reports = [
        {'machine_inventory': '01', 'machine_model': 'JCB', 'machine_plate': 'A1',
         'repair_type': 'Внеплановый ремонт', 'breakdown_reason': 'Потекла гидравлика',
         'downtime_days': 1, 'downtime_hours': 4, 'to_date': date(2026, 6, 1),
         'created_at': datetime(2026, 6, 1)},
        {'machine_inventory': '01', 'machine_model': 'JCB', 'machine_plate': 'A1',
         'repair_type': 'внеплановый', 'breakdown_reason': 'Сломался стартер',
         'downtime_days': 0, 'downtime_hours': 6, 'to_date': date(2026, 6, 20),
         'created_at': datetime(2026, 6, 20)},
        {'machine_inventory': '01', 'machine_model': 'JCB', 'machine_plate': 'A1',
         'repair_type': 'Плановый', 'breakdown_reason': None,
         'downtime_days': 0, 'downtime_hours': 2, 'to_date': date(2026, 5, 1),
         'created_at': datetime(2026, 5, 1)},
    ]
    rows = _build_breakdown_rows(reports)
    r = rows[0]
    check("поломки: 3 ремонта, 2 внеплановых", r['total'] == 3 and r['unplanned'] == 2)
    check("поломки: доля 67%", r['unplanned_pct'] == 67)
    check("поломки: простой 36ч = 1 дн. 12 ч.", r['downtime_str'] == '1 дн. 12 ч.')
    check("поломки: статус bad", r['status'] == 'bad')
    check("поломки: свежая причина первой", r['reasons'][0]['text'] == 'Сломался стартер')
    check("поломки: последний внеплановый", r['last_unplanned'] == date(2026, 6, 20))


def test_filters_sql():
    from database import _filters_sql, FILTER_SCHEMES
    sql, params = _filters_sql({'machine_inventory': '01', 'sender_name': 'Тестов'})
    check("фильтры: SQL с двумя условиями",
          sql == ' AND machine_inventory = %s AND sender_name = %s' and params == ['01', 'Тестов'])
    sql2, params2 = _filters_sql({'project': ''})
    check("фильтры: пустые значения игнорируются", sql2 == '' and params2 == [])
    sql3, params3 = _filters_sql(None)
    check("фильтры: None безопасен", sql3 == '' and params3 == [])
    check("схемы фильтров: 3 типа с ролями",
          set(FILTER_SCHEMES) == {'daily', 'weekly', 'to'} and
          all('person_label' in s and 'machine' in s for s in FILTER_SCHEMES.values()))


def test_timezone():
    from datetime import timezone as dt_tz, timedelta
    from time_utils import now_local, today_local, APP_TZ, PG_TIMEZONE
    n = now_local()
    check("now_local: aware datetime", n.tzinfo is not None)
    offset = n.utcoffset()
    check("UTC+5 по умолчанию (Asia/Tashkent)", offset == timedelta(hours=5))
    check("today_local согласован с now_local", today_local() == n.date())
    check("PG_TIMEZONE задан при валидной зоне",
          PG_TIMEZONE == 'Asia/Tashkent' or PG_TIMEZONE is None)


def test_notifications():
    from notifications import REPORT_TYPE_NAMES, _parse_digest_time
    check("типы отчетов для уведомлений", set(REPORT_TYPE_NAMES) == {'daily', 'weekly', 'to'})
    check("парсинг времени сводки", _parse_digest_time()[0] in range(24))


if __name__ == '__main__':
    tests = [test_form_configs, test_translations, test_value_status,
             test_weekly_groups, test_init_data_validation,
             test_templates_render, test_full_name_validation,
             test_analytics_computations, test_filters_sql, test_timezone,
             test_notifications]
    for t in tests:
        print(f"\n== {t.__name__} ==")
        t()
    print(f"\nALL SMOKE TESTS PASSED ({PASSED} checks)")
