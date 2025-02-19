# test_prompt.py

from sqlmodel import Session, select
from sqlalchemy.engine import Engine

from llm_classifier.database import ClassificationInput, ClassificationResponse
from llm_classifier.validators import get_placeholders


def test_that_prompt_template_has_valid_placeholders(mock_prompt_template: str) -> None:
    placeholders = get_placeholders(mock_prompt_template, ClassificationInput)
    assert len(placeholders) > 0


def test_classification_models(test_engine: Engine) -> None:
    with Session(test_engine) as session:
        # Create a ClassificationInput
        input_1 = ClassificationInput(
            input_text="Test filing text",
            ticker="TEST",
            extra_field="extra_value"
        )
        session.add(input_1)
        session.commit()

        # Create a ClassificationResponse with dynamic fields
        response_data = {
            field: "Test value" if isinstance(field_info.annotation, type(str))
                   else 5 if isinstance(field_info.annotation, type(int))
                   else None
            for field, field_info in ClassificationResponse.model_fields.items()
            if field not in ('id', 'input_id', 'classification_input')
        }
        response_1 = ClassificationResponse(
            **response_data,
            input_id=input_1.id
        )
        session.add(response_1)
        session.commit()

        # Verify that the response is associated with the input
        statement_1 = select(ClassificationInput).where(ClassificationInput.id == input_1.id)
        retrieved_input = session.exec(statement_1).one()
        classification_response = retrieved_input.classification_response
        assert classification_response is not None
        
        # Verify all fields dynamically
        for field, value in response_data.items():
            assert getattr(classification_response, field) == value

        # Verify that deleting the input cascades to the response
        session.delete(input_1)
        session.commit()
        statement_2 = select(ClassificationResponse).where(ClassificationResponse.id == response_1.id)
        retrieved_response = session.exec(statement_2).one_or_none()
        assert retrieved_response is None