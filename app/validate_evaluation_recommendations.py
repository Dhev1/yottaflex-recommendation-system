
import csv
import json

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import Customer, Product, Order, OrderLine


# ============================================================
# CONFIGURATION
# ============================================================

CUTOFF = datetime(
    2026, 7, 1, 0, 0, 0,
    tzinfo=timezone(timedelta(hours=5, minutes=30)),
)

POSITIVE_STATUSES = ["paid", "shipped", "delivered"]

CSV_FILE = Path(
    "reports/evaluation/evaluation_recommendations.csv"
)

MANIFEST_FILE = Path(
    "reports/evaluation/recommendation_manifest.json"
)

EXPECTED_PER_CUSTOMER = 5


# ============================================================
# VALIDATION
# ============================================================

def main():

    print("=" * 65)
    print("YOTTAFLEX - EVALUATION RECOMMENDATION VALIDATION")
    print("=" * 65)

    # --------------------------------------------------------
    # 1. CHECK OUTPUT FILES
    # --------------------------------------------------------

    if not CSV_FILE.exists():
        raise FileNotFoundError(CSV_FILE)

    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(MANIFEST_FILE)

    with open(MANIFEST_FILE, encoding="utf-8") as file:
        manifest = json.load(file)

    print("\n1. Output files")
    print("Recommendation CSV: FOUND")
    print("Recommendation manifest: FOUND")
    print("Model:", manifest["model_name"])

    # --------------------------------------------------------
    # 2. READ RECOMMENDATION CSV
    # --------------------------------------------------------

    recommendations = []

    with open(
        CSV_FILE,
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "customer_id",
            "product_id",
            "score",
            "rank",
            "preferred_category_id",
            "reason",
        }

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError("CSV columns are missing.")

        for row in reader:

            row["rank"] = int(row["rank"])
            row["score"] = float(row["score"])

            recommendations.append(row)

    print("\n2. CSV statistics")
    print(f"Total recommendation rows: {len(recommendations):,}")

    customer_counts = Counter(
        row["customer_id"] for row in recommendations
    )

    customer_products = [
        (row["customer_id"], row["product_id"])
        for row in recommendations
    ]

    duplicate_pairs = (
        len(customer_products) - len(set(customer_products))
    )

    ranks_by_customer = defaultdict(set)

    for row in recommendations:

        ranks_by_customer[row["customer_id"]].add(
            row["rank"]
        )

    incorrect_customer_counts = {
        customer_id: count
        for customer_id, count in customer_counts.items()
        if count != EXPECTED_PER_CUSTOMER
    }

    incorrect_ranks = {
        customer_id: ranks
        for customer_id, ranks in ranks_by_customer.items()
        if ranks != {1, 2, 3, 4, 5}
    }

    print(f"Unique customers: {len(customer_counts):,}")
    print(f"Duplicate customer-product pairs: {duplicate_pairs:,}")
    print(f"Customers without exactly five recommendations: {len(incorrect_customer_counts):,}")
    print(f"Customers with incorrect ranks: {len(incorrect_ranks):,}")

    # --------------------------------------------------------
    # 3. VALIDATE AGAINST DATABASE
    # --------------------------------------------------------

    print("\n3. Checking catalog and purchase history...")

    with DBSession(engine) as db:

        database_customers = {
            str(customer_id)
            for customer_id in db.execute(
                select(Customer.id)
            ).scalars().all()
        }

        eligible_products = {
            str(product_id)
            for product_id in db.execute(
                select(Product.id).where(
                    Product.is_active.is_(True),
                    Product.stock_quantity > 0,
                )
            ).scalars().all()
        }

        historical_purchase_pairs = {
            (
                str(row.customer_id),
                str(row.product_id),
            )
            for row in db.execute(
                select(
                    Order.customer_id,
                    OrderLine.product_id,
                )
                .join(
                    OrderLine,
                    OrderLine.order_id == Order.id,
                )
                .where(
                    Order.placed_at < CUTOFF,
                    Order.status.in_(POSITIVE_STATUSES),
                )
            )
        }

    unknown_customers = (
        set(customer_counts) - database_customers
    )

    missing_customers = (
        database_customers - set(customer_counts)
    )

    unavailable_recommendations = [
        row
        for row in recommendations
        if row["product_id"] not in eligible_products
    ]

    previously_purchased = [
        row
        for row in recommendations
        if (
            row["customer_id"],
            row["product_id"],
        ) in historical_purchase_pairs
    ]

    print(f"Database customers: {len(database_customers):,}")
    print(f"Eligible catalog products: {len(eligible_products):,}")
    print(f"Unknown customers in CSV: {len(unknown_customers):,}")
    print(f"Customers missing from CSV: {len(missing_customers):,}")
    print(f"Unavailable recommendations: {len(unavailable_recommendations):,}")
    print(f"Previously purchased recommendations: {len(previously_purchased):,}")

    # --------------------------------------------------------
    # 4. VALIDATE SCORES AND RANKS
    # --------------------------------------------------------

    invalid_scores = [
        row
        for row in recommendations
        if row["score"] < 0
    ]

    invalid_ranks = [
        row
        for row in recommendations
        if row["rank"] < 1
        or row["rank"] > EXPECTED_PER_CUSTOMER
    ]

    print(f"Invalid scores: {len(invalid_scores):,}")
    print(f"Invalid rank values: {len(invalid_ranks):,}")

    # --------------------------------------------------------
    # 5. FINAL RESULT
    # --------------------------------------------------------

    checks = {
        "Exactly 100,000 recommendation rows": (
            len(recommendations) == 100_000
        ),
        "Exactly 20,000 customers": (
            len(customer_counts) == 20_000
        ),
        "Exactly five recommendations per customer": (
            len(incorrect_customer_counts) == 0
        ),
        "Ranks are exactly 1 through 5": (
            len(incorrect_ranks) == 0
        ),
        "No duplicate customer-product pairs": (
            duplicate_pairs == 0
        ),
        "All customers exist in database": (
            len(unknown_customers) == 0
        ),
        "All database customers are represented": (
            len(missing_customers) == 0
        ),
        "All recommendations are currently eligible": (
            len(unavailable_recommendations) == 0
        ),
        "No previously purchased products": (
            len(previously_purchased) == 0
        ),
        "All scores are non-negative": (
            len(invalid_scores) == 0
        ),
        "All ranks are within 1 to 5": (
            len(invalid_ranks) == 0
        ),
    }

    print("\n" + "=" * 65)
    print("VALIDATION RESULTS")
    print("=" * 65)

    for description, passed in checks.items():

        print(
            f"[{'PASS' if passed else 'FAIL'}] {description}"
        )

    if all(checks.values()):

        print("\nALL VALIDATION CHECKS PASSED.")

    else:

        raise SystemExit(
            "\nVALIDATION FAILED. Do not calculate evaluation metrics yet."
        )


if __name__ == "__main__":
    main()
