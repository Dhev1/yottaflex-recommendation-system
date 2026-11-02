
import pytest

from app.evaluation.metrics import (
    ranking_metrics_at_k,
    catalog_coverage,
    availability_violations,
)


def test_ranking_metrics_hand_calculated_example():

    recommendations = {
        "customer_1": ["A", "X", "B"],
        "customer_2": ["D", "E", "F"],
    }

    ground_truth = {
        "customer_1": {"A", "B", "C"},
        "customer_2": {"Z"},
    }

    result = ranking_metrics_at_k(
        recommendations,
        ground_truth,
        k=3,
    )

    # Customer 1:
    # Precision = 2 / 3
    # Recall = 2 / 3
    #
    # DCG = 1 + 0 + 1/log2(4) = 1.5
    # IDCG = 1 + 1/log2(3) + 1/log2(4)
    #
    # NDCG = 1.5 / IDCG

    expected_ndcg_customer_1 = (
        1.5 / (1 + 1 / 1.584962500721156 + 0.5)
    )

    # Customer 2:
    # Precision = 0
    # Recall = 0
    # NDCG = 0

    assert result["evaluated_customers"] == 2

    assert result["precision_at_3"] == pytest.approx(1 / 3)

    assert result["recall_at_3"] == pytest.approx(1 / 3)

    assert result["ndcg_at_3"] == pytest.approx(
        expected_ndcg_customer_1 / 2
    )


def test_catalog_coverage():

    recommendations = {
        "customer_1": ["A", "B", "C"],
        "customer_2": ["B", "D", "E"],
    }

    eligible_catalog = {
        "A", "B", "C", "D", "E", "F", "G", "H"
    }

    result = catalog_coverage(
        recommendations,
        eligible_catalog,
    )

    # Five distinct products recommended out of eight.
    assert result["unique_recommended_products"] == 5
    assert result["eligible_catalog_products"] == 8
    assert result["covered_catalog_products"] == 5
    assert result["catalog_coverage"] == pytest.approx(5 / 8)


def test_availability_violations():

    recommendations = {
        "customer_1": ["A", "B", "X"],
        "customer_2": ["C", "D", "Y"],
    }

    eligible_products = {"A", "B", "C", "D"}

    result = availability_violations(
        recommendations,
        eligible_products,
    )

    # X and Y are not eligible: 2 out of 6.
    assert result["availability_violations"] == 2
    assert result["total_recommendations"] == 6
    assert result["availability_violation_rate"] == pytest.approx(2 / 6)


def test_customers_without_relevant_items_are_excluded():

    recommendations = {
        "customer_1": ["A", "B", "C"],
    }

    ground_truth = {
        "customer_1": {"A"},
        "customer_2": set(),
    }

    result = ranking_metrics_at_k(
        recommendations,
        ground_truth,
        k=3,
    )

    assert result["evaluated_customers"] == 1
    assert result["precision_at_3"] == pytest.approx(1 / 3)
    assert result["recall_at_3"] == pytest.approx(1.0)


def test_ranking_metrics_reject_zero_k():

    with pytest.raises(ValueError):

        ranking_metrics_at_k(
            {"customer_1": ["A"]},
            {"customer_1": {"A"}},
            k=0,
        )


def test_ranking_metrics_reject_empty_ground_truth():

    with pytest.raises(ValueError):

        ranking_metrics_at_k(
            {"customer_1": ["A"]},
            {"customer_1": set()},
            k=3,
        )


def test_catalog_coverage_rejects_empty_catalog():

    with pytest.raises(ValueError):

        catalog_coverage(
            {"customer_1": ["A"]},
            set(),
        )
