-- Таблицы для PostgreSQL, аналог machines.db (SQLite)

CREATE TABLE IF NOT EXISTS machines (
    id SERIAL PRIMARY KEY,
    inventory_number TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    license_plate TEXT,
    ref_key TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    employee_code TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    position_type TEXT NOT NULL,
    ref_key TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    department_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    ref_key TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
);
