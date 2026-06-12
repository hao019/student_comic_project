import json
import shutil
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.schemas import ArticleInput, NewsInput
from app.services.gemini_image_service import GeminiImageGenerationError
from app.services.story_service import generate_full_comic_from_news, generate_random_sample_article


app = FastAPI(title="AI Comic Demo Generator")

BASE_DIR = Path(__file__).resolve().parents[1]
APP_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/assets", StaticFiles(directory=str(APP_DIR / "static")), name="assets")


class ComicRenameInput(BaseModel):
    filename: str = Field(..., min_length=1, max_length=80)


def article_to_news_input(article: str) -> NewsInput:
    text = article.strip()
    title = next((line.strip() for line in text.splitlines() if line.strip()), "")
    title = title[:40] or "AI 新聞漫畫"

    content = text
    if len(content) < 10:
        content = f"{content}\n請根據這段文字整理成一則清楚的新聞漫畫。"

    return NewsInput(title=title, content=content)


def get_major_emotion(storyboard: dict) -> str:
    emotions = [
        panel.get("emotion")
        for panel in storyboard.get("panels", [])
        if panel.get("emotion")
    ]
    return Counter(emotions).most_common(1)[0][0] if emotions else "neutral"


def summarize_storyboard(storyboard: dict) -> str:
    title = storyboard.get("title") or "未命名漫畫"
    theme = storyboard.get("theme") or storyboard.get("news_type") or "新聞漫畫"
    return f"{title}｜{theme}"


def extract_source_article(storyboard: dict) -> str:
    for key in ("source_article", "original_article", "article"):
        text = str(storyboard.get(key) or "").strip()
        if text:
            return text
    return ""


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/comics/history")
def get_comic_history():
    comic_dir = BASE_DIR / "static" / "outputs" / "comic"
    comic_data_dir = BASE_DIR / "static" / "outputs" / "comic_data"

    if not comic_dir.exists():
        return {"comics": []}

    comics = []
    for image_path in comic_dir.glob("*.png"):
        stat = image_path.stat()
        data_path = comic_data_dir / f"{image_path.stem}.json"
        page_count = 1
        has_article = False

        if data_path.exists():
            try:
                storyboard = json.loads(data_path.read_text(encoding="utf-8"))
                page_urls = storyboard.get("comic_page_urls") or []
                page_count = max(1, len(page_urls))
                has_article = bool(extract_source_article(storyboard))
            except (json.JSONDecodeError, OSError):
                page_count = 1

        comics.append(
            {
                "filename": image_path.name,
                "url": f"/static/outputs/comic/{image_path.name}",
                "created_at": stat.st_mtime,
                "size": stat.st_size,
                "page_count": page_count,
                "editable": data_path.exists(),
                "has_article": has_article,
            }
        )

    comics.sort(key=lambda item: item["created_at"], reverse=True)
    return {"comics": comics}


def get_comic_path(filename: str) -> Path:
    if Path(filename).name != filename or not filename.lower().endswith(".png"):
        raise HTTPException(status_code=400, detail="Invalid comic filename.")

    comic_dir = (BASE_DIR / "static" / "outputs" / "comic").resolve()
    comic_path = (comic_dir / filename).resolve()

    if comic_dir not in comic_path.parents or not comic_path.exists():
        raise HTTPException(status_code=404, detail="Comic not found.")

    return comic_path


def get_comic_data_path(filename: str, must_exist: bool = True) -> Path:
    if Path(filename).name != filename or not filename.lower().endswith(".png"):
        raise HTTPException(status_code=400, detail="Invalid comic filename.")

    comic_data_dir = (BASE_DIR / "static" / "outputs" / "comic_data").resolve()
    comic_data_dir.mkdir(parents=True, exist_ok=True)
    data_path = (comic_data_dir / f"{Path(filename).stem}.json").resolve()

    if comic_data_dir not in data_path.parents:
        raise HTTPException(status_code=400, detail="Invalid comic filename.")

    if must_exist and not data_path.exists():
        raise HTTPException(status_code=404, detail="Editable storyboard not found.")

    return data_path


@app.get("/api/comics/{filename}/download")
def download_comic(filename: str):
    comic_path = get_comic_path(filename)
    return FileResponse(path=comic_path, filename=filename, media_type="image/png")


@app.get("/api/comics/{filename}/storyboard")
def get_comic_storyboard(filename: str):
    get_comic_path(filename)
    data_path = get_comic_data_path(filename)

    try:
        storyboard = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Storyboard data is corrupted.")

    return {"storyboard": storyboard}


@app.get("/api/comics/{filename}/article")
def get_comic_original_article(filename: str):
    get_comic_path(filename)
    data_path = get_comic_data_path(filename)

    try:
        storyboard = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Storyboard data is corrupted.")

    article = extract_source_article(storyboard)
    if not article:
        raise HTTPException(status_code=404, detail="No source article was saved for this comic.")

    return {
        "title": storyboard.get("title") or Path(filename).stem,
        "article": article,
    }


@app.delete("/api/comics/{filename}")
def delete_comic(filename: str):
    comic_path = get_comic_path(filename)
    data_path = get_comic_data_path(filename, must_exist=False)

    comic_path.unlink()
    if data_path.exists():
        data_path.unlink()

    return {"deleted": True, "filename": filename}


@app.patch("/api/comics/{filename}/rename")
@app.post("/api/comics/{filename}/rename")
def rename_comic(filename: str, data: ComicRenameInput):
    comic_path = get_comic_path(filename)
    new_name = data.filename.strip()

    if not new_name.lower().endswith(".png"):
        new_name = f"{new_name}.png"

    if Path(new_name).name != new_name or any(char in new_name for char in '\\/:*?"<>|'):
        raise HTTPException(status_code=400, detail="Invalid comic filename.")

    new_path = comic_path.with_name(new_name)
    old_data_path = get_comic_data_path(filename, must_exist=False)
    new_data_path = get_comic_data_path(new_name, must_exist=False)

    if new_path.exists() and new_path != comic_path:
        raise HTTPException(status_code=409, detail="A comic with that filename already exists.")

    try:
        comic_path.rename(new_path)
        if old_data_path.exists():
            old_data_path.rename(new_data_path)
    except PermissionError:
        try:
            shutil.copy2(comic_path, new_path)
            if old_data_path.exists():
                shutil.copy2(old_data_path, new_data_path)
            comic_path.unlink()
            if old_data_path.exists():
                old_data_path.unlink()
        except PermissionError:
            raise HTTPException(status_code=500, detail="Cannot rename this comic right now.")

    return {
        "renamed": True,
        "filename": new_name,
        "url": f"/static/outputs/comic/{new_name}",
    }


@app.get("/api/story/sample-article")
def get_sample_article():
    try:
        return generate_random_sample_article()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sample article generation failed: {e}")


@app.post("/api/story/generate-from-article")
def generate_story_from_article(data: ArticleInput):
    news = article_to_news_input(data.article)
    try:
        storyboard = generate_full_comic_from_news(
            news,
            generation_settings=data.generation_settings,
            source_article=data.article,
        )
    except GeminiImageGenerationError as e:
        raise HTTPException(status_code=503, detail=str(e))

    comic_image_url = storyboard.get("comic_page_url")
    return {
        "title": storyboard.get("title") or news.title,
        "summary": summarize_storyboard(storyboard),
        "emotion": get_major_emotion(storyboard),
        "comic_image_url": comic_image_url,
        "comic_page_urls": storyboard.get("comic_page_urls") or [comic_image_url],
        "comic_scroll_url": storyboard.get("comic_scroll_url") or comic_image_url,
        "story_fidelity_report": {},
        "storyboard": storyboard,
    }


@app.post("/api/story/generate-comic")
def generate_comic(data: ArticleInput):
    news = article_to_news_input(data.article)
    try:
        storyboard = generate_full_comic_from_news(
            news,
            generation_settings=data.generation_settings,
            source_article=data.article,
        )
    except GeminiImageGenerationError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "title": storyboard.get("title") or news.title,
        "script": {
            "title": storyboard.get("title"),
            "theme": storyboard.get("theme"),
            "panels": storyboard.get("panels", []),
        },
        "comic_url": storyboard.get("comic_page_url"),
        "panel_urls": storyboard.get("panel_urls") or [],
    }
