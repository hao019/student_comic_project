# Student Comic Project

把新聞文章或新聞網址轉換成單頁漫畫的 FastAPI 應用。前端可以貼上文章、抓取 Google News 範例、調整漫畫風格與圖片模型，後端會用 Gemini 產出分鏡腳本，再用 Gemini Image 或本機 SD3.5 Medium 生成漫畫圖，並保存本機歷史紀錄；登入 Google 後也能同步上傳到 Google Drive。

## 功能

- 支援直接貼新聞全文，或輸入公開的 `http://` / `https://` 新聞網址。
- 可從 Google News RSS 抽一篇隨機範例新聞。
- 使用 Gemini 生成 4 到 6 格新聞漫畫分鏡、摘要、分類與圖像提示詞。
- 支援兩種圖片生成模型：
  - `sd35_medium_local`：本機 Stable Diffusion 3.5 Medium，逐格生成後用 Pillow 合成整頁。
  - `gemini_image`：用 Gemini Image 直接生成整頁漫畫。
- 支援漫畫風格 preset：`default`、`monochrome_draft`、`realistic_people`。
- 自動保存漫畫 PNG 與 storyboard JSON 到 `static/outputs/`。
- 漫畫庫支援預覽、下載、重新命名、刪除、收藏與查看原文。
- Google OAuth 登入後，可把漫畫 PNG 與 storyboard JSON 上傳到 Google Drive。

## 專案結構

```text
app/
  main.py                         FastAPI app、API routes、Google OAuth flow
  schemas.py                      Pydantic request/response schemas
  services/
    article_fetcher.py            抓取公開新聞網址內容
    google_news_service.py        讀取 Google News RSS 範例新聞
    google_llm_service.py         Gemini 文字模型與分鏡生成
    gemini_image_service.py       Gemini Image 生成整頁漫畫
    sd35_medium_local_service.py  本機 SD3.5 Medium 圖片生成
    comic_compositor.py           Pillow 漫畫頁合成
    google_drive_service.py       Google OAuth 與 Drive 上傳/讀取/刪除
    news_cleaner.py               清理複製來的新聞正文
    prompt_builder.py             建立圖片生成 prompt
    story_service.py              分鏡、圖片生成與 storyboard 保存流程
  static/
    app.js                        前端互動邏輯
    style.css                     前端樣式
  templates/
    index.html                    主頁面
static/outputs/
  comic/                          生成的漫畫 PNG 與 SD3.5 分格圖
  comic_data/                     storyboard JSON
```

## 安裝

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

編輯 `.env`，至少填入 Gemini API key：

```text
GEMINI_API_KEY=your_gemini_api_key_here
```

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

# Optional: Google OAuth + Drive upload.
GOOGLE_CLIENT_ID=your_google_oauth_client_id_here
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret_here
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback
GOOGLE_DRIVE_FOLDER_NAME=Student Comic Generator
SESSION_COOKIE_SECURE=false
```

本機開發時 `SESSION_COOKIE_SECURE=false` 即可；部署到 HTTPS 環境時再改為 `true`。

## 啟動

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

瀏覽器打開：

```text
http://127.0.0.1:8000/
```

Windows 上也可以使用 helper，它會先停止占用 `127.0.0.1:8000` 的舊行程：

```powershell
.\start_8000.ps1
```

## Google Drive 設定

若要啟用 Google 登入與 Drive 上傳：

1. 到 Google Cloud Console 建立或選擇專案。
2. 啟用 Google Drive API。
3. 設定 OAuth consent screen。
4. 建立 OAuth 2.0 Client ID，類型選擇 `Web application`。
5. 在 Authorized redirect URI 加入：

```text
http://127.0.0.1:8000/auth/google/callback
```

6. 把 Client ID、Client Secret 與 Redirect URI 寫入 `.env`。

應用使用 `drive.file` scope，只會管理由本應用建立或使用者授權給本應用的檔案。登入 token 會保存在 `.local/google_tokens/`，該目錄不應提交到 Git。

## 使用流程

1. 貼上新聞全文，或輸入公開新聞網址。
2. 可選：開啟生成設定，選擇漫畫風格、圖片模型與 SD3.5 參數。
3. 按下生成漫畫。
4. 等待 Gemini 生成分鏡，並由圖片模型產出漫畫。
5. 在結果區預覽、下載、收藏，或從漫畫庫管理歷史作品。
6. 若已登入 Google，生成結果會同步上傳到 Drive。

## API

| Method | Path | 說明 |
| --- | --- | --- |
| `GET` | `/` | 主頁面 |
| `GET` | `/api/story/sample-article` | 從 Google News 取得範例新聞 |
| `POST` | `/api/story/generate-from-article` | 從文章或網址生成漫畫與完整 storyboard |
| `POST` | `/api/story/generate-comic` | 從文章或網址生成漫畫與簡化 script 回應 |
| `GET` | `/api/comics/history` | 讀取本機與 Drive 漫畫歷史 |
| `GET` | `/api/comics/{filename}/download` | 下載本機漫畫 PNG |
| `GET` | `/api/comics/{filename}/storyboard` | 讀取本機 storyboard JSON |
| `GET` | `/api/comics/{filename}/article` | 讀取本機漫畫原始文章 |
| `PATCH` / `POST` | `/api/comics/{filename}/rename` | 重新命名本機漫畫 |
| `DELETE` | `/api/comics/{filename}` | 刪除本機漫畫，並嘗試同步刪除對應 Drive 檔案 |
| `GET` | `/api/drive/files/{file_id}/content` | 讀取 Drive 漫畫圖檔 |
| `GET` | `/api/drive/files/{file_id}/storyboard` | 讀取 Drive storyboard JSON |
| `GET` | `/api/drive/files/{file_id}/article` | 讀取 Drive storyboard 內的原文 |
| `DELETE` | `/api/drive/files/{file_id}` | 刪除 Drive 漫畫圖檔，可帶 `storyboard_file_id` |
| `GET` | `/auth/google/login` | 開始 Google OAuth 登入 |
| `GET` | `/auth/google/callback` | Google OAuth callback |
| `POST` | `/auth/google/logout` | 登出並清除本機 token |
| `GET` | `/api/auth/google/status` | 查詢 Google 登入狀態 |

請求範例：

```json
{
  "article": "新聞標題\n\n新聞正文，或一段公開新聞網址。",
  "generation_settings": {
    "style_preset": "default",
    "image_model": "sd35_medium_local",
    "sd35": {
      "steps": 36,
      "width": 1024,
      "height": 1024,
      "guidance_scale": 4.0,
      "seed": null,
      "max_sequence_length": 512
    }
  }
}
```

可用的 `style_preset`：

```text
default
monochrome_draft
realistic_people
```

可用的 `image_model`：

```text
sd35_medium_local
gemini_image
```

`realistic_people` 會自動使用 `gemini_image`，因為該風格走 Gemini Image 流程。

## Local SD3.5 Medium

UI 預設圖片模型是 `SD3.5 Medium local`。

若設定 `SD35_MEDIUM_LOCAL_BACKEND=diffusers`，FastAPI 會直接用 diffusers 載入 `stabilityai/stable-diffusion-3.5-medium`。這個模型在 Hugging Face 上需要先接受條款，並提供有權限的 `HF_TOKEN`。

若設定 `SD35_MEDIUM_LOCAL_BACKEND=http`，請自行啟動 ComfyUI、Forge 或小型 inference server，並用 `SD35_MEDIUM_LOCAL_URL` 指向它。

HTTP backend 預期 request body：

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
  "num_inference_steps": 36,
  "guidance_scale": 4.0,
  "max_sequence_length": 512,
  "num_images": 1
}
```

可接受的回應格式：

- `image/png` 或 `image/jpeg` bytes
- JSON with `image_base64`, `image`, `sample_base64`
- JSON with `image_url`, `url`, `sample`, `output`
- JSON with an `images` array containing one of the above

SD3.5 流程會先生成每一格，再用 Pillow 合成最終漫畫頁，並把繁中標題、旁白與短句作為 overlay 加上去，避免要求 SD3.5 直接繪製可讀中文字。

## 注意事項

- 新聞網址必須能從本機存取；localhost、private IP 與需要登入的頁面不適合當輸入來源。
- Google News RSS 可能因地區、語言或網路環境回傳不同結果。
- Gemini 與圖片生成都會消耗 API quota 或本機 GPU/CPU 資源。
- 生成結果保存在 `static/outputs/`，不建議提交到 Git。
- `.env`、`.local/`、`venv/`、Python cache 已由 `.gitignore` 排除。