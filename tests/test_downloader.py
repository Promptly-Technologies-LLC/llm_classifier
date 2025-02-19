# test_downloader.py

from llm_classifier.downloader import download_data, Downloader
from llm_classifier.database import ClassificationInput, InputType
from sqlmodel import Session, select
from typing import Any
    
def test_bulk_downloader(test_session: Session):
    """Test a downloader that implements bulk fetching via get_records"""
    class BulkDownloader(Downloader):
        @classmethod
        def get_records(cls, input_type: InputType) -> list[ClassificationInput]:
            return [
                ClassificationInput(
                    input_text=f"Bulk {input_type} 1",
                    extra_field="test",
                    input_type=input_type
                ),
                ClassificationInput(
                    input_text=f"Bulk {input_type} 2", 
                    extra_field="test",
                    input_type=input_type
                )
            ]

    # Test with valid input type
    input_types = ["Posts"]
    result_ids = download_data(test_session, input_types, BulkDownloader)
    
    # Verify records were created
    assert len(result_ids) == 2
    records = test_session.exec(select(ClassificationInput)).all()
    assert len(records) == 2
    assert all(r.input_type == "Posts" for r in records)
    assert {r.input_text for r in records} == {"Bulk Posts 1", "Bulk Posts 2"}

def test_list_downloader(test_session: Session):
    """Test a downloader that uses per-record fetching"""
    class ListDownloader(Downloader):
        @classmethod
        def get_record_ids(cls, input_type: InputType) -> list[Any]:
            return [1, 2, 3] if input_type == "Posts" else []
        
        @classmethod
        def download_record(cls, record_id: Any) -> ClassificationInput | None:
            return ClassificationInput(
                input_text=f"Item {record_id}",
                extra_field="test",
                input_type="Posts"
            )

    input_types = ["Posts"]
    result_ids = download_data(test_session, input_types, ListDownloader)
    
    assert len(result_ids) == 3
    records = test_session.exec(select(ClassificationInput)).all()
    assert len(records) == 3
    assert all(r.input_type == "Posts" for r in records)
    assert {r.input_text for r in records} == {"Item 1", "Item 2", "Item 3"}

def test_mixed_failure_handling(test_session: Session):
    """Test error handling when some records fail to download"""
    class FaultyDownloader(Downloader):
        @classmethod
        def get_record_ids(cls, input_type: InputType) -> list[Any]:
            return [1, 2, 3]
        
        @classmethod
        def download_record(cls, record_id: Any) -> ClassificationInput | None:
            if record_id == 2:  # Simulate failure
                raise ValueError("Test error")
            return ClassificationInput(
                input_text=f"OK {record_id}",
                extra_field="test",
                input_type="Posts"
            )

    input_types = ["Posts"]
    result_ids = download_data(test_session, input_types, FaultyDownloader)
    
    # Should process 2 successful records
    assert len(result_ids) == 2
    records = test_session.exec(select(ClassificationInput)).all()
    assert len(records) == 2
    assert {r.input_text for r in records} == {"OK 1", "OK 3"}