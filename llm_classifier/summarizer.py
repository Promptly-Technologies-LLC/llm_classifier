# summarizer.py

import csv
from datetime import datetime
from pathlib import Path
from sqlmodel import Session, select, col
from typing import Sequence, Any
from llm_classifier.database import ClassificationResponse, ClassificationInput
from statistics import mean, median, stdev

STATS_TEMPLATE = """
Summary Statistics:
Total Inputs Processed: {total}
Mean: {mean:.2f}
Median: {median}
Standard Deviation: {std}"""

def format_stats_summary(numeric_sequence: Sequence[float]) -> str:
    """Format a statistical summary for a numeric field."""
    if not numeric_sequence:
        return "No processed inputs found."

    try:
        std_text = f"{stdev(numeric_sequence):.2f}"
    except:
        std_text = "N/A (need more than one value)"

    return STATS_TEMPLATE.format(
        total=len(numeric_sequence),
        mean=mean(numeric_sequence),
        median=median(numeric_sequence),
        std=std_text
    )


def format_distribution(numeric_sequence: Sequence[float], breakpoints: int = 5) -> str:
    """Format the percentile distribution of a numeric sequence."""
    if not numeric_sequence:
        return "No processed inputs found."

    sorted_sequence = sorted(numeric_sequence)
    percentiles = [n for n in range(0, 101, 100 // breakpoints)]
    lines = ["Distribution:"]

    for p in percentiles:
        index = int(p / 100 * (len(sorted_sequence) - 1))
        lines.append(f"{p}th percentile: {sorted_sequence[index]:.2f}")

    return "\n".join(lines)


def get_numeric_sequence(session: Session, numeric_field: str) -> Sequence[float]:
    """Retrieve all valid numeric values from the processed inputs."""
    today = datetime.now().date()  # Get current date in system timezone
    results: Sequence[int | float] = session.exec(
        select(getattr(ClassificationResponse, numeric_field))
        .where(
            col(ClassificationResponse.input_id).in_(
                select(ClassificationInput.id).where(
                    ClassificationInput.processed_date >= today
                )
            )
        )
    ).all()
    return results


def print_summary_statistics(session: Session, numeric_field: str, breakpoints: int = 5) -> None:
    """Print summary statistics for a numeric field."""
    numeric_sequence: Sequence[float] = get_numeric_sequence(session, numeric_field)
    
    if not numeric_sequence:
        print("No processed inputs found.")
        return
    
    print(format_stats_summary(numeric_sequence))
    print(format_distribution(numeric_sequence, breakpoints=breakpoints))


def get_filtered_responses(
    session: Session,
    where_clauses: list[Any] | None = None
) -> Sequence[ClassificationResponse]:
    """Retrieve filtered results from processed inputs.
    
    Args:
        session: Database session
        where_clauses: List of SQLAlchemy filter clauses
    """
    today = datetime.now().date()
    query = select(ClassificationResponse).join(ClassificationInput).where(
        ClassificationInput.processed_date >= today
    )
    
    if where_clauses:
        query = query.where(*where_clauses)
        
    results: Sequence[ClassificationResponse] = session.exec(query).all()
    return results


def get_exportable_fields(model_class: type[ClassificationResponse]) -> list[str]:
    """Get list of fields to export, excluding internal fields."""
    return [
        f for f in model_class.model_fields 
        if f not in ["id", "input_id", "classification_input"]
    ]


def export_responses(
    session: Session,
    output_csv: str | Path,
    where_clauses: list[Any] | None = None,
    input_fields: list[str] = ["id", "processed_date", "input_type"]
) -> None:
    """Export filtered findings to CSV.
    
    Args:
        session: Database session
        output_csv: Path to output CSV file
        where_clauses: List of SQLAlchemy where clauses for filtering
        input_fields: List of fields to include from related ClassificationInput
    """
    results = get_filtered_responses(session, where_clauses)
    
    if results:
        fields = get_exportable_fields(ClassificationResponse)
        fields = input_fields + fields
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(fields)
            rows = []
            for r in results:
                row = [getattr(r.classification_input, field) for field in input_fields]
                row.extend(getattr(r, field) for field in fields if field not in input_fields)
                rows.append(row)
            csv_writer.writerows(rows)
        print(f"\nExported {len(results)} filtered findings to {output_csv}")
    else:
        print("\nNo matching findings found")