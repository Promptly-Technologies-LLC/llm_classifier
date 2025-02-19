# test_parser.py

from typing import Optional
from sqlmodel import SQLModel, Field
from llm_classifier.parser import get_model_from_json, get_gemini_schema


# Test models with various field types
class SampleResponse(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    string_field: str
    int_field: int
    optional_string: Optional[str] = None
    optional_int: Optional[int] = None


def test_get_model_from_json() -> None:
    # Test with different field types
    json_str = '''
    {
        "string_field": "test",
        "int_field": 42,
        "optional_string": "optional",
        "optional_int": 10
    }
    '''
    result = get_model_from_json(json_str, SampleResponse)
    assert isinstance(result, SampleResponse)
    assert result.string_field == "test"
    assert result.int_field == 42
    assert result.optional_string == "optional"
    assert result.optional_int == 10

    # Test with minimal required fields
    json_str = '''
    {
        "string_field": "test",
        "int_field": 42
    }
    '''
    result = get_model_from_json(json_str, SampleResponse)
    assert isinstance(result, SampleResponse)
    assert result.string_field == "test"
    assert result.int_field == 42
    assert result.optional_string is None
    assert result.optional_int is None


def test_get_gemini_schema() -> None:
    schema = get_gemini_schema(SampleResponse)

    # Expected schema structure
    expected = {
        "type": "object",
        "properties": {
            "string_field": {"type": "string"},
            "int_field": {"type": "integer"},
            "optional_string": {"type": "string"},
            "optional_int": {"type": "integer"}
        },
        "required": ["string_field", "int_field"]
    }

    assert schema == expected, f"Schema mismatch.\nExpected: {expected}\nGot: {schema}"

    # Verify SQLModel-specific fields are excluded
    assert "id" not in schema["properties"]
    assert "input_id" not in schema["properties"]

    # Verify required fields are correct
    assert "string_field" in schema["required"]
    assert "int_field" in schema["required"]
    assert "optional_string" not in schema["required"]
    assert "optional_int" not in schema["required"]