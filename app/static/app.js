const form = document.querySelector("#comic-form");
const articleInput = document.querySelector("#article-input");
const sampleArticleButton = document.querySelector("#sample-article-button");
const clearInputButton = document.querySelector("#clear-input-button");
const toggleSettingsButton = document.querySelector("#toggle-settings-button");
const generationSettingsPanel = document.querySelector("#generation-settings-panel");
const stylePresetInput = document.querySelector("#style-preset");
const styleDescription = document.querySelector("#style-description");
const generateButton = document.querySelector("#generate-button");
const statusMessage = document.querySelector("#status-message");
const errorMessage = document.querySelector("#error-message");
const resultSection = document.querySelector("#result-section");
const summaryText = document.querySelector("#summary-text");
const fidelityReportBlock = document.querySelector("#fidelity-report-block");
const fidelityReportContent = document.querySelector("#fidelity-report-content");
const comicImage = document.querySelector("#comic-image");
const comicImageFrame = document.querySelector("#comic-image-frame");
const comicPageGallery = document.querySelector("#comic-page-gallery");
const imageEmpty = document.querySelector("#image-empty");
const resultPlaceholder = document.querySelector("#result-placeholder");
const resultPanel = document.querySelector(".result-panel");
const generationProgress = document.querySelector("#generation-progress");
const progressBar = document.querySelector("#progress-bar");
const progressSteps = [...document.querySelectorAll(".progress-steps li")];
const comicHistory = document.querySelector("#comic-history");
const historyStatus = document.querySelector("#history-status");
const historyEmpty = document.querySelector("#history-empty");
const refreshHistoryButton = document.querySelector("#refresh-history-button");
const openHistoryButton = document.querySelector("#open-history-button");
const favoriteResultButton = document.querySelector("#favorite-result-button");
const closeHistoryButton = document.querySelector("#close-history-button");
const historyDrawer = document.querySelector("#history-drawer");
const historyOverlay = document.querySelector("#history-overlay");
const googleLoginLink = document.querySelector("#google-login-link");
const googleLogoutButton = document.querySelector("#google-logout-button");
const driveStatus = document.querySelector("#drive-status");
const comicPreviewOverlay = document.querySelector("#comic-preview-overlay");
const comicPreviewHeader = document.querySelector(".comic-preview-header");
const comicPreviewActions = document.querySelector(".comic-preview-actions");
const comicPreviewModal = document.querySelector("#comic-preview-modal");
const comicPreviewImage = document.querySelector("#comic-preview-image");
const comicPreviewTitle = document.querySelector("#comic-preview-title");
const previewDownloadLink = document.querySelector("#preview-download-link");
const previewFavoriteButton = document.querySelector("#preview-favorite-button");
const closePreviewButton = document.querySelector("#close-preview-button");
const dismissPreviewButton = document.querySelector("#dismiss-preview-button");
const comicContextMenu = document.querySelector("#comic-context-menu");
const contextArticleButton = document.querySelector("#context-article-button");
const contextDownloadButton = document.querySelector("#context-download-button");
const contextRenameButton = document.querySelector("#context-rename-button");
const contextDeleteButton = document.querySelector("#context-delete-button");
const renameOverlay = document.querySelector("#rename-overlay");
const renameDialog = document.querySelector("#rename-dialog");
const renameInput = document.querySelector("#rename-input");
const cancelRenameButton = document.querySelector("#cancel-rename-button");
const articleViewOverlay = document.querySelector("#article-view-overlay");
const articleViewDialog = document.querySelector("#article-view-dialog");
const articleViewTitle = document.querySelector("#article-view-title");
const articleViewText = document.querySelector("#article-view-text");
const closeArticleViewButton = document.querySelector("#close-article-view-button");
let progressTimer = null;
let selectedComicFilename = "";
let contextComic = null;
let renameTargetFilename = "";
let currentStoryboard = null;
let currentComicFilename = "";
let historyMode = "history";
let allComicsCache = [];
let previewControlsTimer = null;
let selectedComicHasArticle = false;
let selectedComicDownloadUrl = "";

const progressLabels = [
  "分析文章中...",
  "生成分鏡中...",
  "生成圖片中...",
  "合成漫畫中...",
];

const progressStepThresholds = [0, 22, 55, 78];
const estimatedGenerationMs = 52000;
const settingsStorageKey = "comicGenerationSettings";
const favoritesStorageKey = "favoriteComics";
const comicStylePresets = [
  "default",
  "monochrome_draft",
  "shonen",
  "gag_4koma",
  "infographic",
  "emotional",
  "taiwan_news",
  "internet_meme",
];
const comicStyleDescriptions = {
  default: "乾淨的新聞漫畫版面，色彩柔和，適合一般文章與新聞說明。",
  monochrome_draft: "黑白網點、強烈墨線，漫畫原稿感較重。",
  shonen: "速度線、誇張表情與動態構圖，畫面更有熱血節奏。",
  gag_4koma: "表情簡潔、反應誇張，適合輕鬆有梗的四格漫畫。",
  infographic: "圖標、箭頭與重點標籤更明顯，偏向資訊整理與懶人包。",
  emotional: "重視表情、光影與氣氛，適合情緒轉折較強的故事。",
  taiwan_news: "接近台灣新聞圖解風，版面清楚，適合校園、地方與社會新聞。",
  internet_meme: "迷因反應、誇張節奏與社群感較強，適合輕鬆幽默題材。",
};

const sampleArticle = `校園科技社今天舉辦「AI 創意漫畫工作坊」，學生們把生活中的小故事輸入系統，短短幾分鐘就生成四格漫畫。

活動中，有同學用「忘記帶作業」當主題，AI 先分析情緒，再安排角色表情與分鏡，最後合成一張完整漫畫。

老師表示，這個工具能幫助學生把文字轉成視覺故事，也能訓練大家更清楚地表達事件、情緒與結局。`;

async function loadSampleArticle() {
  const originalText = sampleArticleButton.textContent;
  sampleArticleButton.disabled = true;
  sampleArticleButton.textContent = "產生中...";
  errorMessage.textContent = "";
  statusMessage.textContent = "正在產生隨機範例文章...";

  try {
    const response = await fetch("/api/story/sample-article");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "範例文章產生失敗"));
    }

    const title = data.title ? `${data.title}\n\n` : "";
    articleInput.value = `${title}${data.article || sampleArticle}`.trim();
    statusMessage.textContent = "已產生新的範例文章";
  } catch (error) {
    console.error(error);
    articleInput.value = sampleArticle;
    errorMessage.textContent = "範例文章產生失敗，已改用本地範例。";
    statusMessage.textContent = "";
  } finally {
    sampleArticleButton.disabled = false;
    sampleArticleButton.textContent = originalText;
    articleInput.focus();
  }
}

function getGenerationSettings() {
  return {
    style_preset: stylePresetInput?.value || "default",
  };
}

function syncStyleDescription() {
  if (!styleDescription) {
    return;
  }

  const stylePreset = stylePresetInput?.value || "default";
  styleDescription.textContent = comicStyleDescriptions[stylePreset] || comicStyleDescriptions.default;
}

function saveGenerationSettings() {
  localStorage.setItem(settingsStorageKey, JSON.stringify(getGenerationSettings()));
}

function loadGenerationSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem(settingsStorageKey) || "{}");
    if (!stylePresetInput) {
      return;
    }

    if (comicStylePresets.includes(saved.style_preset)) {
      stylePresetInput.value = saved.style_preset;
    } else {
      stylePresetInput.value = "default";
    }
  } catch (error) {
    console.warn("Could not load generation settings", error);
  }

  syncStyleDescription();
}

function attachPressFeedback() {
  const pressableElements = document.querySelectorAll("button, a.icon-button");

  pressableElements.forEach((element) => {
    element.addEventListener("pointerdown", () => {
      if (element.disabled) {
        return;
      }
      element.classList.add("is-pressing");
    });

    ["pointerup", "pointercancel", "pointerleave", "blur"].forEach((eventName) => {
      element.addEventListener(eventName, () => {
        element.classList.remove("is-pressing");
      });
    });
  });
}

function setLoading(isLoading) {
  generateButton.disabled = isLoading;
  generateButton.textContent = isLoading ? "生成中..." : "生成漫畫";
  statusMessage.textContent = isLoading ? progressLabels[0] : "";
  resultPanel.classList.toggle("is-loading", isLoading);

  if (isLoading) {
    resultPlaceholder.classList.remove("hidden");
    resultPlaceholder.querySelector("p").textContent = "AI 正在分析文章並合成最終漫畫圖...";
  }
}

function getStepFromPercent(percent) {
  let step = 0;
  progressStepThresholds.forEach((threshold, index) => {
    if (percent >= threshold) {
      step = index;
    }
  });
  return step;
}

function setProgress(percent, forcedStep = null) {
  const safePercent = Math.max(0, Math.min(percent, 100));
  const safeStep = forcedStep ?? getStepFromPercent(safePercent);

  progressBar.style.width = `${safePercent}%`;
  statusMessage.textContent = progressLabels[safeStep] || "生成中...";

  progressSteps.forEach((item, index) => {
    item.classList.toggle("is-active", index === safeStep);
    item.classList.toggle("is-complete", index < safeStep);
  });
}

function startProgress() {
  generationProgress.classList.remove("hidden");
  setProgress(6, 0);
  clearInterval(progressTimer);
  const startedAt = Date.now();

  progressTimer = setInterval(() => {
    const elapsed = Date.now() - startedAt;
    const ratio = Math.min(elapsed / estimatedGenerationMs, 1);
    const eased = 1 - Math.pow(1 - ratio, 2.25);
    const percent = Math.min(92, 6 + eased * 86);
    setProgress(percent);
  }, 500);
}

function finishProgress(wasSuccessful) {
  clearInterval(progressTimer);
  progressTimer = null;

  if (wasSuccessful) {
    setProgress(100, progressSteps.length - 1);
    progressSteps.forEach((item) => {
      item.classList.add("is-complete");
      item.classList.remove("is-active");
    });
    statusMessage.textContent = "漫畫生成完成";
    window.setTimeout(() => generationProgress.classList.add("hidden"), 900);
  } else {
    generationProgress.classList.add("hidden");
    progressBar.style.width = "0%";
    progressSteps.forEach((item) => item.classList.remove("is-active", "is-complete"));
  }
}

function resetResult() {
  errorMessage.textContent = "";
  summaryText.textContent = "";
  renderFidelityReport(null);
  currentStoryboard = null;
  currentComicFilename = "";
  syncFavoriteButton();
  comicImage.removeAttribute("src");
  comicImageFrame.classList.add("hidden");
  comicImageFrame.classList.remove("is-expanding");
  comicPageGallery.replaceChildren();
  comicPageGallery.classList.add("hidden");
  imageEmpty.classList.add("hidden");
  resultSection.classList.add("hidden");
  resultPlaceholder.classList.remove("hidden");
  resultPlaceholder.querySelector("p").textContent = "生成完成後，最終漫畫成品會顯示在這裡。";
}

function renderFidelityReport(report) {
  if (!fidelityReportBlock || !fidelityReportContent) {
    return;
  }

  fidelityReportContent.replaceChildren();
  if (!report || typeof report !== "object" || !Object.keys(report).length) {
    fidelityReportBlock.classList.add("hidden");
    return;
  }

  const coverage = Number(report.coverage_ratio ?? 0);
  const expected = report.expected_panel_count ?? "-";
  const actual = report.actual_panel_count ?? "-";
  const revisionAttempts = Number(report.revision_attempts ?? 0);
  const warnings = Array.isArray(report.warnings) ? report.warnings : [];
  const covered = Array.isArray(report.covered_source_terms) ? report.covered_source_terms : [];
  const missing = Array.isArray(report.missing_source_terms) ? report.missing_source_terms : [];
  const criticalMissing = Array.isArray(report.critical_missing_terms) ? report.critical_missing_terms : [];
  const objectFocusWarnings = Array.isArray(report.object_focus_warnings) ? report.object_focus_warnings : [];
  const singular = Array.isArray(report.singular_subjects) ? report.singular_subjects : [];

  const status = document.createElement("div");
  status.className = warnings.length ? "fidelity-status has-warning" : "fidelity-status";
  const revisionText = revisionAttempts > 0 ? `｜已自動修正 ${revisionAttempts} 次` : "";
  status.textContent = warnings.length
    ? `需檢查｜覆蓋率 ${(coverage * 100).toFixed(0)}%｜格數 ${actual}/${expected}${revisionText}`
    : `看起來穩定｜覆蓋率 ${(coverage * 100).toFixed(0)}%｜格數 ${actual}/${expected}${revisionText}`;

  const makeRow = (label, items, emptyText) => {
    const row = document.createElement("div");
    row.className = "fidelity-row";

    const strong = document.createElement("strong");
    strong.textContent = label;

    const span = document.createElement("span");
    span.textContent = items.length ? items.slice(0, 8).join("、") : emptyText;

    row.append(strong, span);
    return row;
  };

  fidelityReportContent.append(
    status,
    makeRow("已覆蓋", covered, "尚未偵測到"),
    makeRow("可能缺漏", missing, "無"),
    makeRow("核心缺漏", criticalMissing, "無"),
    makeRow("物件焦點", objectFocusWarnings, "無"),
    makeRow("單數主體", singular, "無"),
    makeRow("警告", warnings, "無")
  );
  fidelityReportBlock.classList.remove("hidden");
}

function loadFavoriteComics() {
  try {
    const saved = JSON.parse(localStorage.getItem(favoritesStorageKey) || "[]");
    return Array.isArray(saved) ? saved.filter(Boolean) : [];
  } catch (error) {
    console.warn("Could not load favorite comics", error);
    return [];
  }
}

function saveFavoriteComics(favorites) {
  localStorage.setItem(favoritesStorageKey, JSON.stringify([...new Set(favorites)]));
}

function isFavoriteComic(filename) {
  return Boolean(filename) && loadFavoriteComics().includes(filename);
}

function setFavoriteComic(filename, shouldFavorite) {
  if (!filename) {
    return;
  }

  const favorites = loadFavoriteComics();
  const nextFavorites = shouldFavorite
    ? [...favorites, filename]
    : favorites.filter((item) => item !== filename);
  saveFavoriteComics(nextFavorites);
}

function renameFavoriteComic(oldFilename, newFilename) {
  if (!oldFilename || !newFilename) {
    return;
  }

  const favorites = loadFavoriteComics();
  if (!favorites.includes(oldFilename)) {
    return;
  }

  saveFavoriteComics(favorites.map((item) => (item === oldFilename ? newFilename : item)));
}

function syncFavoriteButton() {
  favoriteResultButton.classList.remove("hidden", "is-favorite");
  favoriteResultButton.textContent = "喜愛";
  favoriteResultButton.setAttribute("aria-label", "開啟喜愛漫畫");
  favoriteResultButton.title = "喜愛漫畫";
}

function syncPreviewFavoriteButton() {
  const isFavorite = isFavoriteComic(selectedComicFilename);
  previewFavoriteButton.classList.toggle("is-favorite", isFavorite);
  previewFavoriteButton.textContent = isFavorite ? "♥" : "♡";
  previewFavoriteButton.setAttribute("aria-label", isFavorite ? "移除喜愛" : "加入喜愛");
  previewFavoriteButton.title = isFavorite ? "移除喜愛" : "加入喜愛";
}

function revealPreviewControls() {
  comicPreviewHeader.classList.remove("is-collapsed");
}

function collapsePreviewControls() {
  if (!document.body.classList.contains("comic-preview-open")) {
    return;
  }

  comicPreviewHeader.classList.add("is-collapsed");
}

function schedulePreviewControlsCollapse(delay = 2600) {
  clearTimeout(previewControlsTimer);
  previewControlsTimer = window.setTimeout(collapsePreviewControls, delay);
}

function handlePreviewPointerMove(event) {
  if (!document.body.classList.contains("comic-preview-open")) {
    return;
  }

  const nearRightEdge = event.clientX >= window.innerWidth - 96;
  const nearTop = event.clientY <= 132;
  if (nearRightEdge && nearTop) {
    revealPreviewControls();
    schedulePreviewControlsCollapse();
  }
}

function setCurrentComicFromUrl(imageUrl) {
  currentComicFilename = getFilenameFromUrl(imageUrl);
  syncFavoriteButton();
}

function showImage(imageUrl) {
  if (!imageUrl) {
    imageEmpty.classList.remove("hidden");
    return;
  }

  comicImage.onload = () => {
    imageEmpty.classList.add("hidden");
    resultPlaceholder.classList.add("hidden");
    comicImageFrame.classList.remove("hidden");
    syncFavoriteButton();
  };

  comicImage.onerror = () => {
    comicImageFrame.classList.add("hidden");
    resultPlaceholder.classList.add("hidden");
    imageEmpty.classList.remove("hidden");
  };

  comicImage.src = imageUrl;
}

function showComicPages(pageUrls, scrollUrl = "") {
  const urls = Array.isArray(pageUrls) ? pageUrls.filter(Boolean) : [];
  const displayUrl = scrollUrl || urls[0] || "";

  comicPageGallery.replaceChildren();
  comicPageGallery.classList.add("hidden");

  if (!displayUrl) {
    showImage("");
    return;
  }

  setCurrentComicFromUrl(displayUrl);
  showImage(displayUrl);
}

function getErrorMessage(data, fallback) {
  if (data && typeof data.detail === "string") {
    return data.detail;
  }

  if (data && Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg || "欄位錯誤").join("、");
  }

  return fallback;
}

function setDriveStatus(message, mode = "") {
  if (!driveStatus) {
    return;
  }

  driveStatus.textContent = message;
  driveStatus.classList.toggle("is-connected", mode === "connected");
  driveStatus.classList.toggle("has-warning", mode === "warning");
}

function renderDriveUploadStatus(upload, error = "") {
  if (upload?.comic?.webViewLink) {
    setDriveStatus("已自動存到 Google Drive。", "connected");

    const link = document.createElement("a");
    link.href = upload.comic.webViewLink;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "開啟 Drive 檔案";
    driveStatus.append(" ", link);
    return;
  }

  if (error) {
    setDriveStatus(`漫畫已生成，但同步 Google Drive 失敗：${error}`, "warning");
    return;
  }

  setDriveStatus("尚未登入 Google；漫畫已先存到本機歷史紀錄。");
}

async function syncGoogleAuthStatus() {
  if (!googleLoginLink || !googleLogoutButton) {
    return;
  }

  try {
    const response = await fetch("/api/auth/google/status");
    const data = await response.json();
    const user = data.user || {};

    googleLoginLink.classList.toggle("hidden", Boolean(data.authenticated));
    googleLogoutButton.classList.toggle("hidden", !data.authenticated);

    if (!data.configured) {
      setDriveStatus("尚未設定 Google OAuth，請先在 .env 填入 GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET。", "warning");
    } else if (data.authenticated) {
      setDriveStatus(`已登入 Google：${user.email || user.name || "可同步 Drive"}`, "connected");
    } else {
      setDriveStatus("登入 Google 後，生成完成會自動存到你的 Drive。");
    }
  } catch (error) {
    console.error(error);
    setDriveStatus("無法確認 Google 登入狀態。", "warning");
  }
}

async function logoutGoogle() {
  if (!googleLogoutButton) {
    return;
  }

  googleLogoutButton.disabled = true;
  try {
    await fetch("/auth/google/logout", { method: "POST" });
    await syncGoogleAuthStatus();
  } catch (error) {
    console.error(error);
    setDriveStatus("Google 登出失敗，請稍後再試。", "warning");
  } finally {
    googleLogoutButton.disabled = false;
  }
}

function formatComicDate(timestamp) {
  if (!timestamp) {
    return "未知時間";
  }

  return new Intl.DateTimeFormat("zh-TW", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(timestamp * 1000));
}

function getDownloadUrl(filename) {
  return `/api/comics/${encodeURIComponent(filename)}/download`;
}

function getArticleUrl(filename) {
  return `/api/comics/${encodeURIComponent(filename)}/article`;
}

function getComicDownloadUrl(comicOrFilename) {
  if (comicOrFilename && typeof comicOrFilename === "object") {
    if (comicOrFilename.storage === "drive" && comicOrFilename.drive_file_id) {
      return `/api/drive/files/${encodeURIComponent(comicOrFilename.drive_file_id)}/content`;
    }
    return getDownloadUrl(comicOrFilename.filename);
  }

  return getDownloadUrl(comicOrFilename);
}

function getComicArticleUrl(comicOrFilename) {
  if (comicOrFilename && typeof comicOrFilename === "object") {
    if (comicOrFilename.storage === "drive" && comicOrFilename.drive_storyboard_id) {
      return `/api/drive/files/${encodeURIComponent(comicOrFilename.drive_storyboard_id)}/article`;
    }
    return getArticleUrl(comicOrFilename.filename);
  }

  return getArticleUrl(comicOrFilename);
}

function getFilenameFromUrl(imageUrl) {
  if (!imageUrl) {
    return "";
  }

  const path = imageUrl.split("?")[0];
  const filename = path.substring(path.lastIndexOf("/") + 1);

  try {
    return decodeURIComponent(filename);
  } catch (error) {
    return filename;
  }
}

function hideComicContextMenu() {
  comicContextMenu.classList.add("hidden");
  contextComic = null;
}

function showComicContextMenu(event, comic) {
  event.preventDefault();
  event.stopPropagation();
  contextComic = comic;
  contextArticleButton.disabled = !comic?.has_article;
  contextRenameButton.disabled = comic?.storage === "drive";
  contextDeleteButton.disabled = comic?.storage === "drive";

  const menuWidth = 180;
  const menuHeight = 176;
  const x = Math.min(event.clientX, window.innerWidth - menuWidth - 10);
  const y = Math.min(event.clientY, window.innerHeight - menuHeight - 10);

  comicContextMenu.style.left = `${Math.max(10, x)}px`;
  comicContextMenu.style.top = `${Math.max(10, y)}px`;
  comicContextMenu.classList.remove("hidden");
}

function downloadComic(comicOrFilename) {
  const filename = typeof comicOrFilename === "object" ? comicOrFilename?.filename : comicOrFilename;
  if (!filename) {
    return;
  }

  const link = document.createElement("a");
  link.href = getComicDownloadUrl(comicOrFilename);
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
}

function openRenameDialog(filename) {
  renameTargetFilename = filename;
  renameInput.value = filename.replace(/\.png$/i, "");
  renameOverlay.classList.remove("hidden");
  renameDialog.classList.remove("hidden");

  requestAnimationFrame(() => {
    renameInput.focus();
    renameInput.select();
  });
}

function closeRenameDialog() {
  renameTargetFilename = "";
  renameInput.value = "";
  renameOverlay.classList.add("hidden");
  renameDialog.classList.add("hidden");
}

function getArticleFromStoryboard(storyboard) {
  if (!storyboard) {
    return "";
  }

  const directArticle = storyboard.source_article || storyboard.original_article || storyboard.article;
  if (directArticle) {
    return String(directArticle).trim();
  }

  const newsPreprocess = storyboard.news_preprocess || {};
  const title = String(newsPreprocess.clean_title || "").trim();
  const content = String(newsPreprocess.cleaned_content || "").trim();
  return [title, content].filter(Boolean).join("\n\n").trim();
}

function storyboardIncludesFilename(storyboard, filename) {
  if (!storyboard || !filename) {
    return false;
  }

  const urls = [
    storyboard.comic_page_url,
    storyboard.comic_scroll_url,
    ...(Array.isArray(storyboard.comic_page_urls) ? storyboard.comic_page_urls : []),
  ];

  return urls.map(getFilenameFromUrl).includes(filename);
}

function openArticleView(title, article) {
  articleViewTitle.textContent = title || "原始文章";
  articleViewText.textContent = article || "沒有保存原始文章。";
  articleViewOverlay.classList.toggle("hidden", document.body.classList.contains("comic-preview-open"));
  articleViewDialog.classList.remove("hidden");
  articleViewDialog.setAttribute("aria-hidden", "false");
}

function closeArticleView() {
  articleViewOverlay.classList.add("hidden");
  articleViewDialog.classList.add("hidden");
  articleViewDialog.setAttribute("aria-hidden", "true");
  articleViewText.textContent = "";
}

async function viewOriginalArticle(filename, fallbackTitle = "") {
  const shouldUseCurrentStoryboard = currentStoryboard && (
    !filename
    || filename === selectedComicFilename
    || filename === currentComicFilename
    || storyboardIncludesFilename(currentStoryboard, filename)
  );

  if (shouldUseCurrentStoryboard) {
    const cachedArticle = getArticleFromStoryboard(currentStoryboard);
    if (cachedArticle) {
      openArticleView(currentStoryboard.title || fallbackTitle || filename, cachedArticle);
      return;
    }
  }

  if (!filename) {
    window.alert("這張漫畫沒有可查詢的檔名。");
    return;
  }

  try {
    const comicForArticle = contextComic?.filename === filename ? contextComic : filename;
    const response = await fetch(getComicArticleUrl(comicForArticle));
    const data = await response.json();

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "無法載入原始文章"));
    }

    openArticleView(data.title || fallbackTitle || filename, data.article || "");
  } catch (error) {
    console.error(error);
    window.alert(error.message || "無法載入原始文章");
  }
}

function setHistoryDrawerMode(mode) {
  historyMode = mode === "favorites" ? "favorites" : "history";
  const heading = historyDrawer.querySelector(".history-heading h2");
  const kicker = historyDrawer.querySelector(".panel-kicker");

  if (heading) {
    heading.textContent = historyMode === "favorites" ? "喜愛漫畫" : "先前生成的漫畫";
  }
  if (kicker) {
    kicker.textContent = historyMode === "favorites" ? "Favorites" : "History";
  }
  historyEmpty.textContent = historyMode === "favorites"
    ? "目前還沒有加入喜愛的漫畫。"
    : "目前 Google Drive 裡還沒有可查看的漫畫。";
  refreshHistoryButton.textContent = historyMode === "favorites" ? "重新整理喜愛" : "重新整理雲端";
}

function getVisibleComics(comics) {
  if (historyMode !== "favorites") {
    return comics;
  }

  const favoriteComics = loadFavoriteComics();
  return comics.filter((comic) => favoriteComics.includes(comic.filename));
}

function rerenderCurrentHistory() {
  const visibleComics = getVisibleComics(allComicsCache);
  renderComicHistory(visibleComics);
  historyStatus.textContent = historyMode === "favorites"
    ? (visibleComics.length ? `共 ${visibleComics.length} 張喜愛漫畫` : "")
    : (allComicsCache.length ? `共 ${allComicsCache.length} 張漫畫` : "");
}

function openHistoryDrawer(mode = "history") {
  setHistoryDrawerMode(mode);
  document.body.classList.add("history-drawer-open");
  historyDrawer.setAttribute("aria-hidden", "false");
  historyOverlay.classList.remove("hidden");
  loadComicHistory();
}

function closeHistoryDrawer() {
  document.body.classList.remove("history-drawer-open");
  historyDrawer.setAttribute("aria-hidden", "true");
  historyOverlay.classList.add("hidden");
}

function openComicPreview(imageUrl, title, hasArticle = true, downloadUrl = "") {
  if (!imageUrl) {
    return;
  }

  comicPreviewImage.src = imageUrl;
  comicPreviewImage.alt = title ? `放大的歷史漫畫：${title}` : "放大的歷史漫畫";
  comicPreviewTitle.textContent = title || "漫畫預覽";
  selectedComicFilename = title || "";
  selectedComicDownloadUrl = downloadUrl || "";
  selectedComicHasArticle = Boolean(hasArticle || getArticleFromStoryboard(currentStoryboard));
  closeArticleView();
  if (selectedComicFilename) {
    previewDownloadLink.href = selectedComicDownloadUrl || getDownloadUrl(selectedComicFilename);
    previewDownloadLink.setAttribute("download", selectedComicFilename);
  } else {
    previewDownloadLink.href = imageUrl;
    previewDownloadLink.removeAttribute("download");
  }
  syncPreviewFavoriteButton();
  comicPreviewOverlay.classList.remove("hidden");
  comicPreviewModal.classList.remove("hidden");
  comicPreviewModal.setAttribute("aria-hidden", "false");
  document.body.classList.add("comic-preview-open");
  if (selectedComicHasArticle) {
    viewOriginalArticle(selectedComicFilename || currentComicFilename, comicPreviewTitle.textContent);
  }
  revealPreviewControls();
  schedulePreviewControlsCollapse(3200);
}

function closeComicPreview() {
  closeArticleView();
  document.body.classList.remove("comic-preview-open");
  clearTimeout(previewControlsTimer);
  revealPreviewControls();
  comicPreviewModal.setAttribute("aria-hidden", "true");
  window.setTimeout(() => {
    if (!document.body.classList.contains("comic-preview-open")) {
      comicPreviewOverlay.classList.add("hidden");
      comicPreviewModal.classList.add("hidden");
      comicPreviewImage.removeAttribute("src");
      previewDownloadLink.removeAttribute("href");
      selectedComicFilename = "";
      selectedComicDownloadUrl = "";
      selectedComicHasArticle = false;
      syncPreviewFavoriteButton();
    }
  }, 240);
}

function returnToComicHistory() {
  closeComicPreview();
  window.setTimeout(() => {
    openHistoryDrawer(historyMode);
  }, 240);
}

async function loadComicStoryboard(comicOrFilename) {
  const isDriveComic = comicOrFilename && typeof comicOrFilename === "object" && comicOrFilename.storage === "drive";
  const filename = isDriveComic ? comicOrFilename.filename : comicOrFilename;
  const storyboardUrl = isDriveComic
    ? `/api/drive/files/${encodeURIComponent(comicOrFilename.drive_storyboard_id)}/storyboard`
    : `/api/comics/${encodeURIComponent(filename)}/storyboard`;
  const response = await fetch(storyboardUrl);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(getErrorMessage(data, "無法讀取漫畫編輯資料"));
  }

  return data.storyboard;
}

async function selectHistoryComic(comic) {
  let imageUrl = comic?.url;
  const title = comic?.filename;
  if (!imageUrl) {
    return;
  }

  errorMessage.textContent = "";
  currentStoryboard = null;

  if (comic.editable) {
    try {
      currentStoryboard = await loadComicStoryboard(comic);
      imageUrl = comic.storage === "drive" ? imageUrl : currentStoryboard?.comic_scroll_url || imageUrl;
    } catch (error) {
      console.error(error);
      historyStatus.textContent = error.message || "無法讀取漫畫編輯資料";
    }
  }

  summaryText.textContent = "已選取先前生成的漫畫。";
  renderFidelityReport(currentStoryboard?.story_fidelity_report);
  resultSection.classList.remove("hidden");
  resultPlaceholder.classList.add("hidden");
  showComicPages(
    comic.storage === "drive" ? [imageUrl] : currentStoryboard?.comic_page_urls || [imageUrl],
    comic.storage === "drive" ? imageUrl : currentStoryboard?.comic_scroll_url || imageUrl
  );
  closeHistoryDrawer();
  openComicPreview(
    imageUrl,
    title,
    comic.has_article || Boolean(getArticleFromStoryboard(currentStoryboard)),
    getComicDownloadUrl(comic)
  );
}

function openCurrentResultPreview() {
  const imageUrl = comicImage.getAttribute("src");
  if (!imageUrl || comicImageFrame.classList.contains("hidden")) {
    return;
  }

  const filename = getFilenameFromUrl(imageUrl);
  comicImageFrame.classList.remove("is-expanding");
  void comicImageFrame.offsetWidth;
  comicImageFrame.classList.add("is-expanding");
  window.setTimeout(() => {
    openComicPreview(imageUrl, filename || "漫畫預覽", Boolean(getArticleFromStoryboard(currentStoryboard)));
  }, 260);
}

async function deleteHistoryComic(filename) {
  if (!filename) {
    return;
  }

  const shouldDelete = window.confirm(`確定要刪除 ${filename} 嗎？`);
  if (!shouldDelete) {
    return;
  }

  try {
    const response = await fetch(`/api/comics/${encodeURIComponent(filename)}`, {
      method: "DELETE",
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "刪除失敗"));
    }

    if (selectedComicFilename === filename) {
      closeComicPreview();
    }

    setFavoriteComic(filename, false);
    if (currentComicFilename === filename) {
      currentComicFilename = "";
      syncFavoriteButton();
    }
    await loadComicHistory();
    window.alert(`已刪除 ${data.filename}`);
  } catch (error) {
    console.error(error);
    historyStatus.textContent = error.message || "刪除失敗";
  }
}

async function renameHistoryComic(filename) {
  if (!filename) {
    return;
  }

  const nextName = renameInput.value.trim();
  if (!nextName || nextName === filename || `${nextName}.png` === filename) {
    return;
  }

  try {
    const response = await fetch(`/api/comics/${encodeURIComponent(filename)}/rename`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ filename: nextName }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "重新命名失敗"));
    }

    if (selectedComicFilename === filename) {
      selectedComicFilename = data.filename;
      comicPreviewTitle.textContent = data.filename;
      comicPreviewImage.src = data.url;
      previewDownloadLink.href = getDownloadUrl(data.filename);
      previewDownloadLink.setAttribute("download", data.filename);
      syncPreviewFavoriteButton();
      showComicPages(currentStoryboard?.comic_page_urls || [data.url], currentStoryboard?.comic_scroll_url || data.url);
    }

    renameFavoriteComic(filename, data.filename);
    if (currentComicFilename === filename) {
      currentComicFilename = data.filename;
      syncFavoriteButton();
    }
    await loadComicHistory();
    closeRenameDialog();
    window.alert(`已重新命名為 ${data.filename}`);
  } catch (error) {
    console.error(error);
    historyStatus.textContent = error.message || "重新命名失敗";
    window.alert(error.message || "重新命名失敗");
  }
}

function renderComicHistory(comics) {
  comicHistory.replaceChildren();
  historyEmpty.classList.toggle("hidden", comics.length > 0);
  const favoriteComics = loadFavoriteComics();

  for (const comic of comics) {
    const card = document.createElement("article");
    card.className = "history-card";

    const button = document.createElement("button");
    button.className = "history-card-button";
    button.type = "button";
    button.setAttribute("aria-label", `查看 ${comic.filename}`);
    button.addEventListener("click", () => selectHistoryComic(comic));
    button.addEventListener("contextmenu", (event) => showComicContextMenu(event, comic));
    card.addEventListener("contextmenu", (event) => showComicContextMenu(event, comic));

    const isFavorite = favoriteComics.includes(comic.filename);
    const favoriteButton = document.createElement("button");
    favoriteButton.className = "history-favorite-button";
    favoriteButton.type = "button";
    favoriteButton.textContent = isFavorite ? "♥" : "♡";
    favoriteButton.classList.toggle("is-favorite", isFavorite);
    favoriteButton.setAttribute("aria-label", isFavorite ? `移除喜愛 ${comic.filename}` : `加入喜愛 ${comic.filename}`);
    favoriteButton.title = isFavorite ? "移除喜愛" : "加入喜愛";
    favoriteButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      setFavoriteComic(comic.filename, !isFavoriteComic(comic.filename));
      rerenderCurrentHistory();
    });

    const image = document.createElement("img");
    image.src = comic.url;
    image.alt = comic.filename;
    image.loading = "lazy";

    const meta = document.createElement("div");
    meta.className = "history-meta";

    const name = document.createElement("span");
    name.textContent = comic.filename;

    const date = document.createElement("time");
    const pageLabel = comic.page_count > 1 ? ` · ${comic.page_count} 頁` : "";
    const storageLabel = comic.storage === "drive" ? " · 雲端" : "";
    date.textContent = comic.editable
      ? `${formatComicDate(comic.created_at)} · 可編輯${pageLabel}${storageLabel}`
      : `${formatComicDate(comic.created_at)}${pageLabel}${storageLabel}`;

    meta.append(name, date);
    button.append(image, meta);
    card.append(button, favoriteButton);
    comicHistory.append(card);
  }
}

async function loadComicHistory() {
  historyStatus.textContent = historyMode === "favorites" ? "載入喜愛漫畫中..." : "載入 Google Drive 漫畫中...";
  refreshHistoryButton.disabled = true;

  try {
    const response = await fetch("/api/comics/history");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "無法載入歷史漫畫"));
    }

    allComicsCache = Array.isArray(data.comics) ? data.comics : [];
    rerenderCurrentHistory();
    if (data.drive_error) {
      historyStatus.textContent += `（雲端載入失敗：${data.drive_error}）`;
    }
  } catch (error) {
    console.error(error);
    historyStatus.textContent = error.message || "無法載入歷史漫畫";
    allComicsCache = [];
    renderComicHistory([]);
  } finally {
    refreshHistoryButton.disabled = false;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const article = articleInput.value.trim();
  if (!article) {
    errorMessage.textContent = "請先輸入文章或社群文案";
    return;
  }

  resetResult();
  setLoading(true);
  startProgress();
  setDriveStatus("生成完成後會嘗試同步到 Google Drive...");
  let didGenerate = false;

  try {
    const response = await fetch("/api/story/generate-from-article", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        article,
        generation_settings: getGenerationSettings(),
      }),
    });

    const data = await response.json();
    console.log("API result:", data);

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "生成失敗，請稍後再試"));
    }

    summaryText.textContent = data.summary || data.title || "已完成漫畫生成";
    currentStoryboard = data.storyboard || null;
    renderFidelityReport(data.story_fidelity_report || currentStoryboard?.story_fidelity_report);
    resultSection.classList.remove("hidden");
    resultPlaceholder.classList.add("hidden");
    showComicPages(data.comic_page_urls || [data.comic_image_url], data.comic_scroll_url || data.comic_image_url);
    renderDriveUploadStatus(data.drive_upload, data.drive_upload_error);
    await loadComicHistory();
    didGenerate = true;
  } catch (error) {
    console.error(error);
    errorMessage.textContent = error.message || "生成失敗，請稍後再試";
    resultPlaceholder.classList.remove("hidden");
    resultPlaceholder.querySelector("p").textContent = "生成失敗，請調整輸入內容後再試一次。";
  } finally {
    finishProgress(didGenerate);
    setLoading(false);
  }
});

openHistoryButton.addEventListener("click", () => openHistoryDrawer("history"));
toggleSettingsButton.addEventListener("click", () => {
  generationSettingsPanel.classList.toggle("hidden");
  toggleSettingsButton.classList.toggle(
    "is-active",
    !generationSettingsPanel.classList.contains("hidden")
  );
});
[stylePresetInput].filter(Boolean).forEach((input) => {
  input.addEventListener("input", () => {
    syncStyleDescription();
    saveGenerationSettings();
  });
  input.addEventListener("change", () => {
    syncStyleDescription();
    saveGenerationSettings();
  });
});
sampleArticleButton.addEventListener("click", loadSampleArticle);
clearInputButton.addEventListener("click", () => {
  articleInput.value = "";
  articleInput.focus();
  errorMessage.textContent = "";
});
favoriteResultButton.addEventListener("click", () => {
  openHistoryDrawer("favorites");
});
googleLogoutButton?.addEventListener("click", logoutGoogle);
previewFavoriteButton.addEventListener("click", () => {
  if (!selectedComicFilename) {
    return;
  }

  setFavoriteComic(selectedComicFilename, !isFavoriteComic(selectedComicFilename));
  syncPreviewFavoriteButton();
  rerenderCurrentHistory();
});
comicPreviewActions.addEventListener("mouseenter", () => {
  revealPreviewControls();
  clearTimeout(previewControlsTimer);
});
comicPreviewActions.addEventListener("mouseleave", () => {
  schedulePreviewControlsCollapse(1200);
});
comicPreviewActions.addEventListener("focusin", () => {
  revealPreviewControls();
  clearTimeout(previewControlsTimer);
});
comicPreviewActions.addEventListener("focusout", () => {
  schedulePreviewControlsCollapse(1200);
});
document.addEventListener("mousemove", handlePreviewPointerMove);
comicImage.addEventListener("click", openCurrentResultPreview);
closeHistoryButton.addEventListener("click", closeHistoryDrawer);
historyOverlay.addEventListener("click", closeHistoryDrawer);
refreshHistoryButton.addEventListener("click", loadComicHistory);
comicPreviewOverlay.addEventListener("click", closeComicPreview);
closePreviewButton.addEventListener("click", returnToComicHistory);
dismissPreviewButton.addEventListener("click", closeComicPreview);
articleViewOverlay.addEventListener("click", closeArticleView);
closeArticleViewButton.addEventListener("click", closeArticleView);
contextArticleButton.addEventListener("click", () => {
  if (contextComic) {
    viewOriginalArticle(contextComic.filename, contextComic.filename);
  }
  hideComicContextMenu();
});
contextDownloadButton.addEventListener("click", () => {
  if (contextComic) {
    downloadComic(contextComic);
  }
  hideComicContextMenu();
});
contextRenameButton.addEventListener("click", () => {
  if (contextComic) {
    openRenameDialog(contextComic.filename);
  }
  hideComicContextMenu();
});
contextDeleteButton.addEventListener("click", () => {
  if (contextComic) {
    deleteHistoryComic(contextComic.filename);
  }
  hideComicContextMenu();
});
document.addEventListener("click", (event) => {
  if (!comicContextMenu.contains(event.target)) {
    hideComicContextMenu();
  }
});
window.addEventListener("resize", hideComicContextMenu);
window.addEventListener("scroll", hideComicContextMenu, true);
renameOverlay.addEventListener("click", closeRenameDialog);
cancelRenameButton.addEventListener("click", closeRenameDialog);
renameDialog.addEventListener("submit", (event) => {
  event.preventDefault();
  renameHistoryComic(renameTargetFilename);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (document.body.classList.contains("comic-preview-open")) {
      closeComicPreview();
      return;
    }

    if (!articleViewDialog.classList.contains("hidden")) {
      closeArticleView();
      return;
    }

    if (!renameDialog.classList.contains("hidden")) {
      closeRenameDialog();
      return;
    }

    if (!comicContextMenu.classList.contains("hidden")) {
      hideComicContextMenu();
      return;
    }

    if (document.body.classList.contains("history-drawer-open")) {
      closeHistoryDrawer();
    }
  }
});
loadGenerationSettings();
syncStyleDescription();
attachPressFeedback();
syncGoogleAuthStatus();
loadComicHistory();
