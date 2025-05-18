# test_classifier.py

import pytest
from unittest.mock import patch, AsyncMock
import asyncio
from sqlmodel import select, Session
from litellm import Choices, Message
from litellm.files.main import ModelResponse
from llm_classifier.classifier import (
    classify_input,
    process_single_input
)
from llm_classifier.database import ClassificationInput, ClassificationResponse

# Test classify_input
@pytest.mark.asyncio
async def test_classify_input() -> None:
    # Create a dynamic test response using the model's fields
    test_data = {
        field: (5 if field_info.annotation == int else "test_value")
        for field, field_info in ClassificationResponse.model_fields.items()
        if field not in ('id', 'input_id', 'classification_input')
    }
    
    mock_response = ModelResponse(
        choices=[Choices(
            message=Message(
                content=str(test_data).replace("'", '"')
            )
        )]
    )
    
    with patch('llm_classifier.classifier.acompletion', AsyncMock(return_value=mock_response)):
        result = await classify_input("test prompt", ClassificationResponse)
        assert isinstance(result, ClassificationResponse)
        # Verify all fields are present
        for field_name, expected_value in test_data.items():
            assert getattr(result, field_name) == expected_value

@pytest.mark.asyncio
async def test_classify_input_error() -> None:
    with patch('llm_classifier.classifier.acompletion', AsyncMock(side_effect=Exception("API Error"))):
        result = await classify_input("test prompt", ClassificationResponse)
        assert result is None

# Add fixture for sample inputs
@pytest.fixture
def sample_inputs() -> list[ClassificationInput]:
    return [
        ClassificationInput(input_text="Test filing 1", extra_field="extra1"),
        ClassificationInput(input_text="Test filing 2", extra_field="extra2"),
        ClassificationInput(input_text="Test filing 3", extra_field="extra3")
    ]

# Test process_single_input
@pytest.mark.asyncio
async def test_process_single_input_with_gather(test_session: Session, sample_inputs: list[ClassificationInput], mock_prompt_template: str) -> None:
    # Commit the inputs to the database
    test_session.add_all(sample_inputs)
    test_session.commit()

    # Create a dynamic mock result
    test_data = {
        field: (5 if field_info.annotation == int else "test_value")
        for field, field_info in ClassificationResponse.model_fields.items()
        if field not in ('id', 'input_id', 'classification_input')
    }
    mock_result = ClassificationResponse(**test_data)

    # Patch classify_input to return the mock result
    with patch('llm_classifier.classifier.classify_input', return_value=mock_result):
        # Pass the IDs of the sample inputs
        input_ids: list[int] = [input.id for input in sample_inputs if input.id is not None]
        results = await asyncio.gather(*[process_single_input(id, mock_prompt_template, ClassificationResponse, test_session) for id in input_ids])

    results = test_session.exec(select(ClassificationResponse)).all()
    assert len(results) == len(sample_inputs)
    assert all(isinstance(r, ClassificationResponse) for r in results)
    # Verify all fields are present in each result
    for result in results:
        for field_name, expected_value in test_data.items():
            assert getattr(result, field_name) == expected_value

@pytest.mark.asyncio
async def test_process_single_input_duplicate_prevention(test_session: Session, sample_inputs: list[ClassificationInput], mock_prompt_template: str) -> None:
    # Commit the inputs to the database
    test_session.add_all(sample_inputs)
    test_session.commit()

    mock_result = ClassificationResponse(
        most_investable_insight="test",
        reason_its_investable="reason",
        score=5
    )
    
    # Patch classify_input to return the mock result
    with patch('llm_classifier.classifier.classify_input', return_value=mock_result):
        # Pass the IDs of the sample inputs
        input_ids: list[int] = [input.id for input in sample_inputs if input.id is not None]
        assert all(input_ids)

        # Run classification twice
        results = await asyncio.gather(*[process_single_input(id, mock_prompt_template, ClassificationResponse, test_session) for id in input_ids])
        results = await asyncio.gather(*[process_single_input(id, mock_prompt_template, ClassificationResponse, test_session) for id in input_ids])

    # Verify no duplicates were created
    results = test_session.exec(select(ClassificationResponse)).all()
    assert len(results) == len(sample_inputs)
