# prompt.py

from typing import Optional
from sqlmodel import SQLModel
from llm_classifier.database import DynamicModel, DynamicField, DynamicPrompt
from sqlmodel import Session

# --- Deprecated: Static Data models and Prompt Template ---
# These are kept for legacy support only. For dynamic, user-defined models and prompts,
# see the logic in main.py.

class Input(SQLModel, table=False):
    """[DEPRECATED] Use DynamicModel and related logic for user-defined input models."""
    title: str
    body: str
    user_id: Optional[int] = None
    post_id: Optional[int] = None

class Response(SQLModel, table=False):
    """[DEPRECATED] Use dynamic response handling for user-defined models."""
    sentiment: int
    reason: str

# [DEPRECATED] Use dynamic prompt generation in main.py for user-defined models.
PROMPT_TEMPLATE = """
Analyze the following post and rate the sentiment from 1 to 5, where 1 is negative, 3 is neutral, and 5 is positive.

Before you rate the sentiment, reflect on the sentiment of the post in the "reason" field.

Return your response as JSON with a string "reason" field and an integer "sentiment" field.

Example input:
Title:
"The Future of AI"

Post:
"I think AI is the future of the world. It will change everything."

Example output:
{{
"reason": "The post is positive in the sense that it is bullish on the power of AI, but it does not specify whether the expected change to 'everything' is likely to be positive or negative, so I will rate it a 4 (somewhat positive).",
"sentiment": 4
}}

Title:
{title}

Post:
{body}
"""

# For dynamic prompt generation, see main.py and the DynamicModel logic.

def seed_example_dynamic_models(session: Session):
    """
    Seed the database with example DynamicModel, DynamicField, and DynamicPrompt records
    corresponding to the legacy Input/Response models and PROMPT_TEMPLATE.
    """
    # Check if already seeded
    if session.exec(DynamicModel.select().where(DynamicModel.name == "PostInput")).first():
        return  # Already seeded

    # Create DynamicModel for Input
    input_model = DynamicModel(name="PostInput", description="Input model for a post")
    session.add(input_model)
    session.commit()

    # Add fields for Input
    input_fields = [
        DynamicField(model_id=input_model.id, field_name="title", field_type="string"),
        DynamicField(model_id=input_model.id, field_name="body", field_type="string"),
        DynamicField(model_id=input_model.id, field_name="user_id", field_type="integer"),
        DynamicField(model_id=input_model.id, field_name="post_id", field_type="integer"),
    ]
    session.add_all(input_fields)
    session.commit()

    # Add DynamicPrompt
    prompt = DynamicPrompt(
        model_id=input_model.id,
        name="Default Post Sentiment Prompt",
        template=PROMPT_TEMPLATE,
        description="Prompt for sentiment analysis of a post."
    )
    session.add(prompt)
    session.commit()

    # Optionally, add a DynamicModel for the response schema (not required for prompt generation)
    # response_model = DynamicModel(name="PostResponse", description="Response model for a post sentiment analysis")
    # session.add(response_model)
    # session.commit()
    # response_fields = [
    #     DynamicField(model_id=response_model.id, field_name="sentiment", field_type="integer"),
    #     DynamicField(model_id=response_model.id, field_name="reason", field_type="string"),
    # ]
    # session.add_all(response_fields)
    # session.commit()
