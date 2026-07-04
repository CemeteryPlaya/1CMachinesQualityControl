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

# Session timezone: created_at (DEFAULT CURRENT_TIMESTAMP) и группировки
# created_at::date должны считаться в локальном времени, а не в UTC сервера БД
from time_utils import PG_TIMEZONE
_CONN_OPTIONS = f"-c timezone={PG_TIMEZONE}" if PG_TIMEZONE else None

# --- Пул соединений (psycopg_pool). При его отсутствии — прямые соединения. ---
_POOL_MAX = int(os.getenv("DB_POOL_MAX", "10"))
_pool = None
try:
    from psycopg_pool import ConnectionPool

    class _PooledConn:
        """Прокси: close() возвращает соединение в пул, остальное делегирует."""
        __slots__ = ('_pool', '_conn')

        def __init__(self, pool, conn):
            self._pool = pool
            self._conn = conn

        def __getattr__(self, name):
            return getattr(self._conn, name)

        def close(self):
            # Откатываем незакоммиченную (read-only) транзакцию, чтобы пул
            # не логировал предупреждение на каждый возврат соединения
            try:
                self._conn.rollback()
            except Exception:
                pass
            try:
                self._pool.putconn(self._conn)
            except Exception:
                try:
                    self._conn.close()
                except Exception:
                    pass
except ImportError:
    ConnectionPool = None


def _get_pool():
    global _pool
    if _pool is None and ConnectionPool is not None and _POOL_MAX > 0:
        kwargs = {"row_factory": dict_row, "autocommit": False}
        if _CONN_OPTIONS:
            kwargs["options"] = _CONN_OPTIONS
        _pool = ConnectionPool(
            DATABASE_URL, min_size=1, max_size=_POOL_MAX, open=True,
            kwargs=kwargs,
        )
    return _pool


def get_db_connection():
    """Соединение из пула; при любом сбое пула — прямое соединение.

    Пул — оптимизация, а не точка отказа: если его воркеры не выдали
    соединение за 5 секунд (наблюдалось на Windows/Python 3.14),
    запрос обслуживается напрямую. DB_POOL_MAX=0 отключает пул совсем.
    """
    try:
        pool = _get_pool()
        if pool is not None:
            return _PooledConn(pool, pool.getconn(timeout=5))
    except Exception as e:
        logger.warning(f"Pool unavailable, direct connection fallback: {e}")
    if _CONN_OPTIONS:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row,
                               autocommit=False, options=_CONN_OPTIONS)
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=False)


def _migrate_daily_inspections(cur):
    """Одноразовый перенос ежедневных отчётов из inspections в daily_inspections.

    Идемпотентно: после переноса строки с form_type='daily' удаляются из inspections,
    повторный вызов ничего не находит. Гео-поля извлекаются из results JSONB.
    """
    cur.execute("SELECT COUNT(*) AS cnt FROM inspections WHERE form_type = 'daily'")
    row = cur.fetchone()
    if not row or row['cnt'] == 0:
        return
    cur.execute('''
        INSERT INTO daily_inspections (
            lang, telegram_user_id, inspection_date, project, operator_name,
            machine_inventory, machine_model, machine_plate,
            fuel_amount, fuel_type, motorhours,
            geo_latitude, geo_longitude, geo_address,
            results, created_at
        )
        SELECT lang, telegram_user_id, inspection_date, department, driver_name,
               machine_inventory, machine_model, machine_plate,
               fuel_amount, fuel_type, motorhours,
               NULLIF(results->>'geo_latitude', '')::double precision,
               NULLIF(results->>'geo_longitude', '')::double precision,
               results->>'geo_address',
               results - 'geo_latitude' - 'geo_longitude' - 'geo_address',
               created_at
        FROM inspections WHERE form_type = 'daily'
    ''')
    cur.execute("DELETE FROM inspections WHERE form_type = 'daily'")
    logger.info(f"Migrated {row['cnt']} daily inspections to daily_inspections table")


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
            CREATE TABLE IF NOT EXISTS measurement_units (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                ref_key TEXT,
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
            DO $$ BEGIN
                ALTER TABLE maintenance_reports ADD COLUMN photos JSONB NOT NULL DEFAULT '{}';
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$
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
        cur.execute('''
            CREATE TABLE IF NOT EXISTS daily_inspections (
                id SERIAL PRIMARY KEY,
                lang TEXT NOT NULL DEFAULT 'ru',
                telegram_user_id TEXT,
                inspection_date DATE,
                project TEXT,
                project_ref_key TEXT,
                operator_name TEXT,
                operator_ref_key TEXT,
                machine_inventory TEXT,
                machine_model TEXT,
                machine_plate TEXT,
                machine_ref_key TEXT,
                fuel_amount TEXT,
                fuel_type TEXT,
                motorhours INTEGER DEFAULT 0,
                geo_latitude DOUBLE PRECISION,
                geo_longitude DOUBLE PRECISION,
                geo_address TEXT,
                results JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_daily_inspections_created
            ON daily_inspections(created_at DESC)
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                telegram_user_id TEXT,
                is_superadmin BOOLEAN DEFAULT FALSE,
                can_view_reports BOOLEAN DEFAULT TRUE,
                can_view_history BOOLEAN DEFAULT FALSE,
                receive_instant_notifications BOOLEAN DEFAULT FALSE,
                receive_daily_digest BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS one_c_sync_queue (
                id SERIAL PRIMARY KEY,
                kind TEXT NOT NULL,
                record_id INTEGER,
                payload JSONB NOT NULL,
                attempts INTEGER DEFAULT 0,
                last_error TEXT,
                synced BOOLEAN DEFAULT FALSE,
                next_attempt_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_1c_queue_pending
            ON one_c_sync_queue(synced, next_attempt_at)
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS bot_users (
                id SERIAL PRIMARY KEY,
                telegram_user_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Отправитель отчёта (Ф.И.О зарегистрированного пользователя бота)
        for table in ('inspections', 'daily_inspections', 'maintenance_reports'):
            cur.execute(f'''
                DO $$ BEGIN
                    ALTER TABLE {table} ADD COLUMN sender_name TEXT;
                EXCEPTION WHEN duplicate_column THEN NULL;
                END $$
            ''')
        # Переносим ранее сохранённые ежедневные отчёты из inspections в daily_inspections
        _migrate_daily_inspections(cur)
        conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error initializing database: {e}")
        # Схема обязана быть полной — стартовать с неполной БД опаснее, чем упасть
        raise
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
    'sender_name',
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
                form_type, lang, telegram_user_id, sender_name, inspection_date,
                department, driver_name, mechanic_name,
                machine_inventory, machine_model, machine_plate,
                mileage, motorhours, fuel_amount, fuel_type, results
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s
            ) RETURNING id
        ''', (
            data.get('form_type', 'lv'),
            data.get('lang', 'ru'),
            data.get('telegram_user_id'),
            data.get('sender_name'),
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


def add_inspection_photos(inspection_id: int, photos: Dict[str, Any]) -> None:
    """Добавляет пути к фото в results JSONB существующей инспекции.

    photos — словарь вида {field_id: [relative_path, ...]}.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE inspections
            SET results = COALESCE(results, '{}'::jsonb) || %s
            WHERE id = %s
        ''', (Jsonb({'photos': photos}), inspection_id))
        conn.commit()
        logger.info(f"Photos attached to inspection id={inspection_id}: "
                    f"{ {k: len(v) for k, v in photos.items()} }")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error attaching photos to inspection {inspection_id}: {e}")
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


def delete_nomenclature_stale(parent_ref_key: str, keep_codes: List[str]):
    """Удаляет позиции папки, которых больше нет в 1С (после upsert свежих).

    В отличие от полного DELETE перед загрузкой, не оставляет окно,
    когда параллельный запрос видит пустой справочник.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if keep_codes:
            cur.execute(
                'DELETE FROM nomenclature WHERE parent_ref_key = %s AND NOT (code = ANY(%s))',
                (parent_ref_key, keep_codes))
        else:
            cur.execute('DELETE FROM nomenclature WHERE parent_ref_key = %s',
                        (parent_ref_key,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting stale nomenclature for {parent_ref_key}: {e}")
    finally:
        conn.close()


def delete_nomenclature_by_parent(parent_ref_key: str):
    """Удаляет всю номенклатуру для указанной папки (чтобы не было устаревших)."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM nomenclature WHERE parent_ref_key = %s', (parent_ref_key,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting nomenclature for parent {parent_ref_key}: {e}")
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


def get_nomenclature_by_parent(parent_ref_key: str) -> List[Dict]:
    """Возвращает номенклатуру только для указанного Parent_Key."""
    conn = get_db_connection()
    items = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM nomenclature WHERE parent_ref_key = %s ORDER BY name',
                    (parent_ref_key,))
        items = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching nomenclature by parent {parent_ref_key}: {e}")
    finally:
        conn.close()
    return items


# ============================================================
# MEASUREMENT UNITS
# ============================================================

def upsert_measurement_unit(code: str, name: str, ref_key: str = None):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO measurement_units (code, name, ref_key, last_updated)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                ref_key = COALESCE(EXCLUDED.ref_key, measurement_units.ref_key),
                last_updated = NOW()
        ''', (code, name, ref_key))
        conn.commit()
    except Exception as e:
        logger.error(f"Error upserting measurement unit {code}: {e}")
    finally:
        conn.close()


def get_all_measurement_units() -> List[Dict]:
    conn = get_db_connection()
    items = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM measurement_units ORDER BY name')
        items = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching measurement units: {e}")
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
                lang, telegram_user_id, sender_name, to_date,
                department, department_ref_key,
                machine_inventory, machine_model, machine_plate, machine_ref_key,
                responsible_person, responsible_person_ref_key,
                repair_type, repair_type_ref_key,
                breakdown_reason,
                repair_start_date, repair_end_date,
                downtime_days, downtime_hours,
                used_parts
            ) VALUES (
                %s, %s, %s, %s,
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
            data.get('sender_name'),
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


def add_maintenance_photos(report_id: int, photos: Dict[str, Any]) -> None:
    """Добавляет пути к фото в JSONB-колонку photos отчёта о ТО."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE maintenance_reports
            SET photos = COALESCE(photos, '{}'::jsonb) || %s
            WHERE id = %s
        ''', (Jsonb(photos), report_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error attaching photos to maintenance report {report_id}: {e}")
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


# ============================================================
# DAILY INSPECTIONS (Ежедневные чек-листы — отдельная таблица)
# ============================================================

# Ключи, которые идут в отдельные колонки daily_inspections (не в JSONB)
_DAILY_META_KEYS = {
    'form_type', 'lang', 'telegram_user_id', 'inspection_date',
    'department_uid', 'department_ref_key',
    'driver_uid', 'driver_name', 'driver_ref_key',
    'machine_uid', 'machine_inv', 'model', 'license_plate', 'machine_ref_key',
    'capacity_of_fuel_in_fueltank', 'fuel_type', 'motorhours', 'mileage',
    'geo_latitude', 'geo_longitude', 'geo_address', 'timestamp', 'sender_name',
}


def save_daily_inspection(data: Dict[str, Any]) -> Optional[int]:
    """Сохраняет ежедневный чек-лист в daily_inspections. Возвращает id записи."""
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

        results = {k: v for k, v in data.items() if k not in _DAILY_META_KEYS}

        def to_int(val, default=0):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default

        def to_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return None

        cur.execute('''
            INSERT INTO daily_inspections (
                lang, telegram_user_id, sender_name, inspection_date,
                project, project_ref_key,
                operator_name, operator_ref_key,
                machine_inventory, machine_model, machine_plate, machine_ref_key,
                fuel_amount, fuel_type, motorhours,
                geo_latitude, geo_longitude, geo_address,
                results
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s
            ) RETURNING id
        ''', (
            data.get('lang', 'ru'),
            data.get('telegram_user_id'),
            data.get('sender_name'),
            inspection_date,
            data.get('department_uid'),
            data.get('department_ref_key'),
            data.get('driver_name'),
            data.get('driver_ref_key'),
            data.get('machine_inv'),
            data.get('model'),
            data.get('license_plate'),
            data.get('machine_ref_key'),
            data.get('capacity_of_fuel_in_fueltank'),
            data.get('fuel_type'),
            to_int(data.get('motorhours')),
            to_float(data.get('geo_latitude')),
            to_float(data.get('geo_longitude')),
            data.get('geo_address'),
            Jsonb(results),
        ))
        row = cur.fetchone()
        conn.commit()
        daily_id = row['id'] if row else None
        logger.info(f"Daily inspection saved with id={daily_id}")
        return daily_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving daily inspection: {e}")
        return None
    finally:
        conn.close()


def add_daily_inspection_photos(daily_id: int, photos: Dict[str, Any]) -> None:
    """Добавляет пути к фото в results JSONB записи daily_inspections."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE daily_inspections
            SET results = COALESCE(results, '{}'::jsonb) || %s
            WHERE id = %s
        ''', (Jsonb({'photos': photos}), daily_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error attaching photos to daily inspection {daily_id}: {e}")
    finally:
        conn.close()


def _filters_sql(filters: Optional[Dict[str, str]]) -> tuple:
    """(sql, params) из словаря {имя_колонки: значение}.

    Имена колонок задаются только кодом (белый список на месте вызова),
    значения — параметризованы.
    """
    sql, params = '', []
    for col, val in (filters or {}).items():
        if val:
            sql += f' AND {col} = %s'
            params.append(val)
    return sql, params


def get_daily_inspections(date_from=None, date_to=None, limit: int = 200,
                          filters: Dict[str, str] = None) -> List[Dict]:
    """Возвращает ежедневные чек-листы, новые сверху, с фильтрами."""
    conn = get_db_connection()
    records = []
    try:
        cur = conn.cursor()
        query = 'SELECT * FROM daily_inspections WHERE TRUE'
        params = []
        if date_from:
            query += ' AND created_at::date >= %s'
            params.append(date_from)
        if date_to:
            query += ' AND created_at::date <= %s'
            params.append(date_to)
        fsql, fparams = _filters_sql(filters)
        query += fsql
        params += fparams
        query += ' ORDER BY created_at DESC LIMIT %s'
        params.append(limit)
        cur.execute(query, params)
        records = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching daily inspections: {e}")
    finally:
        conn.close()
    return records


def get_daily_inspection_by_id(daily_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM daily_inspections WHERE id = %s', (daily_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching daily inspection {daily_id}: {e}")
        return None
    finally:
        conn.close()


def get_inspections_history(date_from=None, date_to=None, limit: int = 200,
                            filters: Dict[str, str] = None) -> List[Dict]:
    """Еженедельные чек-листы (inspections) для админки, без тяжёлого results."""
    conn = get_db_connection()
    records = []
    try:
        cur = conn.cursor()
        query = ('SELECT id, form_type, lang, telegram_user_id, sender_name, inspection_date, '
                 'department, driver_name, mechanic_name, machine_inventory, machine_model, '
                 'machine_plate, mileage, motorhours, created_at FROM inspections WHERE TRUE')
        params = []
        if date_from:
            query += ' AND created_at::date >= %s'
            params.append(date_from)
        if date_to:
            query += ' AND created_at::date <= %s'
            params.append(date_to)
        fsql, fparams = _filters_sql(filters)
        query += fsql
        params += fparams
        query += ' ORDER BY created_at DESC LIMIT %s'
        params.append(limit)
        cur.execute(query, params)
        records = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching inspections history: {e}")
    finally:
        conn.close()
    return records


def get_inspection_by_id(inspection_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM inspections WHERE id = %s', (inspection_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching inspection {inspection_id}: {e}")
        return None
    finally:
        conn.close()


def get_maintenance_history(date_from=None, date_to=None, limit: int = 200,
                            filters: Dict[str, str] = None) -> List[Dict]:
    conn = get_db_connection()
    records = []
    try:
        cur = conn.cursor()
        query = 'SELECT * FROM maintenance_reports WHERE TRUE'
        params = []
        if date_from:
            query += ' AND created_at::date >= %s'
            params.append(date_from)
        if date_to:
            query += ' AND created_at::date <= %s'
            params.append(date_to)
        fsql, fparams = _filters_sql(filters)
        query += fsql
        params += fparams
        query += ' ORDER BY created_at DESC LIMIT %s'
        params.append(limit)
        cur.execute(query, params)
        records = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching maintenance history: {e}")
    finally:
        conn.close()
    return records


def get_maintenance_report_by_id(report_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM maintenance_reports WHERE id = %s', (report_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching maintenance report {report_id}: {e}")
        return None
    finally:
        conn.close()


def get_submission_stats_for_date(day) -> Dict[str, Any]:
    """Статистика за день: кто и сколько отчётов отправил (по трём таблицам)."""
    conn = get_db_connection()
    stats = {'daily': [], 'weekly': [], 'to': [],
             'daily_total': 0, 'weekly_total': 0, 'to_total': 0}
    try:
        cur = conn.cursor()
        # Отправитель: Ф.И.О зарегистрированного пользователя бота (sender_name);
        # для старых записей — фолбэк на оператора/водителя/ответственного
        cur.execute('''
            SELECT COALESCE(NULLIF(sender_name, ''), NULLIF(operator_name, ''),
                            telegram_user_id, 'Неизвестно') AS sender,
                   COUNT(*) AS cnt
            FROM daily_inspections WHERE created_at::date = %s
            GROUP BY 1 ORDER BY cnt DESC
        ''', (day,))
        stats['daily'] = [dict(r) for r in cur.fetchall()]
        cur.execute('''
            SELECT COALESCE(NULLIF(sender_name, ''), NULLIF(driver_name, ''),
                            telegram_user_id, 'Неизвестно') AS sender,
                   COUNT(*) AS cnt
            FROM inspections WHERE created_at::date = %s
            GROUP BY 1 ORDER BY cnt DESC
        ''', (day,))
        stats['weekly'] = [dict(r) for r in cur.fetchall()]
        cur.execute('''
            SELECT COALESCE(NULLIF(sender_name, ''), NULLIF(responsible_person, ''),
                            telegram_user_id, 'Неизвестно') AS sender,
                   COUNT(*) AS cnt
            FROM maintenance_reports WHERE created_at::date = %s
            GROUP BY 1 ORDER BY cnt DESC
        ''', (day,))
        stats['to'] = [dict(r) for r in cur.fetchall()]
        stats['daily_total'] = sum(r['cnt'] for r in stats['daily'])
        stats['weekly_total'] = sum(r['cnt'] for r in stats['weekly'])
        stats['to_total'] = sum(r['cnt'] for r in stats['to'])
    except Exception as e:
        logger.error(f"Error fetching submission stats for {day}: {e}")
    finally:
        conn.close()
    return stats


def update_daily_geo_address(daily_id: int, address: str) -> None:
    """Дописывает геокодированный адрес к ежедневному отчёту (фоновая задача)."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('UPDATE daily_inspections SET geo_address = %s WHERE id = %s',
                    (address, daily_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating geo address for daily {daily_id}: {e}")
    finally:
        conn.close()


# ============================================================
# ANALYTICS (пропуски отчётов и поломки по машинам)
# ============================================================

def get_daily_dates_by_machine(filters: Dict[str, str] = None) -> List[Dict]:
    """Даты отправки ежедневных отчётов по каждой машине (у которой был ≥1 отчёт)."""
    conn = get_db_connection()
    rows = []
    try:
        cur = conn.cursor()
        fsql, fparams = _filters_sql(filters)
        cur.execute(f'''
            SELECT COALESCE(NULLIF(machine_inventory, ''), '—') AS machine_inventory,
                   COALESCE(NULLIF(machine_model, ''), 'Неизвестно') AS machine_model,
                   COALESCE(machine_plate, '') AS machine_plate,
                   COUNT(*) AS total,
                   array_agg(DISTINCT created_at::date) AS dates
            FROM daily_inspections WHERE TRUE{fsql}
            GROUP BY 1, 2, 3
        ''', fparams)
        rows = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching daily dates by machine: {e}")
    finally:
        conn.close()
    return rows


def get_weekly_dates_by_machine(filters: Dict[str, str] = None) -> List[Dict]:
    """Даты отправки еженедельных чек-листов по каждой машине."""
    conn = get_db_connection()
    rows = []
    try:
        cur = conn.cursor()
        fsql, fparams = _filters_sql(filters)
        cur.execute(f'''
            SELECT COALESCE(NULLIF(machine_inventory, ''), '—') AS machine_inventory,
                   COALESCE(NULLIF(machine_model, ''), 'Неизвестно') AS machine_model,
                   COALESCE(machine_plate, '') AS machine_plate,
                   COUNT(*) AS total,
                   array_agg(DISTINCT created_at::date) AS dates
            FROM inspections WHERE TRUE{fsql}
            GROUP BY 1, 2, 3
        ''', fparams)
        rows = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching weekly dates by machine: {e}")
    finally:
        conn.close()
    return rows


def get_maintenance_for_analytics(filters: Dict[str, str] = None) -> List[Dict]:
    """Отчёты о ТО для аналитики поломок (только нужные колонки)."""
    conn = get_db_connection()
    rows = []
    try:
        cur = conn.cursor()
        fsql, fparams = _filters_sql(filters)
        cur.execute(f'''
            SELECT machine_inventory, machine_model, machine_plate,
                   repair_type, breakdown_reason,
                   downtime_days, downtime_hours, to_date, created_at
            FROM maintenance_reports WHERE TRUE{fsql}
            ORDER BY created_at DESC
        ''', fparams)
        rows = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching maintenance analytics: {e}")
    finally:
        conn.close()
    return rows


# Конфигурация фильтров по типам отчётов: таблица и колонки для каждой роли.
# Роли: machine (инв. номер), sender (Ф.И.О отправителя), person
# (оператор/водитель/ответственный), project (проект/подразделение).
FILTER_SCHEMES = {
    'daily': {
        'table': 'daily_inspections',
        'machine': 'machine_inventory', 'sender': 'sender_name',
        'person': 'operator_name', 'project': 'project',
        'person_label': 'Оператор', 'project_label': 'Проект',
    },
    'weekly': {
        'table': 'inspections',
        'machine': 'machine_inventory', 'sender': 'sender_name',
        'person': 'driver_name', 'project': 'department',
        'person_label': 'Водитель', 'project_label': 'Подразделение',
    },
    'to': {
        'table': 'maintenance_reports',
        'machine': 'machine_inventory', 'sender': 'sender_name',
        'person': 'responsible_person', 'project': 'department',
        'person_label': 'Ответственный', 'project_label': 'Подразделение',
    },
}


def get_filter_options(rtype: str) -> Dict[str, list]:
    """Уникальные значения для выпадающих фильтров данного типа отчётов."""
    scheme = FILTER_SCHEMES.get(rtype)
    if not scheme:
        return {}
    table = scheme['table']
    options = {'machines': [], 'senders': [], 'persons': [], 'projects': []}
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(f'''
            SELECT DISTINCT machine_inventory, machine_model, machine_plate
            FROM {table}
            WHERE machine_inventory IS NOT NULL AND machine_inventory <> ''
            ORDER BY machine_model, machine_inventory
        ''')
        options['machines'] = [dict(r) for r in cur.fetchall()]
        for key, col in (('senders', scheme['sender']),
                         ('persons', scheme['person']),
                         ('projects', scheme['project'])):
            cur.execute(f'''
                SELECT DISTINCT {col} AS v FROM {table}
                WHERE {col} IS NOT NULL AND {col} <> ''
                ORDER BY 1
            ''')
            options[key] = [r['v'] for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching filter options for {rtype}: {e}")
    finally:
        conn.close()
    return options


# ============================================================
# BOT USERS (регистрация пользователей бота: Ф.И.О отправителя)
# ============================================================

def get_bot_user(telegram_user_id: str) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM bot_users WHERE telegram_user_id = %s',
                    (str(telegram_user_id),))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching bot user {telegram_user_id}: {e}")
        return None
    finally:
        conn.close()


def upsert_bot_user(telegram_user_id: str, full_name: str) -> Optional[int]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO bot_users (telegram_user_id, full_name)
            VALUES (%s, %s)
            ON CONFLICT (telegram_user_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        ''', (str(telegram_user_id), full_name))
        row = cur.fetchone()
        conn.commit()
        return row['id'] if row else None
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting bot user {telegram_user_id}: {e}")
        return None
    finally:
        conn.close()


# ============================================================
# 1C SYNC QUEUE (надёжная доставка документов в 1С)
# ============================================================

def enqueue_1c_task(kind: str, record_id, payload: Dict[str, Any]) -> Optional[int]:
    """Ставит задачу выгрузки в 1С в очередь. kind: checklist | to_report | mileage."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO one_c_sync_queue (kind, record_id, payload)
            VALUES (%s, %s, %s) RETURNING id
        ''', (kind, record_id, Jsonb(payload)))
        row = cur.fetchone()
        conn.commit()
        return row['id'] if row else None
    except Exception as e:
        conn.rollback()
        logger.error(f"Error enqueueing 1C task ({kind}): {e}")
        return None
    finally:
        conn.close()


def fetch_due_1c_tasks(limit: int = 20, max_attempts: int = 20) -> List[Dict]:
    """Задачи очереди 1С, готовые к (пере)отправке."""
    conn = get_db_connection()
    tasks = []
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT * FROM one_c_sync_queue
            WHERE synced = FALSE AND attempts < %s AND next_attempt_at <= CURRENT_TIMESTAMP
            ORDER BY id
            LIMIT %s
        ''', (max_attempts, limit))
        tasks = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching due 1C tasks: {e}")
    finally:
        conn.close()
    return tasks


def mark_1c_task(task_id: int, ok: bool, error: str = None) -> None:
    """Отмечает результат попытки; при неудаче назначает следующую с бэкоффом."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if ok:
            cur.execute('''
                UPDATE one_c_sync_queue
                SET synced = TRUE, last_error = %s, attempts = attempts + 1
                WHERE id = %s
            ''', (error, task_id))
        else:
            # Бэкофф: 5 минут * номер попытки, максимум 60 минут
            cur.execute('''
                UPDATE one_c_sync_queue
                SET attempts = attempts + 1,
                    last_error = %s,
                    next_attempt_at = CURRENT_TIMESTAMP
                        + LEAST(attempts + 1, 12) * INTERVAL '5 minutes'
                WHERE id = %s
            ''', (error, task_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error marking 1C task {task_id}: {e}")
    finally:
        conn.close()


# ============================================================
# APP STATE (ключ-значение: отметки планировщиков и т.п.)
# ============================================================

def claim_app_state(key: str, value: str) -> bool:
    """Атомарно записывает value для key, только если оно отличается.

    Возвращает True, если запись произошла (мы «застолбили» действие),
    False — если значение уже такое (действие выполнено другим инстансом).
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO app_state (key, value, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
                WHERE app_state.value IS DISTINCT FROM EXCLUDED.value
        ''', (key, value))
        claimed = cur.rowcount > 0
        conn.commit()
        return claimed
    except Exception as e:
        conn.rollback()
        logger.error(f"Error claiming app state {key}: {e}")
        return False
    finally:
        conn.close()


# ============================================================
# ADMINS (Администраторы админки)
# ============================================================

# Разрешённые к изменению поля (защита от инъекции имён колонок)
_ADMIN_UPDATABLE_FIELDS = {
    'password_hash', 'full_name', 'telegram_user_id',
    'is_superadmin', 'can_view_reports', 'can_view_history',
    'receive_instant_notifications', 'receive_daily_digest', 'is_active',
}

_ADMIN_FLAG_FIELDS = {
    'is_superadmin', 'can_view_reports', 'can_view_history',
    'receive_instant_notifications', 'receive_daily_digest',
}


def create_admin(username: str, password_hash: str, full_name: str = None,
                 telegram_user_id: str = None, **flags) -> Optional[int]:
    """Создаёт администратора. flags — булевы поля из _ADMIN_FLAG_FIELDS."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO admins (username, password_hash, full_name, telegram_user_id,
                                is_superadmin, can_view_reports, can_view_history,
                                receive_instant_notifications, receive_daily_digest)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            username, password_hash, full_name, telegram_user_id,
            bool(flags.get('is_superadmin')),
            bool(flags.get('can_view_reports', True)),
            bool(flags.get('can_view_history')),
            bool(flags.get('receive_instant_notifications')),
            bool(flags.get('receive_daily_digest')),
        ))
        row = cur.fetchone()
        conn.commit()
        return row['id'] if row else None
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating admin {username}: {e}")
        return None
    finally:
        conn.close()


def get_admin_by_username(username: str) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM admins WHERE username = %s', (username,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching admin {username}: {e}")
        return None
    finally:
        conn.close()


def get_admin_by_telegram_id(telegram_user_id: str) -> Optional[Dict]:
    """Активный администратор по Telegram ID (для входа из Mini App)."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT * FROM admins
            WHERE telegram_user_id = %s AND is_active = TRUE
            LIMIT 1
        ''', (str(telegram_user_id),))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching admin by telegram id {telegram_user_id}: {e}")
        return None
    finally:
        conn.close()


def get_admin_by_id(admin_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM admins WHERE id = %s', (admin_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching admin id={admin_id}: {e}")
        return None
    finally:
        conn.close()


def get_all_admins() -> List[Dict]:
    conn = get_db_connection()
    admins = []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM admins ORDER BY created_at')
        admins = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching admins: {e}")
    finally:
        conn.close()
    return admins


def update_admin(admin_id: int, fields: Dict[str, Any]) -> bool:
    """Обновляет разрешённые поля администратора."""
    safe = {k: v for k, v in fields.items() if k in _ADMIN_UPDATABLE_FIELDS}
    if not safe:
        return False
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        set_clause = ', '.join(f'{k} = %s' for k in safe)
        cur.execute(f'UPDATE admins SET {set_clause} WHERE id = %s',
                    (*safe.values(), admin_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating admin {admin_id}: {e}")
        return False
    finally:
        conn.close()


def get_admins_with_flag(flag: str) -> List[Dict]:
    """Активные администраторы с включённым флагом (для рассылок)."""
    if flag not in _ADMIN_FLAG_FIELDS:
        return []
    conn = get_db_connection()
    admins = []
    try:
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM admins WHERE is_active = TRUE AND {flag} = TRUE')
        admins = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching admins with flag {flag}: {e}")
    finally:
        conn.close()
    return admins


def ensure_default_admin(username: str, password_hash: str) -> None:
    """Создаёт первого суперадмина, если таблица admins пуста."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) AS cnt FROM admins')
        row = cur.fetchone()
        if row and row['cnt'] == 0:
            cur.execute('''
                INSERT INTO admins (username, password_hash, full_name,
                                    is_superadmin, can_view_reports, can_view_history,
                                    receive_instant_notifications, receive_daily_digest)
                VALUES (%s, %s, %s, TRUE, TRUE, TRUE, TRUE, TRUE)
            ''', (username, password_hash, 'Главный администратор'))
            conn.commit()
            logger.warning(f"Default admin '{username}' created — смените пароль после первого входа!")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error ensuring default admin: {e}")
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
