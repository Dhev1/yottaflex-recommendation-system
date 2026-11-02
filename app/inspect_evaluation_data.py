
from pathlib import Path
import pandas as pd
import json

from app.models import (
    Order,
    OrderLine,
    Product,
    Recommendation
)

base = Path("reports/temporal_split")

# 1. Inspect existing chronological exports
files = [
    "training_page_views.csv",
    "training_order_lines.csv",
    "test_orders.csv",
    "test_ground_truth.csv"
]

print("\n========== EXPORT INSPECTION ==========")

for filename in files:
    path = base / filename

    print(f"\n--- {filename} ---")

    if not path.exists():
        print("FILE NOT FOUND")
        continue

    df = pd.read_csv(path, nrows=5)

    print("Columns:", df.columns.tolist())
    print("\nSample records:")
    print(df.head(3).to_string(index=False))

# 2. Inspect chronological split manifest
manifest_path = base / "split_manifest.json"

print("\n========== SPLIT MANIFEST ==========")

if manifest_path.exists():
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(json.dumps(manifest, indent=4))
else:
    print("Manifest not found")

# 3. Inspect database model columns
print("\n========== DATABASE MODEL COLUMNS ==========")

for model in [Order, OrderLine, Product, Recommendation]:
    print(f"\n{model.__name__}:")
    print([column.name for column in model.__table__.columns])

print("\n========== INSPECTION COMPLETED ==========")
