
import csv
import json
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

from app.database import engine
from app.models import Customer, Product
from app.evaluation.metrics import (
    ranking_metrics_at_k,
    catalog_coverage,
    availability_violations,
)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EVALUATION_DIR = PROJECT_ROOT / "reports" / "evaluation"
SPLIT_DIR = PROJECT_ROOT / "reports" / "temporal_split"

RECOMMENDATIONS_FILE = (
    EVALUATION_DIR / "evaluation_recommendations.csv"
)

TEST_ORDERS_FILE = SPLIT_DIR / "test_orders.csv"

GROUND_TRUTH_FILE = (
    SPLIT_DIR / "test_ground_truth.csv"
)

RESULTS_FILE = EVALUATION_DIR / "evaluation_results.json"

CUSTOMER_METRICS_FILE = (
    EVALUATION_DIR / "per_customer_metrics.csv"
)

K = 5

POSITIVE_STATUSES = {
    "paid",
    "shipped",
    "delivered",
}


# ---------------------------------------------------------
# CSV LOADER
# ---------------------------------------------------------

def load_csv(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


# ---------------------------------------------------------
# LOAD AND VALIDATE RECOMMENDATIONS
# ---------------------------------------------------------

def load_recommendations(database_customer_ids):

    rows = load_csv(RECOMMENDATIONS_FILE)

    required_columns = {
        "customer_id",
        "product_id",
        "rank",
    }

    if not rows:
        raise ValueError("Recommendation CSV is empty.")

    if not required_columns.issubset(rows[0].keys()):
        raise ValueError(
            "Recommendation CSV is missing required columns."
        )

    recommendations = defaultdict(list)
    ranks_by_customer = defaultdict(list)
    pairs = set()

    for row in rows:

        customer_id = int(row["customer_id"])
        product_id = int(row["product_id"])
        rank = int(row["rank"])

        pair = (customer_id, product_id)

        if pair in pairs:
            raise ValueError(
                f"Duplicate customer-product recommendation: {pair}"
            )

        pairs.add(pair)

        recommendations[customer_id].append(
            (rank, product_id)
        )

        ranks_by_customer[customer_id].append(rank)

    # Every database customer must have exactly five recommendations.
    recommendation_customer_ids = set(recommendations)

    if recommendation_customer_ids != database_customer_ids:

        missing = (
            database_customer_ids - recommendation_customer_ids
        )

        unknown = (
            recommendation_customer_ids - database_customer_ids
        )

        raise ValueError(
            f"Customer mismatch. Missing: {len(missing)}, "
            f"Unknown: {len(unknown)}"
        )

    # Validate five unique products and ranks 1 through 5.
    for customer_id, customer_rows in recommendations.items():

        if len(customer_rows) != K:
            raise ValueError(
                f"Customer {customer_id} has "
                f"{len(customer_rows)} recommendations, not {K}."
            )

        actual_ranks = sorted(
            ranks_by_customer[customer_id]
        )

        if actual_ranks != list(range(1, K + 1)):
            raise ValueError(
                f"Invalid recommendation ranks for customer "
                f"{customer_id}: {actual_ranks}"
            )

        customer_rows.sort(key=lambda item: item[0])

    # Convert (rank, product_id) into ordered product lists.
    return {
        customer_id: [
            product_id
            for rank, product_id in customer_rows
        ]
        for customer_id, customer_rows in recommendations.items()
    }


# ---------------------------------------------------------
# LOAD TEST ORDERS AND GROUND TRUTH
# ---------------------------------------------------------

def load_ground_truth(database_customer_ids):

    order_rows = load_csv(TEST_ORDERS_FILE)
    ground_truth_rows = load_csv(GROUND_TRUTH_FILE)

    order_status = {}
    order_customer = {}

    for row in order_rows:

        order_id = int(row["order_id"])
        customer_id = int(row["customer_id"])
        status = row["status"].strip().lower()

        if order_id in order_status:
            raise ValueError(
                f"Duplicate test order ID: {order_id}"
            )

        order_status[order_id] = status
        order_customer[order_id] = customer_id

    ground_truth = defaultdict(set)

    for row in ground_truth_rows:

        order_id = int(row["order_id"])
        customer_id = int(row["customer_id"])
        product_id = int(row["product_id"])

        if order_id not in order_status:
            raise ValueError(
                f"Ground-truth order {order_id} "
                f"does not exist in test_orders.csv."
            )

        if order_customer[order_id] != customer_id:
            raise ValueError(
                f"Customer mismatch for order {order_id}."
            )

        status = order_status[order_id]

        # Only completed or financially accepted orders
        # are considered relevant.
        if status not in POSITIVE_STATUSES:
            continue

        if customer_id not in database_customer_ids:
            raise ValueError(
                f"Unknown customer in ground truth: {customer_id}"
            )

        # Set automatically removes duplicate products for
        # the same customer, regardless of purchased quantity.
        ground_truth[customer_id].add(product_id)

    return dict(ground_truth), order_status


# ---------------------------------------------------------
# LOAD ELIGIBLE PRODUCT CATALOG
# ---------------------------------------------------------

def load_eligible_catalog():

    with engine.connect() as connection:

        product_ids = connection.execute(
            select(Product.id).where(
                Product.is_active.is_(True),
                Product.stock_quantity > 0,
            )
        ).scalars().all()

    return set(product_ids)


# ---------------------------------------------------------
# MAIN EVALUATION
# ---------------------------------------------------------

def main():

    print("\nYOTTAFLEX.AI RECOMMENDATION EVALUATION")
    print("=" * 55)

    # 1. Load all database customers.
    with engine.connect() as connection:

        database_customer_ids = set(
            connection.execute(
                select(Customer.id)
            ).scalars().all()
        )

    print(
        f"Database customers: {len(database_customer_ids):,}"
    )

    # 2. Load and validate recommendations.
    recommendations = load_recommendations(
        database_customer_ids
    )

    total_recommendations = sum(
        len(items)
        for items in recommendations.values()
    )

    print(
        f"Recommendation rows: {total_recommendations:,}"
    )

    print("Recommendation structure: VALID")

    # 3. Load positive test ground truth.
    ground_truth, order_status = load_ground_truth(
        database_customer_ids
    )

    positive_customer_ids = set(ground_truth)

    customers_without_positive_test_orders = (
        database_customer_ids - positive_customer_ids
    )

    positive_order_count = sum(
        1
        for status in order_status.values()
        if status in POSITIVE_STATUSES
    )

    positive_test_products = sum(
        len(products)
        for products in ground_truth.values()
    )

    print(f"Positive test orders: {positive_order_count:,}")

    print(
        f"Positive test customer-product pairs: "
        f"{positive_test_products:,}"
    )

    print(
        f"Customers with positive test purchases: "
        f"{len(positive_customer_ids):,}"
    )

    print(
        f"Customers without positive test purchases: "
        f"{len(customers_without_positive_test_orders):,}"
    )

    # 4. Load the current eligible product catalog.
    eligible_catalog = load_eligible_catalog()

    print(
        f"Eligible products (active and in stock): "
        f"{len(eligible_catalog):,}"
    )

    # 5. Calculate ranking metrics.
    ranking_results = ranking_metrics_at_k(
        recommendations,
        ground_truth,
        k=K,
    )

    # 6. Calculate catalog coverage.
    coverage_results = catalog_coverage(
        recommendations,
        eligible_catalog,
    )

    # 7. Calculate availability violations.
    availability_results = availability_violations(
        recommendations,
        eligible_catalog,
    )

    # 8. Calculate individual customer metrics.
    per_customer_rows = []

    for customer_id in sorted(positive_customer_ids):

        customer_result = ranking_metrics_at_k(
            {
                customer_id: recommendations[customer_id]
            },
            {
                customer_id: ground_truth[customer_id]
            },
            k=K,
        )

        per_customer_rows.append({
            "customer_id": customer_id,
            "relevant_test_products": len(
                ground_truth[customer_id]
            ),
            "recommended_products": len(
                recommendations[customer_id]
            ),
            "precision_at_5": customer_result[
                "precision_at_5"
            ],
            "recall_at_5": customer_result[
                "recall_at_5"
            ],
            "ndcg_at_5": customer_result[
                "ndcg_at_5"
            ],
        })

    # 9. Assemble final report.
    results = {
        "project": "YottaFlex.ai",
        "evaluation_type": "chronological_holdout",
        "cutoff": "2026-07-01T00:00:00+05:30",
        "recommendation_model": "category_affinity_train_only",
        "k": K,

        "test_policy": {
            "positive_order_statuses": sorted(
                POSITIVE_STATUSES
            ),
            "relevance": (
                "Binary customer-product relevance; "
                "quantity does not affect relevance."
            ),
            "averaging": (
                "Macro average across customers with at least "
                "one positive test product."
            ),
        },

        "dataset_counts": {
            "database_customers": len(
                database_customer_ids
            ),
            "recommendation_rows": total_recommendations,
            "positive_test_orders": positive_order_count,
            "positive_test_customer_product_pairs": (
                positive_test_products
            ),
            "customers_with_positive_test_purchases": (
                len(positive_customer_ids)
            ),
            "customers_without_positive_test_purchases": (
                len(customers_without_positive_test_orders)
            ),
            "eligible_catalog_products": len(
                eligible_catalog
            ),
        },

        "ranking_metrics": {
            "precision_at_5": ranking_results[
                "precision_at_5"
            ],
            "recall_at_5": ranking_results[
                "recall_at_5"
            ],
            "ndcg_at_5": ranking_results[
                "ndcg_at_5"
            ],
            "evaluated_customers": ranking_results[
                "evaluated_customers"
            ],
        },

        "catalog_metrics": coverage_results,

        "availability_metrics": availability_results,

        "limitations": [
            (
                "Product created_at timestamps were not used "
                "because the synthetic catalog records were "
                "created after the evaluation cutoff."
            ),
            (
                "Availability is checked against the current "
                "active and in-stock catalog snapshot, not "
                "historical availability at each test order time."
            ),
            (
                "The evaluation measures product relevance "
                "against positive test purchases, not clicks "
                "or user satisfaction."
            ),
        ],
    }

    # 10. Save JSON results.
    EVALUATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
        )

    # 11. Save per-customer metrics.
    with CUSTOMER_METRICS_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        fieldnames = [
            "customer_id",
            "relevant_test_products",
            "recommended_products",
            "precision_at_5",
            "recall_at_5",
            "ndcg_at_5",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(per_customer_rows)

    # 12. Display results.
    print("\n" + "=" * 55)
    print("FINAL EVALUATION RESULTS")
    print("=" * 55)

    print(
        f"Precision@5: "
        f"{ranking_results['precision_at_5']:.6f}"
    )

    print(
        f"Recall@5: "
        f"{ranking_results['recall_at_5']:.6f}"
    )

    print(
        f"NDCG@5: "
        f"{ranking_results['ndcg_at_5']:.6f}"
    )

    print(
        f"Catalog Coverage: "
        f"{coverage_results['catalog_coverage']:.6f}"
    )

    print(
        f"Availability Violations: "
        f"{availability_results['availability_violations']:,}"
    )

    print(
        f"Availability Violation Rate: "
        f"{availability_results['availability_violation_rate']:.6f}"
    )

    print("\nReports saved:")
    print(RESULTS_FILE)
    print(CUSTOMER_METRICS_FILE)

    print("\nEvaluation completed successfully.")


if __name__ == "__main__":
    main()
