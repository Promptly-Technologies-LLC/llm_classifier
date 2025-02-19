# conftest.py

# --- Patch prompt models for testing ---

from sqlmodel import SQLModel, Field
import llm_classifier.prompt as prompt

# Patch Input to add an extra field that the prompt template needs
class Input(SQLModel):
    input_text: str
    extra_field: str = Field(default="extra")  # Additional field required for tests

# Patch Response and replace investability with score
class Response(SQLModel):
    most_investable_insight: str
    score: int
    reason_its_investable: str

import pytest
import os
import tempfile
from unittest.mock import patch
from typing import Generator, List
from datetime import datetime, timedelta
from sqlmodel import Session, Field, SQLModel
from sqlalchemy.engine import Engine

with patch("llm_classifier.prompt.Input", new=Input):
    with patch("llm_classifier.prompt.Response", new=Response):
        from llm_classifier.database import init_database, seed_input_types, ClassificationInput, ClassificationResponse

# --- Fixtures ---
@pytest.fixture(scope="session")
def mock_prompt_template() -> str:
    MOCK_PROMPT_TEMPLATE = (
        "Analyze the following text and return a JSON object with investment insights:\n"
        "{input_text}\n"
        "Extra field: {extra_field}\n"
    )
    return MOCK_PROMPT_TEMPLATE


@pytest.fixture(scope="function")
def test_db_path() -> Generator[str, None, None]:
    """Fixture to provide a unique path for the test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        tmp_path = tmp_file.name
    yield tmp_path
    os.remove(tmp_path)


@pytest.fixture(scope="function")
def test_engine(test_db_path: str) -> Generator[Engine, None, None]:
    """Fixture to create an in-memory SQLite database engine for testing."""
    engine = init_database(test_db_path)
    # Create tables for BOTH mock models
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Fixture to create a session for testing."""
    with Session(test_engine) as session:
        seed_input_types(session, input_types=["8-K", "10-K"])
        yield session


@pytest.fixture
def sample_inputs() -> List[ClassificationInput]:
    """Fixture to create sample classification data."""
    now = datetime.now() # Use system timezone
    yesterday = now - timedelta(days=1)
    inputs = [
        ClassificationInput(
            input_text="Test 1",
            date=now,  # Today's date
            extra_field="extra_value_1"
        ),
        ClassificationInput(
            input_text="Test 2",
            date=now,  # Today's date
            extra_field="extra_value_2"
        ),
        ClassificationInput(
            input_text="Test 3",
            date=yesterday,  # Yesterday's date
            extra_field="extra_value_3"
        ),
        ClassificationInput(
            input_text="Test 4",
            date=yesterday,  # Yesterday's date
            extra_field="extra_value_4"
        )
    ]

    return inputs


@pytest.fixture
def sample_responses() -> List[ClassificationResponse]:
    """Fixture to create sample classification responses."""
    responses = [
        ClassificationResponse(
            most_investable_insight="Test 1",
            score=8,  # Meets the min_score criterion
            id=1,
            reason_its_investable="Reason 1",
            input_id=1
        ),
        ClassificationResponse(
            most_investable_insight="Test 2",
            score=9,  # Meets the min_score criterion
            id=2,
            reason_its_investable="Reason 2",
            input_id=2
        ),
        ClassificationResponse(
            most_investable_insight="Test 3",
            score=6,  # Does not meet the min_score criterion
            id=3,
            reason_its_investable="Reason 3",
            input_id=3
        ),
        ClassificationResponse(
            most_investable_insight="Test 4",
            score=5,  # Does not meet the min_score criterion
            id=4,
            reason_its_investable="Reason 4",
            input_id=4
        )
    ]

    return responses


@pytest.fixture
def test_session_with_sample_data(test_session: Session, sample_inputs: List[ClassificationInput], sample_responses: List[ClassificationResponse]) -> Generator[Session, None, None]:
    """Fixture to create sample data in the database."""
    # Add the inputs first.
    for inp in sample_inputs:
        test_session.add(inp)
    test_session.commit()  # Commit to assign IDs

    # Now that inputs have IDs, add the responses.
    for resp, inp in zip(sample_responses, sample_inputs):
        resp.input_id = inp.id  # Ensure input_id is set correctly
        test_session.add(resp)

    test_session.commit()
    yield test_session
