
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_input_data():
    files = {
        "products": "products.csv",
        "routings": "routings.csv",
        "operations": "operations.csv",
        "machines": "machines.csv",
        "machine_calendar": "machine_calendar.csv",
        "materials": "materials.csv",
        "inventory_lots": "inventory_lots.csv",
        "production_orders": "production_orders.csv",
        "changeover_matrix": "changeover_matrix.csv",
    }

    data = {}

    for name, filename in files.items():
        file_path = DATA_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Missing input file: {file_path}")

        data[name] = pd.read_csv(file_path)

    print("Input data loaded successfully!")

    for name, df in data.items():
        print(f"{name}: {len(df)} records")

    return data


def validate_data(data):
    print("\n========== DATA VALIDATION ==========")
    all_valid = True

    # 1. Duplicate ID checks
    primary_keys = {
        "products": "product_id",
        "routings": "routing_id",
        "operations": "operation_id",
        "machines": "machine_id",
        "materials": "material_id",
        "inventory_lots": "lot_id",
        "production_orders": "production_order_id",
    }

    print("\n1. Checking duplicate IDs")

    for table, column in primary_keys.items():
        duplicates = data[table][column].duplicated().sum()
        print(f"{table}: {duplicates} duplicate IDs")

        if duplicates > 0:
            all_valid = False

    # 2. Foreign key checks
    checks = [
        ("Routing -> Product", "routings", "product_id", "products", "product_id"),
        ("Operation -> Routing", "operations", "routing_id", "routings", "routing_id"),
        ("Production Order -> Product", "production_orders", "product_id", "products", "product_id"),
        ("Production Order -> Routing", "production_orders", "routing_id", "routings", "routing_id"),
        ("Machine Calendar -> Machine", "machine_calendar", "machine_id", "machines", "machine_id"),
        ("Inventory Lot -> Material", "inventory_lots", "material_id", "materials", "material_id"),
    ]

    print("\n2. Checking relationships")

    for name, child_table, child_col, parent_table, parent_col in checks:
        child = data[child_table]
        parent = data[parent_table]

        invalid_count = (~child[child_col].isin(parent[parent_col])).sum()
        print(f"{name}: {invalid_count} invalid references")

        if invalid_count > 0:
            all_valid = False

    # 3. Missing value checks
    print("\n3. Checking missing values")

    allowed_missing = {
        "routings": ["effective_to"],
        "production_orders": ["actual_start_date", "actual_end_date"],
    }

    for name, df in data.items():
        allowed_columns = allowed_missing.get(name, [])

        unexpected_missing = df.drop(
            columns=allowed_columns
        ).isnull().sum().sum()

        expected_missing = df[allowed_columns].isnull().sum().sum() if allowed_columns else 0

        print(f"{name}: {expected_missing} expected missing values")

        if unexpected_missing > 0:
            print(f"WARNING: {unexpected_missing} unexpected missing values")
            all_valid = False

    print("\n========== VALIDATION RESULT ==========")

    if all_valid:
        print("SUCCESS: All basic data validation checks passed!")
    else:
        print("WARNING: Data validation found issues.")

    return all_valid


if __name__ == "__main__":
    data = load_input_data()
    validate_data(data)
