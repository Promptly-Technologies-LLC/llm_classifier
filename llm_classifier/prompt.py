# prompt.py

# --- User Customization Section ---
# Define your input fields, response fields, and prompt template here.
# These constants will be imported by main.py to create database records.

# Allowed field types
ALLOWED_FIELD_TYPES = {"string", "integer", "float", "boolean"}

# User-configurable model names
INPUT_MODEL_NAME = "PostInput"
RESPONSE_MODEL_NAME = "PostResponse"

# List of input fields (name, type)
INPUT_FIELDS = [
    ("title", "string"),
    ("body", "string"),
    ("user_id", "integer"),
    ("post_id", "integer"),
]

# List of response fields (name, type)
RESPONSE_FIELDS = [
    ("sentiment", "integer"),
    ("reason", "string"),
]

# Validate field types
for name, typ in INPUT_FIELDS + RESPONSE_FIELDS:
    if typ not in ALLOWED_FIELD_TYPES:
        raise ValueError(f"Invalid field type '{typ}' for field '{name}'. Allowed types: {ALLOWED_FIELD_TYPES}")

# Prompt template string
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
{{title}}

Post:
{{body}}
"""

# --- End of user customization section ---
