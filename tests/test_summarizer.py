# test_summarizer.py

from pathlib import Path
from pytest import CaptureFixture
from sqlmodel import Session
from llm_classifier.summarizer import (
    format_stats_summary,
    print_summary_statistics,
    export_responses,
    get_exportable_fields,
)
from llm_classifier.database import ClassificationResponse

def test_format_stats_summary() -> None:
    """Test statistics formatting with various inputs."""
    # Test with normal data
    scores = [1, 2, 3, 4, 5]
    result = format_stats_summary(scores)
    assert "Total Inputs Processed: 5" in result
    assert "Mean: 3.00" in result
    assert "Median: 3" in result
    assert "Standard Deviation: 1.58" in result

    # Test with empty list
    assert format_stats_summary([]) == "No processed inputs found."

    # Test with single value (where std dev isn't possible)
    result = format_stats_summary([5])
    assert "N/A (need more than one value)" in result


def test_print_summary_statistics(test_session_with_sample_data: Session, capsys: CaptureFixture) -> None:
    """Test the print_summary_statistics function captures correct output."""
    print_summary_statistics(test_session_with_sample_data, numeric_field="score")
    captured = capsys.readouterr()

    assert "Summary Statistics:" in captured.out
    assert "Total Inputs Processed: 4" in captured.out


def test_get_exportable_fields() -> None:
    """Test getting exportable fields from a model."""
    fields = get_exportable_fields(ClassificationResponse)
    # Check excluded fields
    assert "id" not in fields
    assert "input_id" not in fields
    # Check that we have at least one field (without assuming specific fields)
    assert len(fields) > 0


def test_export_responses(test_session_with_sample_data: Session, tmp_path: Path) -> None:
    """Test exporting responses to CSV."""
    output_file = tmp_path / "test_output.csv"
    export_responses(
        test_session_with_sample_data,
        str(output_file),
        where_clauses=[ClassificationResponse.score >= 7], # type: ignore
        input_fields=["extra_field"]  # Use fields that exist in the mock model
    )

    # Get expected fields dynamically
    expected_fields = ["extra_field"] + get_exportable_fields(ClassificationResponse)

    # Verify file contents
    with open(output_file) as f:
        lines = f.readlines()
        assert len(lines) == 3  # Header + 2 results

        # Check header matches expected fields
        header = lines[0].strip().split(',')
        assert header == expected_fields

        # Check data row contains expected number of fields
        data = lines[1].strip().split(',')
        assert len(data) == len(expected_fields)
        # Verify score meets minimum threshold
        score_idx = header.index("score")
        assert int(data[score_idx]) >= 7


def test_export_responses_no_results(test_session_with_sample_data: Session, tmp_path: Path) -> None:
    """Test exporting when no results meet the criteria."""
    output_file = tmp_path / "test_output.csv"
    export_responses(
        test_session_with_sample_data,
        str(output_file),
        where_clauses=[ClassificationResponse.score >= 10], # type: ignore
        input_fields=["extra_field"]
    )

    assert not output_file.exists()
