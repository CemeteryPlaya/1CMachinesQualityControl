-- Таблицы для PostgreSQL, аналог machines.db (SQLite)

CREATE TABLE IF NOT EXISTS machines (
    id SERIAL PRIMARY KEY,
    inventory_number TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    license_plate TEXT,
    ref_key TEXT,
    vehicle_type TEXT DEFAULT 'lv',
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

CREATE TABLE IF NOT EXISTS repair_types (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    ref_key TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
);

CREATE TABLE IF NOT EXISTS mileage_history (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER NOT NULL REFERENCES machines(id),
    mileage INTEGER DEFAULT 0,
    motorhours INTEGER DEFAULT 0,
    source TEXT DEFAULT 'checklist',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mileage_history_machine
ON mileage_history(machine_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS nomenclature (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    ref_key TEXT,
    parent_ref_key TEXT,
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
