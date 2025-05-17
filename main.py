# main.py

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from datetime import date
    import requests
    from typing import override
    from sqlmodel import Session, select
    from sqlalchemy import inspect
    from llm_classifier.database import init_database, seed_input_types, ClassificationInput, ClassificationResponse, InputType, DynamicModel, DynamicField, DynamicValue
    from llm_classifier.downloader import download_data, Downloader
    from llm_classifier.classifier import classify_inputs
    from llm_classifier.prompt import PROMPT_TEMPLATE
    from llm_classifier.summarizer import print_summary_statistics, export_responses

    load_dotenv(override=True)

    class CustomDownloader(Downloader):
        """Define a custom download implementation by overriding either the
        `get_records` method (bulk download strategy) or the `get_record_ids`
        and `get_record` methods (per-record download strategy) of the
        `Downloader` class (see `downloader.py`)."""
        @classmethod
        @override
        def get_records(cls, input_type: InputType) -> list[ClassificationInput]:
            response = requests.get('https://jsonplaceholder.typicode.com/posts')
            response.raise_for_status()
            return [ClassificationInput(
                **record,
                processed_date=date.today(),
                input_type_id=input_type.id,
            ) for record in response.json()]

    # Initialize database
    engine = init_database(os.getenv("DB_PATH", "data.db"))

    with Session(engine) as session:
        INPUT_TYPES = ["Posts"]
        
        # Seed input types
        seed_input_types(session, input_types=INPUT_TYPES)
    
        # Select input types
        name_col = inspect(InputType).columns["name"]
        input_types = session.exec(
            select(InputType).where(name_col.in_(INPUT_TYPES))
        ).all()

        # Download inputs
        ids = download_data(
            session,
            input_types=input_types,
            downloader=CustomDownloader,
        )

        # Classify inputs
        classify_inputs(ids, PROMPT_TEMPLATE, ClassificationResponse, session)

        # Print summary statistics
        print_summary_statistics(
            session, numeric_field="sentiment", breakpoints=5
        )

        # Export findings to CSV
        export_responses(
            session,
            "responses.csv",
            input_fields=["id", "processed_date", "input_type", "title", "body"]
        )

    engine.dispose()

    def get_dynamic_model_fields(session, model_id):
        """Fetch fields for a given DynamicModel."""
        return session.exec(
            select(DynamicField).where(DynamicField.model_id == model_id)
        ).all()

    def collect_dynamic_input(fields):
        """Prompt user for input for each field (console input for demo)."""
        input_data = {}
        for field in fields:
            value = input(f"Enter value for {field.field_name} ({field.field_type}): ")
            input_data[field.field_name] = value
        return input_data

    def store_dynamic_input(session, model_id, user_id, input_data):
        """Store user input as DynamicValue entries."""
        fields = get_dynamic_model_fields(session, model_id)
        field_map = {f.field_name: f for f in fields}
        for name, value in input_data.items():
            field = field_map.get(name)
            if field:
                dv = DynamicValue(
                    model_id=model_id,
                    field_id=field.id,
                    value=str(value),
                    user_id=user_id
                )
                session.add(dv)
        session.commit()

    def build_dynamic_prompt(model, fields, values):
        """Build a prompt template dynamically from fields and values."""
        prompt = f"Input for model: {model.name}\n"
        for field in fields:
            val = values.get(field.field_name, "")
            prompt += f"{field.field_name}: {val}\n"
        return prompt

    # --- Example usage for dynamic models (commented out for demo) ---
    # with Session(engine) as session:
    #     # 1. Pick a dynamic model (replace 1 with your model's id)
    #     model_id = 1
    #     user_id = 123  # Replace with actual user id
    #     model = session.get(DynamicModel, model_id)
    #     fields = get_dynamic_model_fields(session, model_id)
    #     # 2. Collect user input for fields
    #     input_data = collect_dynamic_input(fields)
    #     # 3. Store input in DB
    #     store_dynamic_input(session, model_id, user_id, input_data)
    #     # 4. Build prompt for LLM
    #     prompt = build_dynamic_prompt(model, fields, input_data)
    #     print(prompt)