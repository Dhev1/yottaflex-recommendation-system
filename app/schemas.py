
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# RECOMMENDATION MODEL OPTIONS
# ============================================================

RecommendationModel = Literal["baseline", "personalized"]


# ============================================================
# PRODUCT RESPONSE
# ============================================================

class ProductResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    price: Decimal
    stock_quantity: int
    category_id: int | None = None
    category_name: str | None = None


# ============================================================
# CUSTOMER RESPONSE
# ============================================================

class CustomerResponse(BaseModel):

    id: int
    first_name: str
    last_name: str
    email: str
    city: str | None = None
    country: str | None = None
    is_active: bool


# ============================================================
# INDIVIDUAL RECOMMENDATION
# ============================================================

class RecommendationItem(BaseModel):

    product: ProductResponse

    score: float = Field(ge=0)
    rank: int = Field(ge=1)

    preferred_category_id: int | None = None
    reason: str | None = None


# ============================================================
# COMPLETE RECOMMENDATION RESPONSE
# ============================================================

class RecommendationResponse(BaseModel):

    customer_id: int

    model: RecommendationModel

    model_name: str

    recommendation_count: int

    recommendations: list[RecommendationItem]


# ============================================================
# MODEL EVALUATION RESPONSE
# ============================================================

class ModelEvaluation(BaseModel):

    model_name: str

    precision_at_5: float
    recall_at_5: float
    ndcg_at_5: float

    catalog_coverage: float

    availability_violations: int
    availability_violation_rate: float

    evaluated_customers: int
    recommendation_rows: int


class ModelComparisonResponse(BaseModel):

    cutoff: str

    baseline: ModelEvaluation
    personalized: ModelEvaluation
