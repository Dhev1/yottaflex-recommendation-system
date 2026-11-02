
import random
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select, func, insert
from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import (
    Customer,
    Product,
    Session as SessionModel,
    PageView,
    Order,
    OrderLine,
    ProductRelation,
    Recommendation
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 42

TOTAL_RELATIONS = 20_000
RECOMMENDATIONS_PER_CUSTOMER = 5

BATCH_SIZE = 5_000

GENERATED_AT = datetime(2026, 10, 31, 23, 59, 0)

rng = random.Random(SEED)


# --------------------------------------------------
# GENERATE PRODUCT RELATIONSHIPS
# --------------------------------------------------

def generate_product_relations(db):

    print("Loading products...")

    products = db.execute(
        select(Product.id, Product.category_id)
    ).all()

    category_products = {}

    for product in products:

        if product.category_id is not None:

            category_products.setdefault(
                product.category_id, []
            ).append(product.id)

    valid_categories = [
        ids for ids in category_products.values()
        if len(ids) >= 2
    ]

    if not valid_categories:
        raise ValueError("No suitable product categories found.")

    relations = []
    existing_pairs = set()

    while len(relations) < TOTAL_RELATIONS:

        category = rng.choice(valid_categories)

        source_id, target_id = rng.sample(category, 2)

        pair = (source_id, target_id)

        if pair in existing_pairs:
            continue

        existing_pairs.add(pair)

        relations.append({
            "source_product_id": source_id,
            "target_product_id": target_id,
            "relation_type": "similar_to",
            "strength": Decimal(
                str(round(rng.uniform(0.50, 1.00), 4))
            ),
            "created_at": GENERATED_AT
        })

        if len(relations) % BATCH_SIZE == 0:

            print(
                f"Product relationships generated: "
                f"{len(relations):,}/{TOTAL_RELATIONS:,}"
            )

    db.execute(
        insert(ProductRelation),
        relations
    )

    print(f"Created {len(relations):,} product relationships")


# --------------------------------------------------
# GENERATE CUSTOMER RECOMMENDATIONS
# --------------------------------------------------

def generate_recommendations(db):

    print("Calculating customer browsing preferences...")

    # Find the most-viewed category for each customer.
    category_preferences = db.execute(
        select(
            SessionModel.customer_id,
            Product.category_id,
            func.count(PageView.id).label("view_count")
        )
        .join(
            PageView,
            PageView.session_id == SessionModel.id
        )
        .join(
            Product,
            Product.id == PageView.product_id
        )
        .where(Product.category_id.is_not(None))
        .group_by(
            SessionModel.customer_id,
            Product.category_id
        )
        .order_by(func.count(PageView.id).desc())
    ).all()

    preferred_category = {}

    for row in category_preferences:

        if row.customer_id not in preferred_category:

            preferred_category[row.customer_id] = (
                row.category_id
            )

    # Find products already purchased by each customer.
    print("Loading customer purchase history...")

    purchase_history = db.execute(
        select(
            Order.customer_id,
            OrderLine.product_id
        )
        .join(
            OrderLine,
            OrderLine.order_id == Order.id
        )
    ).all()

    purchased_products = {}

    for row in purchase_history:

        purchased_products.setdefault(
            row.customer_id, set()
        ).add(row.product_id)

    # Only recommend active products with available stock.
    available_products = db.execute(
        select(Product.id, Product.category_id)
        .where(
            Product.is_active.is_(True),
            Product.stock_quantity > 0
        )
    ).all()

    if len(available_products) < RECOMMENDATIONS_PER_CUSTOMER:
        raise ValueError("Not enough available products.")

    category_candidates = {}
    all_candidates = []

    for product in available_products:

        all_candidates.append(product.id)

        if product.category_id is not None:

            category_candidates.setdefault(
                product.category_id, []
            ).append(product.id)

    customers = db.execute(
        select(Customer.id).order_by(Customer.id)
    ).scalars().all()

    print(f"Customers loaded: {len(customers):,}")
    print(f"Available products: {len(all_candidates):,}")

    recommendation_batch = []
    total_generated = 0

    for customer_id in customers:

        already_purchased = purchased_products.get(
            customer_id, set()
        )

        category_id = preferred_category.get(customer_id)

        preferred_products = category_candidates.get(
            category_id, []
        )

        # First try the customer's preferred category.
        preferred_candidates = [
            product_id
            for product_id in preferred_products
            if product_id not in already_purchased
        ]

        selected = preferred_candidates.copy()

        # Add other categories if needed.
        if len(selected) < RECOMMENDATIONS_PER_CUSTOMER:

            fallback_candidates = [
                product_id
                for product_id in all_candidates
                if product_id not in already_purchased
                and product_id not in selected
            ]

            selected.extend(
                fallback_candidates[:]
            )

        if len(selected) < RECOMMENDATIONS_PER_CUSTOMER:

            raise ValueError(
                f"Not enough recommendation candidates "
                f"for customer {customer_id}"
            )

        # Choose five unique recommendations.
        selected_products = rng.sample(
            selected,
            RECOMMENDATIONS_PER_CUSTOMER
        )

        for rank, product_id in enumerate(
            selected_products, start=1
        ):

            score = round(
                1.0 - ((rank - 1) * 0.08)
                + rng.uniform(-0.02, 0.02),
                6
            )

            recommendation_batch.append({
                "customer_id": customer_id,
                "product_id": product_id,
                "model_name": "category_affinity_v1",
                "score": score,
                "rank": rank,
                "reason": (
                    "Based on browsing category preference"
                ),
                "generated_at": GENERATED_AT
            })

            if len(recommendation_batch) >= BATCH_SIZE:

                db.execute(
                    insert(Recommendation),
                    recommendation_batch
                )

                total_generated += len(recommendation_batch)
                recommendation_batch.clear()

        if customer_id % 1000 == 0:

            print(
                f"Customers processed: {customer_id:,}"
            )

    # Insert remaining records.
    if recommendation_batch:

        db.execute(
            insert(Recommendation),
            recommendation_batch
        )

        total_generated += len(recommendation_batch)

    print(
        f"Total recommendations generated: "
        f"{total_generated:,}"
    )


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():

    with DBSession(engine) as db:

        try:

            if db.query(ProductRelation).count() > 0:
                print("Product relationships already exist. Stopping.")
                return

            if db.query(Recommendation).count() > 0:
                print("Recommendations already exist. Stopping.")
                return

            customer_count = db.query(Customer).count()
            product_count = db.query(Product).count()
            order_count = db.query(Order).count()

            if (
                customer_count != 20_000
                or product_count != 10_000
                or order_count != 100_000
            ):
                print("Required source data is missing.")
                return

            print("Starting product relationship generation...")

            generate_product_relations(db)

            print("\nStarting customer recommendation generation...")

            generate_recommendations(db)

            db.commit()

            print("\nAll recommendation data committed successfully!")

        except Exception as error:

            db.rollback()

            print("\nGeneration failed:", error)

            raise


if __name__ == "__main__":
    main()
