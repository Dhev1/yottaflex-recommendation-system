
import random
from decimal import Decimal
from datetime import timedelta

from sqlalchemy import select, insert
from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import (
    Session as SessionModel,
    PageView,
    Product,
    Order,
    OrderLine
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 42
TOTAL_ORDERS = 100_000
BATCH_SIZE = 5_000

TAX_RATE = Decimal("0.18")
STANDARD_SHIPPING = Decimal("40.00")
FREE_SHIPPING_LIMIT = Decimal("999.00")

rng = random.Random(SEED)


# --------------------------------------------------
# GENERATE ORDERS AND ORDER LINES
# --------------------------------------------------

def generate_orders(db):

    print("Loading sessions and product prices...")

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

    if len(sessions) < TOTAL_ORDERS:
        raise ValueError("Not enough sessions to generate orders.")

    product_prices = {
        product.id: product.price
        for product in products
    }

    # Select 100,000 distinct sessions.
    selected_sessions = rng.sample(sessions, TOTAL_ORDERS)

    print(f"Selected {len(selected_sessions):,} sessions")

    for batch_start in range(0, TOTAL_ORDERS, BATCH_SIZE):

        batch_sessions = selected_sessions[
            batch_start:batch_start + BATCH_SIZE
        ]

        session_ids = [s.id for s in batch_sessions]

        # Get products actually viewed in these sessions.
        page_views = db.execute(
            select(
                PageView.session_id,
                PageView.product_id,
                PageView.viewed_at
            ).where(
                PageView.session_id.in_(session_ids)
            )
        ).all()

        views_by_session = {}

        for view in page_views:

            views_by_session.setdefault(
                view.session_id, []
            ).append(view)

        order_rows = []
        order_line_rows = []

        first_order_id = batch_start + 1

        for index, session in enumerate(batch_sessions):

            order_id = first_order_id + index

            available_views = views_by_session.get(
                session.id, []
            )

            if not available_views:
                raise ValueError(
                    f"No page views found for session {session.id}"
                )

            # Keep only unique products viewed in this session.
            viewed_products = {}

            for view in available_views:
                viewed_products[view.product_id] = view.viewed_at

            viewed_product_ids = list(viewed_products.keys())

            # Select 1 to 3 products from viewed products.
            line_count = min(
                rng.randint(1, 3),
                len(viewed_product_ids)
            )

            selected_products = rng.sample(
                viewed_product_ids,
                line_count
            )

            subtotal = Decimal("0.00")
            latest_view_time = max(
                viewed_products[product_id]
                for product_id in selected_products
            )

            for product_id in selected_products:

                quantity = rng.randint(1, 3)
                unit_price = product_prices[product_id]

                line_total = (
                    unit_price * quantity
                ).quantize(Decimal("0.01"))

                subtotal += line_total

                order_line_rows.append({
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": line_total
                })

            subtotal = subtotal.quantize(Decimal("0.01"))

            tax = (
                subtotal * TAX_RATE
            ).quantize(Decimal("0.01"))

            shipping_cost = (
                Decimal("0.00")
                if subtotal >= FREE_SHIPPING_LIMIT
                else STANDARD_SHIPPING
            )

            total_amount = (
                subtotal + tax + shipping_cost
            ).quantize(Decimal("0.01"))

            # Place order after the selected products were viewed.
            placed_at = latest_view_time + timedelta(
                seconds=rng.randint(1, 300)
            )

            # Keep order time within its session.
            if session.ended_at and placed_at > session.ended_at:
                placed_at = session.ended_at

            status = rng.choices(
                [
                    "pending",
                    "paid",
                    "shipped",
                    "delivered",
                    "cancelled",
                    "refunded"
                ],
                weights=[10, 25, 20, 30, 10, 5],
                k=1
            )[0]

            order_rows.append({
                "id": order_id,
                "customer_id": session.customer_id,
                "session_id": session.id,
                "status": status,
                "subtotal": subtotal,
                "tax": tax,
                "shipping_cost": shipping_cost,
                "total_amount": total_amount,
                "currency": "INR",
                "placed_at": placed_at
            })

        # Insert orders first, then their lines.
        db.execute(insert(Order), order_rows)
        db.execute(insert(OrderLine), order_line_rows)

        print(
            f"Orders generated: "
            f"{batch_start + len(batch_sessions):,}/{TOTAL_ORDERS:,} "
            f"| Order lines: {len(order_line_rows):,} in current batch"
        )

    print("\nOrder generation completed!")


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():

    with DBSession(engine) as db:

        try:

            existing_orders = db.query(Order).count()
            existing_lines = db.query(OrderLine).count()

            if existing_orders > 0 or existing_lines > 0:
                print("Order data already exists. Stopping.")
                return

            session_count = db.query(SessionModel).count()
            product_count = db.query(Product).count()

            if session_count != 500_000 or product_count != 10_000:
                print("Required session/product data is missing.")
                return

            print("Starting order generation...")

            generate_orders(db)

            db.commit()

            print("\nAll order data committed successfully!")

        except Exception as error:

            db.rollback()

            print("\nOrder generation failed:", error)

            raise


if __name__ == "__main__":
    main()
