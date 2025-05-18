# test_classifier.py live API integration tests
# run with: uv run pytest -m live

from dotenv import load_dotenv
import pytest
import base64
import io
import asyncio
from PIL import Image
from pydantic import BaseModel
from sqlmodel import Session, select
from llm_classifier.classifier import classify_input, process_single_input
from llm_classifier.database import ClassificationInput, ClassificationResponse

load_dotenv(override=True)

@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create a simple 1-pixel test image as bytes."""
    img = Image.new('RGB', (1, 1), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


@pytest.fixture
def sample_input_with_image(test_session: Session, sample_image_bytes: bytes) -> ClassificationInput:
    """Create a sample input with an image attached."""
    input_with_image = ClassificationInput(
        input_text="Google's revenue is up 10% this quarter.",
        extra_field="Profitability increased by 5%",
        bytes_field=sample_image_bytes
    )
    test_session.add(input_with_image)
    test_session.commit()
    return input_with_image


@pytest.fixture
def sample_input_without_media(test_session: Session) -> ClassificationInput:
    """Create a sample input without media."""
    input_without_media = ClassificationInput(
        input_text="Apple's revenue is up 15% this quarter.",
        extra_field="Profitability increased by 10%"
    )
    test_session.add(input_without_media)
    test_session.commit()
    return input_without_media


@pytest.mark.live
@pytest.mark.asyncio
async def test_classify_input_without_media() -> None:
    """Test the classify_input function without media data."""
    # Test prompt that mentions the image
    test_prompt = (
        "Classify the sentiment of this emoji on a scale from 1 (negative) to 5 (positive): :)\n"
        "Return your response as JSON with a string 'reason' field and an integer 'sentiment' field."
    )
    class ResponseModel(BaseModel):
        reason: str
        sentiment: int

    # Call classify_input with the media data
    result = await classify_input(test_prompt, ResponseModel, None)

    # Verify we got a valid response
    assert result is not None
    assert isinstance(result, ResponseModel)
    assert result.reason
    assert result.sentiment


@pytest.mark.live
@pytest.mark.asyncio
async def test_gather_classified_inputs_without_media(test_session: Session, sample_input_without_media: ClassificationInput, mock_prompt_template: str) -> None:
    """Test that process_single_input function works with `asyncio.gather` an input without media."""
    # Get the ID of the sample input
    input_id = sample_input_without_media.id
    assert input_id is not None

    await asyncio.gather(*[process_single_input(id, mock_prompt_template, ClassificationResponse, test_session) for id in [input_id]])

    # Verify the result
    result = test_session.exec(
        select(ClassificationResponse)
        .where(ClassificationResponse.input_id == input_id)
    ).first()

    assert result is not None
    assert isinstance(result, ClassificationResponse)
    assert result.most_investable_insight
    assert result.reason_its_investable
    assert isinstance(result.score, int)


@pytest.mark.live
@pytest.mark.asyncio
async def test_classify_input_with_media() -> None:
    """Test the classify_input function with media data."""
    # Create a simple test image
    img = Image.new('RGB', (1, 1), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    # Encode the image as base64 with data URL format
    encoded_image = f"data:image/png;base64,{base64.b64encode(img_bytes).decode('utf-8')}"

    # Test prompt that mentions the image
    test_prompt = (
        "Classify the sentiment of this image on a scale from 1 "
        "(cold) to 5 (hot) based on the color. The image is a "
        "1-pixel square. Return your response as JSON with a "
        "string 'reason' field and an integer 'sentiment' field."
    )

    class ResponseModel(BaseModel):
        reason: str
        sentiment: int

    # Call classify_input with the media data
    result = await classify_input(test_prompt, ResponseModel, [encoded_image])

    # Verify we got a valid response
    assert result is not None
    assert isinstance(result, ResponseModel)
    assert result.reason
    assert result.sentiment


@pytest.mark.live
@pytest.mark.asyncio
async def test_gather_classified_inputs_with_media(test_session: Session, sample_input_with_image: ClassificationInput, mock_prompt_template: str) -> None:
    """Test that process_single_input function works with `asyncio.gather` an input with media."""
    # Get the ID of the sample input
    input_id = sample_input_with_image.id
    assert input_id is not None

    await asyncio.gather(*[process_single_input(id, mock_prompt_template, ClassificationResponse, test_session) for id in [input_id]])

    # Verify the result
    result = test_session.exec(
        select(ClassificationResponse)
        .where(ClassificationResponse.input_id == input_id)
    ).first()

    assert result is not None
    assert isinstance(result, ClassificationResponse)
    assert result.most_investable_insight
    assert result.reason_its_investable
    assert isinstance(result.score, int)