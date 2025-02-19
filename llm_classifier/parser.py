# parser.py

from typing import Type, TypeVar
from pydantic import BaseModel
from llm_classifier.validators import get_json


T = TypeVar('T', bound=BaseModel)


def get_model_from_json(content: str, model_class: Type[T]) -> T:
    """Parse JSON from LLM response, handling both direct JSON and markdown-fenced output."""
    parsed_json = get_json(content)
    return model_class.model_validate(parsed_json)


def get_gemini_schema(model_class: Type[T]) -> dict:
    """Convert a Pydantic/SQLModel schema to Gemini-compatible format."""
    schema = model_class.model_json_schema()
    
    def get_type_info(field_info: dict) -> dict:
        """Extract type information handling various field configurations."""
        if "type" in field_info:
            return {"type": field_info["type"]}
        elif "anyOf" in field_info:
            # Handle Optional fields by finding non-null type
            non_null_types = [t for t in field_info["anyOf"] if t["type"] != "null"]
            if non_null_types:
                return {"type": non_null_types[0]["type"]}
        return {"type": "string"}
    
    # Remove only SQLModel-specific fields, not all fields with defaults
    properties = {
        name: get_type_info(info)
        for name, info in schema["properties"].items()
        if name not in ("id", "input_id", "classification_input")
    }
    
    return {
        "type": "object",
        "properties": properties,
        "required": [
            field for field in schema.get("required", [])
            if field not in ("id", "input_id", "classification_input")
        ]
    }