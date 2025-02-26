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

## Customization Guide

### 1. Define Data Models (`prompt.py`)

```python
class Input(SQLModel, table=False):
    """Custom fields for your input data"""
    title: str
    body: str
    author: str

class Response(SQLModel, table=False):
    """Define your classification schema"""
    key_insight: str
    severity: int
    category: str
```

### 2. Create Prompt Template (`prompt.py`)

Requirements:

- All required `Input` fields must be present as `{placeholder}` variables
- Include example JSON matching your `Response` model
- Provide clear formatting and classification instructions

```python
PROMPT_TEMPLATE = """
Analyze this post from {author}:

{title}
{body}

Return JSON with:

- "key_insight" (most important finding)
- "severity" (1-10)
- "category" (most relevant topic)

Example:
{{
    "key_insight": "Example insight",
    "severity": 7,
    "category": "Technology"
}}
"""
```

### 3. Configure Input Types (`main.py`)

In `main.py`, define the document types to process:

```python
seed_input_types(session, input_types=["Blogs", "Tweets"])
```

There must be at least one input type.

### 4. Implement Data Downloader (`main.py`)

Choose a strategy based on your API:

**Bulk Download Approach:**
```python
class CustomDownloader(Downloader):
    @classmethod
    @override
    def get_records(cls, input_type: InputType) -> list[ClassificationInput]:
        response = requests.get('https://api.example.com/data')
        return [ClassificationInput(
            body=item["content"],
            title=item["title"],
            author=item["author"],
            input_type_id=input_type.id
        ) for item in response.json()]
```

**Per-Record Approach:**
```python
class CustomDownloader(Downloader):
    @classmethod
    @override
    def get_record_ids(cls, input_type) -> list[int]:
        ids = requests.get('https://api.example.com/items/list').json()
        return ids

    @classmethod
    @override 
    def get_record(cls, record_id: int) -> ClassificationInput:
        item = requests.get(f'https://api.example.com/items/{record_id}').json()
        return ClassificationInput(
            body=item["content"],
            title=item["title"],
            author=item["author"],
            input_type_id=input_type.id
        )
```

### 5. Customize Output Processing

**Summarization:**

To use `print_summary_statistics`, you must have at least one numeric field in your `Response` model. Otherwise, you should delete or comment out the `print_summary_statistics` call in `main.py`.

```python
print_summary_statistics(
    session, 
    numeric_field="severity",  # Name of your numeric response field
    breakpoints=4  # Percentile scale breakpoints (e.g., 4 prints quartiles)
)
```

**Export Filtering:**

To filter exported responses, you may optionally add a list of SQLAlchemy expressions to the `where_clauses` argument of the `export_responses` function. Each clause should be an expression that filters the responses. In the `input_fields` argument, you should specify any fields from the `Input` model that you want to include with the `Response` data in the exported CSV.

```python
from sqlalchemy import and_

export_responses(
    session,
    "results.csv",
    where_clauses=[
        ClassificationResponse.severity >= 7,
        ClassificationResponse.category == "Security"
    ],
    input_fields=["id", "processed_date", "title"]
)
```

## Example Workflow

The `prompt.py` and `main.py` files in this repo contain an example implementation of the framework that downloads and processes data from the public [JSONPlaceholder API](https://jsonplaceholder.typicode.com/). To use the framework for your own classification needs, follow these steps:

1. Change the `Input` and `Response` models to match your use case
2. Create a prompt template with required placeholders
3. Implement a data downloader for your API
4. Configure input types in `main.py`
5. Customize export filters and summary fields

The framework handles:

- Database management
- Parallel LLM API calls with rate limiting and retries
- Response parsing and validation