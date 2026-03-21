import requests
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from importlib import import_module
from database import upsert_machine, get_all_machines, upsert_employee, get_all_employees

logger = logging.getLogger(__name__)

ODATA_URL = os.getenv("ODATA_URL")
ODATA_USER = os.getenv("ODATA_USER")
ODATA_PASSWORD = os.getenv("ODATA_PASSWORD")

# URLs для должностей и сотрудников
ODATA_POSITIONS_URL = os.getenv("ODATA_POSITIONS_URL")
ODATA_EMPLOYEES_URL = os.getenv("ODATA_EMPLOYEES_URL")

# URL для подразделений
ODATA_DEPARTMENT_URL = os.getenv("ODATA_DEPARTMENT_URL")

# Базовый URL для OData (без конкретного справочника)
ODATA_BASE_URL = os.getenv("ODATA_BASE_URL")

# URL документа ЧекЛистОсмотра для POST
ODATA_DOC_URL = os.getenv("ODATA_DOC_URL")


def _get_auth():
    """Возвращает auth tuple или None"""
    return (ODATA_USER, ODATA_PASSWORD) if ODATA_USER else None


def _odata_get(url: str, params: dict = None) -> dict:
    """Универсальный GET-запрос к OData с обработкой ошибок"""
    response = requests.get(
        url,
        auth=_get_auth(),
        params=params,
        timeout=30,
        headers={"Accept": "application/json"}
    )
    response.raise_for_status()
    return response.json()


# ============================================================
#  MACHINES (без изменений)
# ============================================================

def sync_machines() -> List[Dict[str, Any]]:
    return fetch_machines()


def fetch_machines() -> List[Dict[str, Any]]:
    if not ODATA_URL:
        logger.warning("ODATA_URL not set. returning local data.")
        return get_all_machines()

    try:
        data = _odata_get(ODATA_URL)
        machines_from_1c = data.get("value", [])

        if not machines_from_1c:
            logger.info("No machines returned from 1C.")

        for machine in machines_from_1c:
            inventory_number = machine.get("Code") or machine.get("InventoryNumber")
            name_model = machine.get("Description") or machine.get("Model")
            license_plate = machine.get("LicensePlate") or machine.get("ГосударственныйНомер")
            ref_key = machine.get("Ref_Key")

            if inventory_number:
                upsert_machine(
                    inventory_number=str(inventory_number),
                    model=str(name_model or "Unknown"),
                    license_plate=str(license_plate or ""),
                    ref_key=str(ref_key) if ref_key else None
                )

        logger.info(f"Successfully fetched and updated {len(machines_from_1c)} machines from 1C.")
        return get_all_machines()

    except requests.RequestException as e:
        logger.error(f"Error fetching from 1C: {e}. Switching to offline mode.")
        return get_all_machines()
    except Exception as e:
        logger.error(f"Unexpected error in fetch_machines: {e}")
        return get_all_machines()


# ============================================================
#  EMPLOYEES — исправленная версия
# ============================================================

def sync_employees() -> List[Dict[str, Any]]:
    """Синхронизирует сотрудников (водителей и механиков) с 1С"""
    return fetch_employees()


def _fetch_positions_map() -> Dict[str, str]:
    """
    Загружает справочник должностей.
    Возвращает dict: { Ref_Key -> Description (название должности) }
    """
    positions_map = {}

    if not ODATA_POSITIONS_URL:
        logger.warning("ODATA_POSITIONS_URL not set.")
        return positions_map

    try:
        logger.info(f"Fetching positions from: {ODATA_POSITIONS_URL}")
        data = _odata_get(ODATA_POSITIONS_URL)
        positions = data.get("value", [])

        for pos in positions:
            ref_key = pos.get("Ref_Key")
            description = (pos.get("Description") or "").strip().upper()
            if ref_key and description:
                positions_map[ref_key] = description

        logger.info(f"Loaded {len(positions_map)} positions from 1C")
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")

    return positions_map


def _find_position_keys(positions_map: Dict[str, str], target_names: List[str]) -> set:
    """
    Находит Ref_Key должностей по списку названий.
    target_names — например ["DRIVER", "MECHANIC"]
    Возвращает set из Ref_Key.
    """
    target_upper = {name.upper() for name in target_names}
    keys = set()
    for ref_key, description in positions_map.items():
        if description in target_upper:
            keys.add(ref_key)
            logger.info(f"Target position found: '{description}' -> {ref_key}")
    return keys


def _fetch_staffing_history(target_position_keys: set) -> Dict[str, str]:
    """
    === КЛЮЧЕВОЕ ИЗМЕНЕНИЕ ===
    
    Запрашивает регистр сведений «Кадровая история сотрудников» (срез последних),
    чтобы получить АКТУАЛЬНУЮ должность каждого сотрудника.
    
    Возвращает dict: { Сотрудник_Key -> Должность_Key }
    (только для сотрудников, чья должность входит в target_position_keys)
    """
    employee_position_map = {}

    if not ODATA_BASE_URL:
        logger.error("ODATA_BASE_URL not set — cannot fetch staffing history register.")
        return employee_position_map

    # Возможные названия регистра в разных конфигурациях 1С
    # Попробуем несколько вариантов
    register_variants = [
        "InformationRegister_КадроваяИсторияСотрудников_SliceLast",
        "InformationRegister_КадроваяИсторияСотрудников",
        "InformationRegister_СведенияОРаботникахОрганизаций_SliceLast",
        "InformationRegister_РаботникиОрганизаций_SliceLast",
    ]

    data_fetched = False

    for register_name in register_variants:
        url = f"{ODATA_BASE_URL.rstrip('/')}/{register_name}"
        try:
            logger.info(f"Trying staffing register: {url}")
            data = _odata_get(url, params={"$format": "json"})
            records = data.get("value", [])

            if not records:
                logger.info(f"Register {register_name} returned 0 records, trying next...")
                continue

            logger.info(f"SUCCESS: {register_name} returned {len(records)} records")

            # Логируем первую запись для диагностики полей
            if records:
                logger.debug(f"Sample staffing record keys: {list(records[0].keys())}")

            for record in records:
                # Ищем поле с ключом должности — может называться по-разному
                position_key = (
                    record.get("Должность_Key")
                    or record.get("ДолжностьОрганизации_Key")
                    or record.get("Должность")
                    or ""
                )
                # Ищем поле с ключом сотрудника
                employee_key = (
                    record.get("Сотрудник_Key")
                    or record.get("Сотрудник")
                    or ""
                )

                # Пропускаем пустые ссылки
                if not employee_key or employee_key == "00000000-0000-0000-0000-000000000000":
                    continue
                if not position_key or position_key == "00000000-0000-0000-0000-000000000000":
                    continue

                # Фильтруем только нужные должности
                if position_key in target_position_keys:
                    employee_position_map[employee_key] = position_key

            data_fetched = True
            break  # Нашли рабочий регистр, дальше не пробуем

        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.info(f"Register {register_name} not found (404), trying next...")
                continue
            else:
                logger.error(f"HTTP error accessing {register_name}: {e}")
                continue
        except Exception as e:
            logger.error(f"Error accessing {register_name}: {e}")
            continue

    if not data_fetched:
        logger.error(
            "Could not find staffing history register. "
            "Check $metadata for the correct register name. "
            f"Tried: {register_variants}"
        )

    return employee_position_map


def fetch_employees() -> List[Dict[str, Any]]:
    """
    Получает сотрудников (водителей и механиков) из 1С OData.
    
    АЛГОРИТМ:
    1. Загружаем справочник должностей → находим Ref_Key для DRIVER и MECHANIC
    2. Загружаем регистр кадровой истории (срез последних) → 
       получаем маппинг Сотрудник_Key -> Должность_Key
    3. Загружаем справочник сотрудников → 
       берём только тех, кто есть в маппинге из шага 2
    """

    if not ODATA_EMPLOYEES_URL:
        logger.warning("ODATA_EMPLOYEES_URL not set. returning local data.")
        return get_all_employees()

    try:
        # ШАГ 1: Загружаем должности
        positions_map = _fetch_positions_map()  # { Ref_Key -> Description }

        target_positions = ["DRIVER", "MECHANIC"]
        target_position_keys = _find_position_keys(positions_map, target_positions)

        if not target_position_keys:
            logger.warning(
                f"Positions {target_positions} not found in 1C. "
                f"Available positions: {list(positions_map.values())}"
            )
            return get_all_employees()

        # ШАГ 2: Загружаем кадровую историю — узнаём кто на какой должности
        employee_position_map = _fetch_staffing_history(target_position_keys)
        # { Сотрудник_Key -> Должность_Key } — только водители и механики

        logger.info(
            f"Found {len(employee_position_map)} employees with target positions "
            f"in staffing history register"
        )

        if not employee_position_map:
            logger.warning(
                "No employees found via staffing history. "
                "Falling back to ТекущаяДолжностьОрганизации_Key field..."
            )
            # Фоллбэк — попробуем старый метод (вдруг у кого-то поле заполнено)
            return _fetch_employees_fallback(positions_map, target_position_keys)

        # ШАГ 3: Загружаем справочник сотрудников
        logger.info(f"Fetching employees from: {ODATA_EMPLOYEES_URL}")
        data = _odata_get(ODATA_EMPLOYEES_URL)
        employees_from_1c = data.get("value", [])

        logger.info(f"Received {len(employees_from_1c)} total employees from 1C")

        # Фильтруем и обновляем локальную БД
        drivers_and_mechanics = []
        for employee in employees_from_1c:
            emp_ref_key = employee.get("Ref_Key", "")

            # Проверяем, есть ли этот сотрудник в нашем маппинге
            if emp_ref_key not in employee_position_map:
                continue

            position_key = employee_position_map[emp_ref_key]
            position_name = positions_map.get(position_key, "UNKNOWN")

            employee_code = employee.get("Code") or emp_ref_key
            full_name = employee.get("Description") or "Unknown"

            logger.debug(f"Adding {position_name}: {full_name} (code: {employee_code})")

            upsert_employee(
                employee_code=str(employee_code),
                full_name=str(full_name),
                position_type=position_name,
                ref_key=str(emp_ref_key) if emp_ref_key else None
            )
            drivers_and_mechanics.append({
                "employee_code": employee_code,
                "full_name": full_name,
                "position_type": position_name
            })

        drivers_count = sum(1 for e in drivers_and_mechanics if e["position_type"] == "DRIVER")
        mechanics_count = sum(1 for e in drivers_and_mechanics if e["position_type"] == "MECHANIC")

        logger.info(
            f"Successfully synced {len(drivers_and_mechanics)} employees. "
            f"Drivers: {drivers_count}, Mechanics: {mechanics_count}"
        )
        return get_all_employees()

    except requests.RequestException as e:
        logger.error(f"Error fetching employees from 1C: {e}. Switching to offline mode.")
        return get_all_employees()
    except Exception as e:
        logger.error(f"Unexpected error in fetch_employees: {e}")
        return get_all_employees()


def _fetch_employees_fallback(
    positions_map: Dict[str, str],
    target_position_keys: set
) -> List[Dict[str, Any]]:
    """
    Фоллбэк: старый метод через ТекущаяДолжностьОрганизации_Key.
    Используется только если регистр кадровой истории недоступен.
    """
    try:
        data = _odata_get(ODATA_EMPLOYEES_URL)
        employees_from_1c = data.get("value", [])

        drivers_and_mechanics = []
        for employee in employees_from_1c:
            current_position_key = (
                employee.get("ТекущаяДолжностьОрганизации_Key")
                or employee.get("CurrentPosition_Key")
                or ""
            )

            if current_position_key in target_position_keys:
                emp_ref_key = employee.get("Ref_Key", "")
                employee_code = employee.get("Code") or emp_ref_key
                full_name = employee.get("Description") or "Unknown"
                position_name = positions_map.get(current_position_key, "UNKNOWN")

                if employee_code:
                    upsert_employee(
                        employee_code=str(employee_code),
                        full_name=str(full_name),
                        position_type=position_name,
                        ref_key=str(emp_ref_key) if emp_ref_key else None
                    )
                    drivers_and_mechanics.append({
                        "employee_code": employee_code,
                        "full_name": full_name,
                        "position_type": position_name
                    })

        logger.info(f"Fallback: found {len(drivers_and_mechanics)} employees")
        return get_all_employees()

    except Exception as e:
        logger.error(f"Fallback fetch_employees error: {e}")
        return get_all_employees()


# ============================================================
# DEPARTMENTS (Подразделения)
# ============================================================

def sync_departments() -> List[Dict[str, Any]]:
    """Синхронизирует подразделения из 1С и возвращает список"""
    return fetch_departments()


def fetch_departments() -> List[Dict[str, Any]]:
    """
    Получает подразделения из 1С OData с фильтрацией:
    - Description начинается с "КУП"
    - Parent_Key = "f65d5f0a-33bb-11f0-9341-d8bbc163ec30"
    """
    from database import upsert_department, get_all_departments

    if not ODATA_DEPARTMENT_URL:
        logger.warning("ODATA_DEPARTMENT_URL not set. Returning local data.")
        return get_all_departments()

    try:
        logger.info(f"Fetching departments from: {ODATA_DEPARTMENT_URL}")
        data = _odata_get(ODATA_DEPARTMENT_URL)
        departments_from_1c = data.get("value", [])

        logger.info(f"Received {len(departments_from_1c)} total departments from 1C")

        # Выводим структуру первого элемента для отладки
        if departments_from_1c:
            logger.info(f"Sample department keys: {list(departments_from_1c[0].keys())}")
            logger.info(f"First 3 departments sample:")
            for i, dept in enumerate(departments_from_1c[:3]):
                logger.info(f"  {i+1}. Description: '{dept.get('Description', 'N/A')}', "
                           f"Parent_Key: '{dept.get('Parent_Key', 'N/A')}', "
                           f"Ref_Key: '{dept.get('Ref_Key', 'N/A')}'")

        # Фильтруем и сохраняем в БД
        filtered_departments = []
        target_ref_key = "f65d5f0a-33bb-11f0-9341-d8bbc163ec30"

        kup_count = 0
        special_dept_count = 0

        logger.info(f"Filter: Description starts with 'КУП' OR Ref_Key = '{target_ref_key}'")

        for dept in departments_from_1c:
            description = dept.get("Description", "")
            ref_key = dept.get("Ref_Key", "")

            # Логика OR: либо начинается с "КУП", либо это специальное подразделение
            is_kup = description.startswith("КУП")
            is_special = ref_key == target_ref_key

            if not (is_kup or is_special):
                continue

            if is_kup:
                kup_count += 1
                logger.info(f"✅ КУП dept #{kup_count}: '{description}'")

            if is_special:
                special_dept_count += 1
                logger.info(f"✅ Special dept (by Ref_Key): '{description}'")

            # Проходит фильтры - добавляем
            department_code = dept.get("Code") or ref_key

            logger.debug(f"Adding department: {description} (code: {department_code})")

            upsert_department(
                department_code=str(department_code),
                name=str(description),
                ref_key=str(ref_key)
            )

            filtered_departments.append({
                "department_code": department_code,
                "name": description,
                "ref_key": ref_key
            })

        logger.info(
            f"Filter results: {len(departments_from_1c)} total, "
            f"{kup_count} start with 'КУП', "
            f"{special_dept_count} special (by Ref_Key), "
            f"{len(filtered_departments)} final synced"
        )
        return get_all_departments()

    except requests.RequestException as e:
        logger.error(f"Error fetching departments from 1C: {e}. Switching to offline mode.")
        return get_all_departments()
    except Exception as e:
        logger.error(f"Unexpected error in fetch_departments: {e}")
        return get_all_departments()


# ============================================================
# POST CHECKLIST TO 1C
# ============================================================

# Маппинг: form_field_id → (1С_табличная_часть, 1С_реквизит)
# Имена табличных частей и реквизитов ТОЧНО соответствуют конфигурации 1С
_FIELD_TO_1C = {
    # --- Кузов ---
    "body_state":                   ("Кузов", "СостояниеКузова"),
    "paint_state":                  ("Кузов", "СостояниеЛакокрасочногоПокрытия"),
    "body_cleanliness":             ("Кузов", "ЧистотаКузова"),
    "body_defects":                 ("Кузов", "КакоеЛибоПовреждение"),

    # --- Гидравлическая система ---
    "hydro_oil_level":              ("ГидравлическаяСистема", "СостояниеГидравлическойЖидкостиИИФильров"),
    "hydro_oil_condition":          ("ГидравлическаяСистема", "СостояниеГидравлическойЖидкостиИИФильров"),
    "hydro_oil_system_leakages":    ("ГидравлическаяСистема", "НаличиеКакойЛибоТечиВСистеме"),

    # --- Вспомогательное оборудование (только sv) ---
    "crane_boom_condition":         ("ВспомогательноеОборудование", "СостояниеСтрелы"),
    "slings_or_ropes_condition":    ("ВспомогательноеОборудование", "СостояниеСтропИлиТроса"),
    "safety_latches_condition":     ("ВспомогательноеОборудование", "СостояниеБарабанаТросаЛебедки"),
    "whinch_cable_drum_condition":  ("ВспомогательноеОборудование", "СостояниеБарабанаТросаЛебедки"),
    "secondary_whinch_condition":   ("ВспомогательноеОборудование", "СостояниеВспомогательнойЛебедки"),

    # --- Отсек двигателя ---
    "oil_level":                                    ("ОтсекДвигателя", "УровеньЖидкостей"),
    "filter_conditions":                            ("ОтсекДвигателя", "СостояниеФильтров"),
    "belts_and_rubber_parts_and_pipes_condition":    ("ОтсекДвигателя", "СостояниеРемнейИШланговИПрочиеРезиновыеИзделия"),
    "radiator_condition_and_cleanliness":            ("ОтсекДвигателя", "СостояниеИЧистотаРадиаторовОхлаждения"),
    "other_radiators_condition_and_cleanliness":     ("ОтсекДвигателя", "СостояниеИЧистотаПрочихРадиаторов"),
    "electrical_wires_condition":                    ("ОтсекДвигателя", "СостояниеЭлектропроводки"),
    "starter_and_alternator_condition":              ("ОтсекДвигателя", "СостояниеСтартераИГенератора"),

    # --- Ходовая часть ---
    "differential_condition":                       ("ХодоваяЧасть", "СостояниеГлавнойПарыРедуктора"),
    "final_gear_drive_condition":                   ("ХодоваяЧасть", "СостояниеГлавнойПарыРедуктора"),
    "lower_body_condition":                         ("ХодоваяЧасть", "СостояниеНижнейЧастиКузова"),
    "suspension_condition":                         ("ХодоваяЧасть", "СостояниеПодвески"),
    "gears_and_synchronizers_condition":             ("ХодоваяЧасть", "СостояниеШестеренИСинхронизаторовКПП"),
    "tracks_gears_wheels_driveshafts_condition":     ("ХодоваяЧасть", "СостояниеГусеницыШестеренКолесИПриводныхВалов"),

    # --- Оснащение и инструменты ---
    "protective_equipment":             ("ОснащениеИИнструменты", "НаличиеСредствЗащитыВКабине"),
    "windshield_condition":             ("ОснащениеИИнструменты", "СостояниеВетровогоСтекла"),
    "seat_condition":                   ("ОснащениеИИнструменты", "СостояниеСидений"),
    "belt_condition":                   ("ОснащениеИИнструменты", "СостояниеРемняБезопасности"),
    "signals_and_lights_functionality": ("ОснащениеИИнструменты", "РаботоспособностьЗвуковогоСигналаСигналаЗаднегоХодаФарИФонарей"),
    # cabine_cleanliness — нет в 1С, нужно добавить реквизит

    # --- Прочие элементы ---
    "side_mirrors_and_rear_view_condition":  ("ПрочиеЭлементы", "СостояниеБоковыхЗеркалИЗаднешлВида"),
    "battery_condition":                     ("ПрочиеЭлементы", "СостояниеАккумулятора"),
    # windshield_guards_condition — нет в 1С, нужно добавить реквизит
    "warning_signs":                         ("ПрочиеЭлементы", "НаличиеПредупреждающихЗнаков"),
    "sensors_and_indicators_functionality":  ("ПрочиеЭлементы", "РаботоспособностьИКорректностьДатчиковИИндикаторов"),
    "fire_extinguisher":                     ("ПрочиеЭлементы", "НаличиеИРаботоспсобностьОгнетушителя"),

    # --- Документация (только oa формы) ---
    "registration_certificate":         ("Документация", "НаличиеТехпаспорта"),
    "insurance":                        ("Документация", "НаличиеСтраховогоПолиса"),
    "insurance_end_date":               ("Документация", "ДатаОкончанияСтраховогоПолиса"),
    "technical_inspection":             ("Документация", "НаличиеДокументаТехническогоОсмотра"),
    "technical_inspection_date":        ("Документация", "ДатаОкончанияДокументаТехническогоОсмотра"),
}

# Человекочитаемые названия типов форм для 1С
_FORM_TYPE_LABELS = {
    "lv":    "Легковое (на территории)",
    "lv_oa": "Легковое (вне территории)",
    "sv":    "Спецтехника (на территории)",
    "sv_oa": "Спецтехника (вне территории)",
}

_LANG_LABELS = {
    "ru": "Русский",
    "en": "Английский",
    "kk": "Казахский",
    "uz": "Узбекский",
}

# Порядок табличных частей для LineNumber
_1C_SECTIONS_ORDER = [
    "Кузов", "ГидравлическаяСистема",
    "ВспомогательноеОборудование", "ОтсекДвигателя", "ХодоваяЧасть",
    "ОснащениеИИнструменты", "ПрочиеЭлементы", "Документация",
]


def _to_1c_datetime(raw_date: str) -> str:
    """Преобразует дату в формат ISO для 1С OData"""
    if raw_date:
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw_date, fmt).strftime("%Y-%m-%dT00:00:00")
            except ValueError:
                continue
    return datetime.now().strftime("%Y-%m-%dT00:00:00")


def _build_1c_sections(data: dict) -> Dict[str, list]:
    """
    Группирует поля формы по табличным частям 1С.
    Каждая секция → одна строка (dict) с заполненными реквизитами.
    """
    sections: Dict[str, dict] = {}

    # Поля с типом Edm.DateTime в табличных частях
    _DATETIME_COLUMNS = {
        "ДатаОкончанияСтраховогоПолиса",
        "ДатаОкончанияДокументаТехническогоОсмотра",
    }

    for field_id, value in data.items():
        if not value or field_id not in _FIELD_TO_1C:
            continue

        section_name, column_name = _FIELD_TO_1C[field_id]

        if section_name not in sections:
            sections[section_name] = {}

        # Не перезаписываем, если уже заполнено (для случаев hydro_oil_level / hydro_oil_condition)
        if column_name not in sections[section_name]:
            if column_name in _DATETIME_COLUMNS:
                sections[section_name][column_name] = _to_1c_datetime(str(value))
            else:
                sections[section_name][column_name] = str(value)

    # Преобразуем в формат OData: каждая секция = массив из одной строки
    result = {}
    for section_name in _1C_SECTIONS_ORDER:
        if section_name in sections:
            row = sections[section_name]
            row["LineNumber"] = "1"
            result[section_name] = [row]

    return result


def post_checklist_to_1c(data: dict, inspection_id: int) -> Optional[dict]:
    """
    Отправляет заполненный чек-лист в 1С через OData POST.

    Шапка: ИД, ДатаИнспекции, Подразделение, Водитель, Механик, Машина,
           ТипФормы, Язык, Пробег, Моточасы, КоличествоТоплива, ТипТоплива
    Табличные части: Показания, Кузов, ГидравлическаяСистема, ОтсекДвигателя,
                     ХодоваяЧасть, ОснащениеИИнструменты, ПрочиеЭлементы, Документация
    """
    if not ODATA_DOC_URL:
        logger.warning("ODATA_DOC_URL not set — skipping 1C push")
        return None

    def to_num(val, default=0):
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    form_type = data.get("form_type", "lv")

    # --- Шапка документа ---
    doc_payload = {
        "Date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "Posted": False,
        "ИД": str(inspection_id),
        "ТипФормы": _FORM_TYPE_LABELS.get(form_type, form_type),
        "Язык": _LANG_LABELS.get(data.get("lang", "ru"), data.get("lang", "ru")),
        "ДатаИнспекции": _to_1c_datetime(data.get("inspection_date", "")),

        # Числовые (Edm.Double)
        "Пробег": to_num(data.get("mileage")),
        "Моточасы": to_num(data.get("motorhours")),
        "КоличествоТоплива": to_num(data.get("capacity_of_fuel_in_fueltank")),
        "ТипТоплива": data.get("fuel_type", ""),
    }

    # Ссылочные поля (Edm.Guid) — передаём _Key только если есть GUID
    # Подразделение, Водитель, Механик, Машина — NavigationProperty (ссылки)
    dept_ref = data.get("department_ref_key")
    if dept_ref:
        doc_payload["Подразделение_Key"] = dept_ref

    driver_ref = data.get("driver_ref_key")
    if driver_ref:
        doc_payload["Водитель_Key"] = driver_ref

    mechanic_ref = data.get("mechanic_ref_key")
    if mechanic_ref:
        doc_payload["Механик_Key"] = mechanic_ref

    machine_ref = data.get("machine_ref_key")
    if machine_ref:
        doc_payload["Машина_Key"] = machine_ref

    # --- Табличные части (по секциям) ---
    sections = _build_1c_sections(data)
    doc_payload.update(sections)

    section_names = list(sections.keys())

    try:
        logger.info(
            f"Posting checklist to 1C: inspection_id={inspection_id}, "
            f"form_type={form_type}, sections={section_names}"
        )

        post_url = ODATA_DOC_URL.split("?")[0]

        response = requests.post(
            post_url,
            auth=_get_auth(),
            json=doc_payload,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        if response.status_code in (200, 201):
            result = response.json()
            ref_key = result.get("Ref_Key", "unknown")
            logger.info(f"Checklist posted to 1C: Ref_Key={ref_key}")
            return result
        else:
            body = response.text[:500]
            logger.error(f"1C returned HTTP {response.status_code}: {body}")
            return None

    except requests.RequestException as e:
        logger.error(f"Error posting checklist to 1C: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error posting checklist to 1C: {e}", exc_info=True)
        return None