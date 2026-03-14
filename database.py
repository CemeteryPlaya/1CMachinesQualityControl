import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/checklists"
)

logger = logging.getLogger(__name__)


def get_db_connection():
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=False)
    return conn


def init_db():
    """Инициализирует БД — создаёт таблицы если их нет"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS machines (
                id SERIAL PRIMARY KEY,
                inventory_number TEXT UNIQUE NOT NULL,
                model TEXT NOT NULL,
                license_plate TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                employee_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                position_type TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id SERIAL PRIMARY KEY,
                department_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                ref_key TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS inspections (
                id SERIAL PRIMARY KEY,
                form_type TEXT NOT NULL DEFAULT 'lv',
                lang TEXT NOT NULL DEFAULT 'ru',
                telegram_user_id TEXT,
                inspection_date DATE,
                department TEXT,
                driver_name TEXT,
                mechanic_name TEXT,
                machine_inventory TEXT,
                machine_model TEXT,
                machine_plate TEXT,
                mileage INTEGER DEFAULT 0,
                motorhours INTEGER DEFAULT 0,
                fuel_amount TEXT,
                fuel_type TEXT,
                results JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error initializing database: {e}")
    finally:
        conn.close()


# ============================================================
# MACHINES
# ============================================================

def upsert_machine(inventory_number: str, model: str, license_plate: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO machines (inventory_number, model, license_plate, last_updated)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (inventory_number) DO UPDATE SET
                model = EXCLUDED.model,
                license_plate = EXCLUDED.license_plate,
                last_updated = CURRENT_TIMESTAMP
        ''', (inventory_number, model, license_plate))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting machine {inventory_number}: {e}")
    finally:
        conn.close()


def get_all_machines() -> List[Dict]:
    conn = get_db_connection()
    machines = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM machines')
        machines = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching machines from DB: {e}")
    finally:
        conn.close()
    return machines


def get_machine_by_id(machine_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    machine = None
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM machines WHERE id = %s', (machine_id,))
        row = cur.fetchone()
        if row:
            machine = dict(row)
    except Exception as e:
        logger.error(f"Error fetching machine {machine_id}: {e}")
    finally:
        conn.close()
    return machine


# ============================================================
# EMPLOYEES
# ============================================================

def upsert_employee(employee_code: str, full_name: str, position_type: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO employees (employee_code, full_name, position_type, last_updated)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (employee_code) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                position_type = EXCLUDED.position_type,
                last_updated = CURRENT_TIMESTAMP
        ''', (employee_code, full_name, position_type))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting employee {employee_code}: {e}")
    finally:
        conn.close()


def get_all_employees() -> List[Dict]:
    conn = get_db_connection()
    employees = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM employees')
        employees = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching employees from DB: {e}")
    finally:
        conn.close()
    return employees


def get_employees_by_position(position_type: str) -> List[Dict]:
    conn = get_db_connection()
    employees = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM employees WHERE position_type = %s', (position_type,))
        employees = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching employees by position {position_type}: {e}")
    finally:
        conn.close()
    return employees


def get_employee_by_id(employee_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    employee = None
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM employees WHERE id = %s', (employee_id,))
        row = cur.fetchone()
        if row:
            employee = dict(row)
    except Exception as e:
        logger.error(f"Error fetching employee {employee_id}: {e}")
    finally:
        conn.close()
    return employee


# ============================================================
# DEPARTMENTS
# ============================================================

def upsert_department(department_code: str, name: str, ref_key: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO departments (department_code, name, ref_key, last_updated)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (department_code) DO UPDATE SET
                name = EXCLUDED.name,
                ref_key = EXCLUDED.ref_key,
                last_updated = CURRENT_TIMESTAMP
        ''', (department_code, name, ref_key))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting department {department_code}: {e}")
    finally:
        conn.close()


def get_all_departments() -> List[Dict]:
    conn = get_db_connection()
    departments = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM departments ORDER BY name')
        departments = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
    finally:
        conn.close()
    return departments


def get_department_by_id(department_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    department = None
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM departments WHERE id = %s', (department_id,))
        row = cur.fetchone()
        if row:
            department = dict(row)
    except Exception as e:
        logger.error(f"Error fetching department {department_id}: {e}")
    finally:
        conn.close()
    return department


# ============================================================
# INSPECTIONS
# ============================================================

# Метаданные, которые хранятся в отдельных колонках (не в JSONB)
_INSPECTION_META_KEYS = {
    'form_type', 'lang', 'telegram_user_id', 'inspection_date',
    'department_uid', 'driver_name', 'mechanic_name',
    'machine_inv', 'model', 'license_plate',
    'mileage', 'motorhours',
    'capacity_of_fuel_in_fueltank', 'fuel_type',
    'timestamp', 'driver_uid', 'mechanic_uid', 'machine_uid',
}


def save_inspection(data: Dict[str, Any]) -> Optional[int]:
    """Сохраняет результат инспекции в PostgreSQL. Возвращает id записи."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Парсим дату инспекции
        inspection_date = None
        raw_date = data.get('inspection_date')
        if raw_date:
            for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
                try:
                    inspection_date = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue

        # Собираем все остальные поля в JSONB
        results = {k: v for k, v in data.items() if k not in _INSPECTION_META_KEYS}

        def to_int(val, default=0):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default

        cur.execute('''
            INSERT INTO inspections (
                form_type, lang, telegram_user_id, inspection_date,
                department, driver_name, mechanic_name,
                machine_inventory, machine_model, machine_plate,
                mileage, motorhours, fuel_amount, fuel_type, results
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s
            ) RETURNING id
        ''', (
            data.get('form_type', 'lv'),
            data.get('lang', 'ru'),
            data.get('telegram_user_id'),
            inspection_date,
            data.get('department_uid'),
            data.get('driver_name'),
            data.get('mechanic_name'),
            data.get('machine_inv'),
            data.get('model'),
            data.get('license_plate'),
            to_int(data.get('mileage')),
            to_int(data.get('motorhours')),
            data.get('capacity_of_fuel_in_fueltank'),
            data.get('fuel_type'),
            Jsonb(results),
        ))
        row = cur.fetchone()
        conn.commit()
        inspection_id = row['id'] if row else None
        logger.info(f"Inspection saved with id={inspection_id}")
        return inspection_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving inspection: {e}")
        return None
    finally:
        conn.close()


def save_inspection_from_sheets(data: Dict[str, Any]) -> Optional[int]:
    """Сохраняет инспекцию из Google Sheets (все поля как текст, без резолва UID)."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        inspection_date = None
        raw_date = data.get('inspection_date')
        if raw_date:
            for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
                try:
                    inspection_date = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue

        # Все неструктурированные поля — в JSONB
        meta_keys = {
            'form_type', 'lang', 'source', 'inspection_date',
            'department', 'driver_name', 'mechanic_name',
            'machine', 'mileage', 'motorhours',
            'fuel_amount', 'fuel_type', 'timestamp',
        }
        results = {k: v for k, v in data.items() if k not in meta_keys and v}

        def to_int(val, default=0):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default

        cur.execute('''
            INSERT INTO inspections (
                form_type, lang, telegram_user_id, inspection_date,
                department, driver_name, mechanic_name,
                machine_inventory, machine_model, machine_plate,
                mileage, motorhours, fuel_amount, fuel_type, results
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s
            ) RETURNING id
        ''', (
            data.get('form_type', 'gsheets'),
            data.get('lang', 'ru'),
            None,
            inspection_date,
            data.get('department'),
            data.get('driver_name'),
            data.get('mechanic_name'),
            None,
            data.get('machine'),
            None,
            to_int(data.get('mileage')),
            to_int(data.get('motorhours')),
            data.get('fuel_amount'),
            data.get('fuel_type'),
            Jsonb(results),
        ))
        row = cur.fetchone()
        conn.commit()
        inspection_id = row['id'] if row else None
        logger.info(f"Sheets inspection saved with id={inspection_id}")
        return inspection_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving sheets inspection: {e}", exc_info=True)
        return None
    finally:
        conn.close()


def get_all_inspections() -> List[Dict]:
    conn = get_db_connection()
    inspections = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM inspections ORDER BY created_at DESC')
        inspections = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching inspections: {e}")
    finally:
        conn.close()
    return inspections
