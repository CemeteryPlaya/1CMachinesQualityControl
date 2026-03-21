import os
from flask import Blueprint, render_template, request, jsonify
from importlib import import_module
from datetime import datetime
import odata_service
from database import (get_machine_by_id, get_all_machines, get_employee_by_id,
                       get_employees_by_position, get_department_by_id,
                       get_all_departments, save_inspection,
                       save_inspection_from_sheets)
import logging
import threading
import requests
from bot_instance import BOT_TOKEN
from translations import get_bot_message
from odata_service import post_checklist_to_1c

app_bp = Blueprint('app', __name__)
logger = logging.getLogger(__name__)

FORM_CONFIG_MODULES = {
    "lv": "lv_form_config",
    "lv_oa": "lv_oa_form_config",
    "sv": "sv_form_config",
    "sv_oa": "sv_oa_form_config",
}

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
                           form_type=form_type)

@app_bp.route('/api/machines', methods=['GET'])
def get_machines():
    """Returns list of machines from 1C (or local DB fallback)."""
    try:
        # Trigger sync/fetch
        machines = odata_service.sync_machines()
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

        # 1. Добавляем отметку времени (как в Google Forms)
        data['timestamp'] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

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

        # 5. Асинхронно отправляем в 1С через OData
        data_copy = dict(data)

        def push_to_1c():
            try:
                post_checklist_to_1c(data_copy, inspection_id)
            except Exception as e:
                logger.error(f"Background 1C push failed: {e}")

        threading.Thread(target=push_to_1c, daemon=True).start()

        # 6. Отправляем подтверждение в Telegram
        telegram_user_id = data.get('telegram_user_id')
        lang = data.get('lang', 'ru')

        if telegram_user_id:
            submission_time = data.get('timestamp', datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
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