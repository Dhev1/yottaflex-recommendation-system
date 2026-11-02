
from datetime import datetime, timezone, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import PageView, Order, OrderLine


# July 1, 2026, midnight IST
CUTOFF = datetime(
    2026, 7, 1, 0, 0, 0,
    tzinfo=timezone(timedelta(hours=5, minutes=30))
)


def main():

    with DBSession(engine) as db:

        print("=" * 65)
        print("YOTTAFLEX.AI - TEMPORAL SPLIT INSPECTION")
        print("=" * 65)

        print(f"\nTraining cutoff: {CUTOFF.isoformat()}")

        # Page views
        train_views = db.query(PageView.id).filter(
            PageView.viewed_at < CUTOFF
        ).count()

        test_views = db.query(PageView.id).filter(
            PageView.viewed_at >= CUTOFF
        ).count()

        # Orders
        train_orders = db.query(Order.id).filter(
            Order.placed_at < CUTOFF
        ).count()

        test_orders = db.query(Order.id).filter(
            Order.placed_at >= CUTOFF
        ).count()

        # Order lines belonging to test orders
        test_order_lines = (
            db.query(OrderLine.id)
            .join(Order, OrderLine.order_id == Order.id)
            .filter(Order.placed_at >= CUTOFF)
            .count()
        )

        # Customers with test-period purchases
        test_customers = (
            db.query(Order.customer_id)
            .filter(Order.placed_at >= CUTOFF)
            .distinct()
            .count()
        )

        # Date ranges
        first_view = db.query(
            func.min(PageView.viewed_at)
        ).scalar()

        last_view = db.query(
            func.max(PageView.viewed_at)
        ).scalar()

        first_order = db.query(
            func.min(Order.placed_at)
        ).scalar()

        last_order = db.query(
            func.max(Order.placed_at)
        ).scalar()

        print("\nPAGE VIEW DISTRIBUTION")
        print("-" * 65)
        print(f"Training page views : {train_views:,}")
        print(f"Test page views     : {test_views:,}")
        print(f"Total page views    : {train_views + test_views:,}")

        print("\nORDER DISTRIBUTION")
        print("-" * 65)
        print(f"Training orders     : {train_orders:,}")
        print(f"Test orders         : {test_orders:,}")
        print(f"Total orders        : {train_orders + test_orders:,}")

        print("\nTEST GROUND TRUTH")
        print("-" * 65)
        print(f"Test order lines    : {test_order_lines:,}")
        print(f"Customers purchasing in test period: {test_customers:,}")

        print("\nDATASET TIMESTAMP RANGE")
        print("-" * 65)
        print(f"First page view: {first_view}")
        print(f"Last page view : {last_view}")
        print(f"First order    : {first_order}")
        print(f"Last order     : {last_order}")

        print("\n" + "=" * 65)
        print("TEMPORAL INSPECTION COMPLETED")
        print("=" * 65)


if __name__ == "__main__":
    main()
