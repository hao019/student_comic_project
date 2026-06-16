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

FLUX_KONTEXT_LOCAL_URL = os.getenv("FLUX_KONTEXT_LOCAL_URL", "http://127.0.0.1:7860/generate")
FLUX_KONTEXT_LOCAL_MODEL = os.getenv("FLUX_KONTEXT_LOCAL_MODEL", "flux.1-kontext-dev")
FLUX_KONTEXT_LOCAL_BACKEND = os.getenv("FLUX_KONTEXT_LOCAL_BACKEND", "http").strip().lower()
FLUX_KONTEXT_DIFFUSERS_MODEL_ID = os.getenv(
    "FLUX_KONTEXT_DIFFUSERS_MODEL_ID",
    "black-forest-labs/FLUX.1-Kontext-dev",
)
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
FLUX_KONTEXT_LOCAL_TIMEOUT = int(os.getenv("FLUX_KONTEXT_LOCAL_TIMEOUT", "300"))
FLUX_KONTEXT_LOCAL_WIDTH = int(os.getenv("FLUX_KONTEXT_LOCAL_WIDTH", "1024"))
FLUX_KONTEXT_LOCAL_HEIGHT = int(os.getenv("FLUX_KONTEXT_LOCAL_HEIGHT", "1024"))
FLUX_KONTEXT_LOCAL_STEPS = int(os.getenv("FLUX_KONTEXT_LOCAL_STEPS", "28"))
FLUX_KONTEXT_LOCAL_GUIDANCE = float(os.getenv("FLUX_KONTEXT_LOCAL_GUIDANCE", "3.5"))
FLUX_KONTEXT_LOCAL_SEED = os.getenv("FLUX_KONTEXT_LOCAL_SEED", "").strip()
FLUX_KONTEXT_LOCAL_MAX_SEQUENCE_LENGTH = int(os.getenv("FLUX_KONTEXT_LOCAL_MAX_SEQUENCE_LENGTH", "512"))

_DIFFUSERS_PIPE = None


class FluxKontextLocalError(RuntimeError):
    pass


def _torch_device_and_dtype():
    try:
        import torch
    except ImportError as e:
        raise FluxKontextLocalError(
            "PyTorch is required for FLUX_KONTEXT_LOCAL_BACKEND=diffusers. "
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
        from diffusers import FluxKontextPipeline
    except ImportError as e:
        raise FluxKontextLocalError(
            "diffusers is required for FLUX_KONTEXT_LOCAL_BACKEND=diffusers."
        ) from e

    device, dtype = _torch_device_and_dtype()
    try:
        pipe = FluxKontextPipeline.from_pretrained(
            FLUX_KONTEXT_DIFFUSERS_MODEL_ID,
            torch_dtype=dtype,
            token=HF_TOKEN,
        )
    except Exception as e:
        raise FluxKontextLocalError(
            "Could not load FLUX.1 Kontext [dev] with diffusers. "
            f"Model id: {FLUX_KONTEXT_DIFFUSERS_MODEL_ID}. "
            "Make sure the model is downloaded/cached and that Hugging Face access is configured "
            "for black-forest-labs/FLUX.1-Kontext-dev."
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
        with urlopen(request, timeout=FLUX_KONTEXT_LOCAL_TIMEOUT) as response:
            content_type = response.headers.get("content-type", "")
            return response.read(), content_type
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise FluxKontextLocalError(f"Local FLUX server returned HTTP {e.code}: {detail}") from e
    except URLError as e:
        raise FluxKontextLocalError(
            f"Cannot connect to local FLUX server at {url}. Start your FLUX.1 Kontext [dev] server first."
        ) from e


def _fetch_image_url(image_url: str) -> bytes:
    if image_url.startswith("/"):
        image_url = urljoin(FLUX_KONTEXT_LOCAL_URL, image_url)

    parsed = urlparse(image_url)
    if parsed.scheme in ("http", "https"):
        try:
            with urlopen(image_url, timeout=FLUX_KONTEXT_LOCAL_TIMEOUT) as response:
                return response.read()
        except URLError as e:
            raise FluxKontextLocalError(f"Could not download local FLUX image URL: {image_url}") from e

    image_path = Path(image_url)
    if not image_path.exists():
        raise FluxKontextLocalError(f"Local FLUX response image path does not exist: {image_url}")
    return image_path.read_bytes()


def _decode_json_image(data: bytes) -> bytes:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise FluxKontextLocalError("Local FLUX server returned neither image bytes nor valid JSON.") from e

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

    raise FluxKontextLocalError("Local FLUX JSON response did not include an image.")


def _save_image(image_bytes: bytes, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from io import BytesIO

        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise FluxKontextLocalError("Local FLUX response could not be opened as an image.") from e

    image.save(output_path)


def _generate_with_diffusers(prompt: str, output_path: Path) -> None:
    try:
        import torch
    except ImportError as e:
        raise FluxKontextLocalError("PyTorch is required for diffusers FLUX generation.") from e

    pipe = _get_diffusers_pipe()
    generator = None
    if FLUX_KONTEXT_LOCAL_SEED:
        try:
            seed = int(FLUX_KONTEXT_LOCAL_SEED)
        except ValueError as e:
            raise FluxKontextLocalError("FLUX_KONTEXT_LOCAL_SEED must be an integer.") from e
        generator = torch.Generator("cuda" if torch.cuda.is_available() else "cpu").manual_seed(seed)

    try:
        result = pipe(
            prompt=prompt,
            width=FLUX_KONTEXT_LOCAL_WIDTH,
            height=FLUX_KONTEXT_LOCAL_HEIGHT,
            num_inference_steps=FLUX_KONTEXT_LOCAL_STEPS,
            guidance_scale=FLUX_KONTEXT_LOCAL_GUIDANCE,
            num_images_per_prompt=1,
            generator=generator,
            max_sequence_length=FLUX_KONTEXT_LOCAL_MAX_SEQUENCE_LENGTH,
        )
    except Exception as e:
        raise FluxKontextLocalError(f"FLUX diffusers generation failed: {e}") from e

    image = result.images[0] if getattr(result, "images", None) else None
    if image is None:
        raise FluxKontextLocalError("FLUX diffusers pipeline returned no image.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path)


def generate_image(prompt: str, output_path: Path, url_prefix: str) -> str:
    if FLUX_KONTEXT_LOCAL_BACKEND == "diffusers":
        _generate_with_diffusers(prompt, output_path)
        return f"{url_prefix}/{output_path.name}"

    payload = {
        "prompt": prompt,
        "model": FLUX_KONTEXT_LOCAL_MODEL,
        "width": FLUX_KONTEXT_LOCAL_WIDTH,
        "height": FLUX_KONTEXT_LOCAL_HEIGHT,
        "num_images": 1,
    }
    data, content_type = _request_json(FLUX_KONTEXT_LOCAL_URL, payload)

    if content_type.startswith("image/"):
        image_bytes = data
    else:
        image_bytes = _decode_json_image(data)

    _save_image(image_bytes, output_path)
    return f"{url_prefix}/{output_path.name}"


def generate_comic_page_image(prompt: str, filename: str) -> str:
    return generate_image(
        prompt,
        output_path=COMIC_DIR / filename,
        url_prefix="/static/outputs/comic",
    )
