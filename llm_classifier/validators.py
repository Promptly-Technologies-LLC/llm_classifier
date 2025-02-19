# validators.py

import re
import json
from sqlmodel import SQLModel
from typing import Type, Any
from llm_classifier.database import ClassificationInput
from llm_classifier.prompt import PROMPT_TEMPLATE


class TemplateError(ValueError):
    """Raised when there's an error with the prompt template"""
    def __init__(self, col: str, model: Type[SQLModel]):
        super().__init__(f"Column '{col}' in prompt template not found in {model.__name__} model.")


def get_placeholders(
        prompt_template: str=PROMPT_TEMPLATE,
        model: Type[SQLModel]=ClassificationInput
    ) -> list[str]:
    """
    Get placeholders from prompt template, validating that all prompt template
    placeholders match fields in the model.

    Also validates that all required model fields (non-optional fields
    without default values or factory functions) are present as placeholders in
    the prompt template.

    Args:
        prompt_template: The template string containing {field_name} placeholders
        model: SQLModel class to validate fields against

    Returns:
        List of placeholder names found in the template

    Raises:
        TemplateError: If template contains invalid fields or missing required fields
    """
    placeholders = re.findall(r'\{(\w+)\}', prompt_template)

    # Get the model fields from SQLModel
    model_fields = model.model_fields

    # Check template placeholders exist in model
    invalid_placeholders = [col for col in placeholders if col not in model_fields]
    if invalid_placeholders:
        raise TemplateError(invalid_placeholders[0], model)
    
    # Get required fields (excluding SQLModel internals)
    required_fields = [
        name
        for name, field in model_fields.items()
        if (field.is_required() and 
            name not in ('id', 'input_id', 'classification_input'))
    ]

    # Check required fields are in template
    missing_required = [field for field in required_fields if field not in placeholders]
    if missing_required:
        raise TemplateError(missing_required[0], model)

    return placeholders


def get_json(content: str) -> Any:
    """Extract JSON content from markdown code fence if present."""
    match = re.search(r'```\s*json\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
    if match:
        return json.loads(match.group(1).strip())
    return json.loads(content.strip().strip('"\''))

if __name__ == "__main__":
    print(get_placeholders())