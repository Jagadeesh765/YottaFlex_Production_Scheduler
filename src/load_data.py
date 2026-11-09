import pandas as pd
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_input_data():
    required_files = {
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

    for name, filename in required_files.items():
        file_path = DATA_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Missing file: {file_path}"
            )

        data[name] = pd.read_csv(file_path)

    print("All input files loaded successfully!")

    for name, df in data.items():
        print(f"{name}: {len(df)} records")

    return data


def validate_data(data):
    print("\nChecking data relationships...")

    checks = [
        ("Routing -> Product", "routings", "product_id",
         "products", "product_id"),

        ("Operation -> Routing", "operations", "routing_id",
         "routings", "routing_id"),

        ("Production Order -> Product", "production_orders",
         "product_id", "products", "product_id"),

        ("Production Order -> Routing", "production_orders",
         "routing_id", "routings", "routing_id"),

        ("Machine Calendar -> Machine", "machine_calendar",
         "machine_id", "machines", "machine_id"),
    ]

    for name, child_table, child_col, parent_table, parent_col in checks:
        child = data[child_table]
        parent = data[parent_table]

        if child_col not in child.columns or parent_col not in parent.columns:
            print(f"{name}: COLUMN MISSING")
            continue

        missing = ~child[child_col].isin(parent[parent_col])
        print(f"{name}: {missing.sum()} invalid references")


if __name__ == "__main__":
    data = load_input_data()
    validate_data(data)