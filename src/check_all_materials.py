
import sys
import sqlite3
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

from material_checker import check_order_materials

orders = pd.read_csv(BASE / "data" / "production_orders.csv")

rows = []

for order_id in orders["production_order_id"]:
    rows.extend(check_order_materials(order_id))

results = pd.DataFrame(rows)

results.to_csv(
    BASE / "outputs" / "material_check_results.csv",
    index=False
)

conn = sqlite3.connect(BASE / "database" / "yottaflex.db")

results.to_sql(
    "MaterialCheckResult",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print("Material checks saved successfully!")
print("Total checks:", len(results))
print("Available:", int(results["is_available"].sum()))
print("Unavailable:", int((~results["is_available"]).sum()))
