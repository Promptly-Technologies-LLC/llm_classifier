# main.py

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from datetime import date
    import requests
    from typing import override
    from sqlmodel import Session
    from llm_classifier.database import init_database, seed_input_types, ClassificationInput, ClassificationResponse, InputType
    from llm_classifier.downloader import download_data, Downloader
    from llm_classifier.classifier import classify_inputs
    from llm_classifier.prompt import PROMPT_TEMPLATE
    from llm_classifier.summarizer import print_summary_statistics, export_responses

    load_dotenv(override=True)

    class CustomDownloader(Downloader):
        """Define a custom download implementation by overriding either the
        `get_records` method (bulk download strategy) or the `get_record_ids`
        and `download_record` methods (per-record download strategy) of the
        `Downloader` class (see `downloader.py`)."""
        @classmethod
        @override
        def get_records(cls, input_type: InputType) -> list[ClassificationInput]:
            response = requests.get('https://jsonplaceholder.typicode.com/posts')
            response.raise_for_status()
            return [ClassificationInput(
                **record,
                processed_date=date.today(),
                input_type=input_type,
            ) for record in response.json()]

    # Initialize database
    engine = init_database(os.getenv("DB_PATH", "data.db"))

    with Session(engine) as session:
        # Seed input types
        seed_input_types(session, input_types=["Posts"])

        # Download inputs
        ids = download_data(
            session,
            input_types=["Posts"],
            downloader=CustomDownloader,
        )

        # Classify inputs
        classify_inputs(ids, PROMPT_TEMPLATE, ClassificationResponse, session)

        # Print summary statistics
        print_summary_statistics(session, numeric_field="sentiment")

        # Export findings to CSV
        export_responses(session, "responses.csv", numeric_field="sentiment")

    engine.dispose()