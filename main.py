# main.py

import asyncio
import logging

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from datetime import date
    import requests
    from typing import override
    from sqlmodel import Session, select
    from sqlalchemy import inspect
    from llm_classifier.database import (
        init_database, seed_input_types, ClassificationInput, ClassificationResponse, InputType,
        DynamicModel, DynamicField, DynamicValue,
        get_dynamic_model_fields, collect_dynamic_input, store_dynamic_input, build_dynamic_prompt
    )
    from llm_classifier.downloader import download_data, Downloader
    from llm_classifier.classifier import process_single_input
    from llm_classifier.prompt import INPUT_FIELDS, RESPONSE_FIELDS, PROMPT_TEMPLATE, INPUT_MODEL_NAME, RESPONSE_MODEL_NAME, DynamicPrompt

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

    async def main() -> None:
        # Initialize database
        engine = init_database(os.getenv("DB_PATH", "data.db"))
        with Session(engine) as session:
            # --- Seed dynamic models, fields, and prompt from prompt.py constants ---
            # This block creates or updates the database records for user-defined models, fields, and prompt.
            try:
                model_name = INPUT_MODEL_NAME
                # Check if model already exists
                model = session.exec(select(DynamicModel).where(DynamicModel.name == model_name)).first()
                if not model:
                    model = DynamicModel(name=model_name, description="User-defined input model")
                    session.add(model)
                    session.commit()
                    print(f"Created DynamicModel: {model_name}")
                else:
                    print(f"DynamicModel '{model_name}' already exists, skipping creation.")
                # Add input fields if not present
                for field_name, field_type in INPUT_FIELDS:
                    exists = session.exec(
                        select(DynamicField).where(
                            (DynamicField.model_id == model.id) &
                            (DynamicField.field_name == field_name)
                        )
                    ).first()
                    if not exists:
                        session.add(DynamicField(model_id=model.id, field_name=field_name, field_type=field_type))
                        print(f"  Added field '{field_name}' to model '{model_name}'")
                    else:
                        print(f"  Field '{field_name}' already exists in model '{model_name}', skipping.")
                # Add response fields as a separate model (optional, for completeness)
                response_model_name = RESPONSE_MODEL_NAME
                response_model = session.exec(select(DynamicModel).where(DynamicModel.name == response_model_name)).first()
                if not response_model:
                    response_model = DynamicModel(name=response_model_name, description="User-defined response model")
                    session.add(response_model)
                    session.commit()
                    print(f"Created DynamicModel: {response_model_name}")
                else:
                    print(f"DynamicModel '{response_model_name}' already exists, skipping creation.")
                for field_name, field_type in RESPONSE_FIELDS:
                    exists = session.exec(
                        select(DynamicField).where(
                            (DynamicField.model_id == response_model.id) &
                            (DynamicField.field_name == field_name)
                        )
                    ).first()
                    if not exists:
                        session.add(DynamicField(model_id=response_model.id, field_name=field_name, field_type=field_type))
                        print(f"  Added field '{field_name}' to model '{response_model_name}'")
                    else:
                        print(f"  Field '{field_name}' already exists in model '{response_model_name}', skipping.")
                # Add prompt if not present
                prompt_exists = session.exec(
                    select(DynamicPrompt).where(
                        (DynamicPrompt.model_id == model.id) &
                        (DynamicPrompt.template == PROMPT_TEMPLATE)
                    )
                ).first()
                if not prompt_exists:
                    session.add(DynamicPrompt(
                        model_id=model.id,
                        name="User Prompt Template",
                        template=PROMPT_TEMPLATE,
                        description="User-defined prompt template."
                    ))
                    print(f"Added prompt template for model '{model_name}'")
                else:
                    print(f"Prompt template for model '{model_name}' already exists, skipping.")
                session.commit()
            except Exception as e:
                logging.exception(f"Error during seeding dynamic models: {e}")
            # --- End seeding dynamic models ---
            #
            # Note: Running this seeding logic multiple times will not create duplicates.
            
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

            # Classify inputs concurrently
            results = await asyncio.gather(*[process_single_input(input_id, PROMPT_TEMPLATE, ClassificationResponse, session) for input_id in ids])
            
            # Count successful classifications
            classified_count = sum(1 for result in results if result)
            print(f"Successfully classified {classified_count} inputs")

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

    asyncio.run(main())

