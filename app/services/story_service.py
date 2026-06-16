import json
import re
from pathlib import Path

from app.schemas import NewsComicPageScript
from app.services.google_llm_service import generate_news_comic_page_script
from app.services.google_news_service import fetch_random_google_focus_article
from app.services.image_generation_service import get_image_model, generate_comic_page_image
from app.services.prompt_builder import build_page_prompt


BASE_DIR = Path(__file__).resolve().parents[2]
COMIC_DATA_DIR = BASE_DIR / "static" / "outputs" / "comic_data"
COMIC_DIR = BASE_DIR / "static" / "outputs" / "comic"
COMIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
COMIC_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILENAME_STEM_CHARS = 48


def _news_to_article_text(news) -> str:
    return f"{news.title}\n\n{news.content}".strip()


def _page_script_to_storyboard(script: NewsComicPageScript, source_article: str | None = None) -> dict:
    storyboard = script.model_dump()
    storyboard["theme"] = script.news_type
    storyboard["source_article"] = source_article or ""
    storyboard["allowed_facts"] = script.allowed_facts
    storyboard["locked_text_blocks"] = script.locked_text_blocks

    for panel in storyboard.get("panels", []):
        panel["panel"] = panel.get("panel_id")
        panel["scene"] = panel.get("visual")
        panel["characters"] = panel.get("characters") or []
        panel["emotion"] = script.tone
        panel["narration"] = panel.get("main_text")
        speech = panel.get("speech") or []
        panel["dialogue"] = speech[0] if speech else panel.get("main_text")
        panel.setdefault("image_url", None)
        panel.setdefault("image_error", None)

    return storyboard


def _safe_filename_stem(title: str | None, fallback: str = "新聞漫畫") -> str:
    stem = str(title or "").strip() or fallback
    stem = re.sub(r"\s+", "_", stem)
    stem = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem).strip("._- ")
    if not stem:
        stem = fallback
    return stem[:MAX_FILENAME_STEM_CHARS].rstrip("._- ") or fallback


def _unique_comic_filename(title: str | None) -> str:
    base = _safe_filename_stem(title)
    candidate = f"{base}.png"
    index = 2

    while (COMIC_DIR / candidate).exists() or (COMIC_DATA_DIR / f"{Path(candidate).stem}.json").exists():
        candidate = f"{base}_{index}.png"
        index += 1

    return candidate


def _save_storyboard_for_comic(storyboard: dict, comic_url: str) -> None:
    filename = Path(str(comic_url or "")).name
    data_path = COMIC_DATA_DIR / f"{Path(filename).stem}.json"
    data_path.write_text(
        json.dumps(storyboard, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def generate_full_comic_from_news(news, generation_settings=None, source_article=None):
    article_text = source_article or _news_to_article_text(news)
    script = generate_news_comic_page_script(article_text)
    prompt = build_page_prompt(script, generation_settings)
    comic_filename = _unique_comic_filename(script.title)
    comic_url = generate_comic_page_image(prompt, comic_filename, generation_settings)

    storyboard = _page_script_to_storyboard(script, article_text)
    storyboard["generation_settings"] = generation_settings.model_dump() if generation_settings else {}
    storyboard["image_model"] = get_image_model(generation_settings)
    storyboard["comic_page_url"] = comic_url
    storyboard["comic_scroll_url"] = comic_url
    storyboard["comic_page_urls"] = [comic_url]
    storyboard["panel_urls"] = []
    storyboard["page_prompt"] = prompt
    storyboard["comic_error"] = None
    _save_storyboard_for_comic(storyboard, comic_url)
    return storyboard


def generate_random_sample_article() -> dict:
    sample = fetch_random_google_focus_article()
    title = str(sample.get("title") or "隨機焦點新聞").strip()
    article = str(sample.get("article") or "").strip()

    if not article:
        raise ValueError("Google News returned an empty article.")

    return {
        **sample,
        "title": title,
        "article": article,
    }
