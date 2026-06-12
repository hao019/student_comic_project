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
