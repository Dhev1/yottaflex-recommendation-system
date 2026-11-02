
import csv
import json

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import (
    Customer,
    Product,
    Session as SessionModel,
    PageView,
    Order,
    OrderLine,
)


# ============================================================
# CONFIGURATION
# ============================================================

CUTOFF = datetime(
    2026, 7, 1, 0, 0, 0,
    tzinfo=timezone(timedelta(hours=5, minutes=30)),
)

RECOMMENDATIONS_PER_CUSTOMER = 5

POSITIVE_STATUSES = [
    "paid",
    "shipped",
    "delivered",
]

OUTPUT_DIR = Path("reports/evaluation")

OUTPUT_FILE = OUTPUT_DIR / "evaluation_recommendations.csv"
MANIFEST_FILE = OUTPUT_DIR / "recommendation_manifest.json"

TEMP_CSV = OUTPUT_DIR / "evaluation_recommendations.tmp"
TEMP_MANIFEST = OUTPUT_DIR / "recommendation_manifest.tmp"


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Prevent accidental overwriting of previous evaluation data.
    if (
        OUTPUT_FILE.exists()
        or MANIFEST_FILE.exists()
        or TEMP_CSV.exists()
        or TEMP_MANIFEST.exists()
    ):
        raise FileExistsError(
            "Evaluation output already exists. "
            "Inspect existing files before generating again."
        )

    print("=" * 70)
    print("YOTTAFLEX.AI - TRAINING-ONLY RECOMMENDATION GENERATION")
    print("=" * 70)

    try:

        with DBSession(engine) as db:

            # ------------------------------------------------
            # 1. CUSTOMER CATEGORY PREFERENCES
            # ------------------------------------------------

            print("\n1. Calculating customer browsing preferences...")

            category_query = (
                select(
                    SessionModel.customer_id,
                    Product.category_id,
                    func.count(PageView.id).label("view_count"),
                )
                .join(
                    PageView,
                    PageView.session_id == SessionModel.id,
                )
                .join(
                    Product,
                    Product.id == PageView.product_id,
                )
                .where(
                    PageView.viewed_at < CUTOFF,
                    Product.category_id.is_not(None),
                )
                .group_by(
                    SessionModel.customer_id,
                    Product.category_id,
                )
                .order_by(
                    SessionModel.customer_id,
                    func.count(PageView.id).desc(),
                    Product.category_id,
                )
            )

            preferred_category = {}

            for row in db.execute(category_query):

                if row.customer_id not in preferred_category:

                    preferred_category[row.customer_id] = (
                        row.category_id
                    )

            print(
                "Customers with browsing history:",
                f"{len(preferred_category):,}",
            )

            # ------------------------------------------------
            # 2. PRODUCT POPULARITY FROM TRAINING DATA
            # ------------------------------------------------

            print("\n2. Calculating training-period product popularity...")

            popularity_query = (
                select(
                    PageView.product_id,
                    func.count(PageView.id).label("view_count"),
                )
                .join(
                    Product,
                    Product.id == PageView.product_id,
                )
                .where(
                    PageView.viewed_at < CUTOFF,
                )
                .group_by(PageView.product_id)
            )

            product_popularity = {
                row.product_id: row.view_count
                for row in db.execute(popularity_query)
            }

            print(
                "Products with training-period views:",
                f"{len(product_popularity):,}",
            )

            # ------------------------------------------------
            # 3. HISTORICAL PURCHASE EXCLUSIONS
            # ------------------------------------------------

            print("\n3. Loading confirmed historical purchases...")

            purchase_query = (
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

            purchased_products = defaultdict(set)

            for row in db.execute(purchase_query):

                purchased_products[row.customer_id].add(
                    row.product_id
                )

            print(
                "Customers with historical purchases:",
                f"{len(purchased_products):,}",
            )

            # ------------------------------------------------
            # 4. ELIGIBLE PRODUCT CATALOG
            # ------------------------------------------------

            print("\n4. Loading eligible catalog products...")

            available_query = (
                select(
                    Product.id,
                    Product.category_id,
                )
                .where(
                    Product.is_active.is_(True),
                    Product.stock_quantity > 0,
                )
            )

            available_products = db.execute(
                available_query
            ).all()

            category_candidates = defaultdict(list)
            all_candidates = []

            for product in available_products:

                all_candidates.append(product.id)

                if product.category_id is not None:

                    category_candidates[
                        product.category_id
                    ].append(product.id)

            # Sort products by training-period popularity.
            # Higher view count comes first.
            # Product ID breaks ties deterministically.

            def popularity_sort(product_id):

                return (
                    -product_popularity.get(product_id, 0),
                    product_id,
                )

            for category_id in category_candidates:

                category_candidates[category_id].sort(
                    key=popularity_sort
                )

            all_candidates.sort(key=popularity_sort)

            eligible_catalog_count = len(all_candidates)

            print(
                "Active and in-stock products:",
                f"{eligible_catalog_count:,}",
            )

            if eligible_catalog_count < RECOMMENDATIONS_PER_CUSTOMER:

                raise ValueError(
                    "Not enough eligible products for recommendations."
                )

            # ------------------------------------------------
            # 5. LOAD CUSTOMERS
            # ------------------------------------------------

            print("\n5. Loading customers...")

            customers = db.execute(
                select(Customer.id).order_by(Customer.id)
            ).scalars().all()

            print(f"Customers loaded: {len(customers):,}")

            # ------------------------------------------------
            # 6. GENERATE RECOMMENDATIONS
            # ------------------------------------------------

            print("\n6. Generating recommendations...")

            total_generated = 0
            customers_without_history = 0

            with open(
                TEMP_CSV,
                "w",
                newline="",
                encoding="utf-8",
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "customer_id",
                    "product_id",
                    "score",
                    "rank",
                    "preferred_category_id",
                    "reason",
                ])

                for index, customer_id in enumerate(
                    customers,
                    start=1,
                ):

                    already_purchased = purchased_products.get(
                        customer_id,
                        set(),
                    )

                    category_id = preferred_category.get(
                        customer_id
                    )

                    if category_id is None:

                        customers_without_history += 1

                    # Get eligible products from preferred category.
                    preferred_candidates = [
                        product_id
                        for product_id in category_candidates.get(
                            category_id,
                            [],
                        )
                        if product_id not in already_purchased
                    ]

                    selected = preferred_candidates[
                        :RECOMMENDATIONS_PER_CUSTOMER
                    ]

                    selected_set = set(selected)

                    # Fill remaining slots with globally popular
                    # eligible products.
                    if len(selected) < RECOMMENDATIONS_PER_CUSTOMER:

                        for product_id in all_candidates:

                            if product_id in already_purchased:
                                continue

                            if product_id in selected_set:
                                continue

                            selected.append(product_id)
                            selected_set.add(product_id)

                            if len(selected) == RECOMMENDATIONS_PER_CUSTOMER:
                                break

                    if len(selected) < RECOMMENDATIONS_PER_CUSTOMER:

                        raise ValueError(
                            f"Insufficient candidates for customer "
                            f"{customer_id}."
                        )

                    # Write five unique recommendations.
                    for rank, product_id in enumerate(
                        selected,
                        start=1,
                    ):

                        score = product_popularity.get(
                            product_id,
                            0,
                        )

                        if product_id in preferred_candidates:

                            reason = (
                                "Preferred category ranked by "
                                "training-period popularity"
                            )

                        else:

                            reason = (
                                "Training-period popularity fallback"
                            )

                        writer.writerow([
                            customer_id,
                            product_id,
                            score,
                            rank,
                            category_id,
                            reason,
                        ])

                        total_generated += 1

                    if index % 5000 == 0:

                        print(
                            f"Customers processed: {index:,}"
                        )

            expected_recommendations = (
                len(customers) * RECOMMENDATIONS_PER_CUSTOMER
            )

            if total_generated != expected_recommendations:

                raise ValueError(
                    f"Expected {expected_recommendations:,} "
                    f"recommendations but generated "
                    f"{total_generated:,}."
                )

            # ------------------------------------------------
            # 7. CREATE MANIFEST
            # ------------------------------------------------

            print("\n7. Creating recommendation manifest...")

            manifest = {

                "project": "YottaFlex.ai",

                "model_name": (
                    "category_affinity_training_only_v1"
                ),

                "cutoff": CUTOFF.isoformat(),

                "training_data": {
                    "page_views": (
                        "PageView.viewed_at < cutoff"
                    ),
                    "purchases": (
                        "Order.placed_at < cutoff"
                    ),
                    "purchase_statuses": POSITIVE_STATUSES,
                },

                "catalog_conditions": [
                    "Product.is_active = true",
                    "Product.stock_quantity > 0",
                ],

                "catalog_temporal_assumption": (
                    "The seeded product catalog is treated as "
                    "the candidate catalog for this experiment. "
                    "Product creation timestamps are excluded "
                    "because all seeded products have post-cutoff "
                    "timestamps."
                ),

                "recommendations_per_customer": (
                    RECOMMENDATIONS_PER_CUSTOMER
                ),

                "customer_count": len(customers),

                "eligible_catalog_count": eligible_catalog_count,

                "customers_without_browsing_history": (
                    customers_without_history
                ),

                "total_recommendations": total_generated,

                "ranking_method": (
                    "Preferred-category products ranked by "
                    "pre-cutoff page-view popularity. Remaining "
                    "recommendations use global pre-cutoff "
                    "page-view popularity."
                ),

                "availability_limitation": (
                    "Active status and stock quantity are based "
                    "on the current catalog snapshot. Historical "
                    "stock availability cannot be verified."
                ),

                "database_modified": False,
            }

            with open(
                TEMP_MANIFEST,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    manifest,
                    file,
                    indent=4,
                )

        # ----------------------------------------------------
        # 8. PUBLISH OUTPUT FILES
        # ----------------------------------------------------

        TEMP_CSV.replace(OUTPUT_FILE)
        TEMP_MANIFEST.replace(MANIFEST_FILE)

    except Exception:

        # Remove incomplete temporary files after failure.
        TEMP_CSV.unlink(missing_ok=True)
        TEMP_MANIFEST.unlink(missing_ok=True)

        raise

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("RECOMMENDATION GENERATION COMPLETED")
    print("=" * 70)

    print(f"Customers: {len(customers):,}")
    print(f"Eligible catalog: {eligible_catalog_count:,}")
    print(f"Recommendations: {total_generated:,}")

    print(
        "Customers without browsing history:",
        f"{customers_without_history:,}",
    )

    print(f"\nCSV: {OUTPUT_FILE.resolve()}")
    print(f"Manifest: {MANIFEST_FILE.resolve()}")

    print("\nOriginal database was NOT modified.")
    print("=" * 70)


if __name__ == "__main__":
    main()
