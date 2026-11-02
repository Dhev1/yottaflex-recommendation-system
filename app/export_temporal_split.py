
import csv
import json

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import (
    PageView,
    Session as SessionModel,
    Order,
    OrderLine
)


# ============================================================
# CONFIGURATION
# ============================================================

# July 1, 2026, midnight IST
CUTOFF = datetime(
    2026, 7, 1, 0, 0, 0,
    tzinfo=timezone(timedelta(hours=5, minutes=30))
)

OUTPUT_DIR = Path("reports/temporal_split")

BATCH_SIZE = 10000


# ============================================================
# CSV EXPORT HELPER
# ============================================================

def convert_value(value):

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    return value


def export_query(query, columns, filename):

    filepath = OUTPUT_DIR / filename

    row_count = 0

    with open(
        filepath,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(columns)

        for row in query.yield_per(BATCH_SIZE):

            writer.writerow([
                convert_value(value)
                for value in row
            ])

            row_count += 1

    print(f"{filename}: {row_count:,} rows exported")

    return row_count


# ============================================================
# MAIN EXPORT
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 70)
    print("YOTTAFLEX.AI - TEMPORAL DATA EXPORT")
    print("=" * 70)

    print(f"Training cutoff: {CUTOFF.isoformat()}")
    print(f"Output folder: {OUTPUT_DIR.resolve()}")

    with DBSession(engine) as db:

        # ----------------------------------------------------
        # 1. TRAINING PAGE VIEWS
        # ----------------------------------------------------

        training_views_query = (
            db.query(
                PageView.id,
                SessionModel.customer_id,
                PageView.session_id,
                PageView.product_id,
                PageView.page_type,
                PageView.viewed_at,
                PageView.duration_seconds
            )
            .join(
                SessionModel,
                PageView.session_id == SessionModel.id
            )
            .filter(
                PageView.viewed_at < CUTOFF
            )
            .order_by(PageView.id)
        )

        training_views_count = export_query(
            training_views_query,
            [
                "page_view_id",
                "customer_id",
                "session_id",
                "product_id",
                "page_type",
                "viewed_at",
                "duration_seconds"
            ],
            "training_page_views.csv"
        )

        # ----------------------------------------------------
        # 2. TRAINING ORDER LINES
        # ----------------------------------------------------

        training_lines_query = (
            db.query(
                OrderLine.id,
                Order.id,
                Order.customer_id,
                Order.session_id,
                OrderLine.product_id,
                OrderLine.quantity,
                OrderLine.unit_price,
                OrderLine.line_total,
                Order.placed_at,
                Order.status
            )
            .join(
                Order,
                OrderLine.order_id == Order.id
            )
            .filter(
                Order.placed_at < CUTOFF
            )
            .order_by(Order.placed_at, OrderLine.id)
        )

        training_lines_count = export_query(
            training_lines_query,
            [
                "order_line_id",
                "order_id",
                "customer_id",
                "session_id",
                "product_id",
                "quantity",
                "unit_price",
                "line_total",
                "placed_at",
                "order_status"
            ],
            "training_order_lines.csv"
        )

        # ----------------------------------------------------
        # 3. TEST ORDERS
        # ----------------------------------------------------

        test_orders_query = (
            db.query(
                Order.id,
                Order.customer_id,
                Order.session_id,
                Order.placed_at,
                Order.status,
                Order.subtotal,
                Order.tax,
                Order.shipping_cost,
                Order.total_amount,
                Order.currency
            )
            .filter(
                Order.placed_at >= CUTOFF
            )
            .order_by(Order.placed_at, Order.id)
        )

        test_orders_count = export_query(
            test_orders_query,
            [
                "order_id",
                "customer_id",
                "session_id",
                "placed_at",
                "status",
                "subtotal",
                "tax",
                "shipping_cost",
                "total_amount",
                "currency"
            ],
            "test_orders.csv"
        )

        # ----------------------------------------------------
        # 4. TEST GROUND TRUTH
        # ----------------------------------------------------

        test_ground_truth_query = (
            db.query(
                OrderLine.id,
                Order.id,
                Order.customer_id,
                OrderLine.product_id,
                OrderLine.quantity,
                OrderLine.unit_price,
                OrderLine.line_total,
                Order.placed_at
            )
            .join(
                Order,
                OrderLine.order_id == Order.id
            )
            .filter(
                Order.placed_at >= CUTOFF
            )
            .order_by(Order.placed_at, OrderLine.id)
        )

        test_ground_truth_count = export_query(
            test_ground_truth_query,
            [
                "order_line_id",
                "order_id",
                "customer_id",
                "product_id",
                "quantity",
                "unit_price",
                "line_total",
                "placed_at"
            ],
            "test_ground_truth.csv"
        )

        # ----------------------------------------------------
        # 5. CREATE MANIFEST
        # ----------------------------------------------------

        manifest = {

            "project": "YottaFlex.ai",

            "split_type": "chronological",

            "cutoff": CUTOFF.isoformat(),

            "timezone": "Asia/Kolkata",

            "training_period": {
                "condition": "timestamp < cutoff",
                "page_views": training_views_count,
                "order_lines": training_lines_count
            },

            "test_period": {
                "condition": "order.placed_at >= cutoff",
                "orders": test_orders_count,
                "ground_truth_order_lines": test_ground_truth_count
            },

            "files": [
                "training_page_views.csv",
                "training_order_lines.csv",
                "test_orders.csv",
                "test_ground_truth.csv"
            ],

            "leakage_prevention": [
                "Training interactions use events before the cutoff.",
                "Test orders and order lines are reserved for evaluation.",
                "Existing recommendations are excluded from training inputs."
            ]

        }

        manifest_path = OUTPUT_DIR / "split_manifest.json"

        with open(
            manifest_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                manifest,
                file,
                indent=4
            )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TEMPORAL EXPORT SUMMARY")
    print("=" * 70)

    print(f"Training page views:       {training_views_count:,}")
    print(f"Training order lines:      {training_lines_count:,}")
    print(f"Test orders:               {test_orders_count:,}")
    print(f"Test ground truth lines:   {test_ground_truth_count:,}")

    print("\nManifest created:")
    print(manifest_path.resolve())

    print("\nAll exports completed.")
    print("Original database was NOT modified.")

    print("=" * 70)


if __name__ == "__main__":
    main()
