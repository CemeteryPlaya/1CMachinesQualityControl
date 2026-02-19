import requests
import os
import logging
from typing import List, Dict, Any
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

# === НОВОЕ: базовый URL для OData (без конкретного справочника) ===
# Пример: http://192.168.1.77/HiTechMat/odata/standard.odata
ODATA_BASE_URL = os.getenv("ODATA_BASE_URL")


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

            if inventory_number:
                upsert_machine(
                    inventory_number=str(inventory_number),
                    model=str(name_model or "Unknown"),
                    license_plate=str(license_plate or "")
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
                position_type=position_name
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
                employee_code = employee.get("Code") or employee.get("Ref_Key")
                full_name = employee.get("Description") or "Unknown"
                position_name = positions_map.get(current_position_key, "UNKNOWN")

                if employee_code:
                    upsert_employee(
                        employee_code=str(employee_code),
                        full_name=str(full_name),
                        position_type=position_name
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