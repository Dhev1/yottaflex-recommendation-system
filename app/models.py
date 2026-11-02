
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    Numeric,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    func
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)


# ============================================================
# BASE CLASS
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# 1. CUSTOMER MODEL
# ============================================================

class Customer(Base):

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    first_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )

    city: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    country: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="customer"
    )

    carts: Mapped[list["Cart"]] = relationship(
        back_populates="customer"
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer"
    )

    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="customer"
    )

    def __repr__(self):
        return f"<Customer(id={self.id}, email='{self.email}')>"


# ============================================================
# 2. CATEGORY MODEL
# ============================================================

class Category(Base):

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # One category can contain multiple products
    products: Mapped[list["Product"]] = relationship(
        back_populates="category"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


# ============================================================
# 3. PRODUCT MODEL
# ============================================================

class Product(Base):

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    sku: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    stock_quantity: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    category_id: Mapped[int | None] = mapped_column(
    Integer,
    ForeignKey("categories.id"),
    nullable=True
)

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Category relationship
    category: Mapped["Category | None"] = relationship(
    back_populates="products"
)

    # Other product relationships
    page_views: Mapped[list["PageView"]] = relationship(
        back_populates="product"
    )

    cart_lines: Mapped[list["CartLine"]] = relationship(
        back_populates="product"
    )

    order_lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="product"
    )

    source_relations: Mapped[list["ProductRelation"]] = relationship(
        foreign_keys="ProductRelation.source_product_id",
        back_populates="source_product"
    )

    target_relations: Mapped[list["ProductRelation"]] = relationship(
        foreign_keys="ProductRelation.target_product_id",
        back_populates="target_product"
    )

    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="product"
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"


# ============================================================
# 4. SESSION MODEL
# ============================================================

class Session(Base):

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    device_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    source: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        back_populates="sessions"
    )

    page_views: Mapped[list["PageView"]] = relationship(
        back_populates="session"
    )

    carts: Mapped[list["Cart"]] = relationship(
        back_populates="session"
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="session"
    )

    def __repr__(self):
        return f"<Session(id={self.id}, customer_id={self.customer_id})>"


# ============================================================
# 5. PAGEVIEW MODEL
# ============================================================

class PageView(Base):

    __tablename__ = "page_views"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sessions.id"),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    page_type: Mapped[str] = mapped_column(
        String(50), default="product", nullable=False
    )

    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "duration_seconds >= 0",
            name="ck_page_views_duration_nonnegative"
        ),
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        back_populates="page_views"
    )

    product: Mapped["Product"] = relationship(
        back_populates="page_views"
    )

    def __repr__(self):
        return f"<PageView(id={self.id}, product_id={self.product_id})>"


# ============================================================
# 6. CART MODEL
# ============================================================

class Cart(Base):

    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    session_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sessions.id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30), default="active", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'converted', 'abandoned')",
            name="ck_carts_status"
        ),
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        back_populates="carts"
    )

    session: Mapped["Session | None"] = relationship(
        back_populates="carts"
    )

    lines: Mapped[list["CartLine"]] = relationship(
        back_populates="cart"
    )

    def __repr__(self):
        return f"<Cart(id={self.id}, status='{self.status}')>"


# ============================================================
# 7. CARTLINE MODEL
# ============================================================

class CartLine(Base):

    __tablename__ = "cart_lines"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    cart_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("carts.id"),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "cart_id", "product_id",
            name="uq_cart_lines_cart_product"
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_cart_lines_quantity_positive"
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_cart_lines_price_nonnegative"
        ),
    )

    # Relationships
    cart: Mapped["Cart"] = relationship(
        back_populates="lines"
    )

    product: Mapped["Product"] = relationship(
        back_populates="cart_lines"
    )

    def __repr__(self):
        return f"<CartLine(id={self.id}, quantity={self.quantity})>"


# ============================================================
# 8. ORDER MODEL
# ============================================================

class Order(Base):

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    session_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sessions.id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    shipping_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="INR", nullable=False
    )

    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'paid', 'shipped', "
            "'delivered', 'cancelled', 'refunded')",
            name="ck_orders_status"
        ),
        CheckConstraint(
            "subtotal >= 0 AND tax >= 0 "
            "AND shipping_cost >= 0 AND total_amount >= 0",
            name="ck_orders_amounts_nonnegative"
        ),
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        back_populates="orders"
    )

    session: Mapped["Session | None"] = relationship(
        back_populates="orders"
    )

    lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="order"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, status='{self.status}')>"


# ============================================================
# 9. ORDERLINE MODEL
# ============================================================

class OrderLine(Base):

    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    line_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "order_id", "product_id",
            name="uq_order_lines_order_product"
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_order_lines_quantity_positive"
        ),
        CheckConstraint(
            "unit_price >= 0 AND line_total >= 0",
            name="ck_order_lines_amounts_nonnegative"
        ),
    )

    # Relationships
    order: Mapped["Order"] = relationship(
        back_populates="lines"
    )

    product: Mapped["Product"] = relationship(
        back_populates="order_lines"
    )

    def __repr__(self):
        return f"<OrderLine(id={self.id}, order_id={self.order_id})>"


# ============================================================
# 10. PRODUCTRELATION MODEL
# ============================================================

class ProductRelation(Base):

    __tablename__ = "product_relations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    source_product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    target_product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    strength: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), default=Decimal("1.0000"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "source_product_id",
            "target_product_id",
            "relation_type",
            name="uq_product_relations_pair_type"
        ),
        CheckConstraint(
            "source_product_id != target_product_id",
            name="ck_product_relations_not_self"
        ),
        CheckConstraint(
            "strength >= 0 AND strength <= 1",
            name="ck_product_relations_strength"
        ),
    )

    # Two relationships with the Product table
    source_product: Mapped["Product"] = relationship(
        foreign_keys=[source_product_id],
        back_populates="source_relations"
    )

    target_product: Mapped["Product"] = relationship(
        foreign_keys=[target_product_id],
        back_populates="target_relations"
    )

    def __repr__(self):
        return f"<ProductRelation(id={self.id}, type='{self.relation_type}')>"


# ============================================================
# 11. RECOMMENDATION MODEL
# ============================================================

class Recommendation(Base):

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    score: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), nullable=False
    )

    rank: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "score >= 0",
            name="ck_recommendations_score_nonnegative"
        ),
        CheckConstraint(
            "rank > 0",
            name="ck_recommendations_rank_positive"
        ),
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        back_populates="recommendations"
    )

    product: Mapped["Product"] = relationship(
        back_populates="recommendations"
    )

    def __repr__(self):
        return f"<Recommendation(id={self.id}, rank={self.rank})>"
