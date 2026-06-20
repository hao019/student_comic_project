from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


load_dotenv()

DRIVE_FOLDER_NAME = os.getenv("GOOGLE_DRIVE_FOLDER_NAME", "Student Comic Generator")
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleDriveConfigError(RuntimeError):
    pass


def _require_google_oauth_config() -> tuple[str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise GoogleDriveConfigError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required.")

    return client_id, client_secret


def is_google_oauth_configured() -> bool:
    try:
        _require_google_oauth_config()
    except GoogleDriveConfigError:
        return False
    return True


def _client_config() -> dict[str, Any]:
    client_id, client_secret = _require_google_oauth_config()
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI", "")],
        }
    }


def allow_local_http_oauth(redirect_uri: str) -> None:
    if redirect_uri.startswith("http://127.0.0.1") or redirect_uri.startswith("http://localhost"):
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def build_authorization_url(redirect_uri: str) -> tuple[str, str, str]:
    from google_auth_oauthlib.flow import Flow

    allow_local_http_oauth(redirect_uri)
    flow = Flow.from_client_config(
        _client_config(),
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri,
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authorization_url, state, flow.code_verifier


def fetch_oauth_token(
    authorization_response: str,
    redirect_uri: str,
    state: str,
    code_verifier: str,
) -> dict[str, Any]:
    from google_auth_oauthlib.flow import Flow

    allow_local_http_oauth(redirect_uri)
    flow = Flow.from_client_config(
        _client_config(),
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri,
        state=state,
        code_verifier=code_verifier,
    )
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    return credentials_to_session(credentials)


def credentials_to_session(credentials: Any) -> dict[str, Any]:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }


def credentials_from_session(token_data: dict[str, Any]) -> Any:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleAuthRequest

    credentials = Credentials(**token_data)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleAuthRequest())
    return credentials


def get_user_profile(token_data: dict[str, Any]) -> dict[str, str]:
    credentials = credentials_from_session(token_data)

    from googleapiclient.discovery import build

    oauth_service = build("oauth2", "v2", credentials=credentials, cache_discovery=False)
    profile = oauth_service.userinfo().get().execute()
    return {
        "email": profile.get("email", ""),
        "name": profile.get("name", ""),
        "picture": profile.get("picture", ""),
    }


def _drive_service(token_data: dict[str, Any]) -> Any:
    from googleapiclient.discovery import build

    credentials = credentials_from_session(token_data)
    return build("drive", "v3", credentials=credentials, cache_discovery=False), credentials


def _ensure_app_folder(service: Any) -> str:
    escaped_name = DRIVE_FOLDER_NAME.replace("\\", "\\\\").replace("'", "\\'")
    query = (
        "mimeType='application/vnd.google-apps.folder' "
        f"and name='{escaped_name}' and trashed=false"
    )
    result = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name)",
        pageSize=1,
    ).execute()
    folders = result.get("files", [])
    if folders:
        return folders[0]["id"]

    folder = service.files().create(
        body={
            "name": DRIVE_FOLDER_NAME,
            "mimeType": "application/vnd.google-apps.folder",
        },
        fields="id",
    ).execute()
    return folder["id"]


def _upload_file(service: Any, path: Path, folder_id: str, mime_type: str) -> dict[str, str]:
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(path), mimetype=mime_type, resumable=False)
    created = service.files().create(
        body={"name": path.name, "parents": [folder_id]},
        media_body=media,
        fields="id, name, webViewLink",
    ).execute()
    return {
        "id": created.get("id", ""),
        "name": created.get("name", path.name),
        "webViewLink": created.get("webViewLink", ""),
    }


def _query_files_in_folder(service: Any, folder_id: str, mime_type: str | None = None) -> list[dict[str, Any]]:
    query_parts = [f"'{folder_id}' in parents", "trashed=false"]
    if mime_type:
        query_parts.append(f"mimeType='{mime_type}'")

    files: list[dict[str, Any]] = []
    page_token = None
    while True:
        result = service.files().list(
            q=" and ".join(query_parts),
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
            pageSize=100,
            pageToken=page_token,
        ).execute()
        files.extend(result.get("files", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            return files


def _drive_timestamp_to_epoch(value: str | None) -> float:
    if not value:
        return 0

    from datetime import datetime

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0


def list_comic_bundles(token_data: dict[str, Any]) -> dict[str, Any]:
    service, credentials = _drive_service(token_data)
    folder_id = _ensure_app_folder(service)
    folder_files = _query_files_in_folder(service, folder_id)
    images = [
        file
        for file in folder_files
        if str(file.get("mimeType") or "").startswith("image/")
    ]
    json_files = [
        file
        for file in folder_files
        if file.get("mimeType") == "application/json"
    ]
    json_by_stem = {Path(file["name"]).stem: file for file in json_files}

    comics = []
    for image in images:
        stem = Path(image["name"]).stem
        storyboard = json_by_stem.get(stem)
        comics.append(
            {
                "filename": image["name"],
                "url": f"/api/drive/files/{image['id']}/content",
                "created_at": _drive_timestamp_to_epoch(image.get("createdTime") or image.get("modifiedTime")),
                "size": int(image.get("size") or 0),
                "page_count": 1,
                "editable": bool(storyboard),
                "has_article": bool(storyboard),
                "storage": "drive",
                "drive_file_id": image["id"],
                "drive_storyboard_id": storyboard.get("id") if storyboard else None,
                "drive_web_url": image.get("webViewLink", ""),
            }
        )

    comics.sort(key=lambda item: item["created_at"], reverse=True)
    return {
        "folder_id": folder_id,
        "folder_name": DRIVE_FOLDER_NAME,
        "comics": comics,
        "token_data": credentials_to_session(credentials),
    }


def get_file_metadata(token_data: dict[str, Any], file_id: str) -> dict[str, Any]:
    service, credentials = _drive_service(token_data)
    metadata = service.files().get(
        fileId=file_id,
        fields="id, name, mimeType, size, webViewLink",
    ).execute()
    metadata["token_data"] = credentials_to_session(credentials)
    return metadata


def download_file_bytes(token_data: dict[str, Any], file_id: str) -> dict[str, Any]:
    service, credentials = _drive_service(token_data)
    metadata = service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
    content = service.files().get_media(fileId=file_id).execute()
    return {
        "name": metadata.get("name", file_id),
        "mime_type": metadata.get("mimeType", "application/octet-stream"),
        "content": content,
        "token_data": credentials_to_session(credentials),
    }


def trash_files(token_data: dict[str, Any], file_ids: list[str]) -> dict[str, Any]:
    service, credentials = _drive_service(token_data)
    unique_ids = list(dict.fromkeys(str(file_id or "").strip() for file_id in file_ids if str(file_id or "").strip()))
    trashed_files = []

    for file_id in unique_ids:
        trashed = service.files().update(
            fileId=file_id,
            body={"trashed": True},
            fields="id, name, trashed",
        ).execute()
        trashed_files.append(trashed)

    return {
        "files": trashed_files,
        "token_data": credentials_to_session(credentials),
    }


def upload_comic_bundle(
    token_data: dict[str, Any],
    comic_path: Path,
    storyboard_path: Path | None = None,
) -> dict[str, Any]:
    service, credentials = _drive_service(token_data)
    folder_id = _ensure_app_folder(service)

    uploaded = {
        "folder_name": DRIVE_FOLDER_NAME,
        "folder_id": folder_id,
        "comic": _upload_file(service, comic_path, folder_id, "image/png"),
        "storyboard": None,
        "token_data": credentials_to_session(credentials),
    }

    if storyboard_path and storyboard_path.exists():
        uploaded["storyboard"] = _upload_file(
            service,
            storyboard_path,
            folder_id,
            "application/json",
        )

    return uploaded


def write_drive_metadata(storyboard_path: Path, drive_upload: dict[str, Any]) -> None:
    if not storyboard_path.exists():
        return

    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    upload_copy = dict(drive_upload)
    upload_copy.pop("token_data", None)
    storyboard["drive_upload"] = upload_copy
    storyboard_path.write_text(
        json.dumps(storyboard, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
