# LLM Classifier Framework

A generic text classification framework using Gemini 2.0 Flash in JSON mode. Customize the input models, output schema, and data sources to adapt to your classification needs.

## Quickstart

Before you begin, make sure you have the following installed:

1.  **uv**: This project uses `uv` for package management. Install it using the following command:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    See the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/) for more details.

2.  **Python**: Install Python using `uv`:
    ```bash
    uv python install
    ```

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/chriscarrollsmith/llm-classifier.git
    cd llm-classifier
    ```

2.  Install the project dependencies using `uv`:
    ```bash
    uv sync
    ```

2. Create `.env`:
```
GEMINI_API_KEY=your_key_here
DB_PATH=classifications.db
CONCURRENCY_LIMIT=1
```

3. Implement your custom components in `prompt.py` and `main.py`

## ⚠️ Update: Dynamic User-Defined Models

> **Note:** The framework now supports dynamic, user-defined input models and prompt templates using an Entity-Attribute-Value (EAV) schema. The static `Input` class and `PROMPT_TEMPLATE` in `prompt.py` are **deprecated** and kept for legacy support only. See `main.py` and the `DynamicModel` logic for the new approach.

---

## Customization Guide

### 1. Define Dynamic Data Models (No longer in prompt.py)

Instead of hardcoding your input schema, you can now define new models and fields at runtime. These are stored in the database using the following EAV tables:

- `DynamicModel`: Represents a user-defined model (e.g., "BlogPost", "Tweet").
- `DynamicField`: Represents a field/attribute of a model (e.g., "title", "body").
- `DynamicValue`: Stores the actual user input for each field and model instance.

You can add new models and fields by interacting with the database (see `main.py` for example code).

### 2. Dynamic Prompt Template Generation

Prompt templates are now built dynamically at runtime based on the fields of the selected `DynamicModel`. The framework fetches the field names and values from the database and constructs the prompt accordingly. See the functions in `main.py` for details.

**Deprecated:**
```python
class Input(SQLModel, table=False):
    ...
PROMPT_TEMPLATE = "..."
```
Use the new dynamic system instead.

### 3. Collecting and Storing User Input

- The framework will prompt for input for each field of the selected model.
- Inputs are stored as `DynamicValue` entries in the database.

### 4. Example Usage in main.py

See `main.py` for example functions:
- Fetching model fields: `get_dynamic_model_fields(session, model_id)`
- Collecting user input: `collect_dynamic_input(fields)`
- Storing input: `store_dynamic_input(session, model_id, input_data)`
- Building a dynamic prompt: `build_dynamic_prompt(model_name, input_data)`

---

## Example Workflow (Updated)

1. Define new models and fields dynamically (no code changes needed for new input types).
2. Collect user input for the selected model.
3. Generate prompts dynamically based on the model's fields.
4. Process and classify data as before.

---

The rest of the framework (downloader, output processing, etc.) works as before, but now supports arbitrary user-defined input schemas.

For legacy support, the static `Input` and `PROMPT_TEMPLATE` remain in `prompt.py` but are deprecated.