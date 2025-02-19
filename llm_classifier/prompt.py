# prompt.py

from typing import Optional
from sqlmodel import SQLModel

# --- Data models ---

class Input(SQLModel, table=False):
    """Defines additional fields to include in the input table besides the
    default id and processed_date fields."""
    title: str
    body: str
    user_id: Optional[int] = None
    post_id: Optional[int] = None

class Response(SQLModel, table=False):
    """Defines additional fields to include in the response table besides the
    default id field."""
    sentiment: int
    reason: str

# --- Prompt template ---

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
