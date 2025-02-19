# test_classifier.py

import pytest
from unittest.mock import patch, AsyncMock
from sqlmodel import select, Session
from llm_classifier.classifier import (
    classify_inputs,
    classify_text
)
from llm_classifier.database import ClassificationInput, ClassificationResponse

# Test classify_text
@pytest.mark.asyncio
async def test_classify_text() -> None:
    # Create a dynamic test response using the model's fields
    test_data = {
        field: (5 if field_info.annotation == int else "test_value")
        for field, field_info in ClassificationResponse.model_fields.items()
        if field not in ('id', 'input_id', 'classification_input')
    }
    
    mock_response = {
        'choices': [{
            'message': {
                'content': str(test_data).replace("'", '"')
            }
        }]
    }
    
    with patch('llm_classifier.classifier.acompletion', AsyncMock(return_value=mock_response)):
        result = await classify_text("test prompt", ClassificationResponse)
        assert isinstance(result, ClassificationResponse)
        # Verify all fields are present
        for field_name, expected_value in test_data.items():
            assert getattr(result, field_name) == expected_value

@pytest.mark.asyncio
async def test_classify_text_error() -> None:
    with patch('llm_classifier.classifier.acompletion', AsyncMock(side_effect=Exception("API Error"))):
        result = await classify_text("test prompt", ClassificationResponse)
        assert result is None

# Add fixture for sample inputs
@pytest.fixture
def sample_inputs() -> list[ClassificationInput]:
    return [
        ClassificationInput(input_text="Test filing 1", extra_field="extra1"),
        ClassificationInput(input_text="Test filing 2", extra_field="extra2"),
        ClassificationInput(input_text="Test filing 3", extra_field="extra3")
    ]

# Test classify_inputs
def test_classify_inputs(test_session: Session, sample_inputs: list[ClassificationInput], mock_prompt_template: str) -> None:
    # Create a dynamic mock result
    test_data = {
        field: (5 if field_info.annotation == int else "test_value")
        for field, field_info in ClassificationResponse.model_fields.items()
        if field not in ('id', 'input_id', 'classification_input')
    }
    mock_result = ClassificationResponse(**test_data)
    
    classify_inputs(sample_inputs, mock_prompt_template, ClassificationResponse, test_session)
    
    results = test_session.exec(select(ClassificationResponse)).all()
    assert len(results) == len(sample_inputs)
    assert all(isinstance(r, ClassificationResponse) for r in results)
    # Verify all fields are present in each result
    for result in results:
        for field_name, expected_value in test_data.items():
            assert getattr(result, field_name) == expected_value

def test_classify_inputs_duplicate_prevention(test_session: Session, sample_inputs: list[ClassificationInput], mock_prompt_template: str) -> None:
    mock_result = ClassificationResponse(
        most_investable_insight="test",
        reason_its_investable="reason",
        score=5
    )
    
    # Run classification twice
    classify_inputs(sample_inputs, mock_prompt_template, ClassificationResponse, test_session)
    classify_inputs(sample_inputs, mock_prompt_template, ClassificationResponse, test_session)
    
    # Verify no duplicates were created
    results = test_session.exec(select(ClassificationResponse)).all()
    assert len(results) == len(sample_inputs)
