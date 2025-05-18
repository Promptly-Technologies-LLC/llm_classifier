# main.py

import asyncio

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from datetime import date
    import requests
    from typing import override
    from sqlmodel import Session, select
    from sqlalchemy import inspect
    from llm_classifier.database import init_database, seed_input_types, ClassificationInput, ClassificationResponse, InputType
    from llm_classifier.downloader import download_data, Downloader
    from llm_classifier.classifier import process_single_input
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

    async def main() -> None:
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