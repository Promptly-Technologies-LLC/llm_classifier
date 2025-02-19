# test_validators.py

import pytest
from sqlmodel import SQLModel, Field
from datetime import datetime, UTC
from llm_classifier.validators import (
    get_json,
    TemplateError,
    get_placeholders
)
from typing import Optional


# --- Fixtures ---

@pytest.fixture
def valid_model() -> type[SQLModel]:
    class ValidModel(SQLModel):
        field1: str
        field2: int
    return ValidModel


@pytest.fixture
def model_with_nonrequired_fields() -> type[SQLModel]:
    class ModelWithNonRequiredFields(SQLModel):
        required_field: str
        optional_field: Optional[str] = None
        date_field: datetime = Field(default_factory=lambda: datetime.now(UTC))
    return ModelWithNonRequiredFields


# --- Tests ---

def test_get_json_with_markdown_fence() -> None:
    """Test extracting JSON from markdown code fence."""
    # Without a space between ``` and json
    content = '```json\n{"key": "value"}\n```'
    result = get_json(content)
    assert result == {"key": "value"}

    # With a space between ``` and json
    content = '``` json\n{"key": "value"}\n```'
    result = get_json(content)
    assert result == {"key": "value"}


def test_get_json_without_fence() -> None:
    """Test handling plain JSON without markdown fence."""
    content = '{"key": "value"}'
    result = get_json(content)
    assert result == {"key": "value"}


def test_get_json_with_quotes() -> None:
    """Test handling JSON with surrounding quotes."""
    content = '"{"key": "value"}"'
    result = get_json(content)
    assert result == {"key": "value"}


def test_get_placeholders_with_valid_constants(valid_model: type[SQLModel]) -> None:
    """Test getting placeholders from prompt template."""    
    valid_prompt = """
    Here is some text:
    {field1}
    Here is some more text:
    {field2}
    """

    result = get_placeholders(valid_prompt, valid_model)
    assert result == ['field1', 'field2']


def test_get_placeholders_with_invalid_placeholders(valid_model: type[SQLModel]) -> None:
    """Test that placeholders missing from model raise TemplateError."""
    invalid_prompt = """
    Here is some text:
    {field1}
    Here is some more text:
    {field2}
    Here is an invalid placeholder:
    {nonexistent_field}
    """

    with pytest.raises(TemplateError) as exc_info:
        get_placeholders(invalid_prompt, valid_model)
    assert "nonexistent_field" in str(exc_info.value)


def test_get_placeholders_with_missing_required_fields(model_with_nonrequired_fields: type[SQLModel]) -> None:
    """Test that prompt template missing required model fields raises TemplateError."""
    incomplete_prompt = """
    This prompt only uses:
    {optional_field}
    """

    with pytest.raises(TemplateError) as exc_info:
        get_placeholders(incomplete_prompt, model_with_nonrequired_fields)
    assert "required_field" in str(exc_info.value)


def test_get_placeholders_with_missing_nonrequired_fields(model_with_nonrequired_fields: type[SQLModel]) -> None:
    """Test that prompt template missing non-required model fields does not raise TemplateError."""
    incomplete_prompt = """
    This prompt only uses:
    {required_field}
    """
    result = get_placeholders(incomplete_prompt, model_with_nonrequired_fields)
    assert result == ['required_field']
