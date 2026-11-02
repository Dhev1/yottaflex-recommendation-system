
import csv
from io import StringIO

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ============================================================
# HOME AND HEALTH TESTS
# ============================================================

def test_home_endpoint():

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_endpoint():

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


# ============================================================
# CUSTOMER AND PRODUCT TESTS
# ============================================================

def test_get_existing_customer():

    response = client.get("/customers/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_nonexistent_customer():

    response = client.get("/customers/999999")

    assert response.status_code == 404


def test_get_existing_product():

    response = client.get("/products/812")

    assert response.status_code == 200
    assert response.json()["id"] == 812


# ============================================================
# RECOMMENDATION TESTS
# ============================================================

def test_baseline_recommendations():

    response = client.get(
        "/recommendations/1",
        params={"model": "baseline"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == 1
    assert data["model"] == "baseline"
    assert data["model_name"] == "category_affinity_train_only"
    assert data["recommendation_count"] == 5
    assert len(data["recommendations"]) == 5


def test_personalized_recommendations():

    response = client.get(
        "/recommendations/1",
        params={"model": "personalized"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == 1
    assert data["model"] == "personalized"
    assert data["model_name"] == "personalized_category_affinity_v2"
    assert data["recommendation_count"] == 5
    assert len(data["recommendations"]) == 5


def test_recommendations_for_nonexistent_customer():

    response = client.get("/recommendations/999999")

    assert response.status_code == 404


# ============================================================
# EVALUATION TEST
# ============================================================

def test_model_evaluation():

    response = client.get("/evaluation/models")

    assert response.status_code == 200

    data = response.json()

    assert data["baseline"]["model_name"] == "category_affinity_train_only"
    assert data["personalized"]["model_name"] == "personalized_category_affinity_v2"

    assert data["baseline"]["recommendation_rows"] == 100000
    assert data["personalized"]["recommendation_rows"] == 100000


# ============================================================
# EXPORT TESTS
# ============================================================

def test_json_recommendation_export():

    response = client.get(
        "/recommendations/1/export",
        params={
            "model": "personalized",
            "format": "json",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == 1
    assert data["model"] == "personalized"


def test_csv_recommendation_export():

    response = client.get(
        "/recommendations/1/export",
        params={
            "model": "baseline",
            "format": "csv",
        },
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]

    csv_data = list(
        csv.reader(StringIO(response.text))
    )

    assert csv_data[0][0] == "customer_id"
    assert len(csv_data) == 6
