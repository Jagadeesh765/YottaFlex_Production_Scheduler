
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

products = pd.read_csv(DATA / "products.csv")
materials = pd.read_csv(DATA / "materials.csv")

# Reproducible product-to-material mapping.
bom_rows = []

for index, product in products.iterrows():
    material = materials.iloc[index % len(materials)]

    bom_rows.append({
        "product_id": product["product_id"],
        "material_id": material["material_id"],
        "quantity_per_unit": 1.0,
        "unit": material["unit"]
    })

bom = pd.DataFrame(bom_rows)

bom.to_csv(DATA / "bill_of_materials.csv", index=False)

print("Bill of Materials generated successfully!")
print("Products mapped:", len(bom))
print(bom.head(10).to_string(index=False))
