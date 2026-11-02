
import random
from datetime import timedelta

from sqlalchemy import select, insert
from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import (
    Session as SessionModel,
    Product,
    Cart,
    CartLine
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 42
TOTAL_CARTS = 150_000
BATCH_SIZE = 5_000

rng = random.Random(SEED)


# --------------------------------------------------
# GENERATE CARTS AND CART LINES
# --------------------------------------------------

def generate_carts(db):

    print("Loading existing sessions and products...")

    sessions = db.execute(
        select(
            SessionModel.id,
            SessionModel.customer_id,
            SessionModel.started_at,
            SessionModel.ended_at
        )
    ).all()

    products = db.execute(
        select(Product.id, Product.price)
    ).all()

    if not sessions or not products:
        raise ValueError("Sessions or products are missing.")

    product_prices = {
        product.id: product.price
        for product in products
    }

    product_ids = list(product_prices.keys())

    print(f"Loaded {len(sessions):,} sessions")
    print(f"Loaded {len(products):,} products")

    next_cart_id = 1
    next_cart_line_id = 1

    for batch_start in range(
        1,
        TOTAL_CARTS + 1,
        BATCH_SIZE
    ):

        batch_end = min(
            batch_start + BATCH_SIZE,
            TOTAL_CARTS + 1
        )

        cart_rows = []
        cart_line_rows = []

        for cart_id in range(batch_start, batch_end):

            # Select an existing session
            session = rng.choice(sessions)

            customer_id = session.customer_id
            session_id = session.id

            created_at = session.started_at

            session_end = (
                session.ended_at
                or created_at + timedelta(minutes=30)
            )

            duration = max(
                0,
                int((session_end - created_at).total_seconds())
            )

            updated_at = created_at + timedelta(
                seconds=rng.randint(0, duration)
            )

            # Cart lifecycle status
            status = rng.choices(
                ["converted", "abandoned", "active"],
                weights=[60, 25, 15],
                k=1
            )[0]

            cart_rows.append({
                "id": cart_id,
                "customer_id": customer_id,
                "session_id": session_id,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at
            })

            # Generate 1 to 4 unique products per cart
            line_count = rng.randint(1, 4)

            selected_products = rng.sample(
                product_ids,
                line_count
            )

            for product_id in selected_products:

                quantity = rng.randint(1, 3)

                unit_price = product_prices[product_id]

                cart_line_rows.append({
                    "cart_id": cart_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price
                })

        # Insert cart records
        db.execute(
            insert(Cart),
            cart_rows
        )

        # Insert cart line records
        db.execute(
            insert(CartLine),
            cart_line_rows
        )

        print(
            f"Carts generated: {batch_end - 1:,}/{TOTAL_CARTS:,} "
            f"| Cart lines: {len(cart_line_rows):,} in current batch"
        )

    print("\nCart generation completed!")


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():

    with DBSession(engine) as db:

        try:

            existing_carts = db.query(Cart).count()
            existing_lines = db.query(CartLine).count()

            if existing_carts > 0 or existing_lines > 0:
                print("Cart data already exists. Stopping.")
                return

            session_count = db.query(SessionModel).count()
            product_count = db.query(Product).count()

            if session_count != 500_000 or product_count != 10_000:
                print("Required session/product data is missing.")
                return

            print("Starting cart generation...")

            generate_carts(db)

            db.commit()

            print("\nAll cart data committed successfully!")

        except Exception as error:

            db.rollback()

            print("\nCart generation failed:", error)

            raise


if __name__ == "__main__":
    main()
