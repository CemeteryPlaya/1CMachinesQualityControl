import os
import json
import uuid
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from importlib import import_module
from datetime import datetime
import odata_service
from database import (get_machine_by_id, get_all_machines, get_machines_by_category,
                       get_employee_by_id, get_all_employees,
                       get_employees_by_position, get_department_by_id,
                       get_all_departments, save_inspection,
                       save_inspection_from_sheets, save_maintenance_report,
                       save_mileage_record, get_last_mileage, get_mileage_history,
                       save_daily_inspection, add_daily_inspection_photos,
                       add_maintenance_photos, enqueue_1c_task, get_bot_user)
from notifications import notify_admins_new_report
from telegram_auth import resolve_submit_user
from time_utils import now_local
import sync_worker
import logging
import threading
import requests
from bot_instance import BOT_TOKEN
from translations import get_bot_message, get_webapp_strings

app_bp = Blueprint('app', __name__)
logger = logging.getLogger(__name__)

FORM_CONFIG_MODULES = {
    "lv": "lv_form_config",
    "lv_oa": "lv_oa_form_config",
    "sv": "sv_form_config",
    "sv_oa": "sv_oa_form_config",
    "to": "to_form_config",
    "daily": "daily_form_config",
}

# Базовая директория для фото ежедневных чек-листов.
# В Docker рабочая директория /app, том смонтирован в /app/data.
PHOTO_BASE = os.getenv("PHOTO_STORAGE_DIR", os.path.join(os.getcwd(), "data", "photos"))

# Поля-фотоблоки ежедневной формы: id -> макс. число фото
DAILY_PHOTO_FIELDS = {
    "general_photos": 5,
    "engine_oil_photos": 3,
    "antifreeze_photos": 3,
    "air_filter_photos": 3,
}

ALLOWED_PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def _attach_sender(data: dict) -> None:
    """Дописывает Ф.И.О отправителя (из регистрации в боте) к данным отчёта.

    telegram_user_id к этому моменту уже проверен по подписи initData.
    """
    tg_id = data.get('telegram_user_id')
    if not tg_id:
        return
    user = get_bot_user(str(tg_id))
    if user:
        data['sender_name'] = user['full_name']

FORM_TITLES = {
    "lv": {
        "ru": "Чек-лист инспекции легкового транспорта",
        "en": "Passenger Vehicle Inspection Checklist",
        "kk": "Жеңіл көлікті тексеру тізімі",
        "uz": "Yengil avtomobil tekshiruv ro'yxati"
    },
    "lv_oa": {
        "ru": "Чек-лист инспекции легкового транспорта (выезд)",
        "en": "Passenger Vehicle Inspection Checklist (off-site)",
        "kk": "Жеңіл көлікті тексеру тізімі (шығу)",
        "uz": "Yengil avtomobil tekshiruv ro'yxati (tashqarida)"
    },
    "sv": {
        "ru": "Чек-лист инспекции спецтехники",
        "en": "Special Equipment Inspection Checklist",
        "kk": "Арнайы техниканы тексеру тізімі",
        "uz": "Maxsus texnika tekshiruv ro'yxati"
    },
    "sv_oa": {
        "ru": "Чек-лист инспекции спецтехники (выезд)",
        "en": "Special Equipment Inspection Checklist (off-site)",
        "kk": "Арнайы техниканы тексеру тізімі (шығу)",
        "uz": "Maxsus texnika tekshiruv ro'yxati (tashqarida)"
    },
    "to": {
        "ru": "Отчет о проведенном ТО",
        "en": "Maintenance Report",
        "kk": "ТҚ есебі",
        "uz": "TO hisoboti"
    },
    "daily": {
        "ru": "Ежедневный чек-лист",
        "en": "Daily Checklist",
        "kk": "Күнделікті тексеру тізімі",
        "uz": "Kunlik tekshiruv ro'yxati"
    },
}

@app_bp.route('/')
def index():
    """Renders the inspection form with language support."""
    # Получаем язык из параметров URL, по умолчанию русский
    lang = request.args.get('lang', 'ru')

    # Валидируем язык
    if lang not in ['ru', 'en', 'kk', 'uz']:
        lang = 'ru'

    # Получаем тип формы из параметров URL
    form_type = request.args.get('form_type', 'lv')
    if form_type not in FORM_CONFIG_MODULES:
        form_type = 'lv'

    # Динамически загружаем нужный модуль конфигурации
    module_name = FORM_CONFIG_MODULES[form_type]
    config_module = import_module(module_name)
    form_config = config_module.get_form_config(lang)

    # Заголовки в зависимости от типа формы и языка
    titles = FORM_TITLES.get(form_type, FORM_TITLES["lv"])

    return render_template('index.html',
                           title=titles.get(lang, titles['ru']),
                           questions=form_config,
                           lang=lang,
                           form_type=form_type,
                           ui=get_webapp_strings(lang))

@app_bp.route('/api/machines', methods=['GET'])
def get_machines():
    """Returns list of machines from 1C (or local DB fallback).
    Query params:
        category: 'lv', 'sv', or 'all' (default 'all')
    """
    try:
        # Trigger sync/fetch
        odata_service.sync_machines()
        category = request.args.get('category', 'all')
        if category not in ('lv', 'sv', 'all'):
            category = 'all'
        machines = get_machines_by_category(category)
        return jsonify(machines)
    except Exception as e:
        logger.error(f"Error in /api/machines: {e}")
        return jsonify({"error": str(e)}), 500

@app_bp.route('/submit', methods=['POST'])
def submit_form():
    """Handles form submission."""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data received"}), 400

        # Аутентификация: telegram_user_id из подписанного initData
        ok, auth_error = resolve_submit_user(data)
        if not ok:
            return jsonify({"success": False, "error": auth_error}), 403
        _attach_sender(data)

        # 1. Добавляем отметку времени (как в Google Forms)
        data['timestamp'] = now_local().strftime("%d.%m.%Y %H:%M:%S")

        inspection_date = data.get('inspection_date')
        if inspection_date:
            try:
                date_obj = datetime.strptime(inspection_date, '%Y-%m-%d')
                data['inspection_date'] = date_obj.strftime('%d.%m.%Y')
            except ValueError:
                pass

        insurance_end_date = data.get('insurance_end_date')
        if insurance_end_date:
            try:
                date_obj = datetime.strptime(insurance_end_date, '%Y-%m-%d')
                data['insurance_end_date'] = date_obj.strftime('%d.%m.%Y')
            except ValueError:
                pass

        technical_inspection_date = data.get('technical_inspection_date')
        if technical_inspection_date:
            try:
                date_obj = datetime.strptime(technical_inspection_date, '%Y-%m-%d')
                data['technical_inspection_date'] = date_obj.strftime('%d.%m.%Y')
            except ValueError:
                pass

        # Обработка одометра: пустые поля заменяем на 0
        for odometer_field in ('motorhours', 'mileage'):
            if not data.get(odometer_field):
                data[odometer_field] = '0'

        # Обработка подразделения
        department_uid = data.get('department_uid')
        if department_uid:
            department = get_department_by_id(department_uid)
            if department:
                data['department_uid'] = department['name']
                data['department_ref_key'] = department.get('ref_key')
            else:
                logger.warning(f"Department with ID {department_uid} not found")

        # Обработка водителя
        driver_uid = data.get('driver_uid')
        if driver_uid:
            driver = get_employee_by_id(driver_uid)
            if driver:
                data['driver_uid'] = driver['full_name']
                data['driver_name'] = driver['full_name']
                data['driver_ref_key'] = driver.get('ref_key')
            else:
                logger.warning(f"Driver with ID {driver_uid} not found")

        # Обработка механика
        mechanic_uid = data.get('mechanic_uid')
        if mechanic_uid:
            mechanic = get_employee_by_id(mechanic_uid)
            if mechanic:
                data['mechanic_uid'] = mechanic['full_name']
                data['mechanic_name'] = mechanic['full_name']
                data['mechanic_ref_key'] = mechanic.get('ref_key')
            else:
                logger.warning(f"Mechanic with ID {mechanic_uid} not found")

        # Обработка машины
        machine_uid = data.get('machine_uid')
        if not machine_uid:
             return jsonify({"success": False, "error": "machine_uid is missing"}), 400

        machine = get_machine_by_id(machine_uid)
        if not machine:
            return jsonify({"success": False, "error": "Machine not found"}), 404

        plate = machine['license_plate'] if machine['license_plate'] else 'Нет ГРНЗ'
        formatted_machine = f"Модель: {machine['model']} | ГРНЗ: {plate} | ИН: {machine['inventory_number']}"

        data['machine_uid'] = formatted_machine
        data['machine_inv'] = machine['inventory_number']
        data['model'] = machine['model']
        data['license_plate'] = machine['license_plate']
        data['machine_ref_key'] = machine.get('ref_key')

        # 4. Сохраняем в PostgreSQL
        inspection_id = save_inspection(data)
        if not inspection_id:
            logger.error("Failed to save inspection to PostgreSQL!")
            return jsonify({"success": False, "error": "Failed to save to database"}), 500

        logger.info(f"Inspection saved to PostgreSQL with id={inspection_id}")

        # Push-уведомления админам
        notify_admins_new_report('weekly', inspection_id, {
            'sender': data.get('sender_name') or data.get('driver_name') or data.get('mechanic_name'),
            'telegram_user_id': data.get('telegram_user_id'),
            'machine': data.get('machine_uid'),
            'project': data.get('department_uid'),
        })

        # 4.5. Сохраняем пробег в историю
        mileage_val = int(data.get('mileage', 0) or 0)
        motorhours_val = int(data.get('motorhours', 0) or 0)
        if mileage_val > 0 or motorhours_val > 0:
            save_mileage_record(
                machine_id=machine['id'],
                mileage=mileage_val,
                motorhours=motorhours_val,
                source='checklist'
            )

        # 5. Ставим выгрузку в 1С в надёжную очередь (ретраи в sync_worker)
        machine_ref = machine.get('ref_key')
        machine_vtype = machine.get('vehicle_type', 'lv')

        enqueue_1c_task('checklist', inspection_id, dict(data))
        if machine_ref and (mileage_val > 0 or motorhours_val > 0):
            enqueue_1c_task('mileage', inspection_id, {
                'machine_ref_key': machine_ref,
                'mileage': mileage_val,
                'motorhours': motorhours_val,
                'source': 'checklist',
                'vehicle_type': machine_vtype,
            })
        sync_worker.poke()

        # 6. Отправляем подтверждение в Telegram
        telegram_user_id = data.get('telegram_user_id')
        lang = data.get('lang', 'ru')

        if telegram_user_id:
            submission_time = data.get('timestamp', now_local().strftime("%d.%m.%Y %H:%M:%S"))
            confirmation_text = get_bot_message('submission_confirmed', lang).format(datetime=submission_time)

            def send_message_sync():
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": telegram_user_id, "text": confirmation_text}
                    response = requests.post(url, json=payload, timeout=10)
                    response.raise_for_status()
                    logger.info(f"Confirmation sent to user {telegram_user_id}")
                except Exception as e:
                    logger.error(f"Failed to send confirmation to {telegram_user_id}: {e}")

            threading.Thread(target=send_message_sync, daemon=True).start()

        return jsonify({"success": True, "id": inspection_id})

    except Exception as e:
        logger.error(f"Error in /submit: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app_bp.route('/api/get_machines_form', methods=['GET'])
def get_machines_for_google():
    machines = get_all_machines() # function from database.py
    # Form list of strings
    return jsonify([
        f"Модель: {m['model']} | ГРНЗ: {m['license_plate']} | ИН: {m['inventory_number']}"
        for m in machines
    ])

@app_bp.route('/api/drivers', methods=['GET'])
def get_drivers():
    """Returns list of drivers from 1C (or local DB fallback)."""
    try:
        # Trigger sync/fetch for all employees
        odata_service.sync_employees()
        # Get only drivers
        drivers = get_employees_by_position('DRIVER')
        return jsonify(drivers)
    except Exception as e:
        logger.error(f"Error in /api/drivers: {e}")
        return jsonify({"error": str(e)}), 500

@app_bp.route('/api/mechanics', methods=['GET'])
def get_mechanics():
    """Returns list of mechanics from 1C (or local DB fallback)."""
    try:
        # Trigger sync/fetch for all employees
        odata_service.sync_employees()
        # Get only mechanics
        mechanics = get_employees_by_position('MECHANIC')
        return jsonify(mechanics)
    except Exception as e:
        logger.error(f"Error in /api/mechanics: {e}")
        return jsonify({"error": str(e)}), 500

@app_bp.route('/submit_to', methods=['POST'])
def submit_to_form():
    """Handles maintenance report (TO) submission.

    Принимает JSON (без фото) или multipart (payload + фото поломки/запчастей
    при внеплановом ремонте).
    """
    try:
        if request.is_json:
            data = request.json
        else:
            raw_payload = request.form.get('payload')
            data = json.loads(raw_payload) if raw_payload else None
        if not data:
            return jsonify({"success": False, "error": "No data received"}), 400

        # Аутентификация: telegram_user_id из подписанного initData
        ok, auth_error = resolve_submit_user(data)
        if not ok:
            return jsonify({"success": False, "error": auth_error}), 403
        _attach_sender(data)

        data['timestamp'] = now_local().strftime("%d.%m.%Y %H:%M:%S")

        # Конвертируем даты
        for date_field in ('to_date', 'repair_start_date', 'repair_end_date'):
            raw = data.get(date_field)
            if raw:
                try:
                    date_obj = datetime.strptime(raw, '%Y-%m-%d')
                    data[date_field] = date_obj.strftime('%d.%m.%Y')
                except ValueError:
                    pass

        # Обработка подразделения
        department_uid = data.get('department_uid')
        if department_uid:
            department = get_department_by_id(department_uid)
            if department:
                data['department_uid'] = department['name']
                data['department_ref_key'] = department.get('ref_key')
                logger.info(f"TO department resolved: {department['name']}, ref_key={department.get('ref_key')}")
            else:
                logger.warning(f"TO department with ID {department_uid} not found in DB")
        else:
            logger.warning("TO department_uid is empty in submitted data")

        # Обработка машины
        machine_uid = data.get('machine_uid')
        if not machine_uid:
            return jsonify({"success": False, "error": "machine_uid is missing"}), 400

        machine = get_machine_by_id(machine_uid)
        if not machine:
            return jsonify({"success": False, "error": "Machine not found"}), 404

        plate = machine['license_plate'] if machine['license_plate'] else 'Нет ГРНЗ'
        data['machine_uid'] = f"Модель: {machine['model']} | ГРНЗ: {plate} | ИН: {machine['inventory_number']}"
        data['machine_inv'] = machine['inventory_number']
        data['model'] = machine['model']
        data['license_plate'] = machine['license_plate']
        data['machine_ref_key'] = machine.get('ref_key')

        # Обработка ответственного лица
        responsible_uid = data.get('responsible_person_uid')
        if responsible_uid:
            person = get_employee_by_id(responsible_uid)
            if person:
                data['responsible_person_name'] = person['full_name']
                data['responsible_person_ref_key'] = person.get('ref_key')

        # Обработка вида ремонта
        from database import get_repair_type_by_id
        repair_type_uid = data.get('repair_type_uid')
        if repair_type_uid:
            repair_type = get_repair_type_by_id(repair_type_uid)
            if repair_type:
                data['repair_type_name'] = repair_type['name']
                data['repair_type_ref_key'] = repair_type.get('ref_key')

        # Разрешаем nomenclature_uid -> ref_key в materials_table
        from database import get_all_nomenclature, get_all_measurement_units
        nom_cache = {str(n['id']): n for n in get_all_nomenclature()}
        unit_cache = {str(u['id']): u for u in get_all_measurement_units()}

        materials = data.get('materials_table', [])
        for row in materials:
            nom_id = row.get('nomenclature_uid')
            if nom_id and str(nom_id) in nom_cache:
                nom = nom_cache[str(nom_id)]
                row['nomenclature_uid'] = nom.get('ref_key', '')
                row['nomenclature_name'] = nom.get('name', '')
            unit_id = row.get('unit_uid')
            if unit_id and str(unit_id) in unit_cache:
                unit = unit_cache[str(unit_id)]
                row['unit_uid'] = unit.get('ref_key', '')
                row['unit_name'] = unit.get('name', '')

        # Разрешаем performer_uid -> ref_key в works_table
        emp_cache = {str(e['id']): e for e in get_all_employees()}
        works = data.get('works_table', [])
        for row in works:
            perf_id = row.get('performer_uid')
            if perf_id and str(perf_id) in emp_cache:
                emp = emp_cache[str(perf_id)]
                row['performer_uid'] = emp.get('ref_key', '')
                row['performer_name'] = emp.get('full_name', '')

        # Сохраняем пробег в историю (из формы ТО)
        to_mileage = int(data.get('to_mileage', 0) or 0)
        to_motorhours = int(data.get('to_motorhours', 0) or 0)
        if to_mileage > 0 or to_motorhours > 0:
            save_mileage_record(
                machine_id=machine['id'],
                mileage=to_mileage,
                motorhours=to_motorhours,
                source='maintenance_report'
            )

        # Сохраняем в PostgreSQL
        report_id = save_maintenance_report(data)
        if not report_id:
            return jsonify({"success": False, "error": "Failed to save to database"}), 500

        logger.info(f"Maintenance report saved with id={report_id}")

        # Фото поломки/запчастей (multipart, внеплановый ремонт)
        if not request.is_json:
            try:
                photo_map = _save_uploaded_photos(report_id, {'repair_photos': 10}, 'to')
                if photo_map:
                    add_maintenance_photos(report_id, photo_map)
            except Exception as e:
                logger.error(f"Failed to save repair photos for report {report_id}: {e}")

        # Push-уведомления админам
        notify_admins_new_report('to', report_id, {
            'sender': data.get('sender_name') or data.get('responsible_person_name'),
            'telegram_user_id': data.get('telegram_user_id'),
            'machine': data.get('machine_uid'),
            'project': data.get('department_uid'),
        })

        # Ставим выгрузку в 1С в надёжную очередь (ретраи в sync_worker)
        machine_ref = machine.get('ref_key')
        machine_vtype = machine.get('vehicle_type', 'lv')

        enqueue_1c_task('to_report', report_id, dict(data))
        if machine_ref and (to_mileage > 0 or to_motorhours > 0):
            enqueue_1c_task('mileage', report_id, {
                'machine_ref_key': machine_ref,
                'mileage': to_mileage,
                'motorhours': to_motorhours,
                'source': 'maintenance_report',
                'vehicle_type': machine_vtype,
            })
        sync_worker.poke()

        # Отправляем подтверждение в Telegram
        telegram_user_id = data.get('telegram_user_id')
        lang = data.get('lang', 'ru')

        if telegram_user_id:
            submission_time = data.get('timestamp', now_local().strftime("%d.%m.%Y %H:%M:%S"))
            confirmation_text = get_bot_message('to_submission_confirmed', lang).format(datetime=submission_time)

            def send_message_sync():
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": telegram_user_id, "text": confirmation_text}
                    response = requests.post(url, json=payload, timeout=10)
                    response.raise_for_status()
                    logger.info(f"TO confirmation sent to user {telegram_user_id}")
                except Exception as e:
                    logger.error(f"Failed to send TO confirmation to {telegram_user_id}: {e}")

            threading.Thread(target=send_message_sync, daemon=True).start()

        return jsonify({"success": True, "id": report_id})

    except Exception as e:
        logger.error(f"Error in /submit_to: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app_bp.route('/api/repair_types', methods=['GET'])
def get_repair_types():
    """Returns list of repair types from 1C (or local DB fallback)."""
    try:
        odata_service.sync_repair_types()
        from database import get_all_repair_types
        repair_types = get_all_repair_types()
        return jsonify(repair_types)
    except Exception as e:
        logger.error(f"Error in /api/repair_types: {e}")
        return jsonify({"error": str(e)}), 500


@app_bp.route('/api/nomenclature', methods=['GET'])
def get_nomenclature():
    """Returns list of nomenclature items from 'Автозапчасти' folder."""
    try:
        odata_service.sync_nomenclature()
        from database import get_nomenclature_by_parent
        parent_key = os.getenv("NOMENCLATURE_PARENT_REF_KEY", "cb3fc03e-bd9e-11ed-8fff-000c291c0350")
        items = get_nomenclature_by_parent(parent_key)
        return jsonify(items)
    except Exception as e:
        logger.error(f"Error in /api/nomenclature: {e}")
        return jsonify({"error": str(e)}), 500


@app_bp.route('/api/measurement_units', methods=['GET'])
def get_measurement_units():
    """Returns list of measurement units from 1C."""
    try:
        odata_service.sync_measurement_units()
        from database import get_all_measurement_units
        units = get_all_measurement_units()
        return jsonify(units)
    except Exception as e:
        logger.error(f"Error in /api/measurement_units: {e}")
        return jsonify({"error": str(e)}), 500


@app_bp.route('/api/departments', methods=['GET'])
def get_departments():
    """Returns list of departments from 1C (or local DB fallback)."""
    try:
        # Trigger sync/fetch for departments
        odata_service.sync_departments()
        # Get all departments
        departments = get_all_departments()
        return jsonify(departments)
    except Exception as e:
        logger.error(f"Error in /api/departments: {e}")
        return jsonify({"error": str(e)}), 500


@app_bp.route('/api/last_mileage/<int:machine_id>', methods=['GET'])
def api_last_mileage(machine_id):
    """Returns the last mileage record for a machine."""
    try:
        record = get_last_mileage(machine_id)
        if record:
            return jsonify(record)
        return jsonify({"mileage": 0, "motorhours": 0})
    except Exception as e:
        logger.error(f"Error in /api/last_mileage/{machine_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app_bp.route('/api/mileage_history/<int:machine_id>', methods=['GET'])
def api_mileage_history(machine_id):
    """Returns mileage history for a machine (for chart)."""
    try:
        records = get_mileage_history(machine_id)
        # Serialize datetime for JSON
        for r in records:
            if r.get('recorded_at'):
                r['recorded_at'] = r['recorded_at'].isoformat()
        return jsonify(records)
    except Exception as e:
        logger.error(f"Error in /api/mileage_history/{machine_id}: {e}")
        return jsonify({"error": str(e)}), 500


GSHEETS_API_KEY = os.getenv("GSHEETS_API_KEY", "")


@app_bp.route('/api/inspection', methods=['POST'])
def receive_inspection_from_sheets():
    """Принимает данные инспекции из Google Apps Script и сохраняет в PostgreSQL."""
    try:
        # Проверка API-ключа
        api_key = request.headers.get('X-API-Key', '')
        if not GSHEETS_API_KEY or api_key != GSHEETS_API_KEY:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data received"}), 400

        inspection_id = save_inspection_from_sheets(data)
        if inspection_id:
            logger.info(f"Sheets inspection saved to PostgreSQL with id={inspection_id}")
            return jsonify({"success": True, "id": inspection_id})
        else:
            return jsonify({"success": False, "error": "Failed to save"}), 500

    except Exception as e:
        logger.error(f"Error in /api/inspection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def _reverse_geocode(lat, lon) -> str:
    """Обратное геокодирование координат в адрес через OpenStreetMap Nominatim.

    Возвращает строку адреса или None при ошибке (не блокирует отправку).
    """
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "jsonv2", "accept-language": "ru"},
            headers={"User-Agent": "MachineQualityControlBot/1.0"},
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json().get("display_name")
    except Exception as e:
        logger.warning(f"Reverse geocode failed for ({lat},{lon}): {e}")
        return None


def _save_uploaded_photos(record_id: int, fields_map: dict, subdir: str) -> dict:
    """Сохраняет фото из multipart-запроса на диск.

    fields_map — {field_id: max_count}; файлы кладутся в
    PHOTO_BASE/<subdir>/<record_id>/<field>_<n><ext>.
    Возвращает {field_id: [относительный_путь, ...]} для записи в БД
    (пути используются маршрутом /photos).
    """
    photo_map = {}
    target_dir = os.path.join(PHOTO_BASE, subdir, str(record_id))

    for field_id, max_count in fields_map.items():
        files = request.files.getlist(field_id)
        if not files:
            continue
        saved_paths = []
        for index, file in enumerate(files):
            if index >= max_count:
                break
            if not file or not file.filename:
                continue
            ext = os.path.splitext(secure_filename(file.filename))[1].lower()
            if ext not in ALLOWED_PHOTO_EXT:
                ext = ".jpg"
            os.makedirs(target_dir, exist_ok=True)
            filename = f"{field_id}_{index + 1}{ext}"
            file.save(os.path.join(target_dir, filename))
            saved_paths.append(f"{subdir}/{record_id}/{filename}")
        if saved_paths:
            photo_map[field_id] = saved_paths

    return photo_map


def _save_daily_photos(inspection_id: int) -> dict:
    return _save_uploaded_photos(inspection_id, DAILY_PHOTO_FIELDS, "daily")


@app_bp.route('/submit_daily', methods=['POST'])
def submit_daily_form():
    """Обрабатывает отправку ежедневного чек-листа (multipart: поля + фото).

    Сохраняет только в PostgreSQL (без выгрузки в 1С). Фото — файлами на диск.
    """
    try:
        raw_payload = request.form.get('payload')
        if not raw_payload:
            return jsonify({"success": False, "error": "No payload received"}), 400

        data = json.loads(raw_payload)

        # Аутентификация: telegram_user_id из подписанного initData
        ok, auth_error = resolve_submit_user(data)
        if not ok:
            return jsonify({"success": False, "error": auth_error}), 403
        _attach_sender(data)

        data['form_type'] = 'daily'
        data['timestamp'] = now_local().strftime("%d.%m.%Y %H:%M:%S")

        # Нормализуем дату инспекции
        inspection_date = data.get('inspection_date')
        if inspection_date:
            try:
                date_obj = datetime.strptime(inspection_date, '%Y-%m-%d')
                data['inspection_date'] = date_obj.strftime('%d.%m.%Y')
            except ValueError:
                pass

        # Моточасы: пустое поле -> 0; пробега в ежедневной форме нет
        if not data.get('motorhours'):
            data['motorhours'] = '0'
        data.setdefault('mileage', '0')

        # Обработка проекта (Подразделение 1С)
        department_uid = data.get('department_uid')
        if department_uid:
            department = get_department_by_id(department_uid)
            if department:
                data['department_uid'] = department['name']
                data['department_ref_key'] = department.get('ref_key')
            else:
                logger.warning(f"Daily: department (project) with ID {department_uid} not found")

        # Обработка оператора (справочник водителей 1С)
        driver_uid = data.get('driver_uid')
        if driver_uid:
            driver = get_employee_by_id(driver_uid)
            if driver:
                data['driver_uid'] = driver['full_name']
                data['driver_name'] = driver['full_name']
                data['driver_ref_key'] = driver.get('ref_key')
            else:
                logger.warning(f"Daily: operator (driver) with ID {driver_uid} not found")

        # Время отправки отчёта респондентом (помимо колонки created_at)
        data['submitted_at'] = data['timestamp']

        # Обработка машины
        machine_uid = data.get('machine_uid')
        if not machine_uid:
            return jsonify({"success": False, "error": "machine_uid is missing"}), 400

        machine = get_machine_by_id(machine_uid)
        if not machine:
            return jsonify({"success": False, "error": "Machine not found"}), 404

        plate = machine['license_plate'] if machine['license_plate'] else 'Нет ГРНЗ'
        data['machine_uid'] = f"Модель: {machine['model']} | ГРНЗ: {plate} | ИН: {machine['inventory_number']}"
        data['machine_inv'] = machine['inventory_number']
        data['model'] = machine['model']
        data['license_plate'] = machine['license_plate']
        data['machine_ref_key'] = machine.get('ref_key')

        # Сохраняем в PostgreSQL (отдельная таблица daily_inspections)
        inspection_id = save_daily_inspection(data)
        if not inspection_id:
            logger.error("Failed to save daily inspection to PostgreSQL!")
            return jsonify({"success": False, "error": "Failed to save to database"}), 500

        logger.info(f"Daily inspection saved to PostgreSQL with id={inspection_id}")

        # Обратное геокодирование адреса — в фоне, не задерживает ответ
        lat, lon = data.get('geo_latitude'), data.get('geo_longitude')
        if lat and lon:
            def geocode_bg(daily_id=inspection_id, glat=lat, glon=lon):
                address = _reverse_geocode(glat, glon)
                if address:
                    from database import update_daily_geo_address
                    update_daily_geo_address(daily_id, address)
            threading.Thread(target=geocode_bg, daemon=True).start()

        # Сохраняем фото на диск и привязываем пути к записи
        try:
            photo_map = _save_daily_photos(inspection_id)
            if photo_map:
                add_daily_inspection_photos(inspection_id, photo_map)
        except Exception as e:
            logger.error(f"Failed to save daily photos for inspection {inspection_id}: {e}")

        # Push-уведомления админам
        notify_admins_new_report('daily', inspection_id, {
            'sender': data.get('sender_name') or data.get('driver_name'),
            'telegram_user_id': data.get('telegram_user_id'),
            'machine': data.get('machine_uid'),
            'project': data.get('department_uid'),
            'address': data.get('geo_address'),
        })

        # Сохраняем моточасы в историю пробега
        motorhours_val = int(data.get('motorhours', 0) or 0)
        if motorhours_val > 0:
            save_mileage_record(
                machine_id=machine['id'],
                mileage=0,
                motorhours=motorhours_val,
                source='daily_checklist'
            )

        # Отправляем подтверждение в Telegram
        telegram_user_id = data.get('telegram_user_id')
        lang = data.get('lang', 'ru')
        if telegram_user_id:
            submission_time = data.get('timestamp', now_local().strftime("%d.%m.%Y %H:%M:%S"))
            confirmation_text = get_bot_message('daily_submission_confirmed', lang).format(datetime=submission_time)

            def send_message_sync():
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {"chat_id": telegram_user_id, "text": confirmation_text}
                    response = requests.post(url, json=payload, timeout=10)
                    response.raise_for_status()
                    logger.info(f"Daily confirmation sent to user {telegram_user_id}")
                except Exception as e:
                    logger.error(f"Failed to send daily confirmation to {telegram_user_id}: {e}")

            threading.Thread(target=send_message_sync, daemon=True).start()

        return jsonify({"success": True, "id": inspection_id})

    except Exception as e:
        logger.error(f"Error in /submit_daily: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app_bp.route('/photos/<path:filename>', methods=['GET'])
def serve_photo(filename):
    """Отдаёт сохранённое фото из PHOTO_BASE. Только для активных админов."""
    from flask import session, abort
    from database import get_admin_by_id
    admin_id = session.get('admin_id')
    admin = get_admin_by_id(admin_id) if admin_id else None
    if not admin or not admin.get('is_active'):
        abort(403)
    return send_from_directory(PHOTO_BASE, filename)


@app_bp.route('/health', methods=['GET'])
def health():
    """Лёгкий healthcheck для Docker/мониторинга."""
    return jsonify({"status": "ok"})