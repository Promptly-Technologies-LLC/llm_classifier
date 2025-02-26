# classifier.py

import os
import dotenv
import asyncio
import nest_asyncio
from typing import Type, TypeVar, Sequence
from litellm import acompletion, RateLimitError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from sqlmodel import Session, select

from llm_classifier.database import ClassificationInput, ClassificationResponse
from llm_classifier.validators import get_placeholders
from llm_classifier.parser import get_model_from_json, get_gemini_schema


# --- Constants ---

dotenv.load_dotenv(override=True)
T = TypeVar('T', bound=BaseModel)


# --- Functions ---

# Allow asyncio to run in nested loops
nest_asyncio.apply()


def get_concurrency_limit() -> int:
    """Returns the CONCURRENCY_LIMIT environment variable, or 1 if not set."""
    return int(os.getenv("CONCURRENCY_LIMIT", 1))


def should_retry_error(exception: BaseException) -> bool:
    if isinstance(exception, RateLimitError):
        return True
    return False


@retry(
    retry=retry_if_exception(should_retry_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def classify_text(prompt: str, model_class: Type[T]) -> T | None:
    """Classify a single text using the LLM with retry logic."""
    try:

        async with asyncio.Semaphore(get_concurrency_limit()):
            response = await acompletion(
                model="gemini/gemini-2.0-flash-exp",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object", "response_schema": get_gemini_schema(model_class)}
            )
        return get_model_from_json(response['choices'][0]['message']['content'], model_class)
    except Exception as e:
        print(f"Error during classification: {str(e)}")
        return None


async def process_single_input(input_id: int, prompt_template: str, model_class: Type[T], session: Session) -> None:
    """Process and persist classification for a single input"""
    input: ClassificationInput | None = session.exec(
        select(ClassificationInput)
        .where(ClassificationInput.id == input_id)
    ).first()

    if not input:
        raise ValueError(f"Input with id {input_id} not found")

    dynamic_placeholders = get_placeholders(prompt_template, type(input))
    format_args = {placeholder: getattr(input, placeholder) for placeholder in dynamic_placeholders}
    current_prompt = prompt_template.format(**format_args)

    result = await classify_text(current_prompt, model_class)

    if result:
        existing_input = session.exec(
            select(ClassificationResponse)
            .where(ClassificationResponse.input_id == input_id)
        ).first()

        if not existing_input:
            input.classification_response = ClassificationResponse(
                **result.model_dump()
            )
            session.add(input)
            session.commit()

def classify_inputs(input_ids: Sequence[int], prompt_template: str, model_class: Type[T], session: Session) -> None:
    """Classify a list of inputs, processing and persisting one at a time"""    
    async def process_all() -> None:
        for input_id in input_ids:
            try:
                await process_single_input(input_id, prompt_template, model_class, session)
            except Exception as e:
                print(f"Error processing input {input_id}: {e}")
    
    asyncio.run(process_all())

