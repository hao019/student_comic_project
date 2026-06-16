from pathlib import Path

from app.services.flux_kontext_local_service import generate_comic_page_image as generate_flux_kontext_local
from app.services.gemini_image_service import (
    GeminiImageGenerationError,
    generate_comic_page_image as generate_gemini_image,
)


class ImageGenerationError(RuntimeError):
    pass


def get_image_model(generation_settings=None) -> str:
    if generation_settings is None:
        return "gemini_image"
    return getattr(generation_settings, "image_model", "gemini_image") or "gemini_image"


def generate_comic_page_image(prompt: str, filename: str, generation_settings=None) -> str:
    image_model = get_image_model(generation_settings)

    try:
        if image_model == "flux_kontext_local":
            return generate_flux_kontext_local(prompt, filename)
        return generate_gemini_image(prompt, filename)
    except GeminiImageGenerationError as e:
        raise ImageGenerationError(str(e)) from e
    except ImageGenerationError:
        raise
    except Exception as e:
        model_label = image_model.replace("_", " ")
        raise ImageGenerationError(f"{model_label} image generation failed: {e}") from e


def get_comic_path_from_url(comic_url: str, base_dir: Path) -> Path:
    filename = Path(str(comic_url or "")).name
    return base_dir / "static" / "outputs" / "comic" / filename
