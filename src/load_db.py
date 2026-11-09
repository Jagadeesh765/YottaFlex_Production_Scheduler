
import sqlite3
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "database" / "yottaflex.db"

# CSV files and their corresponding database tables
TABLE_FILES = {
    "Product": "products.csv",
    "Routing": "routings.csv",
    "Operation": "operations.csv",
    "Machine": "machines.csv",
    "MachineCalendar": "machine_calendar.csv",
    "Material": "materials.csv",
    "InventoryLot": "inventory_lots.csv",
    "ProductionOrder": "production_orders.csv",
    "ChangeoverMatrix": "changeover_matrix.csv",
}

# Delete records in reverse dependency order
DELETE_ORDER = [
    "OperationSchedule",
    "ChangeoverMatrix",
    "ProductionOrder",
    "InventoryLot",
    "MachineCalendar",
    "Operation",
    "Routing",
    "Product",
    "Machine",
    "Material",
]


def load_database():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. Run init_db.py first."
        )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        # Clear previous records
        for table in DELETE_ORDER:
            conn.execute(f"DELETE FROM {table}")

        total_records = 0

        for table, filename in TABLE_FILES.items():
            file_path = DATA_DIR / filename

            if not file_path.exists():
                raise FileNotFoundError(
                    f"CSV file not found: {file_path}"
                )

            with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                columns = reader.fieldnames

                database_columns = [
                    row[1]
                    for row in conn.execute(
                        f"PRAGMA table_info({table})"
                    ).fetchall()
                ]

                if columns != database_columns:
                    raise ValueError(
                        f"Column mismatch in {filename}\n"
                        f"CSV: {columns}\n"
                        f"Database: {database_columns}"
                    )

                rows = [
                    tuple(
                        None if value == "" else value
                        for value in row.values()
                    )
                    for row in reader
                ]

            if rows:
                placeholders = ", ".join(["?"] * len(columns))
                column_names = ", ".join(columns)

                query = (
                    f"INSERT INTO {table} ({column_names}) "
                    f"VALUES ({placeholders})"
                )

                conn.executemany(query, rows)

            count = len(rows)
            total_records += count
            print(f"{table}: {count} records inserted")

        conn.commit()

        print("\nDatabase loading completed successfully!")
        print("Total records inserted:", total_records)
        print("Database location:", DB_PATH)


if __name__ == "__main__":
    try:
        load_database()
    except Exception as error:
        print("\nDatabase loading failed:", error)
        raise
