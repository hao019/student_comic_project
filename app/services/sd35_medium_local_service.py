import base64
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from PIL import Image


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
COMIC_DIR = BASE_DIR / "static" / "outputs" / "comic"
COMIC_DIR.mkdir(parents=True, exist_ok=True)

SD35_MEDIUM_LOCAL_URL = os.getenv("SD35_MEDIUM_LOCAL_URL", "http://127.0.0.1:7860/generate")
SD35_MEDIUM_LOCAL_MODEL = os.getenv("SD35_MEDIUM_LOCAL_MODEL", "stable-diffusion-3.5-medium")
SD35_MEDIUM_LOCAL_BACKEND = os.getenv("SD35_MEDIUM_LOCAL_BACKEND", "http").strip().lower()
SD35_MEDIUM_DIFFUSERS_MODEL_ID = os.getenv(
    "SD35_MEDIUM_DIFFUSERS_MODEL_ID",
    "stabilityai/stable-diffusion-3.5-medium",
)
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
SD35_MEDIUM_LOCAL_TIMEOUT = int(os.getenv("SD35_MEDIUM_LOCAL_TIMEOUT", "300"))
SD35_MEDIUM_LOCAL_WIDTH = int(os.getenv("SD35_MEDIUM_LOCAL_WIDTH", "1024"))
SD35_MEDIUM_LOCAL_HEIGHT = int(os.getenv("SD35_MEDIUM_LOCAL_HEIGHT", "1024"))
SD35_MEDIUM_LOCAL_STEPS = int(os.getenv("SD35_MEDIUM_LOCAL_STEPS", "30"))
SD35_MEDIUM_LOCAL_GUIDANCE = float(os.getenv("SD35_MEDIUM_LOCAL_GUIDANCE", "4.0"))
SD35_MEDIUM_LOCAL_SEED = os.getenv("SD35_MEDIUM_LOCAL_SEED", "").strip()
SD35_MEDIUM_LOCAL_MAX_SEQUENCE_LENGTH = int(os.getenv("SD35_MEDIUM_LOCAL_MAX_SEQUENCE_LENGTH", "512"))
SD35_MEDIUM_PANEL_TARGET_PIXELS = int(os.getenv("SD35_MEDIUM_PANEL_TARGET_PIXELS", "1048576"))
SD35_MEDIUM_PANEL_MAX_SIDE = int(os.getenv("SD35_MEDIUM_PANEL_MAX_SIDE", "1408"))
SD35_MEDIUM_PANEL_MIN_SIDE = int(os.getenv("SD35_MEDIUM_PANEL_MIN_SIDE", "512"))
SD35_MEDIUM_PANEL_MAX_ASPECT = float(os.getenv("SD35_MEDIUM_PANEL_MAX_ASPECT", "3.0"))
SD35_MEDIUM_CLIP_NEGATIVE_PROMPT = os.getenv(
    "SD35_MEDIUM_CLIP_NEGATIVE_PROMPT",
    "text, writing, logo, watermark, signature, speech bubble, text box, blurry, low detail, bad hands",
)
SD35_MEDIUM_NEGATIVE_PROMPT = os.getenv(
    "SD35_MEDIUM_NEGATIVE_PROMPT",
    (
        "readable text, fake letters, gibberish writing, random Chinese characters, random Japanese characters, "
        "random English text, logo, watermark, signature, speech bubble, word balloon, caption box, "
        "title bar, UI screenshot, cluttered layout, cropped subject, close-up headshot, blurry, low detail, "
        "muddy colors, distorted face, deformed hands, extra fingers, bad anatomy, unfinished sketch"
    ),
)

_DIFFUSERS_PIPE = None


class SD35MediumLocalError(RuntimeError):
    pass


def _split_sd35_prompts(prompt: str) -> tuple[str, str]:
    prompt = (prompt or "").strip()
    if not prompt:
        return "", ""

    clip_marker = "CLIP prompt:"
    t5_marker = "T5 prompt:"
    if clip_marker in prompt and t5_marker in prompt:
        clip_start = prompt.index(clip_marker) + len(clip_marker)
        t5_start = prompt.index(t5_marker)
        clip_prompt = prompt[clip_start:t5_start].strip()
        t5_prompt = prompt[t5_start + len(t5_marker):].strip()
    else:
        lines = [line.strip() for line in prompt.splitlines() if line.strip()]
        clip_prompt = lines[0] if lines else prompt
        t5_prompt = prompt

    clip_words = clip_prompt.split()
    if len(clip_words) > 65:
        clip_prompt = " ".join(clip_words[:65])

    t5_prompt = _limit_t5_prompt(t5_prompt or clip_prompt)
    return clip_prompt, t5_prompt


def _limit_t5_prompt(prompt: str) -> str:
    words = str(prompt or "").split()
    max_words = max(120, min(320, int(SD35_MEDIUM_LOCAL_MAX_SEQUENCE_LENGTH * 0.58)))
    if len(words) <= max_words:
        return str(prompt or "").strip()
    return " ".join(words[:max_words]).rstrip(" ,.;:")


def _round_to_multiple(value: float, multiple: int = 64) -> int:
    return max(multiple, int(round(value / multiple)) * multiple)


def _resolve_generation_size(image_size: tuple[int, int] | None = None) -> tuple[int, int]:
    if not image_size:
        return SD35_MEDIUM_LOCAL_WIDTH, SD35_MEDIUM_LOCAL_HEIGHT

    source_w, source_h = image_size
    if source_w <= 0 or source_h <= 0:
        return SD35_MEDIUM_LOCAL_WIDTH, SD35_MEDIUM_LOCAL_HEIGHT

    aspect = source_w / source_h
    aspect = max(1 / SD35_MEDIUM_PANEL_MAX_ASPECT, min(SD35_MEDIUM_PANEL_MAX_ASPECT, aspect))
    width = (SD35_MEDIUM_PANEL_TARGET_PIXELS * aspect) ** 0.5
    height = width / aspect

    scale = min(SD35_MEDIUM_PANEL_MAX_SIDE / max(width, height), 1.0)
    width *= scale
    height *= scale

    if min(width, height) < SD35_MEDIUM_PANEL_MIN_SIDE:
        scale = SD35_MEDIUM_PANEL_MIN_SIDE / min(width, height)
        width *= scale
        height *= scale

    width = min(width, SD35_MEDIUM_PANEL_MAX_SIDE)
    height = min(height, SD35_MEDIUM_PANEL_MAX_SIDE)
    return _round_to_multiple(width), _round_to_multiple(height)


def _torch_device_and_dtype():
    try:
        import torch
    except ImportError as e:
        raise SD35MediumLocalError(
            "PyTorch is required for SD35_MEDIUM_LOCAL_BACKEND=diffusers. "
            "Install torch or use the HTTP backend."
        ) from e

    if torch.cuda.is_available():
        return "cuda", torch.bfloat16
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps", torch.float16
    return "cpu", torch.float32


def _get_diffusers_pipe():
    global _DIFFUSERS_PIPE

    if _DIFFUSERS_PIPE is not None:
        return _DIFFUSERS_PIPE

    try:
        from diffusers import StableDiffusion3Pipeline
    except ImportError as e:
        raise SD35MediumLocalError(
            "diffusers is required for SD35_MEDIUM_LOCAL_BACKEND=diffusers."
        ) from e

    device, dtype = _torch_device_and_dtype()
    try:
        pipe = StableDiffusion3Pipeline.from_pretrained(
            SD35_MEDIUM_DIFFUSERS_MODEL_ID,
            torch_dtype=dtype,
            token=HF_TOKEN,
        )
    except Exception as e:
        detail = str(e)
        if "GatedRepoError" in detail or "gated repo" in detail.lower() or "403" in detail:
            raise SD35MediumLocalError(
                "Cannot access SD3.5 Medium on Hugging Face. "
                "Open https://huggingface.co/stabilityai/stable-diffusion-3.5-medium, "
                "request/accept access with the same Hugging Face account used by HF_TOKEN, "
                "then restart the FastAPI server."
            ) from e
        raise SD35MediumLocalError(
            "Could not load SD3.5 Medium with diffusers. "
            f"Model id: {SD35_MEDIUM_DIFFUSERS_MODEL_ID}. "
            "Make sure the model is downloaded/cached and that Hugging Face access is configured "
            f"for stabilityai/stable-diffusion-3.5-medium. Detail: {detail}"
        ) from e

    try:
        pipe.enable_model_cpu_offload()
    except Exception:
        pipe.to(device)

    _DIFFUSERS_PIPE = pipe
    return _DIFFUSERS_PIPE


def _request_json(url: str, payload: dict) -> tuple[bytes, str]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json,image/png,image/jpeg,*/*",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=SD35_MEDIUM_LOCAL_TIMEOUT) as response:
            content_type = response.headers.get("content-type", "")
            return response.read(), content_type
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SD35MediumLocalError(f"Local SD3.5 Medium server returned HTTP {e.code}: {detail}") from e
    except URLError as e:
        raise SD35MediumLocalError(
            f"Cannot connect to local SD3.5 Medium server at {url}. Start your SD3.5 Medium server first."
        ) from e


def _fetch_image_url(image_url: str) -> bytes:
    if image_url.startswith("/"):
        image_url = urljoin(SD35_MEDIUM_LOCAL_URL, image_url)

    parsed = urlparse(image_url)
    if parsed.scheme in ("http", "https"):
        try:
            with urlopen(image_url, timeout=SD35_MEDIUM_LOCAL_TIMEOUT) as response:
                return response.read()
        except URLError as e:
            raise SD35MediumLocalError(f"Could not download local SD3.5 Medium image URL: {image_url}") from e

    image_path = Path(image_url)
    if not image_path.exists():
        raise SD35MediumLocalError(f"Local SD3.5 Medium response image path does not exist: {image_url}")
    return image_path.read_bytes()


def _decode_json_image(data: bytes) -> bytes:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SD35MediumLocalError("Local SD3.5 Medium server returned neither image bytes nor valid JSON.") from e

    for key in ("image_base64", "sample_base64"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            encoded = value.split(",", 1)[-1] if value.startswith("data:") else value
            return base64.b64decode(encoded)

    image_value = payload.get("image")
    if isinstance(image_value, str) and image_value.strip():
        if "://" in image_value or image_value.startswith("/") or (len(image_value) < 260 and Path(image_value).exists()):
            return _fetch_image_url(image_value)
        encoded = image_value.split(",", 1)[-1] if image_value.startswith("data:") else image_value
        return base64.b64decode(encoded)

    for key in ("image_url", "url", "sample", "output"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return _fetch_image_url(value)

    images = payload.get("images")
    if isinstance(images, list) and images:
        first_image = images[0]
        if isinstance(first_image, str):
            is_path_like = "://" in first_image or first_image.startswith("/") or (len(first_image) < 260 and Path(first_image).exists())
            return _fetch_image_url(first_image) if is_path_like else base64.b64decode(first_image)
        if isinstance(first_image, dict):
            for key in ("image_base64", "image", "url", "image_url"):
                value = first_image.get(key)
                if isinstance(value, str) and value.strip():
                    return _fetch_image_url(value) if key in ("url", "image_url") else base64.b64decode(value.split(",", 1)[-1])

    raise SD35MediumLocalError("Local SD3.5 Medium JSON response did not include an image.")


def _save_image(image_bytes: bytes, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from io import BytesIO

        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise SD35MediumLocalError("Local SD3.5 Medium response could not be opened as an image.") from e

    image.save(output_path)


def _generate_with_diffusers(prompt: str, output_path: Path, image_size: tuple[int, int] | None = None) -> None:
    try:
        import torch
    except ImportError as e:
        raise SD35MediumLocalError("PyTorch is required for diffusers SD3.5 Medium generation.") from e

    pipe = _get_diffusers_pipe()
    clip_prompt, t5_prompt = _split_sd35_prompts(prompt)
    width, height = _resolve_generation_size(image_size)
    generator = None
    if SD35_MEDIUM_LOCAL_SEED:
        try:
            seed = int(SD35_MEDIUM_LOCAL_SEED)
        except ValueError as e:
            raise SD35MediumLocalError("SD35_MEDIUM_LOCAL_SEED must be an integer.") from e
        generator = torch.Generator("cuda" if torch.cuda.is_available() else "cpu").manual_seed(seed)

    try:
        result = pipe(
            prompt=clip_prompt,
            prompt_2=clip_prompt,
            prompt_3=t5_prompt,
            negative_prompt=SD35_MEDIUM_CLIP_NEGATIVE_PROMPT,
            negative_prompt_2=SD35_MEDIUM_CLIP_NEGATIVE_PROMPT,
            negative_prompt_3=SD35_MEDIUM_NEGATIVE_PROMPT,
            width=width,
            height=height,
            num_inference_steps=SD35_MEDIUM_LOCAL_STEPS,
            guidance_scale=SD35_MEDIUM_LOCAL_GUIDANCE,
            num_images_per_prompt=1,
            generator=generator,
            max_sequence_length=SD35_MEDIUM_LOCAL_MAX_SEQUENCE_LENGTH,
        )
    except Exception as e:
        raise SD35MediumLocalError(f"SD3.5 Medium diffusers generation failed: {e}") from e

    image = result.images[0] if getattr(result, "images", None) else None
    if image is None:
        raise SD35MediumLocalError("SD3.5 Medium diffusers pipeline returned no image.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path)


def generate_image(
    prompt: str,
    output_path: Path,
    url_prefix: str,
    image_size: tuple[int, int] | None = None,
) -> str:
    if SD35_MEDIUM_LOCAL_BACKEND == "diffusers":
        _generate_with_diffusers(prompt, output_path, image_size=image_size)
        return f"{url_prefix}/{output_path.name}"

    clip_prompt, t5_prompt = _split_sd35_prompts(prompt)
    width, height = _resolve_generation_size(image_size)
    payload = {
        "prompt": clip_prompt,
        "prompt_2": clip_prompt,
        "prompt_3": t5_prompt,
        "negative_prompt": SD35_MEDIUM_CLIP_NEGATIVE_PROMPT,
        "negative_prompt_2": SD35_MEDIUM_CLIP_NEGATIVE_PROMPT,
        "negative_prompt_3": SD35_MEDIUM_NEGATIVE_PROMPT,
        "model": SD35_MEDIUM_LOCAL_MODEL,
        "width": width,
        "height": height,
        "num_inference_steps": SD35_MEDIUM_LOCAL_STEPS,
        "guidance_scale": SD35_MEDIUM_LOCAL_GUIDANCE,
        "num_images": 1,
    }
    data, content_type = _request_json(SD35_MEDIUM_LOCAL_URL, payload)

    if content_type.startswith("image/"):
        image_bytes = data
    else:
        image_bytes = _decode_json_image(data)

    _save_image(image_bytes, output_path)
    return f"{url_prefix}/{output_path.name}"


def generate_comic_page_image(prompt: str, filename: str, image_size: tuple[int, int] | None = None) -> str:
    return generate_image(
        prompt,
        output_path=COMIC_DIR / filename,
        url_prefix="/static/outputs/comic",
        image_size=image_size,
    )
