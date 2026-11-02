
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

from sqlalchemy.orm import Session as DBSession

from app.database import engine
from app import validation
from app.validation import EXPECTED_COUNTS, TABLE_MODELS


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

DATASET_START = "2025-01-01"
DATASET_END = "2026-10-31 23:00:00"

REPORTS_DIR.mkdir(exist_ok=True)


# ============================================================
# 1. RUN EXISTING VALIDATION AND CAPTURE OUTPUT
# ============================================================

def run_validation():

    output_buffer = StringIO()

    with redirect_stdout(output_buffer):
        validation.main()

    output = output_buffer.getvalue()

    if "All checks passed." in output:
        status = "PASS"
        failures = 0
    else:
        status = "FAIL"

        match = re.search(
            r"Checks requiring investigation:\s*(\d+)",
            output
        )

        failures = int(match.group(1)) if match else None

    return {
        "status": status,
        "total_failures": failures,
        "validation_output": output
    }


# ============================================================
# 2. GET ACTUAL TABLE COUNTS
# ============================================================

def get_table_counts():

    counts = {}

    with DBSession(engine) as db:

        for table_name, model in TABLE_MODELS.items():

            actual = db.query(model).count()
            expected = EXPECTED_COUNTS[table_name]

            counts[table_name] = {
                "expected": expected,
                "actual": actual,
                "status": "PASS" if actual == expected else "FAIL"
            }

    return counts


# ============================================================
# 3. GENERATE CSV TABLE COUNT REPORT
# ============================================================

def generate_counts_csv(counts):

    file_path = REPORTS_DIR / "table_counts.csv"

    with open(file_path, "w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        writer.writerow([
            "table_name",
            "expected_rows",
            "actual_rows",
            "status"
        ])

        for table_name, details in counts.items():

            writer.writerow([
                table_name,
                details["expected"],
                details["actual"],
                details["status"]
            ])

    print(f"Created: {file_path}")


# ============================================================
# 4. GENERATE JSON VALIDATION REPORT
# ============================================================

def generate_validation_json(validation_result, counts, generated_at):

    file_path = REPORTS_DIR / "validation_report.json"

    report = {
        "project": "YottaFlex.ai",
        "report_generated_at": generated_at,
        "overall_status": validation_result["status"],
        "total_failures": validation_result["total_failures"],
        "table_counts": counts,
        "validation_output": validation_result["validation_output"]
    }

    with open(file_path, "w", encoding="utf-8") as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Created: {file_path}")


# ============================================================
# 5. GENERATE HUMAN-READABLE TEXT REPORT
# ============================================================

def generate_validation_txt(validation_result, counts, generated_at):

    file_path = REPORTS_DIR / "validation_report.txt"

    with open(file_path, "w", encoding="utf-8") as file:

        file.write("=" * 70 + "\n")
        file.write("YOTTAFLEX.AI - DATA QUALITY REPORT\n")
        file.write("=" * 70 + "\n\n")

        file.write(f"Report generated: {generated_at}\n")
        file.write(
            f"Overall status: {validation_result['status']}\n"
        )
        file.write(
            f"Total failures: {validation_result['total_failures']}\n\n"
        )

        file.write("TABLE RECORD COUNTS\n")
        file.write("-" * 70 + "\n")

        for table_name, details in counts.items():

            file.write(
                f"{table_name:<22} "
                f"Expected: {details['expected']:>10,} | "
                f"Actual: {details['actual']:>10,} | "
                f"{details['status']}\n"
            )

        file.write("\n")
        file.write("COMPLETE VALIDATION OUTPUT\n")
        file.write("-" * 70 + "\n")
        file.write(validation_result["validation_output"])

    print(f"Created: {file_path}")


# ============================================================
# 6. GENERATE DATASET MANIFEST
# ============================================================

def generate_manifest(counts, generated_at):

    file_path = REPORTS_DIR / "dataset_manifest.json"

    total_rows = sum(
        details["actual"]
        for details in counts.values()
    )

    manifest = {
        "project": "YottaFlex.ai",
        "dataset_name": "E-commerce Recommendation Dataset",
        "manifest_generated_at": generated_at,
        "dataset_period": {
            "start": DATASET_START,
            "end": DATASET_END
        },
        "database": {
            "system": "PostgreSQL",
            "database_name": "yottaflex_db"
        },
        "generation": {
            "random_seed": 42,
            "currency": "INR",
            "recommendation_model": "category_affinity_v1"
        },
        "dataset_summary": {
            "number_of_tables": len(counts),
            "total_records": total_rows,
            "table_counts": {
                table_name: details["actual"]
                for table_name, details in counts.items()
            }
        },
        "data_integrity": {
            "validation_status": "See validation_report.json",
            "seed_scripts_rerun_during_reporting": False
        }
    }

    with open(file_path, "w", encoding="utf-8") as file:

        json.dump(
            manifest,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Created: {file_path}")


# ============================================================
# 7. GENERATE DATA DICTIONARY FROM SQLALCHEMY MODELS
# ============================================================

def generate_data_dictionary():

    file_path = REPORTS_DIR / "data_dictionary.md"

    with open(file_path, "w", encoding="utf-8") as file:

        file.write("# YottaFlex.ai - Data Dictionary\n\n")

        file.write(
            "This document describes the database tables and columns "
            "using the SQLAlchemy model definitions.\n\n"
        )

        for table_name, model in TABLE_MODELS.items():

            table = model.__table__

            file.write(f"## {table_name}\n\n")

            file.write("| Column | Data Type | Nullable | Primary Key | Foreign Key |\n")
            file.write("|---|---|---|---|---|\n")

            for column in table.columns:

                foreign_key_targets = [
                    fk.target_fullname
                    for fk in column.foreign_keys
                ]

                foreign_key_text = (
                    ", ".join(foreign_key_targets)
                    if foreign_key_targets
                    else "-"
                )

                file.write(
                    f"| {column.name} "
                    f"| {column.type} "
                    f"| {'Yes' if column.nullable else 'No'} "
                    f"| {'Yes' if column.primary_key else 'No'} "
                    f"| {foreign_key_text} |\n"
                )

            file.write("\n### Constraints\n\n")

            if table.constraints:

                for constraint in table.constraints:

                    name = constraint.name or "Unnamed"
                    constraint_type = type(constraint).__name__

                    file.write(
                        f"- **{constraint_type}** "
                        f"({name}): `{constraint}`\n"
                    )

            else:
                file.write("No additional constraints defined.\n")

            file.write("\n")

    print(f"Created: {file_path}")


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():

    print("=" * 70)
    print("YOTTAFLEX.AI - REPORT GENERATION")
    print("=" * 70)

    generated_at = datetime.now().astimezone().isoformat()

    print("\nRunning existing validation checks...")

    validation_result = run_validation()

    print(validation_result["validation_output"])

    print("\nCollecting database record counts...")

    counts = get_table_counts()

    print("\nGenerating reports...\n")

    generate_counts_csv(counts)

    generate_validation_json(
        validation_result,
        counts,
        generated_at
    )

    generate_validation_txt(
        validation_result,
        counts,
        generated_at
    )

    generate_manifest(
        counts,
        generated_at
    )

    generate_data_dictionary()

    print("\n" + "=" * 70)
    print("REPORT GENERATION SUMMARY")
    print("=" * 70)

    print(f"Validation status: {validation_result['status']}")

    print(f"Total records: {sum(item['actual'] for item in counts.values()):,}")

    print(f"Reports folder: {REPORTS_DIR}")

    print("\nGenerated files:")

    for file_path in sorted(REPORTS_DIR.iterdir()):
        if file_path.is_file():
            print(f"  - {file_path.name}")

    print("=" * 70)


if __name__ == "__main__":
    main()
