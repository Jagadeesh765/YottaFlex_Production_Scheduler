# YottaFlex Production Scheduling System

# Data Dictionary

## 1. Product

Description:
Stores manufacturing product information.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| product_id | VARCHAR(25) | Yes | Primary Key |
| sku | VARCHAR(30) | Yes | Unique |
| product_name | VARCHAR(100) | Yes | Not Empty |
| category | VARCHAR(50) | Yes | Valid Category |
| unit | VARCHAR(20) | Yes | Valid Unit |
| created_at | DATETIME | Yes | Valid Date |

Primary Key:
product_id

Example ID:
PROD-2026-000001

Relationships:
- One Product can have multiple Routings.
- One Product can have multiple Production Orders.

Validation:
- Product ID must be unique.
- SKU must be unique.
- Product name cannot be empty.
- Category and unit must contain valid values.

---

## 2. Routing

Description:
Defines the sequence of manufacturing processes required to produce a product.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| routing_id | VARCHAR(40) | Yes | Primary Key |
| product_id | VARCHAR(25) | Yes | Foreign Key |
| routing_version | INTEGER | Yes | Must be positive |
| effective_from | DATE | Yes | Valid Date |
| effective_to | DATE | No | Must be after effective_from |
| status | VARCHAR(20) | Yes | ACTIVE, INACTIVE |

Primary Key:
routing_id

Foreign Key:
product_id references Product(product_id)

Example ID:
ROUTE-SKU001-01

Relationships:
- One Product can have multiple Routings.
- One Routing can contain multiple Operations.

Validation:
- Routing ID must be unique.
- Every Routing must reference a valid Product.
- Routing version must be positive.
- Only one active routing version should apply to a product for a given production date.

---

## 3. Operation

Description:
Stores manufacturing operations and their sequence within a routing.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| operation_id | VARCHAR(30) | Yes | Primary Key |
| routing_id | VARCHAR(40) | Yes | Foreign Key |
| operation_name | VARCHAR(100) | Yes | Not Empty |
| operation_sequence | INTEGER | Yes | Must be positive |
| setup_time | INTEGER | Yes | Cannot be negative |
| processing_time | INTEGER | Yes | Must be greater than zero |
| time_unit | VARCHAR(20) | Yes | Valid Time Unit |

Primary Key:
operation_id

Foreign Key:
routing_id references Routing(routing_id)

Example ID:
OP-2026-000001

Relationships:
- One Routing can contain multiple Operations.
- Each Operation belongs to one Routing.
- One Operation can have multiple Operation Schedules.

Validation:
- Operation ID must be unique.
- Operation sequence must be unique within a Routing.
- Processing time must be greater than zero.
- Setup time cannot be negative.
- Every Operation must belong to a valid Routing.

---

## 4. Machine

Description:
Stores details about machines available for production operations.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| machine_id | VARCHAR(30) | Yes | Primary Key |
| machine_name | VARCHAR(100) | Yes | Not Empty |
| machine_type | VARCHAR(50) | Yes | Valid Type |
| work_center_id | VARCHAR(30) | Yes | Valid Work Center |
| capacity | DECIMAL(12,2) | Yes | Must be greater than zero |
| capacity_unit | VARCHAR(20) | Yes | Valid Unit |
| status | VARCHAR(20) | Yes | ACTIVE, INACTIVE, MAINTENANCE |

Primary Key:
machine_id

Example ID:
MACH-2026-000001

Relationships:
- One Machine can have multiple MachineCalendar records.
- One Machine can be assigned to multiple Operation Schedules.
- One Machine can have multiple ChangeoverMatrix records.

Validation:
- Machine ID must be unique.
- Machine capacity must be greater than zero.
- Machine status must be valid.
- Inactive or maintenance machines must not receive production schedules.

---

## 5. MachineCalendar

Description:
Stores machine working schedules, shifts, breaks, and unavailable periods.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| calendar_id | VARCHAR(30) | Yes | Primary Key |
| machine_id | VARCHAR(30) | Yes | Foreign Key |
| calendar_date | DATE | Yes | Valid Date |
| shift_start | TIME | Yes | Valid Time |
| shift_end | TIME | Yes | Must be after shift_start |
| break_duration | INTEGER | Yes | Cannot be negative |
| available_minutes | INTEGER | Yes | Cannot be negative |
| is_working_day | BOOLEAN | Yes | TRUE or FALSE |

Primary Key:
calendar_id

Foreign Key:
machine_id references Machine(machine_id)

Relationships:
- Each MachineCalendar record belongs to one Machine.
- One Machine can have multiple MachineCalendar records.

Validation:
- Every calendar record must reference a valid Machine.
- Shift end must be after shift start.
- Break duration cannot be negative.
- Available minutes cannot be negative.
- Non-working days must not be used for production scheduling.

---

## 6. Material

Description:
Stores information about raw materials required for manufacturing products.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| material_id | VARCHAR(30) | Yes | Primary Key |
| material_name | VARCHAR(100) | Yes | Not Empty |
| material_type | VARCHAR(50) | Yes | Valid Type |
| unit | VARCHAR(20) | Yes | Valid Unit |
| lead_time_days | INTEGER | Yes | Cannot be negative |
| status | VARCHAR(20) | Yes | ACTIVE, INACTIVE |

Primary Key:
material_id

Example ID:
MAT-2026-000001

Relationships:
- One Material can have multiple Inventory Lots.
- Materials can be required by multiple Operations.

Validation:
- Material ID must be unique.
- Material name cannot be empty.
- Lead time cannot be negative.
- Material status must be valid.

---

## 7. InventoryLot

Description:
Stores details about available material stock, including quantities and availability dates.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| lot_id | VARCHAR(30) | Yes | Primary Key |
| material_id | VARCHAR(30) | Yes | Foreign Key |
| lot_number | VARCHAR(50) | Yes | Unique |
| quantity_received | DECIMAL(12,2) | Yes | Greater than zero |
| quantity_available | DECIMAL(12,2) | Yes | Cannot be negative |
| received_date | DATE | Yes | Valid Date |
| available_from | DATETIME | Yes | Valid Date and Time |
| expiry_date | DATE | No | Must be after received_date |
| lot_status | VARCHAR(20) | Yes | Valid Status |

Primary Key:
lot_id

Foreign Key:
material_id references Material(material_id)

Relationships:
- Each InventoryLot belongs to one Material.
- One Material can have multiple Inventory Lots.

Validation:
- Every InventoryLot must reference a valid Material.
- Available quantity cannot exceed received quantity.
- Available quantity cannot be negative.
- Expiry date must be after received date.
- Expired or unavailable lots must not be used for production.

---

## 8. ProductionOrder

Description:
Stores customer production orders and their required quantities and delivery dates.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| production_order_id | VARCHAR(30) | Yes | Primary Key |
| product_id | VARCHAR(25) | Yes | Foreign Key |
| routing_id | VARCHAR(40) | Yes | Foreign Key |
| order_quantity | INTEGER | Yes | Must be greater than zero |
| planned_start_date | DATETIME | Yes | Valid Date and Time |
| planned_end_date | DATETIME | Yes | Must be after planned_start_date |
| actual_start_date | DATETIME | No | Valid Date and Time |
| actual_end_date | DATETIME | No | Must be after actual_start_date |
| due_date | DATETIME | Yes | Valid Date and Time |
| priority | INTEGER | Yes | Must be positive |
| order_status | VARCHAR(20) | Yes | Valid Status |

Primary Key:
production_order_id

Foreign Keys:
- product_id references Product(product_id)
- routing_id references Routing(routing_id)

Example ID:
PO-2026-000001

Relationships:
- One Product can have multiple Production Orders.
- Each Production Order uses one Routing.
- Each Production Order can generate multiple Operation Schedules.

Validation:
- Order quantity must be greater than zero.
- Planned end date must be after planned start date.
- Every Production Order must reference a valid Product and Routing.
- Order status must be valid.

---

## 9. OperationSchedule

Description:
Stores the scheduled start and end times of production operations on assigned machines.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| schedule_id | VARCHAR(30) | Yes | Primary Key |
| production_order_id | VARCHAR(30) | Yes | Foreign Key |
| operation_id | VARCHAR(30) | Yes | Foreign Key |
| machine_id | VARCHAR(30) | Yes | Foreign Key |
| scheduled_start | DATETIME | Yes | Valid Date and Time |
| scheduled_end | DATETIME | Yes | Must be after scheduled_start |
| setup_duration | INTEGER | Yes | Cannot be negative |
| processing_duration | INTEGER | Yes | Must be greater than zero |
| schedule_status | VARCHAR(20) | Yes | Valid Status |

Primary Key:
schedule_id

Foreign Keys:
- production_order_id references ProductionOrder(production_order_id)
- operation_id references Operation(operation_id)
- machine_id references Machine(machine_id)

Relationships:
- Each OperationSchedule belongs to one Production Order.
- Each OperationSchedule is assigned to one Operation and one Machine.

Validation:
- Scheduled end must be after scheduled start.
- Machine must be available during the scheduled period.
- Scheduled operations must respect routing sequence.
- Setup and processing durations must be valid.
- Machine schedules must not overlap.
- Operations must be scheduled within machine working shifts.

---

## 10. ChangeoverMatrix

Description:
Stores the setup time required when switching a machine from one product to another.

| Field | Data Type | Required | Validation |
|---|---|---|---|
| changeover_id | VARCHAR(30) | Yes | Primary Key |
| machine_id | VARCHAR(30) | Yes | Foreign Key |
| from_product_id | VARCHAR(25) | Yes | Foreign Key |
| to_product_id | VARCHAR(25) | Yes | Foreign Key |
| changeover_time | INTEGER | Yes | Cannot be negative |
| changeover_type | VARCHAR(30) | Yes | Valid Type |

Primary Key:
changeover_id

Foreign Keys:
- machine_id references Machine(machine_id)
- from_product_id references Product(product_id)
- to_product_id references Product(product_id)

Relationships:
- Each ChangeoverMatrix record belongs to one Machine.
- One Machine can have multiple ChangeoverMatrix records.
- Each record defines the transition time between two products on a machine.

Validation:
- Machine ID must reference a valid Machine.
- Both product IDs must reference valid Products.
- Changeover time cannot be negative.
- A changeover record must define a valid product transition.
- Changeover time must be considered between consecutive jobs on the same machine.

---

# End of Data Dictionary