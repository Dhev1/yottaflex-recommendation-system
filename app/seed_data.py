
import random
from decimal import Decimal

from faker import Faker
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Customer, Category, Product


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SEED = 42

CUSTOMER_COUNT = 20000
PRODUCT_COUNT = 10000

fake = Faker("en_IN")
Faker.seed(SEED)

random_generator = random.Random(SEED)


# --------------------------------------------------
# CATEGORY DATA
# --------------------------------------------------

CATEGORY_NAMES = [
    "Electronics",
    "Mobiles",
    "Laptops",
    "Fashion",
    "Footwear",
    "Home Appliances",
    "Furniture",
    "Books",
    "Sports",
    "Beauty",
    "Groceries",
    "Kitchen",
    "Toys",
    "Automotive",
    "Gaming",
    "Watches",
    "Accessories",
    "Health",
    "Stationery",
    "Travel"
]


# --------------------------------------------------
# GENERATE CATEGORIES
# --------------------------------------------------

def generate_categories(db):

    categories = []

    for index, name in enumerate(CATEGORY_NAMES, start=1):

        category = Category(
            id=index,
            name=name,
            description=f"Products related to {name}",
            is_active=True
        )

        categories.append(category)

    db.add_all(categories)
    db.flush()

    print(f"Created {len(categories)} categories")

    return categories


# --------------------------------------------------
# GENERATE CUSTOMERS
# --------------------------------------------------

def generate_customers(db):

    batch_size = 1000

    for start in range(1, CUSTOMER_COUNT + 1, batch_size):

        customers = []

        end = min(start + batch_size, CUSTOMER_COUNT + 1)

        for customer_id in range(start, end):

            customer = Customer(
                id=customer_id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.unique.email(),
                city=fake.city(),
                country=fake.country(),
                is_active=random_generator.choice([True, True, True, False])
            )

            customers.append(customer)

        db.add_all(customers)
        db.flush()

        print(f"Generated customers: {end - 1}/{CUSTOMER_COUNT}")

    print("Customer generation completed")


# --------------------------------------------------
# GENERATE PRODUCTS
# --------------------------------------------------

def generate_products(db):

    batch_size = 1000

    category_ids = list(range(1, len(CATEGORY_NAMES) + 1))

    for start in range(1, PRODUCT_COUNT + 1, batch_size):

        products = []

        end = min(start + batch_size, PRODUCT_COUNT + 1)

        for product_id in range(start, end):

            price = Decimal(
                random_generator.randrange(100, 100000)
            ) / Decimal("100")

            product = Product(
                id=product_id,
                name=fake.catch_phrase(),
                description=fake.sentence(),
                sku=f"SKU-{product_id:06d}",
                price=price,
                stock_quantity=random_generator.randint(0, 500),
                category_id=random_generator.choice(category_ids),
                is_active=random_generator.choice([True, True, True, False])
            )

            products.append(product)

        db.add_all(products)
        db.flush()

        print(f"Generated products: {end - 1}/{PRODUCT_COUNT}")

    print("Product generation completed")


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():

    with Session(engine) as db:

        try:

            # Prevent accidental duplicate generation
            if db.query(Customer).first():
                print("Customers already exist. Stopping generation.")
                return

            if db.query(Category).first():
                print("Categories already exist. Stopping generation.")
                return

            if db.query(Product).first():
                print("Products already exist. Stopping generation.")
                return

            print("Starting synthetic data generation...")

            generate_categories(db)

            generate_customers(db)

            generate_products(db)

            db.commit()

            print("\nSynthetic data generation completed successfully!")

        except Exception as error:

            db.rollback()

            print("Data generation failed:", error)

            raise


if __name__ == "__main__":
    main()
