# downloader.py

from typing import Sequence, Any, Protocol, Optional
from dotenv import load_dotenv
from sqlmodel import Session

from llm_classifier.database import InputType, ClassificationInput

load_dotenv(override=True)


class Downloader(Protocol):
    """Interface for different download approaches"""
    @classmethod
    def get_records(cls, input_type: InputType) -> list[ClassificationInput]:
        """Bulk download approach - override this for APIs that return full data in one call"""
        return []

    @classmethod
    def get_record_ids(cls, input_type: InputType) -> list[Any]:
        """List-based approach - override this for APIs that require per-record fetching"""
        return []

    @classmethod
    def download_record(cls, record_id: Any) -> Optional[ClassificationInput]:
        """Override this for list-based APIs that need per-record detail calls"""
        return None


def download_data(
    session: Session,
    input_types: Sequence[InputType],
    downloader: type[Downloader]
) -> Sequence[int]:
    """Download data using the provided strategy, persisting each record to the
    database. We upload the records to the database one at a time rather than in
    bulk to avoid memory management issues.

    Returns a list of database ids for the created database records.
    """
    ids: list[int] = []
    for input_type in input_types:
        # Try bulk download first, fall back to per-record fetching
        records: list[ClassificationInput | Any]
        if downloader.get_records != Downloader.get_records:
            records = downloader.get_records(input_type)
        else:
            records = [id for id in downloader.get_record_ids(input_type)]

        for record in records:
            try:
                downloaded_data: ClassificationInput | None
                if isinstance(record, ClassificationInput):
                    downloaded_data = record
                else:
                    downloaded_data = downloader.download_record(record)

                if downloaded_data is None:
                    continue

                session.add(downloaded_data)
                session.commit()
                ids.append(downloaded_data.id)
            except Exception as e:
                print(f"Error processing record: {e}")
                session.rollback()

    return ids
