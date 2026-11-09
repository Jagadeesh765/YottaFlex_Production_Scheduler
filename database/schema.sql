-- YottaFlex Production Scheduling System
-- Database Schema

PRAGMA foreign_keys = ON;

-- 1. Product
CREATE TABLE IF NOT EXISTS Product (
    product_id TEXT PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 2. Routing
CREATE TABLE IF NOT EXISTS Routing (
    routing_id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    routing_version INTEGER NOT NULL CHECK (routing_version > 0),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'INACTIVE')),
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    CHECK (effective_to IS NULL OR effective_to > effective_from)
);

-- 3. Operation
CREATE TABLE IF NOT EXISTS Operation (
    operation_id TEXT PRIMARY KEY,
    routing_id TEXT NOT NULL,
    operation_name TEXT NOT NULL,
    operation_sequence INTEGER NOT NULL CHECK (operation_sequence > 0),
    setup_time INTEGER NOT NULL CHECK (setup_time >= 0),
    processing_time INTEGER NOT NULL CHECK (processing_time > 0),
    time_unit TEXT NOT NULL,
    UNIQUE (routing_id, operation_sequence),
    FOREIGN KEY (routing_id) REFERENCES Routing(routing_id)
);

-- 4. Machine
CREATE TABLE IF NOT EXISTS Machine (
    machine_id TEXT PRIMARY KEY,
    machine_name TEXT NOT NULL,
    machine_type TEXT NOT NULL,
    work_center_id TEXT NOT NULL,
    capacity REAL NOT NULL CHECK (capacity > 0),
    capacity_unit TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'MAINTENANCE'))
);

-- 5. MachineCalendar
CREATE TABLE IF NOT EXISTS MachineCalendar (
    calendar_id TEXT PRIMARY KEY,
    machine_id TEXT NOT NULL,
    calendar_date TEXT NOT NULL,
    shift_start TEXT NOT NULL,
    shift_end TEXT NOT NULL,
    break_duration INTEGER NOT NULL CHECK (break_duration >= 0),
    available_minutes INTEGER NOT NULL CHECK (available_minutes >= 0),
    is_working_day INTEGER NOT NULL CHECK (is_working_day IN (0, 1)),
    FOREIGN KEY (machine_id) REFERENCES Machine(machine_id),
    CHECK (shift_end > shift_start)
);

-- 6. Material
CREATE TABLE IF NOT EXISTS Material (
    material_id TEXT PRIMARY KEY,
    material_name TEXT NOT NULL,
    material_type TEXT NOT NULL,
    unit TEXT NOT NULL,
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days >= 0),
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'INACTIVE'))
);

-- 7. InventoryLot
CREATE TABLE IF NOT EXISTS InventoryLot (
    lot_id TEXT PRIMARY KEY,
    material_id TEXT NOT NULL,
    lot_number TEXT NOT NULL UNIQUE,
    quantity_received REAL NOT NULL CHECK (quantity_received > 0),
    quantity_available REAL NOT NULL CHECK (quantity_available >= 0),
    received_date TEXT NOT NULL,
    available_from TEXT NOT NULL,
    expiry_date TEXT,
    lot_status TEXT NOT NULL,
    FOREIGN KEY (material_id) REFERENCES Material(material_id),
    CHECK (quantity_available <= quantity_received),
    CHECK (expiry_date IS NULL OR expiry_date > received_date)
);

-- 8. ProductionOrder
CREATE TABLE IF NOT EXISTS ProductionOrder (
    production_order_id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    routing_id TEXT NOT NULL,
    order_quantity INTEGER NOT NULL CHECK (order_quantity > 0),
    planned_start_date TEXT NOT NULL,
    planned_end_date TEXT NOT NULL,
    actual_start_date TEXT,
    actual_end_date TEXT,
    due_date TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK (priority > 0),
    order_status TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    FOREIGN KEY (routing_id) REFERENCES Routing(routing_id),
    CHECK (planned_end_date > planned_start_date),
    CHECK (
        actual_end_date IS NULL
        OR actual_start_date IS NULL
        OR actual_end_date > actual_start_date
    )
);

-- 9. OperationSchedule
CREATE TABLE IF NOT EXISTS OperationSchedule (
    schedule_id TEXT PRIMARY KEY,
    production_order_id TEXT NOT NULL,
    operation_id TEXT NOT NULL,
    machine_id TEXT NOT NULL,
    scheduled_start TEXT NOT NULL,
    scheduled_end TEXT NOT NULL,
    setup_duration INTEGER NOT NULL CHECK (setup_duration >= 0),
    processing_duration INTEGER NOT NULL CHECK (processing_duration > 0),
    schedule_status TEXT NOT NULL,
    FOREIGN KEY (production_order_id)
        REFERENCES ProductionOrder(production_order_id),
    FOREIGN KEY (operation_id) REFERENCES Operation(operation_id),
    FOREIGN KEY (machine_id) REFERENCES Machine(machine_id),
    CHECK (scheduled_end > scheduled_start)
);

-- 10. ChangeoverMatrix
CREATE TABLE IF NOT EXISTS ChangeoverMatrix (
    changeover_id TEXT PRIMARY KEY,
    from_product_id TEXT NOT NULL,
    to_product_id TEXT NOT NULL,
    from_machine_type TEXT NOT NULL,
    to_machine_type TEXT NOT NULL,
    changeover_minutes INTEGER NOT NULL CHECK (changeover_minutes >= 0),
    FOREIGN KEY (from_product_id) REFERENCES Product(product_id),
    FOREIGN KEY (to_product_id) REFERENCES Product(product_id)
);


-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_routing_product
ON Routing(product_id);

CREATE INDEX IF NOT EXISTS idx_operation_routing
ON Operation(routing_id);

CREATE INDEX IF NOT EXISTS idx_calendar_machine_date
ON MachineCalendar(machine_id, calendar_date);

CREATE INDEX IF NOT EXISTS idx_inventory_material
ON InventoryLot(material_id);

CREATE INDEX IF NOT EXISTS idx_schedule_machine_time
ON OperationSchedule(machine_id, scheduled_start, scheduled_end);

CREATE INDEX IF NOT EXISTS idx_order_due_date
ON ProductionOrder(due_date);