# Student Comic Project

FastAPI project that turns a news article into a manga-style comic using Gemini text and Gemini image generation.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill in `GEMINI_API_KEY` in `.env`.

## Google Login + Drive

To let users sign in with Google and auto-save generated comics to their own Drive:

1. Open Google Cloud Console and create/select a project.
2. Enable the Google Drive API.
3. Configure the OAuth consent screen.
4. Create an OAuth 2.0 Client ID with application type `Web application`.
5. Add this authorized redirect URI:

```text
http://127.0.0.1:8000/auth/google/callback
```

6. Add these values to `.env`:

```text
GOOGLE_CLIENT_ID=your_google_oauth_client_id_here
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret_here
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback
GOOGLE_DRIVE_FOLDER_NAME=Student Comic Generator
```

The app requests Google Drive `drive.file` permission and uploads each generated PNG plus its storyboard JSON to the user's Drive folder.

## Run

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

## GitHub

This project ignores local secrets, virtual environments, Python caches, and generated comic outputs.

After Git is installed, initialize and push with:

```powershell
git init
git add .
git commit -m "Initial project setup"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git
git push -u origin main
```
