
from decimal import Decimal, ROUND_HALF_EVEN

from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app.models import (
    Customer,
    Category,
    Product,
    Session as SessionModel,
    PageView,
    Cart,
    CartLine,
    Order,
    OrderLine,
    ProductRelation,
    Recommendation,
)


# ============================================================
# CONFIGURATION
# ============================================================

EXPECTED_COUNTS = {
    "customers": 20_000,
    "categories": 20,
    "products": 10_000,
    "sessions": 500_000,
    "page_views": 1_497_995,
    "carts": 150_000,
    "cart_lines": 375_671,
    "orders": 100_000,
    "order_lines": 173_646,
    "product_relations": 20_000,
    "recommendations": 100_000,
}


TABLE_MODELS = {
    "customers": Customer,
    "categories": Category,
    "products": Product,
    "sessions": SessionModel,
    "page_views": PageView,
    "carts": Cart,
    "cart_lines": CartLine,
    "orders": Order,
    "order_lines": OrderLine,
    "product_relations": ProductRelation,
    "recommendations": Recommendation,
}


# ============================================================
# COMMON VALIDATION HELPER
# ============================================================

def print_check(label, invalid_count):
    passed = invalid_count == 0

    print(
        f"{label:<42} "
        f"Invalid: {invalid_count:>7,} | "
        f"{'PASS' if passed else 'FAIL'}"
    )

    return 0 if passed else 1


# ============================================================
# 1. RECORD COUNT VALIDATION
# ============================================================

def validate_record_counts(db):

    print("\n1. RECORD COUNT VALIDATION")
    print("-" * 65)

    failures = 0

    for table_name, model in TABLE_MODELS.items():

        actual = db.query(model).count()
        expected = EXPECTED_COUNTS[table_name]

        passed = actual == expected

        if not passed:
            failures += 1

        print(
            f"{table_name:<22} "
            f"Expected: {expected:>10,} | "
            f"Actual: {actual:>10,} | "
            f"{'PASS' if passed else 'FAIL'}"
        )

    return failures


# ============================================================
# 2. PRIMARY KEY VALIDATION
# ============================================================

def validate_primary_keys(db):

    print("\n2. PRIMARY KEY VALIDATION")
    print("-" * 65)

    failures = 0

    for table_name, model in TABLE_MODELS.items():

        # Check NULL primary keys.
        null_count = (
            db.query(model.id)
            .filter(model.id.is_(None))
            .count()
        )

        # Check duplicate primary keys.
        duplicate_count = (
            db.query(model.id)
            .group_by(model.id)
            .having(func.count(model.id) > 1)
            .count()
        )

        passed = (
            null_count == 0
            and duplicate_count == 0
        )

        if not passed:
            failures += 1

        print(
            f"{table_name:<22} "
            f"NULL IDs: {null_count:>5} | "
            f"Duplicate IDs: {duplicate_count:>5} | "
            f"{'PASS' if passed else 'FAIL'}"
        )

    return failures


# ============================================================
# 3. FOREIGN KEY VALIDATION
# ============================================================

def validate_foreign_keys(db):

    print("\n3. FOREIGN KEY VALIDATION")
    print("-" * 65)

    relationships = [

        (Product, Product.category_id,
         Category, "Product -> Category"),

        (SessionModel, SessionModel.customer_id,
         Customer, "Session -> Customer"),

        (PageView, PageView.session_id,
         SessionModel, "PageView -> Session"),

        (PageView, PageView.product_id,
         Product, "PageView -> Product"),

        (Cart, Cart.customer_id,
         Customer, "Cart -> Customer"),

        (Cart, Cart.session_id,
         SessionModel, "Cart -> Session"),

        (CartLine, CartLine.cart_id,
         Cart, "CartLine -> Cart"),

        (CartLine, CartLine.product_id,
         Product, "CartLine -> Product"),

        (Order, Order.customer_id,
         Customer, "Order -> Customer"),

        (Order, Order.session_id,
         SessionModel, "Order -> Session"),

        (OrderLine, OrderLine.order_id,
         Order, "OrderLine -> Order"),

        (OrderLine, OrderLine.product_id,
         Product, "OrderLine -> Product"),

        (ProductRelation, ProductRelation.source_product_id,
         Product, "Relation -> Source Product"),

        (ProductRelation, ProductRelation.target_product_id,
         Product, "Relation -> Target Product"),

        (Recommendation, Recommendation.customer_id,
         Customer, "Recommendation -> Customer"),

        (Recommendation, Recommendation.product_id,
         Product, "Recommendation -> Product"),
    ]

    failures = 0

    for child_model, fk_column, parent_model, description in relationships:

        invalid_count = (
            db.query(child_model.id)
            .outerjoin(
                parent_model,
                fk_column == parent_model.id
            )
            .filter(
                fk_column.isnot(None),
                parent_model.id.is_(None)
            )
            .count()
        )

        failures += print_check(
            description,
            invalid_count
        )

    return failures


# ============================================================
# 4. BUSINESS RULE VALIDATION
# ============================================================

def validate_business_rules(db):

    print("\n4. BUSINESS RULE VALIDATION")
    print("-" * 65)

    failures = 0

    # --------------------------------------------------------
    # Product rules
    # --------------------------------------------------------

    failures += print_check(
        "Product price must be positive",
        db.query(Product.id)
        .filter(Product.price <= 0)
        .count()
    )

    failures += print_check(
        "Product stock must be nonnegative",
        db.query(Product.id)
        .filter(Product.stock_quantity < 0)
        .count()
    )

    # --------------------------------------------------------
    # Page-view rules
    # --------------------------------------------------------

    failures += print_check(
        "Page-view duration between 5 and 300",
        db.query(PageView.id)
        .filter(
            (PageView.duration_seconds < 5)
            | (PageView.duration_seconds > 300)
        )
        .count()
    )

    # --------------------------------------------------------
    # Cart rules
    # --------------------------------------------------------

    failures += print_check(
        "Allowed cart statuses",
        db.query(Cart.id)
        .filter(
            Cart.status.notin_(
                ["active", "converted", "abandoned"]
            )
        )
        .count()
    )

    failures += print_check(
        "Cart-line quantity between 1 and 3",
        db.query(CartLine.id)
        .filter(
            (CartLine.quantity < 1)
            | (CartLine.quantity > 3)
        )
        .count()
    )

    failures += print_check(
        "Cart-line unit price nonnegative",
        db.query(CartLine.id)
        .filter(CartLine.unit_price < 0)
        .count()
    )

    failures += print_check(
        "Cart-line price matches product price",
        db.query(CartLine.id)
        .join(
            Product,
            CartLine.product_id == Product.id
        )
        .filter(
            CartLine.unit_price != Product.price
        )
        .count()
    )

    # --------------------------------------------------------
    # Order rules
    # --------------------------------------------------------

    allowed_order_statuses = [
        "pending",
        "paid",
        "shipped",
        "delivered",
        "cancelled",
        "refunded",
    ]

    failures += print_check(
        "Allowed order statuses",
        db.query(Order.id)
        .filter(
            Order.status.notin_(allowed_order_statuses)
        )
        .count()
    )

    failures += print_check(
        "Order monetary amounts nonnegative",
        db.query(Order.id)
        .filter(
            (Order.subtotal < 0)
            | (Order.tax < 0)
            | (Order.shipping_cost < 0)
            | (Order.total_amount < 0)
        )
        .count()
    )

    # --------------------------------------------------------
    # Order-line rules
    # --------------------------------------------------------

    failures += print_check(
        "Order-line quantity between 1 and 3",
        db.query(OrderLine.id)
        .filter(
            (OrderLine.quantity < 1)
            | (OrderLine.quantity > 3)
        )
        .count()
    )

    failures += print_check(
        "Order-line prices nonnegative",
        db.query(OrderLine.id)
        .filter(
            (OrderLine.unit_price < 0)
            | (OrderLine.line_total < 0)
        )
        .count()
    )

    failures += print_check(
        "Order-line total = unit price x quantity",
        db.query(OrderLine.id)
        .filter(
            OrderLine.line_total
            != OrderLine.unit_price * OrderLine.quantity
        )
        .count()
    )

    failures += print_check(
        "Order-line price matches product price",
        db.query(OrderLine.id)
        .join(
            Product,
            OrderLine.product_id == Product.id
        )
        .filter(
            OrderLine.unit_price != Product.price
        )
        .count()
    )

    # --------------------------------------------------------
    # Order subtotal validation
    # --------------------------------------------------------

    line_sums = (
        db.query(
            OrderLine.order_id.label("order_id"),
            func.sum(OrderLine.line_total).label("line_sum"),
        )
        .group_by(OrderLine.order_id)
        .subquery()
    )

    subtotal_query = (
        db.query(Order.id)
        .outerjoin(
            line_sums,
            Order.id == line_sums.c.order_id
        )
        .filter(
            Order.subtotal
            != func.coalesce(line_sums.c.line_sum, 0)
        )
    )

    failures += print_check(
        "Order subtotal = sum of order lines",
        subtotal_query.count()
    )

    # --------------------------------------------------------
    # Order tax validation
    # Uses the same Decimal rounding as seed_orders.py.
    # --------------------------------------------------------

    tax_records = db.query(
        Order.subtotal,
        Order.tax
    ).all()

    tax_invalid_count = 0

    for subtotal, actual_tax in tax_records:

        expected_tax = (
            Decimal(str(subtotal))
            * Decimal("0.18")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_EVEN
        )

        if Decimal(str(actual_tax)) != expected_tax:
            tax_invalid_count += 1

    failures += print_check(
        "Order tax follows 18% calculation",
        tax_invalid_count
    )

    # --------------------------------------------------------
    # Shipping validation
    # Free shipping at subtotal >= 999.
    # Otherwise shipping cost must be 40.
    # --------------------------------------------------------

    shipping_invalid = (
        (
            (Order.subtotal >= 999)
            & (Order.shipping_cost != 0)
        )
        |
        (
            (Order.subtotal < 999)
            & (Order.shipping_cost != 40)
        )
    )

    failures += print_check(
        "Order shipping follows threshold",
        db.query(Order.id)
        .filter(shipping_invalid)
        .count()
    )

    # --------------------------------------------------------
    # Order total validation
    # --------------------------------------------------------

    failures += print_check(
        "Order total = subtotal + tax + shipping",
        db.query(Order.id)
        .filter(
            Order.total_amount
            != (
                Order.subtotal
                + Order.tax
                + Order.shipping_cost
            )
        )
        .count()
    )

    # --------------------------------------------------------
    # Product relation rules
    # --------------------------------------------------------

    failures += print_check(
        "No self-referencing product relations",
        db.query(ProductRelation.id)
        .filter(
            ProductRelation.source_product_id
            == ProductRelation.target_product_id
        )
        .count()
    )

    failures += print_check(
        "Allowed product relation type",
        db.query(ProductRelation.id)
        .filter(
            ProductRelation.relation_type != "similar_to"
        )
        .count()
    )

    failures += print_check(
        "Relationship strength between 0.50 and 1.00",
        db.query(ProductRelation.id)
        .filter(
            (ProductRelation.strength < 0.50)
            | (ProductRelation.strength > 1.00)
        )
        .count()
    )

    # --------------------------------------------------------
    # Recommendation basic rules
    # --------------------------------------------------------

    failures += print_check(
        "Recommendation scores nonnegative",
        db.query(Recommendation.id)
        .filter(Recommendation.score < 0)
        .count()
    )

    failures += print_check(
        "Recommendation ranks positive",
        db.query(Recommendation.id)
        .filter(Recommendation.rank <= 0)
        .count()
    )

    return failures


# ============================================================
# 5. TIMESTAMP AND CROSS-ENTITY LIFECYCLE VALIDATION
# ============================================================

def validate_timestamps_and_lifecycle(db):

    print("\n5. TIMESTAMP AND LIFECYCLE VALIDATION")
    print("-" * 65)

    failures = 0

    # --------------------------------------------------------
    # SESSION RULES
    # Sessions must have valid start/end timestamps.
    # Duration must be between 60 and 3600 seconds.
    # --------------------------------------------------------

    session_duration = func.extract(
        "epoch",
        SessionModel.ended_at - SessionModel.started_at
    )

    invalid_sessions = db.query(SessionModel.id).filter(
        (SessionModel.started_at.is_(None))
        | (SessionModel.ended_at.is_(None))
        | (SessionModel.ended_at < SessionModel.started_at)
        | (session_duration < 60)
        | (session_duration > 3600)
    )

    failures += print_check(
        "Session duration between 60 and 3600 seconds",
        invalid_sessions.count()
    )

    # --------------------------------------------------------
    # PAGE VIEW RULES
    # Every page view must occur within its session.
    # Each session must contain 1 to 5 page views.
    # --------------------------------------------------------

    invalid_page_view_times = (
        db.query(PageView.id)
        .join(
            SessionModel,
            PageView.session_id == SessionModel.id
        )
        .filter(
            (PageView.viewed_at < SessionModel.started_at)
            | (PageView.viewed_at > SessionModel.ended_at)
        )
    )

    failures += print_check(
        "Page views occur within session timestamps",
        invalid_page_view_times.count()
    )

    page_view_counts = (
        db.query(
            PageView.session_id.label("session_id"),
            func.count(PageView.id).label("view_count")
        )
        .group_by(PageView.session_id)
        .subquery()
    )

    invalid_page_view_counts = (
        db.query(SessionModel.id)
        .outerjoin(
            page_view_counts,
            SessionModel.id == page_view_counts.c.session_id
        )
        .filter(
            (func.coalesce(page_view_counts.c.view_count, 0) < 1)
            | (func.coalesce(page_view_counts.c.view_count, 0) > 5)
        )
    )

    failures += print_check(
        "Each session has 1 to 5 page views",
        invalid_page_view_counts.count()
    )

    # --------------------------------------------------------
    # CART RULES
    # Cart customer must match its session customer.
    # Cart creation must equal session start.
    # Cart update must be within the session.
    # Each cart must have 1 to 4 lines.
    # --------------------------------------------------------

    failures += print_check(
        "Cart must have a session reference",
        db.query(Cart.id)
        .filter(Cart.session_id.is_(None))
        .count()
    )

    invalid_cart_customers = (
        db.query(Cart.id)
        .join(
            SessionModel,
            Cart.session_id == SessionModel.id
        )
        .filter(
            Cart.customer_id != SessionModel.customer_id
        )
    )

    failures += print_check(
        "Cart customer matches session customer",
        invalid_cart_customers.count()
    )

    invalid_cart_creation = (
        db.query(Cart.id)
        .join(
            SessionModel,
            Cart.session_id == SessionModel.id
        )
        .filter(
            Cart.created_at != SessionModel.started_at
        )
    )

    failures += print_check(
        "Cart creation matches session start",
        invalid_cart_creation.count()
    )

    invalid_cart_updates = (
        db.query(Cart.id)
        .join(
            SessionModel,
            Cart.session_id == SessionModel.id
        )
        .filter(
            (Cart.updated_at < SessionModel.started_at)
            | (Cart.updated_at > SessionModel.ended_at)
            | (Cart.updated_at < Cart.created_at)
        )
    )

    failures += print_check(
        "Cart update occurs within session",
        invalid_cart_updates.count()
    )

    cart_line_counts = (
        db.query(
            CartLine.cart_id.label("cart_id"),
            func.count(CartLine.id).label("line_count")
        )
        .group_by(CartLine.cart_id)
        .subquery()
    )

    invalid_cart_line_counts = (
        db.query(Cart.id)
        .outerjoin(
            cart_line_counts,
            Cart.id == cart_line_counts.c.cart_id
        )
        .filter(
            (func.coalesce(cart_line_counts.c.line_count, 0) < 1)
            | (func.coalesce(cart_line_counts.c.line_count, 0) > 4)
        )
    )

    failures += print_check(
        "Each cart has 1 to 4 product lines",
        invalid_cart_line_counts.count()
    )

    # --------------------------------------------------------
    # ORDER RULES
    # Order customer must match session customer.
    # Order timestamp must be within its session.
    # One order per session in this generated dataset.
    # --------------------------------------------------------

    failures += print_check(
        "Order must have a session reference",
        db.query(Order.id)
        .filter(Order.session_id.is_(None))
        .count()
    )

    invalid_order_customers = (
        db.query(Order.id)
        .join(
            SessionModel,
            Order.session_id == SessionModel.id
        )
        .filter(
            Order.customer_id != SessionModel.customer_id
        )
    )

    failures += print_check(
        "Order customer matches session customer",
        invalid_order_customers.count()
    )

    invalid_order_times = (
        db.query(Order.id)
        .join(
            SessionModel,
            Order.session_id == SessionModel.id
        )
        .filter(
            (Order.placed_at < SessionModel.started_at)
            | (Order.placed_at > SessionModel.ended_at)
        )
    )

    failures += print_check(
        "Order timestamp occurs within session",
        invalid_order_times.count()
    )

    duplicate_session_orders = (
        db.query(
            Order.session_id
        )
        .group_by(Order.session_id)
        .having(func.count(Order.id) > 1)
    )

    failures += print_check(
        "Only one order per session",
        duplicate_session_orders.count()
    )

    # --------------------------------------------------------
    # ORDER-LINE / PAGE-VIEW CONSISTENCY
    # Every purchased product must have been viewed in the
    # same session before or at the order timestamp.
    # --------------------------------------------------------

    matching_prior_view = (
        db.query(PageView.id)
        .filter(
            PageView.session_id == Order.session_id,
            PageView.product_id == OrderLine.product_id,
            PageView.viewed_at <= Order.placed_at
        )
        .correlate(Order, OrderLine)
        .exists()
    )

    order_lines_without_prior_view = (
        db.query(OrderLine.id)
        .join(
            Order,
            OrderLine.order_id == Order.id
        )
        .filter(~matching_prior_view)
    )

    failures += print_check(
        "Purchased products viewed before order",
        order_lines_without_prior_view.count()
    )

    # --------------------------------------------------------
    # ADVISORY CHECK
    # A page-view duration may extend beyond session end.
    # The seed script allows this, so report it without
    # treating it as a validation failure.
    # --------------------------------------------------------

    remaining_session_seconds = func.extract(
        "epoch",
        SessionModel.ended_at - PageView.viewed_at
    )

    duration_overrun_count = (
        db.query(PageView.id)
        .join(
            SessionModel,
            PageView.session_id == SessionModel.id
        )
        .filter(
            PageView.viewed_at <= SessionModel.ended_at,
            PageView.duration_seconds > remaining_session_seconds
        )
        .count()
    )

    print(
        f"{'Advisory: views extend beyond session end':<42} "
        f"Count: {duration_overrun_count:>7,} | "
        f"INFO"
    )

    return failures

# ============================================================
# 6. RECOMMENDATION DATA VALIDATION
# ============================================================

def validate_recommendations(db):

    print("\n6. RECOMMENDATION DATA VALIDATION")
    print("-" * 65)

    failures = 0

    # --------------------------------------------------------
    # Each customer must have exactly 5 recommendations.
    # --------------------------------------------------------

    recommendation_counts = (
        db.query(
            Recommendation.customer_id.label("customer_id"),
            func.count(Recommendation.id).label("rec_count")
        )
        .group_by(Recommendation.customer_id)
        .subquery()
    )

    invalid_customer_counts = (
        db.query(Customer.id)
        .outerjoin(
            recommendation_counts,
            Customer.id == recommendation_counts.c.customer_id
        )
        .filter(
            func.coalesce(recommendation_counts.c.rec_count, 0) != 5
        )
    )

    failures += print_check(
        "Exactly 5 recommendations per customer",
        invalid_customer_counts.count()
    )

    # --------------------------------------------------------
    # Each customer must have ranks 1, 2, 3, 4, 5.
    # --------------------------------------------------------

    invalid_rank_groups = (
        db.query(Recommendation.customer_id)
        .group_by(Recommendation.customer_id)
        .having(
            (func.count(Recommendation.id) != 5)
            | (func.count(func.distinct(Recommendation.rank)) != 5)
            | (func.min(Recommendation.rank) != 1)
            | (func.max(Recommendation.rank) != 5)
        )
    )

    failures += print_check(
        "Recommendation ranks are exactly 1 to 5",
        invalid_rank_groups.count()
    )

    # --------------------------------------------------------
    # No duplicate customer-product recommendations.
    # --------------------------------------------------------

    duplicate_customer_products = (
        db.query(
            Recommendation.customer_id,
            Recommendation.product_id
        )
        .group_by(
            Recommendation.customer_id,
            Recommendation.product_id
        )
        .having(func.count(Recommendation.id) > 1)
    )

    failures += print_check(
        "No duplicate customer-product recommendations",
        duplicate_customer_products.count()
    )

    # --------------------------------------------------------
    # Do not recommend products already purchased
    # by the same customer.
    # --------------------------------------------------------

    purchased_product_exists = (
        db.query(OrderLine.id)
        .join(
            Order,
            OrderLine.order_id == Order.id
        )
        .filter(
            Order.customer_id == Recommendation.customer_id,
            OrderLine.product_id == Recommendation.product_id
        )
        .correlate(Recommendation)
        .exists()
    )

    purchased_recommendations = (
        db.query(Recommendation.id)
        .filter(purchased_product_exists)
    )

    failures += print_check(
        "Previously purchased products not recommended",
        purchased_recommendations.count()
    )

    # --------------------------------------------------------
    # Recommended products must be active and in stock.
    # --------------------------------------------------------

    unavailable_recommendations = (
        db.query(Recommendation.id)
        .join(
            Product,
            Recommendation.product_id == Product.id
        )
        .filter(
            (Product.is_active.is_(False))
            | (Product.stock_quantity <= 0)
        )
    )

    failures += print_check(
        "Recommended products active and in stock",
        unavailable_recommendations.count()
    )

    # --------------------------------------------------------
    # Product relations must not contain duplicate
    # source-product, target-product and relation-type pairs.
    # --------------------------------------------------------

    duplicate_relations = (
        db.query(
            ProductRelation.source_product_id,
            ProductRelation.target_product_id,
            ProductRelation.relation_type
        )
        .group_by(
            ProductRelation.source_product_id,
            ProductRelation.target_product_id,
            ProductRelation.relation_type
        )
        .having(func.count(ProductRelation.id) > 1)
    )

    failures += print_check(
        "No duplicate product relationships",
        duplicate_relations.count()
    )

    return failures

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():

    try:

        with DBSession(engine) as db:

            print("=" * 65)
            print("YOTTAFLEX.AI - DATA QUALITY VALIDATION")
            print("=" * 65)

            total_failures = 0

            total_failures += validate_record_counts(db)

            total_failures += validate_primary_keys(db)

            total_failures += validate_foreign_keys(db)

            total_failures += validate_business_rules(db)

            total_failures += validate_timestamps_and_lifecycle(db)

            total_failures += validate_recommendations(db)
            print("\n" + "=" * 65)
            print("VALIDATION SUMMARY")
            print("=" * 65)

            if total_failures == 0:
                print("All checks passed.")
            else:
                print(
                    f"Checks requiring investigation: "
                    f"{total_failures}"
                )

            print("=" * 65)

    except Exception as error:

        print("\nVALIDATION ERROR:")
        print(error)

        raise


if __name__ == "__main__":
    main()
