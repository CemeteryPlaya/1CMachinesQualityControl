from flask import Blueprint, render_template, request, jsonify
from importlib import import_module
from sheets_service import append_inspection_data
from datetime import datetime
import odata_service
from database import get_machine_by_id, get_all_machines, get_employee_by_id, get_employees_by_position, get_department_by_id
import logging
import threading
import requests
from bot_instance import BOT_TOKEN
from translations import get_bot_message

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
            else:
                logger.warning(f"Department with ID {department_uid} not found")

        # Обработка водителя
        driver_uid = data.get('driver_uid')
        if driver_uid:
            driver = get_employee_by_id(driver_uid)
            if driver:
                formatted_driver = f"{driver['full_name']}"
                data['driver_uid'] = formatted_driver
                data['driver_name'] = driver['full_name']
            else:
                logger.warning(f"Driver with ID {driver_uid} not found")

        # Обработка механика
        mechanic_uid = data.get('mechanic_uid')
        if mechanic_uid:
            mechanic = get_employee_by_id(mechanic_uid)
            if mechanic:
                formatted_mechanic = f"{mechanic['full_name']}"
                data['mechanic_uid'] = formatted_mechanic
                data['mechanic_name'] = mechanic['full_name']
            else:
                logger.warning(f"Mechanic with ID {mechanic_uid} not found")

        # Обработка машины
        machine_uid = data.get('machine_uid')
        if not machine_uid:
             return jsonify({"success": False, "error": "machine_uid is missing"}), 400

        machine = get_machine_by_id(machine_uid)
        if not machine:
            return jsonify({"success": False, "error": "Machine not found"}), 404

        # 2. Формируем единую строку для столбца "Машина"
        plate = machine['license_plate'] if machine['license_plate'] else 'Нет ГРНЗ'
        formatted_machine = f"Модель: {machine['model']} | ГРНЗ: {plate} | ИН: {machine['inventory_number']}"

        # Записываем её в machine_uid, который мапится на заголовок "Машина"
        data['machine_uid'] = formatted_machine

        # 3. Инъекция деталей в отдельные поля (если столбцы в таблице остались)
        data['machine_inv'] = machine['inventory_number']
        data['model'] = machine['model']
        data['license_plate'] = machine['license_plate']

        # 4. Указываем верное имя листа (убедитесь, что оно совпадает с Sheets)
        success = append_inspection_data(data, sheet_name='Ответы на форму')

        if success:
            # Send confirmation message to user via bot in background thread
            telegram_user_id = data.get('telegram_user_id')
            lang = data.get('lang', 'ru')

            logger.info(f"Form submitted successfully. telegram_user_id: {telegram_user_id}, lang: {lang}")

            if telegram_user_id:
                # Format confirmation message with submission timestamp
                submission_time = data.get('timestamp', datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
                confirmation_text = get_bot_message('submission_confirmed', lang).format(datetime=submission_time)

                logger.info(f"Preparing to send confirmation message to user {telegram_user_id}")

                # Send message in background thread to not block response
                def send_message_sync():
                    logger.info(f"Background thread started for user {telegram_user_id}")
                    try:
                        # Use Telegram Bot API directly via requests (sync)
                        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        payload = {
                            "chat_id": telegram_user_id,
                            "text": confirmation_text
                        }
                        logger.info(f"Sending message to chat_id={telegram_user_id}: {confirmation_text}")

                        response = requests.post(url, json=payload, timeout=10)
                        response.raise_for_status()

                        logger.info(f"✅ Confirmation message sent successfully to user {telegram_user_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to send confirmation message to {telegram_user_id}: {e}", exc_info=True)

                # Start background thread
                thread = threading.Thread(target=send_message_sync, name=f"TelegramBot-{telegram_user_id}")
                thread.daemon = True
                thread.start()
                logger.info(f"Background thread started: {thread.name}")
            else:
                logger.warning("telegram_user_id is missing - cannot send confirmation message")

            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to save to Google Sheets"}), 500

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
        from database import get_all_departments
        # Trigger sync/fetch for departments
        odata_service.sync_departments()
        # Get all departments
        departments = get_all_departments()
        return jsonify(departments)
    except Exception as e:
        logger.error(f"Error in /api/departments: {e}")
        return jsonify({"error": str(e)}), 500