
from sqlalchemy import text

from app.database import engine


def main():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    current_setting('TIMEZONE') AS database_timezone,
                    now() AS database_current_time,
                    min(viewed_at) AS first_page_view,
                    max(viewed_at) AS last_page_view
                FROM page_views
            """)
        ).mappings().one()

        print("=" * 65)
        print("POSTGRESQL TIMEZONE INSPECTION")
        print("=" * 65)

        for key, value in result.items():
            print(f"{key}: {value}")

        print("=" * 65)


if __name__ == "__main__":
    main()
