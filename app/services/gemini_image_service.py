import os
import base64
from io import BytesIO
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from google.genai import errors
from PIL import Image


BASE_DIR = Path(__file__).resolve().parents[2]
COMIC_DIR = BASE_DIR / "static" / "outputs" / "comic"
COMIC_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_IMAGE_MODEL = "gemini-3-pro-image-preview"
PRIMARY_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", DEFAULT_IMAGE_MODEL)
EXTRA_IMAGE_MODELS = [
    model.strip()
    for model in os.getenv("GEMINI_IMAGE_FALLBACK_MODELS", "").split(",")
    if model.strip()
]
IMAGE_MODELS = list(dict.fromkeys([
    PRIMARY_IMAGE_MODEL,
    "gemini-3.1-flash-image-preview",
    *EXTRA_IMAGE_MODELS,
]))

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

    outputs = list(getattr(response, "outputs", None) or [])
    if outputs:
        return outputs

    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        parts.extend(getattr(content, "parts", None) or [])

    return parts


def _part_to_image(part: Any) -> Image.Image | None:
    data = getattr(part, "data", None)
    if data:
        return Image.open(BytesIO(base64.b64decode(data))).convert("RGB")

    inline_data = getattr(part, "inline_data", None)
    if inline_data is None:
        return None

    if hasattr(part, "as_image"):
        return part.as_image()

    data = getattr(inline_data, "data", None)
    if not data:
        return None

    return Image.open(BytesIO(data)).convert("RGB")


def _generate_image_response(client: Any, model_name: str, prompt: str) -> Any:
    return client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )


def generate_image(prompt: str, output_path: Path, url_prefix: str) -> str:
    client = get_client()
    last_error: Exception | None = None

    for model_name in IMAGE_MODELS:
        try:
            response = _generate_image_response(client, model_name, prompt)

            for part in _response_parts(response):
                image = _part_to_image(part)
                if image is None:
                    continue

                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(output_path)
                return f"{url_prefix}/{output_path.name}"

            last_error = GeminiImageGenerationError(
                f"Gemini Image API returned no image data for model {model_name}."
            )
            print(last_error)
        except errors.ClientError as e:
            print(f"Gemini image generation failed: {model_name}")
            print(e)
            last_error = e
        except Exception as e:
            print(f"Gemini image generation failed: {model_name}")
            print(e)
            last_error = e

    raise GeminiImageGenerationError(
        f"Gemini image generation failed after fallback models: {last_error}"
    )


def generate_comic_page_image(prompt: str, filename: str) -> str:
    return generate_image(
        prompt,
        output_path=COMIC_DIR / filename,
        url_prefix="/static/outputs/comic",
    )
