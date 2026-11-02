
import csv
import json
from functools import lru_cache
from io import StringIO
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import bindparam, text

from app.config import APP_NAME
from app.database import check_database_connection, engine
from app.schemas import (
    CustomerResponse,
    ModelComparisonResponse,
    ModelEvaluation,
    ProductResponse,
    RecommendationItem,
    RecommendationResponse,
)


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description="E-commerce Recommendation Intelligence API",
    version="1.0.0",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVALUATION_DIR = PROJECT_ROOT / "reports" / "evaluation"

MODEL_FILES = {
    "baseline": EVALUATION_DIR / "evaluation_recommendations.csv",
    "personalized": EVALUATION_DIR / "personalized_recommendations.csv",
}

MODEL_NAMES = {
    "baseline": "category_affinity_train_only",
    "personalized": "personalized_category_affinity_v2",
}


# ============================================================
# LOAD RECOMMENDATION DATA
# ============================================================

@lru_cache(maxsize=2)
def load_recommendation_data(model: str) -> dict[int, list[dict]]:
    """
    Load a validated recommendation CSV into memory.
    The original CSV file is never modified.
    """

    file_path = MODEL_FILES[model]

    if not file_path.exists():
        raise FileNotFoundError(
            f"Recommendation file not found: {file_path}"
        )

    recommendations = {}

    with file_path.open(
        mode="r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            customer_id = int(row["customer_id"])

            recommendations.setdefault(customer_id, []).append({
                "product_id": int(row["product_id"]),
                "score": float(row["score"]),
                "rank": int(row["rank"]),
                "preferred_category_id": (
                    int(row["preferred_category_id"])
                    if row["preferred_category_id"]
                    else None
                ),
                "reason": row.get("reason") or None,
            })

    for customer_rows in recommendations.values():
        customer_rows.sort(key=lambda item: item["rank"])

    return recommendations


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_customer(customer_id: int):
    query = text("""
        SELECT
            id,
            first_name,
            last_name,
            email,
            city,
            country,
            is_active
        FROM customers
        WHERE id = :customer_id
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"customer_id": customer_id},
        ).mappings().first()

    return result


def get_product(product_id: int):
    query = text("""
        SELECT
            p.id,
            p.name,
            p.sku,
            p.price,
            p.stock_quantity,
            p.category_id,
            c.name AS category_name
        FROM products p
        LEFT JOIN categories c
            ON p.category_id = c.id
        WHERE p.id = :product_id
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"product_id": product_id},
        ).mappings().first()

    return result


def get_available_products(product_ids: list[int]) -> dict[int, dict]:
    """
    Return only products that are currently active and in stock.
    """

    if not product_ids:
        return {}

    query = text("""
        SELECT
            p.id,
            p.name,
            p.sku,
            p.price,
            p.stock_quantity,
            p.category_id,
            c.name AS category_name
        FROM products p
        LEFT JOIN categories c
            ON p.category_id = c.id
        WHERE
            p.id IN :product_ids
            AND p.is_active = TRUE
            AND p.stock_quantity > 0
    """).bindparams(
        bindparam("product_ids", expanding=True)
    )

    with engine.connect() as connection:
        results = connection.execute(
            query,
            {"product_ids": product_ids},
        ).mappings().all()

    return {
        row["id"]: dict(row)
        for row in results
    }


# ============================================================
# RECOMMENDATION RESPONSE BUILDER
# ============================================================

def build_recommendation_response(
    customer_id: int,
    model: Literal["baseline", "personalized"],
) -> RecommendationResponse:

    customer = get_customer(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} does not exist.",
        )

    try:
        recommendation_data = load_recommendation_data(model)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )

    customer_recommendations = recommendation_data.get(
        customer_id,
        [],
    )

    if not customer_recommendations:
        raise HTTPException(
            status_code=404,
            detail=f"No recommendations found for customer {customer_id}.",
        )

    product_ids = [
        item["product_id"]
        for item in customer_recommendations
    ]

    try:
        available_products = get_available_products(product_ids)

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve product information: {str(error)}",
        )

    response_items = []

    for item in customer_recommendations:

        product_data = available_products.get(item["product_id"])

        # Do not return unavailable or out-of-stock products.
        if product_data is None:
            continue

        product = ProductResponse(**product_data)

        response_items.append(
            RecommendationItem(
                product=product,
                score=item["score"],
                rank=item["rank"],
                preferred_category_id=item["preferred_category_id"],
                reason=item["reason"],
            )
        )

    return RecommendationResponse(
        customer_id=customer_id,
        model=model,
        model_name=MODEL_NAMES[model],
        recommendation_count=len(response_items),
        recommendations=response_items,
    )


# ============================================================
# HOME ENDPOINT
# ============================================================

@app.get("/")
def home():
    return {
        "message": "Welcome to YottaFlex Recommendation System",
        "status": "running",
    }


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get("/health")
def health_check():

    try:
        db_status = check_database_connection()

        return {
            "application": "healthy",
            "database": "connected" if db_status else "disconnected",
        }

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(error)}",
        )


# ============================================================
# CUSTOMER ENDPOINT
# ============================================================

@app.get(
    "/customers/{customer_id}",
    response_model=CustomerResponse,
)
def customer_details(customer_id: int):

    try:
        customer = get_customer(customer_id)

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve customer: {str(error)}",
        )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found.",
        )

    return dict(customer)


# ============================================================
# PRODUCT ENDPOINT
# ============================================================

@app.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def product_details(product_id: int):

    try:
        product = get_product(product_id)

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve product: {str(error)}",
        )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail=f"Product {product_id} not found.",
        )

    return dict(product)


# ============================================================
# RECOMMENDATION ENDPOINT
# ============================================================

@app.get(
    "/recommendations/{customer_id}",
    response_model=RecommendationResponse,
)
def customer_recommendations(
    customer_id: int,
    model: Literal["baseline", "personalized"] = Query(
        default="baseline",
        description="Choose baseline or personalized recommendation model.",
    ),
):

    try:
        return build_recommendation_response(
            customer_id=customer_id,
            model=model,
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Recommendation service error: {str(error)}",
        )


# ============================================================
# MODEL EVALUATION ENDPOINT
# ============================================================

def load_model_evaluation(
    file_path: Path,
) -> ModelEvaluation:

    with file_path.open(
        mode="r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    return ModelEvaluation(
        model_name=data["recommendation_model"],
        precision_at_5=data["ranking_metrics"]["precision_at_5"],
        recall_at_5=data["ranking_metrics"]["recall_at_5"],
        ndcg_at_5=data["ranking_metrics"]["ndcg_at_5"],
        catalog_coverage=data["catalog_metrics"]["catalog_coverage"],
        availability_violations=data["availability_metrics"][
            "availability_violations"
        ],
        availability_violation_rate=data["availability_metrics"][
            "availability_violation_rate"
        ],
        evaluated_customers=data["ranking_metrics"]["evaluated_customers"],
        recommendation_rows=data["dataset_counts"]["recommendation_rows"],
    )


@app.get(
    "/evaluation/models",
    response_model=ModelComparisonResponse,
)
def compare_model_evaluations():

    baseline_file = EVALUATION_DIR / "evaluation_results.json"
    personalized_file = (
        EVALUATION_DIR / "personalized_evaluation_results.json"
    )

    try:
        baseline = load_model_evaluation(baseline_file)
        personalized = load_model_evaluation(personalized_file)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Evaluation result file not found: {str(error)}",
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load evaluation results: {str(error)}",
        )

    return ModelComparisonResponse(
        cutoff="2026-07-01T00:00:00+05:30",
        baseline=baseline,
        personalized=personalized,
    )


# ============================================================
# RECOMMENDATION EXPORT ENDPOINT
# ============================================================

@app.get("/recommendations/{customer_id}/export")
def export_customer_recommendations(
    customer_id: int,
    model: Literal["baseline", "personalized"] = "baseline",
    format: Literal["json", "csv"] = "json",
):

    try:
        result = build_recommendation_response(
            customer_id=customer_id,
            model=model,
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Export failed: {str(error)}",
        )

    if format == "json":
        return result

    output = StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "customer_id",
        "model",
        "model_name",
        "product_id",
        "product_name",
        "sku",
        "price",
        "stock_quantity",
        "category_id",
        "category_name",
        "score",
        "rank",
        "preferred_category_id",
        "reason",
    ])

    for item in result.recommendations:

        writer.writerow([
            result.customer_id,
            result.model,
            result.model_name,
            item.product.id,
            item.product.name,
            item.product.sku,
            item.product.price,
            item.product.stock_quantity,
            item.product.category_id,
            item.product.category_name,
            item.score,
            item.rank,
            item.preferred_category_id,
            item.reason,
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename=customer_{customer_id}_"
                f"{model}_recommendations.csv"
            )
        },
    )
