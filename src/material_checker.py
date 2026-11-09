
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

bom = pd.read_csv(DATA / "bill_of_materials.csv")
inventory = pd.read_csv(DATA / "inventory_lots.csv")
orders = pd.read_csv(DATA / "production_orders.csv")

for col in ["available_from", "expiry_date"]:
    inventory[col] = pd.to_datetime(inventory[col])

def check_order_materials(order_id):
    order = orders[orders["production_order_id"] == order_id]

    if order.empty:
        return {"error": "Production order not found"}

    order = order.iloc[0]
    product_bom = bom[bom["product_id"] == order["product_id"]]
    schedule_date = pd.to_datetime(order["planned_start_date"])
    results = []

    for _, item in product_bom.iterrows():
        required = float(order["order_quantity"]) * float(item["quantity_per_unit"])

        valid_lots = inventory[
            (inventory["material_id"] == item["material_id"]) &
            (inventory["lot_status"] == "AVAILABLE") &
            (inventory["available_from"] <= schedule_date) &
            (inventory["expiry_date"] >= schedule_date)
        ]

        available = float(valid_lots["quantity_available"].sum())

        results.append({
            "production_order_id": order_id,
            "material_id": item["material_id"],
            "required_quantity": required,
            "available_quantity": available,
            "is_available": available >= required
        })

    return results


if __name__ == "__main__":
    result = check_order_materials("PO-00001")
    print("MATERIAL REQUIREMENT CHECK")
    print(pd.DataFrame(result).to_string(index=False))
