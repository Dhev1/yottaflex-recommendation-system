
import random
from datetime import datetime, timedelta

from sqlalchemy import insert
from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import (
    Customer,
    Product,
    Session as SessionModel,
    PageView
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 42

TOTAL_SESSIONS = 500_000
BATCH_SIZE = 5_000

DATA_START = datetime(2025, 1, 1)
DATA_END = datetime(2026, 10, 31, 23, 0, 0)

DEVICE_TYPES = ["mobile", "desktop", "tablet"]

TRAFFIC_SOURCES = [
    "organic_search",
    "direct",
    "social",
    "email",
    "referral",
    "paid_ads"
]

rng = random.Random(SEED)


# --------------------------------------------------
# GENERATE SESSION AND PAGE-VIEW DATA
# --------------------------------------------------

def generate_activity(db):

    next_page_view_id = 1

    total_seconds = int(
        (DATA_END - DATA_START).total_seconds()
    )

    print("Starting session generation...")

    for batch_start in range(1, TOTAL_SESSIONS + 1, BATCH_SIZE):

        batch_end = min(
            batch_start + BATCH_SIZE,
            TOTAL_SESSIONS + 1
        )

        session_rows = []
        page_view_rows = []

        for session_id in range(batch_start, batch_end):

            # Choose a customer
            customer_id = rng.randint(1, 20_000)

            # Generate session start time
            started_at = DATA_START + timedelta(
                seconds=rng.randint(0, total_seconds)
            )

            # Session duration: 1 minute to 1 hour
            session_duration = rng.randint(60, 3600)

            ended_at = started_at + timedelta(
                seconds=session_duration
            )

            # Session details
            session_rows.append({
                "id": session_id,
                "customer_id": customer_id,
                "device_type": rng.choice(DEVICE_TYPES),
                "source": rng.choice(TRAFFIC_SOURCES),
                "started_at": started_at,
                "ended_at": ended_at
            })

            # Generate 1 to 5 product page views
            view_count = rng.randint(1, 5)

            view_offsets = sorted(
                rng.sample(
                    range(session_duration + 1),
                    view_count
                )
            )

            for offset in view_offsets:

                viewed_at = started_at + timedelta(
                    seconds=offset
                )

                page_view_rows.append({
                    "id": next_page_view_id,
                    "session_id": session_id,
                    "product_id": rng.randint(1, 10_000),
                    "page_type": "product_detail",
                    "viewed_at": viewed_at,
                    "duration_seconds": rng.randint(5, 300)
                })

                next_page_view_id += 1

        # Insert the session batch
        db.execute(
            insert(SessionModel),
            session_rows
        )

        # Insert corresponding page views
        db.execute(
            insert(PageView),
            page_view_rows
        )

        print(
            f"Sessions generated: {batch_end - 1:,}/{TOTAL_SESSIONS:,} "
            f"| Page views generated: {next_page_view_id - 1:,}"
        )

    print("\nSession and page-view generation completed!")


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():

    with DBSession(engine) as db:

        try:

            customer_count = db.query(Customer).count()
            product_count = db.query(Product).count()

            session_count = db.query(SessionModel).count()
            page_view_count = db.query(PageView).count()

            if customer_count != 20_000 or product_count != 10_000:
                print("Required customer/product data is missing.")
                return

            if session_count > 0 or page_view_count > 0:
                print("Sessions or page views already exist.")
                print("Stopping to prevent duplicate generation.")
                return

            generate_activity(db)

            # Commit all generated records
            db.commit()

            print("\nAll activity data committed successfully!")

        except Exception as error:

            db.rollback()

            print("\nGeneration failed:", error)

            raise


if __name__ == "__main__":
    main()
