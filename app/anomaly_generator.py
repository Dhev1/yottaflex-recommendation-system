
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import (
    Product,
    Session as SessionModel,
    PageView,
    Order,
    OrderLine,
    Recommendation,
)


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ANOMALY_DIR = PROJECT_ROOT / "reports" / "anomalies"

ANOMALY_DIR.mkdir(parents=True, exist_ok=True)

# Provisional chronological cutoff.
# We will use and document the final split in Stage 9.
TRAIN_TEST_CUTOFF = datetime(
    2026, 7, 1, 0, 0, 0,
    tzinfo=timezone(timedelta(hours=5, minutes=30))
)


# ============================================================
# HELPERS
# ============================================================

def to_iso(value):

    if isinstance(value, datetime):
        return value.isoformat()

    return value


def require_candidate(candidate, anomaly_name):

    if candidate is None:
        raise RuntimeError(
            f"No suitable baseline record found for {anomaly_name}. "
            "The clean database was not modified."
        )

    return candidate


# ============================================================
# A01 — PURCHASE BEFORE PRODUCT VIEW
# ============================================================

def create_purchase_before_view(db):

    candidates = (
        db.query(Order, OrderLine, PageView, SessionModel)
        .join(OrderLine, OrderLine.order_id == Order.id)
        .join(
            PageView,
            (PageView.session_id == Order.session_id)
            & (PageView.product_id == OrderLine.product_id)
        )
        .join(SessionModel, SessionModel.id == Order.session_id)
        .filter(PageView.viewed_at <= Order.placed_at)
        .order_by(Order.id, PageView.viewed_at)
        .limit(1000)
        .all()
    )

    candidate = next(
        (
            item for item in candidates
            if item[2].viewed_at > item[3].started_at
        ),
        None
    )

    order, order_line, page_view, session = require_candidate(
        candidate,
        "A01 purchase before product view"
    )

    injected_order_time = (
        page_view.viewed_at - timedelta(seconds=1)
    )

    return {
        "anomaly_id": "A01",
        "anomaly_type": "purchase_before_product_view",
        "description": (
            "The synthetic order timestamp is moved to one second "
            "before the product was viewed."
        ),
        "entity_type": "order",
        "entity_id": order.id,
        "customer_id": order.customer_id,
        "session_id": order.session_id,
        "product_id": order_line.product_id,
        "baseline_value": {
            "order_placed_at": to_iso(order.placed_at),
            "product_viewed_at": to_iso(page_view.viewed_at),
        },
        "injected_value": {
            "order_placed_at": to_iso(injected_order_time),
            "product_viewed_at": to_iso(page_view.viewed_at),
        },
        "expected_detection": (
            "The purchased product must have a matching prior "
            "product view in the same session."
        ),
        "validation_rule": "PURCHASE_BEFORE_PRODUCT_VIEW",
    }


# ============================================================
# A02 — MISSING PRODUCT CATEGORY
# ============================================================

def create_missing_category(db):

    product = (
        db.query(Product)
        .filter(Product.category_id.isnot(None))
        .order_by(Product.id)
        .first()
    )

    product = require_candidate(
        product,
        "A02 missing product category"
    )

    return {
        "anomaly_id": "A02",
        "anomaly_type": "missing_product_category",
        "description": (
            "The synthetic product record has its category reference "
            "removed."
        ),
        "entity_type": "product",
        "entity_id": product.id,
        "customer_id": None,
        "session_id": None,
        "product_id": product.id,
        "baseline_value": {
            "category_id": product.category_id,
        },
        "injected_value": {
            "category_id": None,
        },
        "expected_detection": (
            "Every product in the recommendation dataset should "
            "have a valid category."
        ),
        "validation_rule": "PRODUCT_CATEGORY_REQUIRED",
    }


# ============================================================
# A03 — TRAINING / TEST DATA LEAKAGE
# ============================================================

def create_training_test_leakage(db):

    candidate = (
        db.query(Order, OrderLine)
        .join(OrderLine, OrderLine.order_id == Order.id)
        .filter(Order.placed_at >= TRAIN_TEST_CUTOFF)
        .order_by(Order.placed_at, Order.id)
        .first()
    )

    order, order_line = require_candidate(
        candidate,
        "A03 training/test leakage"
    )

    synthetic_recommendation_time = (
        TRAIN_TEST_CUTOFF - timedelta(seconds=1)
    )

    return {
        "anomaly_id": "A03",
        "anomaly_type": "training_test_leakage",
        "description": (
            "A synthetic training recommendation is generated "
            "before the cutoff using a product the same customer "
            "purchases in the test period."
        ),
        "entity_type": "recommendation",
        "entity_id": None,
        "customer_id": order.customer_id,
        "session_id": order.session_id,
        "product_id": order_line.product_id,
        "baseline_value": {
            "test_purchase_order_id": order.id,
            "test_purchase_at": to_iso(order.placed_at),
            "training_cutoff": to_iso(TRAIN_TEST_CUTOFF),
        },
        "injected_value": {
            "synthetic_recommendation_generated_at": to_iso(
                synthetic_recommendation_time
            ),
            "recommendation_uses_future_purchase_information": True,
        },
        "expected_detection": (
            "Training recommendations and customer preferences "
            "must not use purchases occurring at or after the "
            "training/test cutoff."
        ),
        "validation_rule": "NO_FUTURE_DATA_IN_TRAINING",
    }


# ============================================================
# A04 — DISCONTINUED PRODUCT RECOMMENDATION
# ============================================================

def create_discontinued_recommendation(db):

    candidate = (
        db.query(Recommendation, Product)
        .join(Product, Product.id == Recommendation.product_id)
        .filter(
            Product.is_active.is_(True),
            Product.stock_quantity > 0
        )
        .order_by(Recommendation.id)
        .first()
    )

    recommendation, product = require_candidate(
        candidate,
        "A04 discontinued product recommendation"
    )

    return {
        "anomaly_id": "A04",
        "anomaly_type": "discontinued_product_recommendation",
        "description": (
            "The synthetic product availability state is changed "
            "to inactive and out of stock while its recommendation "
            "remains present."
        ),
        "entity_type": "recommendation",
        "entity_id": recommendation.id,
        "customer_id": recommendation.customer_id,
        "session_id": None,
        "product_id": product.id,
        "baseline_value": {
            "product_is_active": product.is_active,
            "stock_quantity": product.stock_quantity,
        },
        "injected_value": {
            "product_is_active": False,
            "stock_quantity": 0,
            "recommendation_remains_present": True,
        },
        "expected_detection": (
            "A recommended product must be active and have "
            "available stock."
        ),
        "validation_rule": "RECOMMENDED_PRODUCT_AVAILABLE",
    }


# ============================================================
# GENERATE ANOMALY FILES
# ============================================================

def generate_csv(anomalies):

    file_path = ANOMALY_DIR / "anomaly_cases.csv"

    columns = [
        "anomaly_id",
        "anomaly_type",
        "description",
        "entity_type",
        "entity_id",
        "customer_id",
        "session_id",
        "product_id",
        "baseline_value",
        "injected_value",
        "expected_detection",
        "validation_rule",
    ]

    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(file, fieldnames=columns)

        writer.writeheader()

        for anomaly in anomalies:

            row = anomaly.copy()

            row["baseline_value"] = json.dumps(
                row["baseline_value"]
            )

            row["injected_value"] = json.dumps(
                row["injected_value"]
            )

            writer.writerow(row)

    print(f"Created: {file_path}")


def generate_ground_truth(anomalies):

    file_path = ANOMALY_DIR / "ground_truth.json"

    ground_truth = {
        "project": "YottaFlex.ai",
        "dataset": "Controlled Anomaly Test Cases",
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_database": "yottaflex_db",
        "clean_baseline_modified": False,
        "training_test_cutoff": to_iso(TRAIN_TEST_CUTOFF),
        "anomaly_count": len(anomalies),
        "anomaly_catalog": anomalies,
    }

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            ground_truth,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Created: {file_path}")


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():

    print("=" * 65)
    print("YOTTAFLEX.AI - CONTROLLED ANOMALY GENERATION")
    print("=" * 65)

    with DBSession(engine) as db:

        anomalies = [
            create_purchase_before_view(db),
            create_missing_category(db),
            create_training_test_leakage(db),
            create_discontinued_recommendation(db),
        ]

    generate_csv(anomalies)

    generate_ground_truth(anomalies)

    print("\n" + "=" * 65)
    print("ANOMALY GENERATION SUMMARY")
    print("=" * 65)

    for anomaly in anomalies:
        print(
            f"{anomaly['anomaly_id']} | "
            f"{anomaly['anomaly_type']} | "
            f"{anomaly['validation_rule']}"
        )

    print(f"\nTotal anomaly scenarios: {len(anomalies)}")
    print("Clean baseline database modified: NO")
    print(f"Output directory: {ANOMALY_DIR}")

    print("=" * 65)


if __name__ == "__main__":
    main()
