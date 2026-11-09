
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Project configuration
SEED = 20261022

# Set random seed for reproducibility
np.random.seed(SEED)

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

print("YottaFlex Data Generator Initialized")
print("Random Seed:", SEED)
print("Data folder:", DATA_DIR)
print("Output folder:", OUTPUT_DIR)


def generate_products(count=100):
    categories = ["Electronics", "Automotive", "Industrial", "Consumer"]
    units = ["PCS", "KG", "BOX"]

    products = []

    for i in range(1, count + 1):
        products.append({
            "product_id": f"PROD-{i:06d}",
            "sku": f"SKU-{i:03d}",
            "product_name": f"Product {i}",
            "category": np.random.choice(categories),
            "unit": np.random.choice(units),
            "created_at": datetime.now().isoformat()
        })

    return pd.DataFrame(products)


# Generate 100 products
products_df = generate_products()

# Save product data
products_df.to_csv(DATA_DIR / "products.csv", index=False)

print("Products generated:", len(products_df))

# Generate routing data for all products
routing_data = []

for index, product in products_df.iterrows():
    routing_data.append({
        "routing_id": f"ROUTE-{index + 1:06d}",
        "product_id": product["product_id"],
        "routing_version": 1,
        "effective_from": "2026-01-01",
        "effective_to": None,
        "status": "ACTIVE"
    })

routing_df = pd.DataFrame(routing_data)

routing_df.to_csv(DATA_DIR / "routings.csv", index=False)

print("Routings generated:", len(routing_df))

# Generate 2,000 operations
operation_names = [
    "Cutting", "Drilling", "Welding", "Assembly",
    "Painting", "Inspection", "Packaging"
]

operation_data = []

for i in range(1, 2001):
    routing_number = ((i - 1) // 20) + 1

    operation_data.append({
        "operation_id": f"OP-{i:06d}",
        "routing_id": f"ROUTE-{routing_number:06d}",
        "operation_name": np.random.choice(operation_names),
        "operation_sequence": ((i - 1) % 20) + 1,
        "setup_time": int(np.random.randint(10, 61)),
        "processing_time": int(np.random.randint(15, 181)),
        "time_unit": "MINUTES"
    })

operations_df = pd.DataFrame(operation_data)

operations_df.to_csv(
    DATA_DIR / "operations.csv",
    index=False
)

print("Operations generated:", len(operations_df))

# Generate 40 machines
machine_types = ["CNC", "Welding", "Assembly", "Painting", "Packaging"]

machine_data = []

for i in range(1, 41):
    machine_data.append({
        "machine_id": f"MACH-{i:03d}",
        "machine_name": f"Machine {i}",
        "machine_type": np.random.choice(machine_types),
        "work_center_id": f"WC-{((i - 1) // 5) + 1:02d}",
        "capacity": int(np.random.randint(50, 201)),
        "capacity_unit": "PCS_PER_HOUR",
        "status": "ACTIVE"
    })

machines_df = pd.DataFrame(machine_data)

machines_df.to_csv(DATA_DIR / "machines.csv", index=False)

print("Machines generated:", len(machines_df))

# Generate machine calendar data
calendar_data = []

start_date = datetime(2026, 1, 1)

for machine_id in range(1, 41):
    # Extended calendar: January 1 to February 13, 2026
    for day in range(44):
        calendar_date = start_date + timedelta(days=day)

        is_working_day = 1 if calendar_date.weekday() < 5 else 0

        calendar_data.append({
            "calendar_id": f"CAL-{machine_id:03d}-{day + 1:03d}",
            "machine_id": f"MACH-{machine_id:03d}",
            "calendar_date": calendar_date.strftime("%Y-%m-%d"),
            "shift_start": "09:00",
            "shift_end": "17:00",
            "break_duration": 60 if is_working_day else 0,
            "available_minutes": 420 if is_working_day else 0,
            "is_working_day": is_working_day
        })

calendar_df = pd.DataFrame(calendar_data)

calendar_df.to_csv(DATA_DIR / "machine_calendar.csv", index=False)

print("Machine calendar records generated:", len(calendar_df))

# Generate 200 materials
material_types = ["RAW_MATERIAL", "COMPONENT", "PACKAGING"]

material_data = []

for i in range(1, 201):
    material_data.append({
        "material_id": f"MAT-{i:04d}",
        "material_name": f"Material {i}",
        "material_type": np.random.choice(material_types),
        "unit": np.random.choice(["KG", "PCS", "LITRE"]),
        "lead_time_days": int(np.random.randint(1, 15)),
        "status": "ACTIVE"
    })

materials_df = pd.DataFrame(material_data)

materials_df.to_csv(DATA_DIR / "materials.csv", index=False)

print("Materials generated:", len(materials_df))

# Generate inventory lots
inventory_data = []

for i in range(1, 301):
    material_number = np.random.randint(1, 201)
    quantity = int(np.random.randint(100, 1001))
    received_date = datetime(2026, 1, 1) + timedelta(days=int(np.random.randint(0, 30)))

    inventory_data.append({
        "lot_id": f"LOT-{i:05d}",
        "material_id": f"MAT-{material_number:04d}",
        "lot_number": f"LOTNUM-{i:05d}",
        "quantity_received": quantity,
        "quantity_available": quantity,
        "received_date": received_date.strftime("%Y-%m-%d"),
        "available_from": (received_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "expiry_date": (received_date + timedelta(days=365)).strftime("%Y-%m-%d"),
        "lot_status": "AVAILABLE"
    })

inventory_df = pd.DataFrame(inventory_data)

inventory_df.to_csv(DATA_DIR / "inventory_lots.csv", index=False)

print("Inventory lots generated:", len(inventory_df))

# Generate 500 production orders
order_data = []

for i in range(1, 501):
    product_number = int(np.random.randint(1, 101))
    start_date = datetime(2026, 1, 1) + timedelta(days=int(np.random.randint(0, 30)))
    end_date = start_date + timedelta(days=int(np.random.randint(1, 6)))
    due_date = end_date + timedelta(days=int(np.random.randint(1, 11)))

    order_data.append({
        "production_order_id": f"PO-{i:05d}",
        "product_id": f"PROD-{product_number:06d}",
        "routing_id": f"ROUTE-{product_number:06d}",
        "order_quantity": int(np.random.randint(10, 501)),
        "planned_start_date": start_date.strftime("%Y-%m-%d"),
        "planned_end_date": end_date.strftime("%Y-%m-%d"),
        "actual_start_date": None,
        "actual_end_date": None,
        "due_date": due_date.strftime("%Y-%m-%d"),
        "priority": int(np.random.randint(1, 6)),
        "order_status": "PENDING"
    })

orders_df = pd.DataFrame(order_data)

orders_df.to_csv(DATA_DIR / "production_orders.csv", index=False)

print("Production orders generated:", len(orders_df))
