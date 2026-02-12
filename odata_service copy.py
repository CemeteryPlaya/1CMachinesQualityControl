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

def sync_machines() -> List[Dict[str, Any]]:
    return fetch_machines()

def fetch_machines() -> List[Dict[str, Any]]:
    """
    Fetches machines from 1C OData.
    If successful, updates the local database and returns the fresh data.
    If failed, returns the data from the local database (dual mode).
    """
    
    # 1C OData usually returns data in a 'value' key
    # Example URL: http://host/base/odata/standard.odata/Catalog_Machines?$format=json
    
    if not ODATA_URL:
        logger.warning("ODATA_URL not set. returning local data.")
        return get_all_machines()

    try:
        # Timeout set to 10 seconds to avoid hanging
        response = requests.get(
            ODATA_URL, 
            auth=(ODATA_USER, ODATA_PASSWORD) if ODATA_USER else None,
            timeout=10,
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        
        data = response.json()
        machines_from_1c = data.get("value", [])
        
        if not machines_from_1c:
            logger.info("No machines returned from 1C.")
            
        # Update local DB
        for machine in machines_from_1c:
            # Adjust these keys based on actual OData response fields
            # Assuming 1C fields are named similarly or mapped here
            inventory_number = machine.get("Code") or machine.get("InventoryNumber") # Example
            name_model = machine.get("Description") or machine.get("Model")
            license_plate = machine.get("LicensePlate") or machine.get("ГосударственныйНомер") # Placeholder key
            
            # If 1C keys are Cyrillic or specific, they need to be mapped.
            # For now using generic placeholders as requested in prompt "Logika 1C (OData)"
            
            # Using defaults to avoid crashes if keys missing
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


def sync_employees() -> List[Dict[str, Any]]:
    """Синхронизирует сотрудников (водителей и механиков) с 1С"""
    return fetch_employees()


def fetch_employees() -> List[Dict[str, Any]]:
    """
    Fetches employees (drivers and mechanics) from 1C OData.
    If successful, updates the local database and returns the fresh data.
    If failed, returns the data from the local database (dual mode).
    """

    if not ODATA_EMPLOYEES_URL:
        logger.warning("ODATA_EMPLOYEES_URL not set. returning local data.")
        return get_all_employees()

    try:
        # Получаем список должностей для фильтрации
        positions_map = {}
        logger.info(f"Fetching positions from: {ODATA_POSITIONS_URL}")
        try:
            pos_response = requests.get(
                ODATA_POSITIONS_URL,
                auth=(ODATA_USER, ODATA_PASSWORD) if ODATA_USER else None,
                timeout=10,
                headers={"Accept": "application/json"}
            )
            pos_response.raise_for_status()
            positions_data = pos_response.json()
            positions = positions_data.get("value", [])

            # Логируем структуру первой должности для диагностики
            if len(positions) > 0:
                logger.debug(f"Sample position data (first record): {positions[0]}")

            # Создаем маппинг Ref_Key -> Code для должностей
            for pos in positions:
                ref_key = pos.get("Ref_Key")
                code = pos.get("Code")
                if ref_key and code:
                    positions_map[ref_key] = code
                    logger.debug(f"Position mapping: {ref_key} -> {code}")

            logger.info(f"Loaded {len(positions_map)} positions from 1C")
            # Логируем DRIVER и MECHANIC если они есть
            driver_keys = [k for k, v in positions_map.items() if v == "DRIVER"]
            mechanic_keys = [k for k, v in positions_map.items() if v == "MECHANIC"]
            logger.info(f"Found DRIVER positions: {len(driver_keys)}, MECHANIC positions: {len(mechanic_keys)}")
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")

        # Получаем список сотрудников
        logger.info(f"Fetching employees from: {ODATA_EMPLOYEES_URL}")
        emp_response = requests.get(
            ODATA_EMPLOYEES_URL,
            auth=(ODATA_USER, ODATA_PASSWORD) if ODATA_USER else None,
            timeout=10,
            headers={"Accept": "application/json"}
        )
        emp_response.raise_for_status()

        data = emp_response.json()
        employees_from_1c = data.get("value", [])

        if not employees_from_1c:
            logger.warning("No employees returned from 1C.")
        else:
            logger.info(f"Received {len(employees_from_1c)} total employees from 1C")
            # Логируем структуру первого сотрудника для диагностики
            if len(employees_from_1c) > 0:
                logger.debug(f"Sample employee data (first record): {employees_from_1c[0]}")

        # Фильтруем и обновляем локальную БД
        drivers_and_mechanics = []
        for employee in employees_from_1c:
            # Получаем ключ текущей должности
            current_position_key = employee.get("ТекущаяДолжностьОрганизации_Key") or employee.get("CurrentPosition_Key")

            # Проверяем, является ли сотрудник водителем или механиком
            position_code = positions_map.get(current_position_key, "")

            if position_code in ["DRIVER", "MECHANIC"]:
                # Извлекаем данные сотрудника
                employee_code = employee.get("Code") or employee.get("Ref_Key")
                full_name = employee.get("Description") or employee.get("ФИО") or "Unknown"
                position_type = position_code

                if employee_code:
                    logger.debug(f"Adding {position_type}: {full_name} (code: {employee_code})")
                    upsert_employee(
                        employee_code=str(employee_code),
                        full_name=str(full_name),
                        position_type=position_type
                    )
                    drivers_and_mechanics.append({
                        "employee_code": employee_code,
                        "full_name": full_name,
                        "position_type": position_type
                    })

        logger.info(f"Successfully fetched and updated {len(drivers_and_mechanics)} employees (drivers and mechanics) from 1C.")
        logger.info(f"Breakdown - Drivers: {sum(1 for e in drivers_and_mechanics if e['position_type'] == 'DRIVER')}, Mechanics: {sum(1 for e in drivers_and_mechanics if e['position_type'] == 'MECHANIC')}")
        return get_all_employees()

    except requests.RequestException as e:
        logger.error(f"Error fetching employees from 1C: {e}. Switching to offline mode.")
        return get_all_employees()
    except Exception as e:
        logger.error(f"Unexpected error in fetch_employees: {e}")
        return get_all_employees()
