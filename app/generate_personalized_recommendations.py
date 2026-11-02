
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

POSITIVE_STATUSES = ["paid", "shipped", "delivered"]

OUTPUT_DIR = Path("reports/evaluation")

OUTPUT_FILE = OUTPUT_DIR / "personalized_recommendations.csv"
MANIFEST_FILE = OUTPUT_DIR / "personalized_recommendation_manifest.json"

TEMP_CSV = OUTPUT_DIR / "personalized_recommendations.tmp"
TEMP_MANIFEST = OUTPUT_DIR / "personalized_recommendation_manifest.tmp"


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Never overwrite existing evaluation artifacts.
    if any(path.exists() for path in [
        OUTPUT_FILE,
        MANIFEST_FILE,
        TEMP_CSV,
        TEMP_MANIFEST,
    ]):
        raise FileExistsError(
            "Personalized output already exists. "
            "Inspect existing files before running again."
        )

    print("=" * 70)
    print("YOTTAFLEX.AI - PERSONALIZED RECOMMENDATION GENERATION")
    print("=" * 70)

    try:

        with DBSession(engine) as db:

            # ------------------------------------------------
            # 1. INDIVIDUAL CUSTOMER-PRODUCT VIEW FREQUENCY
            # ------------------------------------------------

            print("\n1. Calculating individual product-view frequency...")

            personal_query = (
                select(
                    SessionModel.customer_id,
                    PageView.product_id,
                    Product.category_id,
                    func.count(PageView.id).label("personal_views"),
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
                    PageView.product_id,
                    Product.category_id,
                )
            )

            personal_views = defaultdict(dict)
            customer_category_views = defaultdict(lambda: defaultdict(int))

            for row in db.execute(personal_query):

                personal_views[row.customer_id][row.product_id] = {
                    "category_id": row.category_id,
                    "view_count": row.personal_views,
                }

                customer_category_views[
                    row.customer_id
                ][row.category_id] += row.personal_views

            preferred_category = {
                customer_id: sorted(
                    category_counts.items(),
                    key=lambda item: (-item[1], item[0]),
                )[0][0]
                for customer_id, category_counts
                in customer_category_views.items()
            }

            print(
                "Customers with browsing history:",
                f"{len(personal_views):,}",
            )

            print(
                "Unique customer-product view pairs:",
                f"{sum(len(items) for items in personal_views.values()):,}",
            )

            # ------------------------------------------------
            # 2. GLOBAL AND CATEGORY POPULARITY
            # ------------------------------------------------

            print("\n2. Calculating popularity tie-breakers...")

            popularity_query = (
                select(
                    PageView.product_id,
                    func.count(PageView.id).label("view_count"),
                )
                .where(PageView.viewed_at < CUTOFF)
                .group_by(PageView.product_id)
            )

            product_popularity = {
                row.product_id: row.view_count
                for row in db.execute(popularity_query)
            }

            product_category_query = select(
                Product.id,
                Product.category_id,
            )

            product_categories = {
                row.id: row.category_id
                for row in db.execute(product_category_query)
            }

            category_popularity = defaultdict(int)

            for product_id, view_count in product_popularity.items():

                category_id = product_categories.get(product_id)

                if category_id is not None:
                    category_popularity[category_id] += view_count

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

            # ------------------------------------------------
            # 4. ELIGIBLE CATALOG
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

            eligible_products = {
                row.id: row.category_id
                for row in db.execute(available_query)
            }

            print(
                "Active and in-stock products:",
                f"{len(eligible_products):,}",
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
            # 6. GENERATE PERSONALIZED RECOMMENDATIONS
            # ------------------------------------------------

            print("\n6. Generating personalized recommendations...")

            total_generated = 0
            customers_without_history = 0
            customers_with_insufficient_candidates = 0

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

                    category_id = preferred_category.get(customer_id)

                    if category_id is None:
                        customers_without_history += 1

                    already_purchased = purchased_products.get(
                        customer_id,
                        set(),
                    )

                    # Only products personally viewed by this
                    # customer, not previously purchased, and
                    # currently eligible are considered.

                    candidates = []

                    for product_id, history in personal_views.get(
                        customer_id,
                        {},
                    ).items():

                        if product_id in already_purchased:
                            continue

                        if product_id not in eligible_products:
                            continue

                        product_category = eligible_products[product_id]

                        personal_count = history["view_count"]

                        global_count = product_popularity.get(
                            product_id,
                            0,
                        )

                        category_count = category_popularity.get(
                            product_category,
                            0,
                        )

                        # Ranking priority:
                        # 1. Preferred category first.
                        # 2. Higher individual view frequency.
                        # 3. Higher category popularity.
                        # 4. Higher global popularity.
                        # 5. Product ID for deterministic ties.

                        sort_key = (
                            0 if product_category == category_id else 1,
                            -personal_count,
                            -category_count,
                            -global_count,
                            product_id,
                        )

                        candidates.append((
                            sort_key,
                            product_id,
                            personal_count,
                            product_category,
                        ))

                    candidates.sort(key=lambda item: item[0])

                    selected = candidates[
                        :RECOMMENDATIONS_PER_CUSTOMER
                    ]

                    if len(selected) < RECOMMENDATIONS_PER_CUSTOMER:

                        customers_with_insufficient_candidates += 1

                        raise ValueError(
                            f"Customer {customer_id} has only "
                            f"{len(selected)} eligible personalized "
                            f"candidates. Expected "
                            f"{RECOMMENDATIONS_PER_CUSTOMER}."
                        )

                    for rank, item in enumerate(selected, start=1):

                        _, product_id, personal_count, product_category = item

                        if product_category == category_id:
                            reason = (
                                "Preferred category ranked by "
                                "individual product-view frequency"
                            )
                        else:
                            reason = (
                                "Other personally viewed product "
                                "ranked by individual view frequency"
                            )

                        writer.writerow([
                            customer_id,
                            product_id,
                            personal_count,
                            rank,
                            category_id,
                            reason,
                        ])

                        total_generated += 1

                    if index % 5000 == 0:

                        print(
                            f"Customers processed: {index:,}"
                        )

            # ------------------------------------------------
            # 7. VERIFY GENERATED COUNT
            # ------------------------------------------------

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
            # 8. CREATE MANIFEST
            # ------------------------------------------------

            print("\n7. Creating personalized recommendation manifest...")

            manifest = {

                "project": "YottaFlex.ai",

                "model_name": "personalized_category_affinity_v2",

                "algorithm_type": (
                    "Personalized implicit-feedback recommendation"
                ),

                "cutoff": CUTOFF.isoformat(),

                "training_data": {
                    "page_views": "PageView.viewed_at < cutoff",
                    "purchases": "Order.placed_at < cutoff",
                    "purchase_statuses": POSITIVE_STATUSES,
                },

                "catalog_conditions": [
                    "Product.is_active = true",
                    "Product.stock_quantity > 0",
                ],

                "catalog_temporal_assumption": (
                    "The seeded product catalog is treated as the "
                    "candidate catalog for this experiment. "
                    "Product creation timestamps are excluded because "
                    "all seeded products have post-cutoff timestamps."
                ),

                "recommendations_per_customer": (
                    RECOMMENDATIONS_PER_CUSTOMER
                ),

                "customer_count": len(customers),

                "eligible_catalog_count": len(eligible_products),

                "customers_without_browsing_history": (
                    customers_without_history
                ),

                "customers_with_insufficient_candidates": (
                    customers_with_insufficient_candidates
                ),

                "total_recommendations": total_generated,

                "ranking_method": (
                    "Products personally viewed before cutoff and "
                    "not previously purchased are ranked first by "
                    "preferred category, then individual customer "
                    "product-view frequency. Category and global "
                    "popularity are deterministic tie-breakers."
                ),

                "score_definition": (
                    "Number of pre-cutoff page views by the individual "
                    "customer for the recommended product."
                ),

                "availability_limitation": (
                    "Active status and stock quantity are based on "
                    "the current catalog snapshot. Historical stock "
                    "availability cannot be verified."
                ),

                "database_modified": False,
            }

            with open(
                TEMP_MANIFEST,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(manifest, file, indent=4)

        # ----------------------------------------------------
        # 9. PUBLISH OUTPUT FILES
        # ----------------------------------------------------

        TEMP_CSV.replace(OUTPUT_FILE)
        TEMP_MANIFEST.replace(MANIFEST_FILE)

    except Exception:

        TEMP_CSV.unlink(missing_ok=True)
        TEMP_MANIFEST.unlink(missing_ok=True)

        raise

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PERSONALIZED RECOMMENDATION GENERATION COMPLETED")
    print("=" * 70)

    print(f"Customers: {len(customers):,}")
    print(f"Eligible catalog: {len(eligible_products):,}")
    print(f"Recommendations: {total_generated:,}")

    print(
        "Customers without browsing history:",
        f"{customers_without_history:,}",
    )

    print(
        "Customers with insufficient candidates:",
        f"{customers_with_insufficient_candidates:,}",
    )

    print(f"\nCSV: {OUTPUT_FILE.resolve()}")
    print(f"Manifest: {MANIFEST_FILE.resolve()}")

    print("\nOriginal database was NOT modified.")
    print("=" * 70)


if __name__ == "__main__":
    main()
