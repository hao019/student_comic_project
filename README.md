# Student Comic Project

把新聞文章或新聞網址轉成一頁式漫畫的 FastAPI 專案。系統會先整理文章內容，再用 Gemini 產生漫畫腳本與整頁漫畫圖片；登入 Google 後，也可以把生成結果自動備份到使用者自己的 Google Drive。

## 功能

- 貼上新聞全文，或輸入公開新聞網址，自動整理成可生成漫畫的文章內容。
- 從 Google News 抓取隨機焦點新聞作為範例文章。
- 使用 Gemini 文字模型產生 4 到 6 格新聞漫畫腳本。
- 使用 Gemini 圖像模型產生單張 PNG 漫畫頁。
- 支援不同漫畫風格 preset，例如預設、黑白草稿、少年漫畫、四格搞笑、資訊圖表、情緒敘事、台灣新聞、網路迷因。
- 本機保留生成紀錄，可預覽、下載、重新命名、刪除。
- 可將喜愛漫畫保存在瀏覽器 localStorage。
- Google 登入後，自動上傳漫畫 PNG 與 storyboard JSON 到 Google Drive。

## 專案結構

```text
app/
  main.py                         FastAPI 入口與 API routes
  schemas.py                      Pydantic request/response schema
  services/
    article_fetcher.py            抓取公開新聞網址內容
    google_news_service.py        讀取 Google News RSS 並整理範例文章
    google_llm_service.py         Gemini 文字生成
    gemini_image_service.py       Gemini 圖像生成
    google_drive_service.py       Google OAuth 與 Drive 上傳/讀取
    news_cleaner.py               清理複製新聞內容
    prompt_builder.py             組合圖像生成 prompt
    story_service.py              串接文章、腳本、圖片與 storyboard
  static/
    app.js                        前端互動邏輯
    style.css                     前端樣式
  templates/
    index.html                    主頁
static/outputs/
  comic/                          生成的漫畫 PNG
  comic_data/                     生成的 storyboard JSON
```

## 安裝

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

接著編輯 `.env`，至少填入 Gemini API key：

```text
GEMINI_API_KEY=your_gemini_api_key_here
```

也可以使用 `GOOGLE_API_KEY`，程式會優先讀取 `GOOGLE_API_KEY`，沒有時才讀取 `GEMINI_API_KEY`。

## 環境變數

```text
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_TEXT_MODEL=gemini-3.1-pro-preview
GEMINI_IMAGE_MODEL=gemini-3.1-flash-image

# Optional: local SD3.5 Medium image generation.
HF_TOKEN=your_huggingface_token_with_sd35_medium_access
SD35_MEDIUM_LOCAL_BACKEND=diffusers
SD35_MEDIUM_DIFFUSERS_MODEL_ID=stabilityai/stable-diffusion-3.5-medium
SD35_MEDIUM_LOCAL_URL=http://127.0.0.1:7860/generate
SD35_MEDIUM_LOCAL_MODEL=stable-diffusion-3.5-medium
SD35_MEDIUM_LOCAL_WIDTH=1024
SD35_MEDIUM_LOCAL_HEIGHT=1024
SD35_MEDIUM_LOCAL_TIMEOUT=300
SD35_MEDIUM_LOCAL_STEPS=36
SD35_MEDIUM_LOCAL_GUIDANCE=4.0
SD35_MEDIUM_LOCAL_MAX_SEQUENCE_LENGTH=512
SD35_MEDIUM_PANEL_TARGET_PIXELS=1179648
SD35_MEDIUM_PANEL_MAX_SIDE=1536
SD35_MEDIUM_PANEL_MIN_SIDE=512
SD35_MEDIUM_PANEL_MAX_ASPECT=3.0
SD35_MEDIUM_CLIP_NEGATIVE_PROMPT=text, writing, logo, watermark, signature, speech bubble, text box, blurry, low detail, bad hands
SD35_MEDIUM_NEGATIVE_PROMPT=two-page spread, multiple pages, contact sheet, storyboard sheet, thumbnail grid, manga manuscript notes, dense text, tiny text, illegible text, fake letters, gibberish writing, random Chinese characters, random Japanese characters, random English text, numbers, typography, captions, subtitles, labels, signs, posters with writing, documents full of writing, forms, handwritten notes, newspaper text, UI screenshot, game UI text, monitor text, watermark, signature, logo, cluttered layout, too many panels, tiny panels, cropped page, low quality, single portrait, close-up face, headshot, blindfold, eyes covered, white strip over face, blank banner over face, text box over face, speech bubble, word balloon, thought bubble, title bar, caption strip, caption box, yellow label box, large empty rectangle, monochrome photo, blurry, soft focus, low detail, muddy colors, distorted face, deformed hands, extra fingers, bad anatomy, unfinished sketch

GOOGLE_CLIENT_ID=your_google_oauth_client_id_here
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret_here
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback
GOOGLE_DRIVE_FOLDER_NAME=Student Comic Generator
SESSION_COOKIE_SECURE=false
```

`SESSION_COOKIE_SECURE=true` 適合 HTTPS 部署環境；本機開發通常保持 `false` 或不設定。

## Google 登入與 Drive

若要讓使用者登入 Google，並把生成漫畫自動儲存到自己的 Drive：

1. 到 Google Cloud Console 建立或選擇一個專案。
2. 啟用 Google Drive API。
3. 設定 OAuth consent screen。
4. 建立 OAuth 2.0 Client ID，Application type 選 `Web application`。
5. 新增 Authorized redirect URI：

```text
http://127.0.0.1:8000/auth/google/callback
```

6. 把 Client ID、Client Secret 與 redirect URI 填入 `.env`。

本專案會要求 Google Drive `drive.file` 權限，只能存取此 app 建立或使用者透過此 app 選用的檔案。登入成功後，token 會儲存在 `.local/google_tokens/`，這個資料夾不應提交到 Git。

## 執行

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

開啟：

```text
http://127.0.0.1:8000/
```

## 使用方式

1. 在文字框貼上新聞全文，或貼上一個公開的 `http://` / `https://` 新聞網址。
2. 選擇漫畫風格。
3. 按下「生成漫畫」。
4. 生成後可以預覽、下載、加入喜愛、重新命名或刪除。
5. 如果已登入 Google，漫畫 PNG 與 storyboard JSON 會同步上傳到 Google Drive。

也可以按「範例文章」從 Google News 抓取一則焦點新聞來測試。

## API

| Method | Path | 說明 |
| --- | --- | --- |
| `GET` | `/` | 主頁 |
| `GET` | `/api/story/sample-article` | 從 Google News 取得範例文章 |
| `POST` | `/api/story/generate-from-article` | 由文章或新聞網址生成完整漫畫資料 |
| `POST` | `/api/story/generate-comic` | 由文章或新聞網址生成漫畫與簡化結果 |
| `GET` | `/api/comics/history` | 取得本機與 Drive 漫畫紀錄 |
| `GET` | `/api/comics/{filename}/download` | 下載本機漫畫 PNG |
| `GET` | `/api/comics/{filename}/storyboard` | 讀取本機 storyboard JSON |
| `GET` | `/api/comics/{filename}/article` | 讀取本機漫畫的原始文章 |
| `PATCH` / `POST` | `/api/comics/{filename}/rename` | 重新命名本機漫畫 |
| `DELETE` | `/api/comics/{filename}` | 刪除本機漫畫 |
| `GET` | `/auth/google/login` | 開始 Google OAuth 登入 |
| `GET` | `/auth/google/callback` | Google OAuth callback |
| `POST` | `/auth/google/logout` | 登出並清除本機 token |
| `GET` | `/api/auth/google/status` | 檢查 Google 登入狀態 |

生成 API request 範例：

```json
{
  "article": "貼上新聞全文，或貼上一個公開新聞網址",
  "generation_settings": {
    "style_preset": "default"
  }
}
```

可用的 `style_preset`：

```text
default
monochrome_draft
shonen
gag_4koma
infographic
emotional
taiwan_news
internet_meme
```

### Local SD3.5 Medium

The UI can choose `SD3.5 Medium local` as the image model.

Set `SD35_MEDIUM_LOCAL_BACKEND=diffusers` to load
`stabilityai/stable-diffusion-3.5-medium` directly in the FastAPI process. The
model is gated on Hugging Face, so accept the model terms and set `HF_TOKEN`
before generating.

For SD3.5 Medium, the app generates each comic panel separately, then composes
the final page with Pillow. This keeps the panel count stable and adds
Traditional Chinese text as an overlay instead of asking SD3.5 to render text.

Set `SD35_MEDIUM_LOCAL_BACKEND=http` if you prefer to start your own local
runtime separately, for example ComfyUI, Forge, or a small inference server, and
expose an HTTP endpoint configured by `SD35_MEDIUM_LOCAL_URL`.

Expected request body:

```json
{
  "prompt": "short CLIP prompt under 77 tokens",
  "prompt_2": "short CLIP prompt under 77 tokens",
  "prompt_3": "full T5 comic prompt",
  "negative_prompt": "short CLIP negative prompt under 77 tokens",
  "negative_prompt_2": "short CLIP negative prompt under 77 tokens",
  "negative_prompt_3": "full T5 negative prompt",
  "model": "stable-diffusion-3.5-medium",
  "width": 1024,
  "height": 1024,
  "num_images": 1
}
```

Accepted responses:

- `image/png` or `image/jpeg` bytes
- JSON with `image_base64`, `image`, `sample_base64`
- JSON with `image_url`, `url`, `sample`, `output`
- JSON with an `images` array containing one of the above

### Windows port 8000 helper

Use this helper instead of starting uvicorn manually when you want the app on
`http://127.0.0.1:8000/`:

```powershell
.\start_8000.ps1
```

It stops any existing process listening on `127.0.0.1:8000` before starting
FastAPI, which prevents `WinError 10048` port conflicts.

## 注意事項

- 新聞網址抓取只接受公開網站，會拒絕 localhost、private IP、非 HTML 或內容太少的頁面。
- Google News 範例文章需要連網，若新聞原文抓取失敗，會嘗試用 RSS 摘要改寫成短文。
- Gemini 文字與圖像生成都會消耗 API quota。若圖像 quota 不足，API 會回傳 503 錯誤。
- 生成檔案會放在 `static/outputs/`，不建議提交到 Git。
- `.env`、`.local/`、`venv/`、Python cache 與生成輸出都應保持在 `.gitignore`。

## GitHub

初始化並推送到 GitHub：

```powershell
git init
git add .
git commit -m "Initial project setup"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git
git push -u origin main
```
