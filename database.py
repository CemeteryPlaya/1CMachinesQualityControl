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
                ref_key TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Миграции: добавляем колонки если нет
        cur.execute('''
            DO $$ BEGIN
                ALTER TABLE machines ADD COLUMN ref_key TEXT;
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$
        ''')
        cur.execute('''
            DO $$ BEGIN
                ALTER TABLE machines ADD COLUMN vehicle_type TEXT DEFAULT 'lv';
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                employee_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                position_type TEXT NOT NULL,
                ref_key TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            DO $$ BEGIN
                ALTER TABLE employees ADD COLUMN ref_key TEXT;
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$
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
            CREATE TABLE IF NOT EXISTS repair_types (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                ref_key TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS nomenclature (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                ref_key TEXT,
                parent_ref_key TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_reports (
                id SERIAL PRIMARY KEY,
                lang TEXT NOT NULL DEFAULT 'ru',
                telegram_user_id TEXT,
                to_date DATE,
                department TEXT,
                department_ref_key TEXT,
                machine_inventory TEXT,
                machine_model TEXT,
                machine_plate TEXT,
                machine_ref_key TEXT,
                responsible_person TEXT,
                responsible_person_ref_key TEXT,
                repair_type TEXT,
                repair_type_ref_key TEXT,
                breakdown_reason TEXT,
                repair_start_date DATE,
                repair_end_date DATE,
                downtime_days INTEGER DEFAULT 0,
                downtime_hours INTEGER DEFAULT 0,
                used_parts TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        cur.execute('''
            CREATE TABLE IF NOT EXISTS mileage_history (
                id SERIAL PRIMARY KEY,
                machine_id INTEGER NOT NULL REFERENCES machines(id),
                mileage INTEGER DEFAULT 0,
                motorhours INTEGER DEFAULT 0,
                source TEXT DEFAULT 'checklist',
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_mileage_history_machine
            ON mileage_history(machine_id, recorded_at DESC)
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

def upsert_machine(inventory_number: str, model: str, license_plate: str,
                    ref_key: str = None, vehicle_type: str = 'lv'):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO machines (inventory_number, model, license_plate, ref_key, vehicle_type, last_updated)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (inventory_number) DO UPDATE SET
                model = EXCLUDED.model,
                license_plate = EXCLUDED.license_plate,
                ref_key = COALESCE(EXCLUDED.ref_key, machines.ref_key),
                vehicle_type = EXCLUDED.vehicle_type,
                last_updated = CURRENT_TIMESTAMP
        ''', (inventory_number, model, license_plate, ref_key, vehicle_type))
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


def get_machines_by_category(category: str) -> List[Dict]:
    """Возвращает машины по категории: lv, sv или all"""
    conn = get_db_connection()
    machines = []
    try:
        cur = conn.cursor()
        if category == 'all':
            cur.execute('SELECT * FROM machines')
        else:
            cur.execute('SELECT * FROM machines WHERE vehicle_type = %s', (category,))
        machines = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching machines by category {category}: {e}")
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

def upsert_employee(employee_code: str, full_name: str, position_type: str, ref_key: str = None):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO employees (employee_code, full_name, position_type, ref_key, last_updated)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (employee_code) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                position_type = EXCLUDED.position_type,
                ref_key = COALESCE(EXCLUDED.ref_key, employees.ref_key),
                last_updated = CURRENT_TIMESTAMP
        ''', (employee_code, full_name, position_type, ref_key))
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
    'department_ref_key', 'driver_ref_key', 'mechanic_ref_key', 'machine_ref_key',
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


# ============================================================
# REPAIR TYPES (Виды ТО)
# ============================================================

def upsert_repair_type(code: str, name: str, ref_key: str = None):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO repair_types (code, name, ref_key, last_updated)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                ref_key = COALESCE(EXCLUDED.ref_key, repair_types.ref_key),
                last_updated = CURRENT_TIMESTAMP
        ''', (code, name, ref_key))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting repair type {code}: {e}")
    finally:
        conn.close()


def get_all_repair_types() -> List[Dict]:
    conn = get_db_connection()
    types = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM repair_types ORDER BY name')
        types = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching repair types: {e}")
    finally:
        conn.close()
    return types


def get_repair_type_by_id(type_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    repair_type = None
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM repair_types WHERE id = %s', (type_id,))
        row = cur.fetchone()
        if row:
            repair_type = dict(row)
    except Exception as e:
        logger.error(f"Error fetching repair type {type_id}: {e}")
    finally:
        conn.close()
    return repair_type


# ============================================================
# NOMENCLATURE (Номенклатура)
# ============================================================

def upsert_nomenclature(code: str, name: str, ref_key: str = None, parent_ref_key: str = None):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO nomenclature (code, name, ref_key, parent_ref_key, last_updated)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                ref_key = COALESCE(EXCLUDED.ref_key, nomenclature.ref_key),
                parent_ref_key = COALESCE(EXCLUDED.parent_ref_key, nomenclature.parent_ref_key),
                last_updated = CURRENT_TIMESTAMP
        ''', (code, name, ref_key, parent_ref_key))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting nomenclature {code}: {e}")
    finally:
        conn.close()


def get_all_nomenclature() -> List[Dict]:
    conn = get_db_connection()
    items = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM nomenclature ORDER BY name')
        items = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching nomenclature: {e}")
    finally:
        conn.close()
    return items


# ============================================================
# MAINTENANCE REPORTS (Отчеты о ТО)
# ============================================================

def save_maintenance_report(data: Dict[str, Any]) -> Optional[int]:
    """Сохраняет отчет о ТО в PostgreSQL. Возвращает id записи."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        def parse_date(raw):
            if not raw:
                return None
            for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
                try:
                    return datetime.strptime(raw, fmt).date()
                except ValueError:
                    continue
            return None

        def to_int(val, default=0):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default

        cur.execute('''
            INSERT INTO maintenance_reports (
                lang, telegram_user_id, to_date,
                department, department_ref_key,
                machine_inventory, machine_model, machine_plate, machine_ref_key,
                responsible_person, responsible_person_ref_key,
                repair_type, repair_type_ref_key,
                breakdown_reason,
                repair_start_date, repair_end_date,
                downtime_days, downtime_hours,
                used_parts
            ) VALUES (
                %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s,
                %s, %s,
                %s, %s,
                %s
            ) RETURNING id
        ''', (
            data.get('lang', 'ru'),
            data.get('telegram_user_id'),
            parse_date(data.get('to_date')),
            data.get('department_uid'),
            data.get('department_ref_key'),
            data.get('machine_inv'),
            data.get('model'),
            data.get('license_plate'),
            data.get('machine_ref_key'),
            data.get('responsible_person_name'),
            data.get('responsible_person_ref_key'),
            data.get('repair_type_name'),
            data.get('repair_type_ref_key'),
            data.get('breakdown_reason'),
            parse_date(data.get('repair_start_date')),
            parse_date(data.get('repair_end_date')),
            to_int(data.get('downtime_days')),
            to_int(data.get('downtime_hours')),
            data.get('used_parts'),
        ))
        row = cur.fetchone()
        conn.commit()
        report_id = row['id'] if row else None
        logger.info(f"Maintenance report saved with id={report_id}")
        return report_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving maintenance report: {e}")
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


# ============================================================
# MILEAGE HISTORY (История пробега)
# ============================================================

def save_mileage_record(machine_id: int, mileage: int = 0, motorhours: int = 0,
                        source: str = 'checklist') -> Optional[int]:
    """Сохраняет запись пробега в историю."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO mileage_history (machine_id, mileage, motorhours, source)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (machine_id, mileage, motorhours, source))
        row = cur.fetchone()
        conn.commit()
        record_id = row['id'] if row else None
        logger.info(f"Mileage record saved: machine_id={machine_id}, mileage={mileage}, motorhours={motorhours}")
        return record_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving mileage record: {e}")
        return None
    finally:
        conn.close()


def get_last_mileage(machine_id: int) -> Optional[Dict]:
    """Возвращает последнюю запись пробега для машины."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT * FROM mileage_history
            WHERE machine_id = %s
            ORDER BY recorded_at DESC
            LIMIT 1
        ''', (machine_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching last mileage for machine {machine_id}: {e}")
        return None
    finally:
        conn.close()


def get_mileage_history(machine_id: int, limit: int = 50) -> List[Dict]:
    """Возвращает историю пробега для машины (для графика)."""
    conn = get_db_connection()
    records = []
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT * FROM mileage_history
            WHERE machine_id = %s
            ORDER BY recorded_at ASC
            LIMIT %s
        ''', (machine_id, limit))
        records = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching mileage history for machine {machine_id}: {e}")
    finally:
        conn.close()
    return records
