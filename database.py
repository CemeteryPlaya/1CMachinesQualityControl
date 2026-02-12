import sqlite3
import logging
from typing import List, Dict, Optional
from datetime import datetime

DB_NAME = "machines.db"

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def check_table_exists(conn, table_name: str) -> bool:
    """Проверяет существование таблицы"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None

def get_table_columns(conn, table_name: str) -> set:
    """Получает список колонок таблицы"""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}

def init_db():
    """Инициализирует БД с проверкой структуры и миграцией при необходимости"""
    conn = get_db_connection()
    try:
        # Проверяем таблицу machines
        if check_table_exists(conn, 'machines'):
            logger.info("Table 'machines' exists, checking structure...")
            columns = get_table_columns(conn, 'machines')
            required_columns = {'id', 'inventory_number', 'model', 'license_plate', 'last_updated'}

            if not required_columns.issubset(columns):
                logger.warning("Table 'machines' has incorrect structure. Recreating...")
                conn.execute('DROP TABLE machines')
                conn.commit()

        # Проверяем таблицу employees
        if check_table_exists(conn, 'employees'):
            logger.info("Table 'employees' exists, checking structure...")
            columns = get_table_columns(conn, 'employees')
            required_columns = {'id', 'employee_code', 'full_name', 'position_type', 'last_updated'}

            if not required_columns.issubset(columns):
                logger.warning("Table 'employees' has incorrect structure. Recreating...")
                conn.execute('DROP TABLE employees')
                conn.commit()

        # Создаем таблицы если их нет
        conn.execute('''
            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_number TEXT UNIQUE NOT NULL,
                model TEXT NOT NULL,
                license_plate TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                position_type TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        conn.close()

def upsert_machine(inventory_number: str, model: str, license_plate: str):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO machines (inventory_number, model, license_plate, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(inventory_number) DO UPDATE SET
                model = excluded.model,
                license_plate = excluded.license_plate,
                last_updated = CURRENT_TIMESTAMP
        ''', (inventory_number, model, license_plate))
        conn.commit()
    except Exception as e:
        logger.error(f"Error upserting machine {inventory_number}: {e}")
    finally:
        conn.close()

def get_all_machines() -> List[Dict]:
    conn = get_db_connection()
    machines = []
    try:
        rows = conn.execute('SELECT * FROM machines').fetchall()
        for row in rows:
            machines.append(dict(row))
    except Exception as e:
        logger.error(f"Error fetching machines from DB: {e}")
    finally:
        conn.close()
    return machines

def get_machine_by_id(machine_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    machine = None
    try:
        row = conn.execute('SELECT * FROM machines WHERE id = ?', (machine_id,)).fetchone()
        if row:
            machine = dict(row)
    except Exception as e:
        logger.error(f"Error fetching machine {machine_id}: {e}")
    finally:
        conn.close()
    return machine


def upsert_employee(employee_code: str, full_name: str, position_type: str):
    """Adds or updates an employee in the database"""
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO employees (employee_code, full_name, position_type, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(employee_code) DO UPDATE SET
                full_name = excluded.full_name,
                position_type = excluded.position_type,
                last_updated = CURRENT_TIMESTAMP
        ''', (employee_code, full_name, position_type))
        conn.commit()
    except Exception as e:
        logger.error(f"Error upserting employee {employee_code}: {e}")
    finally:
        conn.close()


def get_all_employees() -> List[Dict]:
    """Returns all employees from database"""
    conn = get_db_connection()
    employees = []
    try:
        rows = conn.execute('SELECT * FROM employees').fetchall()
        for row in rows:
            employees.append(dict(row))
    except Exception as e:
        logger.error(f"Error fetching employees from DB: {e}")
    finally:
        conn.close()
    return employees


def get_employees_by_position(position_type: str) -> List[Dict]:
    """Returns employees filtered by position type (DRIVER or MECHANIC)"""
    conn = get_db_connection()
    employees = []
    try:
        rows = conn.execute('SELECT * FROM employees WHERE position_type = ?', (position_type,)).fetchall()
        for row in rows:
            employees.append(dict(row))
    except Exception as e:
        logger.error(f"Error fetching employees by position {position_type}: {e}")
    finally:
        conn.close()
    return employees


def get_employee_by_id(employee_id: int) -> Optional[Dict]:
    """Returns employee by ID"""
    conn = get_db_connection()
    employee = None
    try:
        row = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
        if row:
            employee = dict(row)
    except Exception as e:
        logger.error(f"Error fetching employee {employee_id}: {e}")
    finally:
        conn.close()
    return employee
