# YottaFlex.ai - Data Dictionary

This document describes the database tables and columns using the SQLAlchemy model definitions.

## customers

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| first_name | VARCHAR(100) | No | No | - |
| last_name | VARCHAR(100) | No | No | - |
| email | VARCHAR(255) | No | No | - |
| city | VARCHAR(100) | Yes | No | - |
| country | VARCHAR(100) | Yes | No | - |
| is_active | BOOLEAN | No | No | - |
| created_at | DATETIME | No | No | - |

### Constraints

- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<customers>, primary_key=True, nullable=False))`
- **UniqueConstraint** (Unnamed): `UniqueConstraint(Column('email', String(length=255), table=<customers>, nullable=False))`

## categories

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| name | VARCHAR(100) | No | No | - |
| description | TEXT | Yes | No | - |
| is_active | BOOLEAN | No | No | - |
| created_at | DATETIME | No | No | - |

### Constraints

- **UniqueConstraint** (Unnamed): `UniqueConstraint(Column('name', String(length=100), table=<categories>, nullable=False))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<categories>, primary_key=True, nullable=False))`

## products

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| name | VARCHAR(200) | No | No | - |
| description | TEXT | Yes | No | - |
| sku | VARCHAR(100) | No | No | - |
| price | NUMERIC(10, 2) | No | No | - |
| stock_quantity | INTEGER | No | No | - |
| category_id | INTEGER | Yes | No | categories.id |
| is_active | BOOLEAN | No | No | - |
| created_at | DATETIME | No | No | - |

### Constraints

- **UniqueConstraint** (Unnamed): `UniqueConstraint(Column('sku', String(length=100), table=<products>, nullable=False))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x0000014474870310>, None, table=Table('products', MetaData(), Column('id', Integer(), table=<products>, primary_key=True, nullable=False), Column('name', String(length=200), table=<products>, nullable=False), Column('description', Text(), table=<products>), Column('sku', String(length=100), table=<products>, nullable=False), Column('price', Numeric(precision=10, scale=2), table=<products>, nullable=False), Column('stock_quantity', Integer(), table=<products>, nullable=False, default=ScalarElementColumnDefault(0)), Column('category_id', Integer(), ForeignKey('categories.id'), table=<products>), Column('is_active', Boolean(), table=<products>, nullable=False, default=ScalarElementColumnDefault(True)), Column('created_at', DateTime(timezone=True), table=<products>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447465f9d0; now>, for_update=False)), schema=None))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<products>, primary_key=True, nullable=False))`

## sessions

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| customer_id | INTEGER | No | No | customers.id |
| device_type | VARCHAR(50) | Yes | No | - |
| source | VARCHAR(100) | Yes | No | - |
| started_at | DATETIME | No | No | - |
| ended_at | DATETIME | Yes | No | - |

### Constraints

- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144749E73D0>, None, table=Table('sessions', MetaData(), Column('id', Integer(), table=<sessions>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<sessions>, nullable=False), Column('device_type', String(length=50), table=<sessions>), Column('source', String(length=100), table=<sessions>), Column('started_at', DateTime(timezone=True), table=<sessions>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447475c9d0; now>, for_update=False)), Column('ended_at', DateTime(timezone=True), table=<sessions>), schema=None))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<sessions>, primary_key=True, nullable=False))`

## page_views

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| session_id | INTEGER | No | No | sessions.id |
| product_id | INTEGER | No | No | products.id |
| page_type | VARCHAR(50) | No | No | - |
| viewed_at | DATETIME | No | No | - |
| duration_seconds | INTEGER | No | No | - |

### Constraints

- **CheckConstraint** (ck_page_views_duration_nonnegative): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x0000014474770A50>, name='ck_page_views_duration_nonnegative', table=Table('page_views', MetaData(), Column('id', Integer(), table=<page_views>, primary_key=True, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<page_views>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<page_views>, nullable=False), Column('page_type', String(length=50), table=<page_views>, nullable=False, default=ScalarElementColumnDefault('product')), Column('viewed_at', DateTime(timezone=True), table=<page_views>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447475d940; now>, for_update=False)), Column('duration_seconds', Integer(), table=<page_views>, nullable=False, default=ScalarElementColumnDefault(0)), schema=None))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<page_views>, primary_key=True, nullable=False))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144748DB470>, None, table=Table('page_views', MetaData(), Column('id', Integer(), table=<page_views>, primary_key=True, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<page_views>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<page_views>, nullable=False), Column('page_type', String(length=50), table=<page_views>, nullable=False, default=ScalarElementColumnDefault('product')), Column('viewed_at', DateTime(timezone=True), table=<page_views>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447475d940; now>, for_update=False)), Column('duration_seconds', Integer(), table=<page_views>, nullable=False, default=ScalarElementColumnDefault(0)), schema=None))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144748D90D0>, None, table=Table('page_views', MetaData(), Column('id', Integer(), table=<page_views>, primary_key=True, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<page_views>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<page_views>, nullable=False), Column('page_type', String(length=50), table=<page_views>, nullable=False, default=ScalarElementColumnDefault('product')), Column('viewed_at', DateTime(timezone=True), table=<page_views>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447475d940; now>, for_update=False)), Column('duration_seconds', Integer(), table=<page_views>, nullable=False, default=ScalarElementColumnDefault(0)), schema=None))`

## carts

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| customer_id | INTEGER | No | No | customers.id |
| session_id | INTEGER | Yes | No | sessions.id |
| status | VARCHAR(30) | No | No | - |
| created_at | DATETIME | No | No | - |
| updated_at | DATETIME | No | No | - |

### Constraints

- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144781BECA0>, None, table=Table('carts', MetaData(), Column('id', Integer(), table=<carts>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<carts>, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<carts>), Column('status', String(length=30), table=<carts>, nullable=False, default=ScalarElementColumnDefault('active')), Column('created_at', DateTime(timezone=True), table=<carts>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x144746aa690; now>, for_update=False)), Column('updated_at', DateTime(timezone=True), table=<carts>, nullable=False, onupdate=ColumnElementColumnDefault(<sqlalchemy.sql.functions.now at 0x1447469f8a0; now>), server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447469f570; now>, for_update=False)), schema=None))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<carts>, primary_key=True, nullable=False))`
- **CheckConstraint** (ck_carts_status): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x000001447475EC40>, name='ck_carts_status', table=Table('carts', MetaData(), Column('id', Integer(), table=<carts>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<carts>, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<carts>), Column('status', String(length=30), table=<carts>, nullable=False, default=ScalarElementColumnDefault('active')), Column('created_at', DateTime(timezone=True), table=<carts>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x144746aa690; now>, for_update=False)), Column('updated_at', DateTime(timezone=True), table=<carts>, nullable=False, onupdate=ColumnElementColumnDefault(<sqlalchemy.sql.functions.now at 0x1447469f8a0; now>), server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447469f570; now>, for_update=False)), schema=None))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x0000014474857BA0>, None, table=Table('carts', MetaData(), Column('id', Integer(), table=<carts>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<carts>, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<carts>), Column('status', String(length=30), table=<carts>, nullable=False, default=ScalarElementColumnDefault('active')), Column('created_at', DateTime(timezone=True), table=<carts>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x144746aa690; now>, for_update=False)), Column('updated_at', DateTime(timezone=True), table=<carts>, nullable=False, onupdate=ColumnElementColumnDefault(<sqlalchemy.sql.functions.now at 0x1447469f8a0; now>), server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447469f570; now>, for_update=False)), schema=None))`

## cart_lines

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| cart_id | INTEGER | No | No | carts.id |
| product_id | INTEGER | No | No | products.id |
| quantity | INTEGER | No | No | - |
| unit_price | NUMERIC(10, 2) | No | No | - |

### Constraints

- **CheckConstraint** (ck_cart_lines_quantity_positive): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x00000144746AB650>, name='ck_cart_lines_quantity_positive', table=Table('cart_lines', MetaData(), Column('id', Integer(), table=<cart_lines>, primary_key=True, nullable=False), Column('cart_id', Integer(), ForeignKey('carts.id'), table=<cart_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<cart_lines>, nullable=False), Column('quantity', Integer(), table=<cart_lines>, nullable=False, default=ScalarElementColumnDefault(1)), Column('unit_price', Numeric(precision=10, scale=2), table=<cart_lines>, nullable=False), schema=None))`
- **UniqueConstraint** (uq_cart_lines_cart_product): `UniqueConstraint(Column('cart_id', Integer(), ForeignKey('carts.id'), table=<cart_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<cart_lines>, nullable=False))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<cart_lines>, primary_key=True, nullable=False))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x0000014474B1BB50>, None, table=Table('cart_lines', MetaData(), Column('id', Integer(), table=<cart_lines>, primary_key=True, nullable=False), Column('cart_id', Integer(), ForeignKey('carts.id'), table=<cart_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<cart_lines>, nullable=False), Column('quantity', Integer(), table=<cart_lines>, nullable=False, default=ScalarElementColumnDefault(1)), Column('unit_price', Numeric(precision=10, scale=2), table=<cart_lines>, nullable=False), schema=None))`
- **CheckConstraint** (ck_cart_lines_price_nonnegative): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x000001447478C5A0>, name='ck_cart_lines_price_nonnegative', table=Table('cart_lines', MetaData(), Column('id', Integer(), table=<cart_lines>, primary_key=True, nullable=False), Column('cart_id', Integer(), ForeignKey('carts.id'), table=<cart_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<cart_lines>, nullable=False), Column('quantity', Integer(), table=<cart_lines>, nullable=False, default=ScalarElementColumnDefault(1)), Column('unit_price', Numeric(precision=10, scale=2), table=<cart_lines>, nullable=False), schema=None))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x0000014474821A30>, None, table=Table('cart_lines', MetaData(), Column('id', Integer(), table=<cart_lines>, primary_key=True, nullable=False), Column('cart_id', Integer(), ForeignKey('carts.id'), table=<cart_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<cart_lines>, nullable=False), Column('quantity', Integer(), table=<cart_lines>, nullable=False, default=ScalarElementColumnDefault(1)), Column('unit_price', Numeric(precision=10, scale=2), table=<cart_lines>, nullable=False), schema=None))`

## orders

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| customer_id | INTEGER | No | No | customers.id |
| session_id | INTEGER | Yes | No | sessions.id |
| status | VARCHAR(30) | No | No | - |
| subtotal | NUMERIC(12, 2) | No | No | - |
| tax | NUMERIC(12, 2) | No | No | - |
| shipping_cost | NUMERIC(12, 2) | No | No | - |
| total_amount | NUMERIC(12, 2) | No | No | - |
| currency | VARCHAR(3) | No | No | - |
| placed_at | DATETIME | No | No | - |

### Constraints

- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144781BEF70>, None, table=Table('orders', MetaData(), Column('id', Integer(), table=<orders>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<orders>, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<orders>), Column('status', String(length=30), table=<orders>, nullable=False, default=ScalarElementColumnDefault('pending')), Column('subtotal', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('tax', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('shipping_cost', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('total_amount', Numeric(precision=12, scale=2), table=<orders>, nullable=False), Column('currency', String(length=3), table=<orders>, nullable=False, default=ScalarElementColumnDefault('INR')), Column('placed_at', DateTime(timezone=True), table=<orders>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447479c550; now>, for_update=False)), schema=None))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<orders>, primary_key=True, nullable=False))`
- **CheckConstraint** (ck_orders_amounts_nonnegative): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x00000144747635C0>, name='ck_orders_amounts_nonnegative', table=Table('orders', MetaData(), Column('id', Integer(), table=<orders>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<orders>, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<orders>), Column('status', String(length=30), table=<orders>, nullable=False, default=ScalarElementColumnDefault('pending')), Column('subtotal', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('tax', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('shipping_cost', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('total_amount', Numeric(precision=12, scale=2), table=<orders>, nullable=False), Column('currency', String(length=3), table=<orders>, nullable=False, default=ScalarElementColumnDefault('INR')), Column('placed_at', DateTime(timezone=True), table=<orders>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447479c550; now>, for_update=False)), schema=None))`
- **CheckConstraint** (ck_orders_status): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x000001447479C950>, name='ck_orders_status', table=Table('orders', MetaData(), Column('id', Integer(), table=<orders>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<orders>, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<orders>), Column('status', String(length=30), table=<orders>, nullable=False, default=ScalarElementColumnDefault('pending')), Column('subtotal', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('tax', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('shipping_cost', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('total_amount', Numeric(precision=12, scale=2), table=<orders>, nullable=False), Column('currency', String(length=3), table=<orders>, nullable=False, default=ScalarElementColumnDefault('INR')), Column('placed_at', DateTime(timezone=True), table=<orders>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447479c550; now>, for_update=False)), schema=None))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144748B8F90>, None, table=Table('orders', MetaData(), Column('id', Integer(), table=<orders>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<orders>, nullable=False), Column('session_id', Integer(), ForeignKey('sessions.id'), table=<orders>), Column('status', String(length=30), table=<orders>, nullable=False, default=ScalarElementColumnDefault('pending')), Column('subtotal', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('tax', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('shipping_cost', Numeric(precision=12, scale=2), table=<orders>, nullable=False, default=ScalarElementColumnDefault(Decimal('0.00'))), Column('total_amount', Numeric(precision=12, scale=2), table=<orders>, nullable=False), Column('currency', String(length=3), table=<orders>, nullable=False, default=ScalarElementColumnDefault('INR')), Column('placed_at', DateTime(timezone=True), table=<orders>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447479c550; now>, for_update=False)), schema=None))`

## order_lines

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| order_id | INTEGER | No | No | orders.id |
| product_id | INTEGER | No | No | products.id |
| quantity | INTEGER | No | No | - |
| unit_price | NUMERIC(10, 2) | No | No | - |
| line_total | NUMERIC(12, 2) | No | No | - |

### Constraints

- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144748DB6A0>, None, table=Table('order_lines', MetaData(), Column('id', Integer(), table=<order_lines>, primary_key=True, nullable=False), Column('order_id', Integer(), ForeignKey('orders.id'), table=<order_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<order_lines>, nullable=False), Column('quantity', Integer(), table=<order_lines>, nullable=False), Column('unit_price', Numeric(precision=10, scale=2), table=<order_lines>, nullable=False), Column('line_total', Numeric(precision=12, scale=2), table=<order_lines>, nullable=False), schema=None))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<order_lines>, primary_key=True, nullable=False))`
- **CheckConstraint** (ck_order_lines_amounts_nonnegative): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x000001447454BDD0>, name='ck_order_lines_amounts_nonnegative', table=Table('order_lines', MetaData(), Column('id', Integer(), table=<order_lines>, primary_key=True, nullable=False), Column('order_id', Integer(), ForeignKey('orders.id'), table=<order_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<order_lines>, nullable=False), Column('quantity', Integer(), table=<order_lines>, nullable=False), Column('unit_price', Numeric(precision=10, scale=2), table=<order_lines>, nullable=False), Column('line_total', Numeric(precision=12, scale=2), table=<order_lines>, nullable=False), schema=None))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x000001447498E390>, None, table=Table('order_lines', MetaData(), Column('id', Integer(), table=<order_lines>, primary_key=True, nullable=False), Column('order_id', Integer(), ForeignKey('orders.id'), table=<order_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<order_lines>, nullable=False), Column('quantity', Integer(), table=<order_lines>, nullable=False), Column('unit_price', Numeric(precision=10, scale=2), table=<order_lines>, nullable=False), Column('line_total', Numeric(precision=12, scale=2), table=<order_lines>, nullable=False), schema=None))`
- **UniqueConstraint** (uq_order_lines_order_product): `UniqueConstraint(Column('order_id', Integer(), ForeignKey('orders.id'), table=<order_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<order_lines>, nullable=False))`
- **CheckConstraint** (ck_order_lines_quantity_positive): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x00000144747B1D30>, name='ck_order_lines_quantity_positive', table=Table('order_lines', MetaData(), Column('id', Integer(), table=<order_lines>, primary_key=True, nullable=False), Column('order_id', Integer(), ForeignKey('orders.id'), table=<order_lines>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<order_lines>, nullable=False), Column('quantity', Integer(), table=<order_lines>, nullable=False), Column('unit_price', Numeric(precision=10, scale=2), table=<order_lines>, nullable=False), Column('line_total', Numeric(precision=12, scale=2), table=<order_lines>, nullable=False), schema=None))`

## product_relations

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| source_product_id | INTEGER | No | No | products.id |
| target_product_id | INTEGER | No | No | products.id |
| relation_type | VARCHAR(50) | No | No | - |
| strength | NUMERIC(6, 4) | No | No | - |
| created_at | DATETIME | No | No | - |

### Constraints

- **UniqueConstraint** (uq_product_relations_pair_type): `UniqueConstraint(Column('source_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('target_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('relation_type', String(length=50), table=<product_relations>, nullable=False))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<product_relations>, primary_key=True, nullable=False))`
- **CheckConstraint** (ck_product_relations_strength): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x00000144747B9D10>, name='ck_product_relations_strength', table=Table('product_relations', MetaData(), Column('id', Integer(), table=<product_relations>, primary_key=True, nullable=False), Column('source_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('target_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('relation_type', String(length=50), table=<product_relations>, nullable=False), Column('strength', Numeric(precision=6, scale=4), table=<product_relations>, nullable=False, default=ScalarElementColumnDefault(Decimal('1.0000'))), Column('created_at', DateTime(timezone=True), table=<product_relations>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447479ca50; now>, for_update=False)), schema=None))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144748DBD30>, None, table=Table('product_relations', MetaData(), Column('id', Integer(), table=<product_relations>, primary_key=True, nullable=False), Column('source_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('target_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('relation_type', String(length=50), table=<product_relations>, nullable=False), Column('strength', Numeric(precision=6, scale=4), table=<product_relations>, nullable=False, default=ScalarElementColumnDefault(Decimal('1.0000'))), Column('created_at', DateTime(timezone=True), table=<product_relations>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447479ca50; now>, for_update=False)), schema=None))`
- **CheckConstraint** (ck_product_relations_not_self): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x00000144747AC3C0>, name='ck_product_relations_not_self', table=Table('product_relations', MetaData(), Column('id', Integer(), table=<product_relations>, primary_key=True, nullable=False), Column('source_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('target_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('relation_type', String(length=50), table=<product_relations>, nullable=False), Column('strength', Numeric(precision=6, scale=4), table=<product_relations>, nullable=False, default=ScalarElementColumnDefault(Decimal('1.0000'))), Column('created_at', DateTime(timezone=True), table=<product_relations>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447479ca50; now>, for_update=False)), schema=None))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144748727F0>, None, table=Table('product_relations', MetaData(), Column('id', Integer(), table=<product_relations>, primary_key=True, nullable=False), Column('source_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('target_product_id', Integer(), ForeignKey('products.id'), table=<product_relations>, nullable=False), Column('relation_type', String(length=50), table=<product_relations>, nullable=False), Column('strength', Numeric(precision=6, scale=4), table=<product_relations>, nullable=False, default=ScalarElementColumnDefault(Decimal('1.0000'))), Column('created_at', DateTime(timezone=True), table=<product_relations>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x1447479ca50; now>, for_update=False)), schema=None))`

## recommendations

| Column | Data Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | INTEGER | No | Yes | - |
| customer_id | INTEGER | No | No | customers.id |
| product_id | INTEGER | No | No | products.id |
| model_name | VARCHAR(100) | No | No | - |
| score | NUMERIC(10, 6) | No | No | - |
| rank | INTEGER | No | No | - |
| reason | TEXT | Yes | No | - |
| generated_at | DATETIME | No | No | - |

### Constraints

- **CheckConstraint** (ck_recommendations_score_nonnegative): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x00000144747CCCB0>, name='ck_recommendations_score_nonnegative', table=Table('recommendations', MetaData(), Column('id', Integer(), table=<recommendations>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<recommendations>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<recommendations>, nullable=False), Column('model_name', String(length=100), table=<recommendations>, nullable=False), Column('score', Numeric(precision=10, scale=6), table=<recommendations>, nullable=False), Column('rank', Integer(), table=<recommendations>, nullable=False), Column('reason', Text(), table=<recommendations>), Column('generated_at', DateTime(timezone=True), table=<recommendations>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x144747c08c0; now>, for_update=False)), schema=None))`
- **PrimaryKeyConstraint** (Unnamed): `PrimaryKeyConstraint(Column('id', Integer(), table=<recommendations>, primary_key=True, nullable=False))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144781BDFD0>, None, table=Table('recommendations', MetaData(), Column('id', Integer(), table=<recommendations>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<recommendations>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<recommendations>, nullable=False), Column('model_name', String(length=100), table=<recommendations>, nullable=False), Column('score', Numeric(precision=10, scale=6), table=<recommendations>, nullable=False), Column('rank', Integer(), table=<recommendations>, nullable=False), Column('reason', Text(), table=<recommendations>), Column('generated_at', DateTime(timezone=True), table=<recommendations>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x144747c08c0; now>, for_update=False)), schema=None))`
- **CheckConstraint** (ck_recommendations_rank_positive): `CheckConstraint(<sqlalchemy.sql.elements.TextClause object at 0x0000014474727B50>, name='ck_recommendations_rank_positive', table=Table('recommendations', MetaData(), Column('id', Integer(), table=<recommendations>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<recommendations>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<recommendations>, nullable=False), Column('model_name', String(length=100), table=<recommendations>, nullable=False), Column('score', Numeric(precision=10, scale=6), table=<recommendations>, nullable=False), Column('rank', Integer(), table=<recommendations>, nullable=False), Column('reason', Text(), table=<recommendations>), Column('generated_at', DateTime(timezone=True), table=<recommendations>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x144747c08c0; now>, for_update=False)), schema=None))`
- **ForeignKeyConstraint** (Unnamed): `ForeignKeyConstraint(<sqlalchemy.sql.base.ReadOnlyColumnCollection object at 0x00000144781BF1A0>, None, table=Table('recommendations', MetaData(), Column('id', Integer(), table=<recommendations>, primary_key=True, nullable=False), Column('customer_id', Integer(), ForeignKey('customers.id'), table=<recommendations>, nullable=False), Column('product_id', Integer(), ForeignKey('products.id'), table=<recommendations>, nullable=False), Column('model_name', String(length=100), table=<recommendations>, nullable=False), Column('score', Numeric(precision=10, scale=6), table=<recommendations>, nullable=False), Column('rank', Integer(), table=<recommendations>, nullable=False), Column('reason', Text(), table=<recommendations>), Column('generated_at', DateTime(timezone=True), table=<recommendations>, nullable=False, server_default=DefaultClause(<sqlalchemy.sql.functions.now at 0x144747c08c0; now>, for_update=False)), schema=None))`

