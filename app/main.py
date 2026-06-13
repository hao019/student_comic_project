import json
import os
import secrets
import shutil
import hashlib
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.schemas import ArticleInput, NewsInput
from app.services.gemini_image_service import GeminiImageGenerationError
from app.services.google_drive_service import (
    GoogleDriveConfigError,
    build_authorization_url,
    download_file_bytes,
    fetch_oauth_token,
    get_user_profile,
    is_google_oauth_configured,
    list_comic_bundles,
    upload_comic_bundle,
    write_drive_metadata,
)
from app.services.story_service import generate_full_comic_from_news, generate_random_sample_article


app = FastAPI(title="AI Comic Demo Generator")

BASE_DIR = Path(__file__).resolve().parents[1]
APP_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/assets", StaticFiles(directory=str(APP_DIR / "static")), name="assets")

SESSION_COOKIE = "student_comic_session"
GOOGLE_EMAIL_COOKIE = "student_comic_google_email"
SESSION_STORE: dict[str, dict] = {}
TOKEN_DIR = BASE_DIR / ".local" / "google_tokens"


class ComicRenameInput(BaseModel):
    filename: str = Field(..., min_length=1, max_length=80)


def get_session(request: Request) -> dict:
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        return load_single_saved_google_auth() or {}

    session = SESSION_STORE.get(session_id)
    if session is not None:
        return session

    session = {}
    email = request.cookies.get(GOOGLE_EMAIL_COOKIE)
    if email:
        saved_auth = load_saved_google_auth(email)
        if saved_auth:
            session.update(saved_auth)
    else:
        saved_auth = load_single_saved_google_auth()
        if saved_auth:
            session.update(saved_auth)

    SESSION_STORE[session_id] = session
    return session


def get_or_create_session_id(request: Request) -> str:
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id and session_id in SESSION_STORE:
        return session_id

    session_id = secrets.token_urlsafe(32)
    SESSION_STORE[session_id] = {}
    return session_id


def set_session_cookie(response: RedirectResponse, session_id: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        httponly=True,
        samesite="lax",
        secure=os.getenv("SESSION_COOKIE_SECURE", "").lower() == "true",
        max_age=60 * 60 * 24 * 14,
    )


def set_google_email_cookie(response, email: str) -> None:
    response.set_cookie(
        GOOGLE_EMAIL_COOKIE,
        email,
        httponly=True,
        samesite="lax",
        secure=os.getenv("SESSION_COOKIE_SECURE", "").lower() == "true",
        max_age=60 * 60 * 24 * 30,
    )


def token_file_for_email(email: str) -> Path:
    digest = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    return TOKEN_DIR / f"{digest}.json"


def save_google_auth(email: str, token_data: dict, profile: dict | None = None) -> None:
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "email": email,
        "google_token": token_data,
        "google_user": profile or {},
    }
    token_file_for_email(email).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_saved_google_auth(email: str) -> dict | None:
    path = token_file_for_email(email)
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    token_data = payload.get("google_token")
    if not isinstance(token_data, dict):
        return None

    return {
        "google_token": token_data,
        "google_user": payload.get("google_user") or {"email": email},
    }


def load_single_saved_google_auth() -> dict | None:
    if not TOKEN_DIR.exists():
        return None

    token_files = list(TOKEN_DIR.glob("*.json"))
    if len(token_files) != 1:
        return None

    try:
        payload = json.loads(token_files[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    email = str(payload.get("email") or "").strip()
    token_data = payload.get("google_token")
    if not email or not isinstance(token_data, dict):
        return None

    return {
        "google_token": token_data,
        "google_user": payload.get("google_user") or {"email": email},
    }


def clear_saved_google_auth(email: str | None) -> None:
    if not email:
        return

    path = token_file_for_email(email)
    if path.exists():
        path.unlink()


def google_redirect_uri(request: Request) -> str:
    configured_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if configured_uri:
        return configured_uri
    return str(request.url_for("google_auth_callback"))


def get_drive_paths(storyboard: dict) -> tuple[Path, Path | None]:
    comic_url = storyboard.get("comic_page_url") or storyboard.get("comic_scroll_url") or ""
    filename = Path(str(comic_url)).name
    if not filename:
        raise ValueError("Generated comic filename is missing.")

    comic_path = BASE_DIR / "static" / "outputs" / "comic" / filename
    storyboard_path = BASE_DIR / "static" / "outputs" / "comic_data" / f"{Path(filename).stem}.json"
    return comic_path, storyboard_path


def maybe_upload_storyboard_to_drive(request: Request, storyboard: dict) -> dict | None:
    session = get_session(request)
    token_data = session.get("google_token")
    if not token_data:
        return None

    comic_path, storyboard_path = get_drive_paths(storyboard)
    drive_upload = upload_comic_bundle(
        token_data,
        comic_path=comic_path,
        storyboard_path=storyboard_path,
    )
    session["google_token"] = drive_upload.pop("token_data")
    write_drive_metadata(storyboard_path, drive_upload)
    storyboard["drive_upload"] = drive_upload
    return drive_upload


def get_google_token_or_401(request: Request) -> dict:
    session = get_session(request)
    token_data = session.get("google_token")
    if not token_data:
        raise HTTPException(status_code=401, detail="Please sign in with Google first.")
    return token_data


def update_google_token(request: Request, token_data: dict | None) -> None:
    if not token_data:
        return
    session = get_session(request)
    if session:
        session["google_token"] = token_data
        email = (session.get("google_user") or {}).get("email")
        if email:
            save_google_auth(email, token_data, session.get("google_user"))


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


@app.get("/auth/google/login")
def google_login(request: Request):
    session_id = get_or_create_session_id(request)
    redirect_uri = google_redirect_uri(request)

    try:
        authorization_url, state, code_verifier = build_authorization_url(redirect_uri)
    except GoogleDriveConfigError as e:
        return HTMLResponse(
            """
            <!doctype html>
            <html lang="zh-Hant">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Google 登入尚未設定</title>
                <style>
                  body { margin: 0; min-height: 100vh; display: grid; place-items: center; color: #f8fafc; background: #080b12; font-family: "Microsoft JhengHei", Arial, sans-serif; }
                  main { width: min(36rem, calc(100% - 2rem)); border: 1px solid rgba(148, 163, 184, 0.24); border-radius: 8px; padding: 1.25rem; background: rgba(15, 23, 42, 0.94); }
                  h1 { margin: 0 0 0.75rem; font-size: 1.3rem; }
                  p, li { color: #cbd5e1; line-height: 1.7; }
                  code { color: #67e8f9; }
                  a { color: #5eead4; font-weight: 800; }
                </style>
              </head>
              <body>
                <main>
                  <h1>Google 登入尚未設定</h1>
                  <p>後端沒有讀到 <code>GOOGLE_CLIENT_ID</code> 和 <code>GOOGLE_CLIENT_SECRET</code>。</p>
                  <p>請到 Google Cloud Console 建立 OAuth 2.0 Web Client，並把下列設定加入 <code>.env</code>：</p>
                  <ul>
                    <li><code>GOOGLE_CLIENT_ID=...</code></li>
                    <li><code>GOOGLE_CLIENT_SECRET=...</code></li>
                    <li><code>GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback</code></li>
                  </ul>
                  <p>改完後重新啟動 FastAPI，再回來按 Google 登入。</p>
                  <p><a href="/">回首頁</a></p>
                </main>
              </body>
            </html>
            """,
            status_code=500,
        )

    SESSION_STORE[session_id]["oauth_state"] = state
    SESSION_STORE[session_id]["oauth_code_verifier"] = code_verifier
    response = RedirectResponse(authorization_url)
    set_session_cookie(response, session_id)
    return response


@app.get("/auth/google/callback", name="google_auth_callback")
def google_auth_callback(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)
    session = SESSION_STORE.get(session_id or "")
    if not session:
        raise HTTPException(status_code=400, detail="Login session expired. Please try again.")

    expected_state = session.get("oauth_state")
    actual_state = request.query_params.get("state")
    if not expected_state or expected_state != actual_state:
        raise HTTPException(status_code=400, detail="Invalid Google OAuth state.")

    code_verifier = session.get("oauth_code_verifier")
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Login session expired. Please try Google login again.")

    redirect_uri = google_redirect_uri(request)
    token_data = fetch_oauth_token(str(request.url), redirect_uri, expected_state, code_verifier)
    profile = get_user_profile(token_data)
    email = profile.get("email", "")

    session["google_token"] = token_data
    session["google_user"] = profile
    session.pop("oauth_state", None)
    session.pop("oauth_code_verifier", None)
    if email:
        save_google_auth(email, token_data, profile)

    response = RedirectResponse("/")
    set_session_cookie(response, session_id or get_or_create_session_id(request))
    if email:
        set_google_email_cookie(response, email)
    return response


@app.post("/auth/google/logout")
def google_logout(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)
    session = get_session(request)
    email = (session.get("google_user") or {}).get("email") or request.cookies.get(GOOGLE_EMAIL_COOKIE)
    if session_id:
        SESSION_STORE.pop(session_id, None)
    clear_saved_google_auth(email)

    response = JSONResponse({"authenticated": False})
    response.delete_cookie(SESSION_COOKIE)
    response.delete_cookie(GOOGLE_EMAIL_COOKIE)
    return response


@app.get("/api/auth/google/status")
def google_auth_status(request: Request):
    is_configured = is_google_oauth_configured()

    session = get_session(request)
    token_data = session.get("google_token")
    if not token_data:
        return {"authenticated": False, "configured": is_configured}

    try:
        profile = get_user_profile(token_data)
    except Exception:
        session.pop("google_token", None)
        return {"authenticated": False, "configured": is_configured}

    session["google_user"] = profile
    email = profile.get("email")
    if email:
        save_google_auth(email, token_data, profile)

    return {
        "authenticated": True,
        "configured": is_configured,
        "user": profile,
    }


def get_local_comics() -> list[dict]:
    comic_dir = BASE_DIR / "static" / "outputs" / "comic"
    comic_data_dir = BASE_DIR / "static" / "outputs" / "comic_data"

    if not comic_dir.exists():
        return []

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
                "storage": "local",
            }
        )

    comics.sort(key=lambda item: item["created_at"], reverse=True)
    return comics


@app.get("/api/comics/history")
def get_comic_history(request: Request):
    comics = []
    drive_error = None
    token_data = get_session(request).get("google_token")

    if token_data:
        try:
            drive_result = list_comic_bundles(token_data)
            update_google_token(request, drive_result.pop("token_data", None))
            comics.extend(drive_result.get("comics", []))
        except Exception as e:
            drive_error = str(e)

    comics.sort(key=lambda item: item["created_at"], reverse=True)
    return {"comics": comics, "drive_error": drive_error}


@app.get("/api/drive/files/{file_id}/content")
def get_drive_file_content(file_id: str, request: Request):
    token_data = get_google_token_or_401(request)
    try:
        file_data = download_file_bytes(token_data, file_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not read Google Drive file: {e}")

    update_google_token(request, file_data.pop("token_data", None))
    return Response(
        content=file_data["content"],
        media_type=file_data["mime_type"],
    )


@app.get("/api/drive/files/{file_id}/storyboard")
def get_drive_storyboard(file_id: str, request: Request):
    token_data = get_google_token_or_401(request)
    try:
        file_data = download_file_bytes(token_data, file_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not read Google Drive storyboard: {e}")

    update_google_token(request, file_data.pop("token_data", None))
    try:
        storyboard = json.loads(file_data["content"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=500, detail="Drive storyboard data is corrupted.")

    return {"storyboard": storyboard}


@app.get("/api/drive/files/{file_id}/article")
def get_drive_article(file_id: str, request: Request):
    token_data = get_google_token_or_401(request)
    try:
        file_data = download_file_bytes(token_data, file_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not read Google Drive storyboard: {e}")

    update_google_token(request, file_data.pop("token_data", None))
    try:
        storyboard = json.loads(file_data["content"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=500, detail="Drive storyboard data is corrupted.")

    article = extract_source_article(storyboard)
    if not article:
        raise HTTPException(status_code=404, detail="No source article was saved for this Drive comic.")

    return {
        "title": storyboard.get("title") or file_data["name"],
        "article": article,
    }


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
def generate_story_from_article(data: ArticleInput, request: Request):
    news = article_to_news_input(data.article)
    try:
        storyboard = generate_full_comic_from_news(
            news,
            generation_settings=data.generation_settings,
            source_article=data.article,
        )
    except GeminiImageGenerationError as e:
        raise HTTPException(status_code=503, detail=str(e))

    drive_upload = None
    drive_upload_error = None
    try:
        drive_upload = maybe_upload_storyboard_to_drive(request, storyboard)
    except Exception as e:
        drive_upload_error = str(e)

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
        "drive_upload": drive_upload,
        "drive_upload_error": drive_upload_error,
    }


@app.post("/api/story/generate-comic")
def generate_comic(data: ArticleInput, request: Request):
    news = article_to_news_input(data.article)
    try:
        storyboard = generate_full_comic_from_news(
            news,
            generation_settings=data.generation_settings,
            source_article=data.article,
        )
    except GeminiImageGenerationError as e:
        raise HTTPException(status_code=503, detail=str(e))

    drive_upload = None
    drive_upload_error = None
    try:
        drive_upload = maybe_upload_storyboard_to_drive(request, storyboard)
    except Exception as e:
        drive_upload_error = str(e)

    return {
        "title": storyboard.get("title") or news.title,
        "script": {
            "title": storyboard.get("title"),
            "theme": storyboard.get("theme"),
            "panels": storyboard.get("panels", []),
        },
        "comic_url": storyboard.get("comic_page_url"),
        "panel_urls": storyboard.get("panel_urls") or [],
        "drive_upload": drive_upload,
        "drive_upload_error": drive_upload_error,
    }
