
import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALUATION_DIR = PROJECT_ROOT / "reports" / "evaluation"

BASELINE_FILE = EVALUATION_DIR / "evaluation_results.json"
PERSONALIZED_FILE = (
    EVALUATION_DIR / "personalized_evaluation_results.json"
)

COMPARISON_JSON = EVALUATION_DIR / "model_comparison.json"
COMPARISON_CSV = EVALUATION_DIR / "model_comparison.csv"


def load_results(path):

    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():

    if COMPARISON_JSON.exists() or COMPARISON_CSV.exists():
        raise FileExistsError(
            "A model comparison report already exists. "
            "Do not overwrite it."
        )

    baseline = load_results(BASELINE_FILE)
    personalized = load_results(PERSONALIZED_FILE)

    if baseline["cutoff"] != personalized["cutoff"]:
        raise ValueError("The models use different evaluation cutoffs.")

    if baseline["dataset_counts"] != personalized["dataset_counts"]:
        raise ValueError(
            "The models use different evaluation dataset counts."
        )

    metrics = [
        ("Precision@5", "ranking_metrics", "precision_at_5"),
        ("Recall@5", "ranking_metrics", "recall_at_5"),
        ("NDCG@5", "ranking_metrics", "ndcg_at_5"),
        ("Catalog Coverage", "catalog_metrics", "catalog_coverage"),
        (
            "Availability Violations",
            "availability_metrics",
            "availability_violations",
        ),
        (
            "Availability Violation Rate",
            "availability_metrics",
            "availability_violation_rate",
        ),
    ]

    comparison_rows = []

    for label, section, key in metrics:

        baseline_value = baseline[section][key]
        personalized_value = personalized[section][key]

        difference = personalized_value - baseline_value

        if baseline_value != 0:
            relative_change_percent = (
                difference / baseline_value
            ) * 100
        else:
            relative_change_percent = None

        if label in {
            "Precision@5",
            "Recall@5",
            "NDCG@5",
            "Catalog Coverage",
        }:
            winner = (
                "Personalized"
                if personalized_value > baseline_value
                else "Baseline"
                if baseline_value > personalized_value
                else "Tie"
            )
        else:
            winner = (
                "Personalized"
                if personalized_value < baseline_value
                else "Baseline"
                if baseline_value < personalized_value
                else "Tie"
            )

        comparison_rows.append({
            "metric": label,
            "baseline": baseline_value,
            "personalized": personalized_value,
            "difference": difference,
            "relative_change_percent": relative_change_percent,
            "better_result": winner,
        })

    report = {
        "project": "YottaFlex.ai",
        "comparison_type": "chronological_holdout",
        "cutoff": baseline["cutoff"],
        "baseline_model": baseline["recommendation_model"],
        "personalized_model": personalized["recommendation_model"],
        "same_evaluation_dataset": True,
        "dataset_counts": baseline["dataset_counts"],
        "metrics": comparison_rows,
        "interpretation": {
            "ranking_performance": (
                "The baseline has higher Precision@5, Recall@5 "
                "and NDCG@5 in this evaluation."
            ),
            "catalog_coverage": (
                "The personalized model has substantially higher "
                "catalog coverage."
            ),
            "availability": (
                "Both models have zero availability violations."
            ),
        },
    }

    with COMPARISON_JSON.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    with COMPARISON_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        fieldnames = [
            "metric",
            "baseline",
            "personalized",
            "difference",
            "relative_change_percent",
            "better_result",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(comparison_rows)

    print("\nYOTTAFLEX.AI MODEL COMPARISON")
    print("=" * 85)

    print(
        f"{'Metric':<30}"
        f"{'Baseline':>15}"
        f"{'Personalized':>18}"
        f"{'Better result':>20}"
    )

    print("-" * 85)

    for row in comparison_rows:

        print(
            f"{row['metric']:<30}"
            f"{row['baseline']:>15.6f}"
            f"{row['personalized']:>18.6f}"
            f"{row['better_result']:>20}"
        )

    print("\nSame cutoff:", report["cutoff"])
    print("Same evaluation dataset: YES")

    print("\nReports saved:")
    print(COMPARISON_JSON)
    print(COMPARISON_CSV)


if __name__ == "__main__":
    main()
