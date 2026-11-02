
import math
from collections.abc import Mapping, Sequence
from typing import Hashable


def _unique_in_order(items):
    """Remove duplicate items while preserving recommendation order."""
    return list(dict.fromkeys(items))


def ranking_metrics_at_k(
    recommendations: Mapping[Hashable, Sequence[Hashable]],
    ground_truth: Mapping[Hashable, set],
    k: int = 5,
) -> dict:
    """
    Calculate macro-averaged Precision@K, Recall@K and NDCG@K.

    Only customers with at least one relevant test product
    are included in the averages.

    Precision denominator is always K.
    Relevance is binary: a product is either relevant or not.
    """

    if k <= 0:
        raise ValueError("k must be greater than zero.")

    precision_scores = []
    recall_scores = []
    ndcg_scores = []

    customers_with_relevant_items = 0
    customers_without_recommendations = 0

    for customer_id, relevant_products in ground_truth.items():

        relevant = set(relevant_products)

        # Customers without positive test purchases are not
        # included in ranking metric averages.
        if not relevant:
            continue

        customers_with_relevant_items += 1

        ranked_products = _unique_in_order(
            recommendations.get(customer_id, [])
        )[:k]

        if not ranked_products:
            customers_without_recommendations += 1

        hits = [
            1 if product_id in relevant else 0
            for product_id in ranked_products
        ]

        hit_count = sum(hits)

        # Precision@K: relevant recommendations / K.
        precision = hit_count / k

        # Recall@K: relevant recommendations retrieved /
        # all relevant products for this customer.
        recall = hit_count / len(relevant)

        # DCG@K with binary relevance.
        dcg = sum(
            relevance / math.log2(rank + 1)
            for rank, relevance in enumerate(hits, start=1)
        )

        # Ideal DCG: all relevant products ranked first.
        ideal_hits = min(len(relevant), k)

        idcg = sum(
            1 / math.log2(rank + 1)
            for rank in range(1, ideal_hits + 1)
        )

        ndcg = dcg / idcg if idcg > 0 else 0.0

        precision_scores.append(precision)
        recall_scores.append(recall)
        ndcg_scores.append(ndcg)

    if customers_with_relevant_items == 0:
        raise ValueError(
            "No customers have positive test ground truth."
        )

    evaluated_customers = customers_with_relevant_items

    return {
        f"precision_at_{k}": (
            sum(precision_scores) / evaluated_customers
        ),
        f"recall_at_{k}": (
            sum(recall_scores) / evaluated_customers
        ),
        f"ndcg_at_{k}": (
            sum(ndcg_scores) / evaluated_customers
        ),
        "evaluated_customers": evaluated_customers,
        "customers_without_recommendations": (
            customers_without_recommendations
        ),
    }


def catalog_coverage(
    recommendations: Mapping[Hashable, Sequence[Hashable]],
    eligible_catalog: set,
) -> dict:
    """
    Calculate catalog coverage.

    Coverage = distinct recommended products /
               eligible catalog products.
    """

    if not eligible_catalog:
        raise ValueError("Eligible catalog cannot be empty.")

    recommended_products = {
        product_id
        for product_list in recommendations.values()
        for product_id in product_list
    }

    covered_products = (
        recommended_products & eligible_catalog
    )

    return {
        "catalog_coverage": (
            len(covered_products) / len(eligible_catalog)
        ),
        "unique_recommended_products": len(
            recommended_products
        ),
        "eligible_catalog_products": len(eligible_catalog),
        "covered_catalog_products": len(covered_products),
    }


def availability_violations(
    recommendations: Mapping[Hashable, Sequence[Hashable]],
    eligible_products: set,
) -> dict:
    """
    Calculate recommendations that are not in the supplied
    eligible product set.

    The eligible set must represent the catalog snapshot
    chosen for the evaluation.
    """

    all_recommendations = [
        product_id
        for product_list in recommendations.values()
        for product_id in product_list
    ]

    total = len(all_recommendations)

    violation_count = sum(
        1
        for product_id in all_recommendations
        if product_id not in eligible_products
    )

    return {
        "availability_violations": violation_count,
        "availability_violation_rate": (
            violation_count / total if total else 0.0
        ),
        "total_recommendations": total,
    }
