import os
from io import BytesIO
from pathlib import Path
from typing import Any

from google import genai
from google.genai import errors
from PIL import Image


BASE_DIR = Path(__file__).resolve().parents[2]
COMIC_DIR = BASE_DIR / "static" / "outputs" / "comic"
COMIC_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")

_CLIENT: Any | None = None


class GeminiImageGenerationError(RuntimeError):
    pass


def get_client() -> Any:
    global _CLIENT

    if _CLIENT is not None:
        return _CLIENT

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY is required for Gemini image generation.")

    _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT


def _response_parts(response: Any) -> list[Any]:
    parts = list(getattr(response, "parts", None) or [])
    if parts:
        return parts

    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        parts.extend(getattr(content, "parts", None) or [])

    return parts


def _part_to_image(part: Any) -> Image.Image | None:
    inline_data = getattr(part, "inline_data", None)
    if inline_data is None:
        return None

    if hasattr(part, "as_image"):
        return part.as_image()

    data = getattr(inline_data, "data", None)
    if not data:
        return None

    return Image.open(BytesIO(data)).convert("RGB")


def generate_image(prompt: str, output_path: Path, url_prefix: str) -> str:
    client = get_client()
    try:
        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=[prompt],
        )
    except errors.ClientError as e:
        message = str(e)
        status_code = getattr(e, "status_code", None)
        if status_code == 429 or "RESOURCE_EXHAUSTED" in message:
            raise GeminiImageGenerationError(
                f"Gemini image quota exhausted for model {GEMINI_IMAGE_MODEL}. "
                "Please check Google AI Studio billing/quota or try again later."
            ) from e
        raise GeminiImageGenerationError(
            f"Gemini image generation failed for model {GEMINI_IMAGE_MODEL}: {e}"
        ) from e
    except Exception as e:
        raise GeminiImageGenerationError(
            f"Gemini image generation failed for model {GEMINI_IMAGE_MODEL}: {e}"
        ) from e

    for part in _response_parts(response):
        image = _part_to_image(part)
        if image is None:
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return f"{url_prefix}/{output_path.name}"

    raise GeminiImageGenerationError("Gemini Image API returned no image data.")


def generate_comic_page_image(prompt: str, filename: str) -> str:
    return generate_image(
        prompt,
        output_path=COMIC_DIR / filename,
        url_prefix="/static/outputs/comic",
    )
