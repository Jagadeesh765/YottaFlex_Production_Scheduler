
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "yottaflex.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def initialize_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    # Start with a fresh database to avoid duplicate records.
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
            schema = file.read()

        conn.executescript(schema)

        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        print("Database initialized successfully!")
        print("Database location:", DB_PATH)
        print("\nAvailable tables:")

        for table in tables:
            print(table[0])


if __name__ == "__main__":
    initialize_database()
