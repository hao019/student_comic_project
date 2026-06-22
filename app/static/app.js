const form = document.querySelector("#comic-form");
const articleInput = document.querySelector("#article-input");
const sampleArticleButton = document.querySelector("#sample-article-button");
const sampleSourceLink = document.querySelector("#sample-source-link");
const clearInputButton = document.querySelector("#clear-input-button");
const toggleSettingsButton = document.querySelector("#toggle-settings-button");
const generationSettingsPanel = document.querySelector("#generation-settings-panel");
const stylePresetInput = document.querySelector("#style-preset");
const imageModelInput = document.querySelector("#image-model");
const styleDescription = document.querySelector("#style-description");
const generateButton = document.querySelector("#generate-button");
const statusMessage = document.querySelector("#status-message");
const errorMessage = document.querySelector("#error-message");
const toastStack = document.querySelector("#toast-stack");
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
const historySearchInput = document.querySelector("#history-search-input");
const historyCategoryTabs = document.querySelector("#history-category-tabs");
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
const previewAnalysisButton = document.querySelector("#preview-analysis-button");
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
const homeNavButton = document.querySelector("#home-nav-button");
const libraryNavButton = document.querySelector("#library-nav-button");
const analysisNavButton = document.querySelector("#analysis-nav-button");
const generateView = document.querySelector("#generate-view");
const analysisView = document.querySelector("#analysis-view");
const analysisBackButton = document.querySelector("#analysis-back-button");
const analysisEmpty = document.querySelector("#analysis-empty");
const analysisContent = document.querySelector("#analysis-content");
const analysisTitle = document.querySelector("#analysis-title");
const analysisArticle = document.querySelector("#analysis-article");
const analysisUnderstanding = document.querySelector("#analysis-understanding");
const analysisPanels = document.querySelector("#analysis-panels");
const analysisPrompt = document.querySelector("#analysis-prompt");
const analysisFinalImage = document.querySelector("#analysis-final-image");
const analysisImageModelLabel = document.querySelector("#analysis-image-model-label");
const historyAllButton = document.querySelector("#history-all-button");
const historyFavoritesButton = document.querySelector("#history-favorites-button");
let progressTimer = null;
let selectedComicFilename = "";
let contextComic = null;
let renameTargetFilename = "";
let currentStoryboard = null;
let currentComicFilename = "";
let currentAnalysisComic = null;
let currentAnalysisError = "";
let historyMode = "history";
let allComicsCache = [];
let activeHistoryCategory = "all";
let previewControlsTimer = null;
let selectedComicHasArticle = false;

function showToast(message, variant = "status", duration = 3600) {
  if (!toastStack || !message) {
    return;
  }

  const toast = document.createElement("div");
  toast.className = `toast-message is-${variant}`;
  toast.textContent = message;
  toastStack.append(toast);

  window.requestAnimationFrame(() => toast.classList.add("is-visible"));
  window.setTimeout(() => {
    toast.classList.add("is-leaving");
    toast.classList.remove("is-visible");
    window.setTimeout(() => toast.remove(), 850);
  }, duration);
}
let selectedComicDownloadUrl = "";

const progressLabels = [
  "分析文章中...",
  "生成分鏡中...",
  "生成圖片中...",
  "合成漫畫中...",
];

const progressStepThresholds = [0, 22, 55, 78];
const estimatedGenerationMs = 52000;
const defaultImageModel = "sd35_medium_local";
const defaultStylePreset = "cinematic_anime";
const settingsStorageKey = "comicGenerationSettings:v3";
const favoritesStorageKey = "favoriteComics";
const lastAnalysisComicStorageKey = "lastAnalysisComic";
const historyCategories = [
  { id: "all", label: "全部", keywords: [] },
  { id: "lifestyle", label: "生活", keywords: ["生活", "天氣", "交通", "教育", "校園", "消費", "美食", "旅遊"] },
  { id: "politics", label: "政治", keywords: ["政治", "總統", "立法院", "行政院", "監察院", "選舉", "政黨", "市長", "川普"] },
  { id: "society", label: "社會", keywords: ["社會", "司法", "法院", "檢調", "警", "災", "事故", "案件"] },
  { id: "health", label: "健康", keywords: ["健康", "醫院", "醫療", "登革熱", "疫", "衛生", "公衛", "病"] },
  { id: "finance", label: "財經", keywords: ["財經", "商業", "投資", "市場", "IPO", "證券", "股", "經濟"] },
  { id: "entertainment", label: "娛樂", keywords: ["娛樂", "藝人", "男團", "影視", "明星", "表志勳"] },
  { id: "international", label: "國際", keywords: ["國際", "中國", "美國", "伊朗", "SpaceX", "外交"] },
  { id: "sports", label: "體育", keywords: ["體育", "棒球", "籃球", "足球", "賽", "選手"] },
  { id: "warm", label: "暖聞", keywords: ["暖聞", "善心", "公益", "感人", "助人", "溫馨"] },
  { id: "auto", label: "車訊", keywords: ["車訊", "汽車", "電動車", "機車", "車廠", "車款"] },
];
const comicStylePresets = [
  "cinematic_anime",
  "default",
  "monochrome_draft",
  "shonen",
  "gag_4koma",
  "infographic",
  "emotional",
  "taiwan_news",
  "internet_meme",
];
const imageModelOptions = [
  "gemini_image",
  "sd35_medium_local",
];
const comicStyleDescriptions = {
  cinematic_anime: "接近日系動畫電影感，乾淨漫畫線條、柔和光影、細緻背景與濕潤反光，適合你提供的參考風格。",
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

function setSampleSourceLink(sourceUrl) {
  if (!sampleSourceLink) {
    return;
  }

  const url = String(sourceUrl || "").trim();
  if (!url) {
    sampleSourceLink.classList.add("hidden");
    sampleSourceLink.removeAttribute("href");
    sampleSourceLink.textContent = "";
    sampleSourceLink.title = "";
    return;
  }

  sampleSourceLink.href = url;
  sampleSourceLink.textContent = url;
  sampleSourceLink.title = url;
  sampleSourceLink.classList.remove("hidden");
}

async function loadSampleArticle() {
  const originalText = sampleArticleButton.textContent;
  sampleArticleButton.disabled = true;
  sampleArticleButton.textContent = "抓取中...";
  errorMessage.textContent = "";
  statusMessage.textContent = "正在從 Google 新聞抓取隨機焦點新聞...";
  showToast("正在從 Google 新聞抓取隨機焦點新聞...", "status", 2200);

  try {
    const response = await fetch("/api/story/sample-article");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "Google 焦點新聞抓取失敗"));
    }

    const title = data.title ? `${data.title}\n\n` : "";
    articleInput.value = `${title}${data.article || sampleArticle}`.trim();
    const sourceUrl = data.source_url || data.sourceUrl || data.url || data.link;
    setSampleSourceLink(sourceUrl);
    statusMessage.textContent = sourceUrl
      ? "已抓取一則 Google 焦點新聞，來源網址已載入。"
      : "已抓取一則 Google 焦點新聞，但本次來源未提供網址。";
    showToast("已抓取一則 Google 焦點新聞", "success");
  } catch (error) {
    console.error(error);
    articleInput.value = sampleArticle;
    setSampleSourceLink("");
    errorMessage.textContent = "Google 焦點新聞抓取失敗，已改用本地範例。";
    showToast("Google 焦點新聞抓取失敗，已改用本地範例。", "error");
    statusMessage.textContent = "";
  } finally {
    sampleArticleButton.disabled = false;
    sampleArticleButton.textContent = originalText;
    articleInput.focus();
  }
}

function getGenerationSettings() {
  const imageModel = imageModelInput?.value || defaultImageModel;
  return {
    style_preset: imageModel === "sd35_medium_local"
      ? defaultStylePreset
      : stylePresetInput?.value || defaultStylePreset,
    image_model: imageModel,
  };
}

function syncStyleDescription() {
  if (!styleDescription) {
    return;
  }

  if (imageModelInput?.value === "sd35_medium_local") {
    styleDescription.textContent = "SD3.5 本地版目前固定使用電影感日系漫畫風格。";
    return;
  }

  const stylePreset = stylePresetInput?.value || defaultStylePreset;
  styleDescription.textContent = comicStyleDescriptions[stylePreset] || comicStyleDescriptions[defaultStylePreset];
}

function syncStyleControls() {
  if (!stylePresetInput) {
    return;
  }

  const isLocalModel = imageModelInput?.value === "sd35_medium_local";
  stylePresetInput.disabled = isLocalModel;
  if (isLocalModel) {
    stylePresetInput.value = defaultStylePreset;
  }
  syncStyleDescription();
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
      stylePresetInput.value = defaultStylePreset;
    }

    if (imageModelInput) {
      imageModelInput.value = imageModelOptions.includes(saved.image_model)
        ? saved.image_model
        : defaultImageModel;
    }
  } catch (error) {
    console.warn("Could not load generation settings", error);
  }

  syncStyleControls();
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
    showToast("AI 正在分析文章並合成最終漫畫圖...", "status", 2600);
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
    showToast("漫畫生成完成", "success");
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
  currentAnalysisComic = null;
  currentAnalysisError = "";
  renderAiAnalysis();
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
  if (!favoriteResultButton) {
    return;
  }

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
  revealPreviewControls();
}

function schedulePreviewControlsCollapse(delay = 2600) {
  clearTimeout(previewControlsTimer);
  revealPreviewControls();
}

function handlePreviewPointerMove(event) {
  revealPreviewControls();
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
  renderAiAnalysis();
}

function setActiveMainNav(activeButton) {
  [homeNavButton, libraryNavButton, analysisNavButton]
    .filter(Boolean)
    .forEach((button) => button.classList.toggle("is-active", button === activeButton));
}

function showMainView(viewName = "generate") {
  const isAnalysis = viewName === "analysis";
  const isLibrary = viewName === "library";
  if (isAnalysis) {
    closeHistoryDrawer();
    closeComicPreview();
    hideComicContextMenu();
  }

  generateView?.classList.toggle("hidden", isAnalysis || isLibrary);
  analysisView?.classList.toggle("hidden", !isAnalysis);
  historyDrawer?.classList.toggle("hidden", !isLibrary);
  historyDrawer?.setAttribute("aria-hidden", String(!isLibrary));
  setActiveMainNav(isAnalysis ? analysisNavButton : isLibrary ? libraryNavButton : homeNavButton);

  if (isAnalysis) {
    ensureAnalysisStoryboard();
  }
}

function formatJsonBlock(value) {
  return JSON.stringify(value, null, 2);
}

function getStoryboardTitle(storyboard) {
  return storyboard?.title
    || storyboard?.news_preprocess?.clean_title
    || storyboard?.news_preprocess?.fetched_title
    || "未命名新聞";
}

function getStoryboardArticle(storyboard) {
  return getArticleFromStoryboard(storyboard)
    || storyboard?.news_preprocess?.cleaned_content
    || storyboard?.news_preprocess?.original_input
    || "此作品沒有保存原始新聞內文。";
}

function getFinalComicUrl(storyboard) {
  return storyboard?.comic_scroll_url
    || storyboard?.comic_page_url
    || (Array.isArray(storyboard?.comic_page_urls) ? storyboard.comic_page_urls[0] : "")
    || currentAnalysisComic?.url
    || comicImage?.getAttribute("src")
    || "";
}

function getImageModelLabel(imageModel) {
  if (imageModel === "sd35_medium_local") {
    return "SD3.5 Medium 本地版";
  }
  return "Gemini Image";
}

function getStoryboardImageModel(storyboard) {
  return storyboard?.image_model
    || storyboard?.generation_settings?.image_model
    || defaultImageModel;
}

function renderAiAnalysis() {
  if (!analysisEmpty || !analysisContent) {
    return;
  }

  const storyboard = currentStoryboard;
  const comic = currentAnalysisComic;
  const hasStoryboard = storyboard && typeof storyboard === "object";
  const hasComic = comic && typeof comic === "object";
  const hasAnalysisTarget = hasStoryboard || hasComic;
  analysisEmpty.classList.toggle("hidden", hasAnalysisTarget);
  analysisContent.classList.toggle("hidden", !hasAnalysisTarget);

  if (!hasAnalysisTarget) {
    return;
  }

  if (analysisImageModelLabel) {
    analysisImageModelLabel.textContent = getImageModelLabel(
      hasStoryboard ? getStoryboardImageModel(storyboard) : comic.image_model || defaultImageModel
    );
  }

  if (!hasStoryboard) {
    analysisTitle.textContent = comic.title || comic.filename || "未命名漫畫";
    analysisArticle.textContent = currentAnalysisError
      ? `已找到作品，但讀取 storyboard 失敗：${currentAnalysisError}`
      : "這張作品只有漫畫圖片，沒有保存原始新聞或 storyboard JSON。請選取有流程資料的作品，或重新生成一篇漫畫後查看完整 AI 流程。";
    analysisUnderstanding.textContent = formatJsonBlock({
      status: "missing_storyboard",
      reason: currentAnalysisError || "此舊作品缺少 comic_data JSON，因此無法還原新聞理解、分鏡與 Prompt Builder。",
      filename: comic.filename || "",
      storage: comic.storage || "local",
    });
    analysisPanels.replaceChildren();
    const missingPanel = document.createElement("p");
    missingPanel.textContent = "沒有分鏡資料。作品庫中 editable 為 true 的作品才會有完整分鏡流程。";
    analysisPanels.append(missingPanel);
    analysisPrompt.textContent = "沒有保存最終 prompt。";

    const fallbackImageUrl = getFinalComicUrl(null);
    if (fallbackImageUrl) {
      analysisFinalImage.src = fallbackImageUrl;
      analysisFinalImage.classList.remove("hidden");
    } else {
      analysisFinalImage.removeAttribute("src");
      analysisFinalImage.classList.add("hidden");
    }
    return;
  }

  analysisTitle.textContent = getStoryboardTitle(storyboard);
  analysisArticle.textContent = getStoryboardArticle(storyboard);

  const understanding = {
    news_type: storyboard.news_type || storyboard.theme || "",
    tone: storyboard.tone || getMajorPanelEmotion(storyboard) || "",
    story_shape: storyboard.story_shape || "",
    summary: storyboard.summary || "",
  };
  analysisUnderstanding.textContent = formatJsonBlock(understanding);

  analysisPanels.replaceChildren();
  const panels = Array.isArray(storyboard.panels) ? storyboard.panels : [];
  panels.forEach((panel, index) => {
    const card = document.createElement("article");
    card.className = "analysis-panel-card";

    const title = document.createElement("strong");
    title.textContent = `Panel ${panel.panel_id || index + 1}: ${panel.panel_title || panel.title || "分鏡"}`;

    const pre = document.createElement("pre");
    pre.className = "analysis-pre code-pre";
    pre.textContent = formatJsonBlock({
      panel_id: panel.panel_id || panel.panel || index + 1,
      panel_title: panel.panel_title || panel.title || "",
      visual: panel.visual || panel.scene || "",
      speech: panel.speech || panel.dialogue || [],
      callouts: panel.callouts || [],
    });

    card.append(title, pre);
    analysisPanels.append(card);
  });

  if (!panels.length) {
    const emptyPanels = document.createElement("p");
    emptyPanels.textContent = "此作品沒有保存分鏡資料。";
    analysisPanels.append(emptyPanels);
  }

  analysisPrompt.textContent = storyboard.page_prompt || "此作品沒有保存最終 prompt。";

  const finalComicUrl = getFinalComicUrl(storyboard);
  if (finalComicUrl) {
    analysisFinalImage.src = finalComicUrl;
    analysisFinalImage.classList.remove("hidden");
  } else {
    analysisFinalImage.removeAttribute("src");
    analysisFinalImage.classList.add("hidden");
  }
}

function getMajorPanelEmotion(storyboard) {
  const panels = Array.isArray(storyboard?.panels) ? storyboard.panels : [];
  const emotion = panels.find((panel) => panel.emotion)?.emotion;
  return emotion || "";
}

function mountHistoryAsMainView() {
  const pageShell = document.querySelector(".page-shell");
  if (!pageShell || !historyDrawer) {
    return;
  }

  historyDrawer.classList.add("hidden");
  historyDrawer.setAttribute("aria-hidden", "true");
  pageShell.append(historyDrawer);
}

function getComicKey(comic) {
  return [comic?.storage || "local", comic?.filename || "", comic?.drive_storyboard_id || ""].join("|");
}

function rememberAnalysisComic(comic) {
  if (!comic?.filename) {
    return;
  }

  currentAnalysisComic = comic;
  try {
    localStorage.setItem(lastAnalysisComicStorageKey, JSON.stringify({
      filename: comic.filename,
      storage: comic.storage || "local",
      drive_storyboard_id: comic.drive_storyboard_id || "",
    }));
  } catch (error) {
    console.warn("Could not save last analysis comic", error);
  }
}

function getSavedAnalysisComicRef() {
  try {
    return JSON.parse(localStorage.getItem(lastAnalysisComicStorageKey) || "null");
  } catch (error) {
    console.warn("Could not read last analysis comic", error);
    return null;
  }
}

function findComicFromRef(comics, ref) {
  if (!Array.isArray(comics) || !ref) {
    return null;
  }

  return comics.find((comic) => {
    if (ref.drive_storyboard_id && comic.drive_storyboard_id === ref.drive_storyboard_id) {
      return true;
    }
    return comic.filename === ref.filename && (comic.storage || "local") === (ref.storage || "local");
  }) || null;
}

function shouldLoadComicStoryboard(comic) {
  return Boolean(comic) && (comic.storage === "local" || Boolean(comic.drive_storyboard_id));
}

async function ensureAnalysisStoryboard() {
  if (currentStoryboard || !shouldLoadComicStoryboard(currentAnalysisComic)) {
    renderAiAnalysis();
    return;
  }

  try {
    currentStoryboard = await loadComicStoryboard(currentAnalysisComic);
    currentAnalysisError = "";
  } catch (error) {
    console.warn("Could not restore analysis storyboard", error);
    currentAnalysisError = error.message || "未知錯誤";
  }
  renderAiAnalysis();
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
  contextDeleteButton.disabled = comic?.storage === "drive" && !comic?.drive_file_id;

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

function renderHistoryCategoryTabs() {
  if (!historyCategoryTabs) {
    return;
  }

  historyCategoryTabs.replaceChildren();

  historyCategories.forEach((category) => {
    const button = document.createElement("button");
    button.className = "history-category-tab";
    button.type = "button";
    button.textContent = category.label;
    button.classList.toggle("is-active", category.id === activeHistoryCategory);
    button.setAttribute("aria-pressed", category.id === activeHistoryCategory ? "true" : "false");
    button.addEventListener("click", () => {
      activeHistoryCategory = category.id;
      renderHistoryCategoryTabs();
      rerenderCurrentHistory();
    });
    historyCategoryTabs.append(button);
  });
}

function setHistoryDrawerMode(mode) {
  historyMode = mode === "favorites" ? "favorites" : "history";
  const heading = historyDrawer.querySelector(".history-heading h2");
  const kicker = historyDrawer.querySelector(".panel-kicker");
  const isFavorites = historyMode === "favorites";

  if (heading) {
    heading.textContent = isFavorites ? "喜愛漫畫" : "先前生成的漫畫";
  }
  if (kicker) {
    kicker.textContent = isFavorites ? "Favorites" : "History";
  }
  historyEmpty.textContent = isFavorites
    ? "目前還沒有加入喜愛的漫畫。"
    : "目前還沒有符合條件的漫畫。";
  refreshHistoryButton.textContent = isFavorites ? "重新整理喜愛" : "重新整理漫畫";
  historyAllButton?.classList.toggle("is-active", !isFavorites);
  historyFavoritesButton?.classList.toggle("is-active", isFavorites);
  historyAllButton?.setAttribute("aria-selected", String(!isFavorites));
  historyFavoritesButton?.setAttribute("aria-selected", String(isFavorites));
}

function normalizeSearchText(value) {
  return String(value || "").toLowerCase();
}

function getLooseSearchTerms(query) {
  const normalizedQuery = normalizeSearchText(query).trim();
  if (!normalizedQuery) {
    return [];
  }

  const spacedTerms = normalizedQuery.split(/\s+/).filter(Boolean);
  if (spacedTerms.length > 1) {
    return spacedTerms;
  }

  if (normalizedQuery.length <= 2) {
    return [normalizedQuery];
  }

  const terms = [normalizedQuery];
  for (let index = 0; index < normalizedQuery.length - 1; index += 1) {
    terms.push(normalizedQuery.slice(index, index + 2));
  }

  return [...new Set(terms)];
}

function hasLooseCharacterMatch(searchText, query) {
  const queryChars = [...new Set([...normalizeSearchText(query).replace(/\s+/g, "")])];
  if (queryChars.length < 3) {
    return false;
  }

  const hitCount = queryChars.filter((char) => searchText.includes(char)).length;
  return hitCount >= Math.ceil(queryChars.length * 0.6);
}

function getComicSearchText(comic) {
  return normalizeSearchText([
    comic?.filename,
    comic?.title,
    comic?.category,
    comic?.news_type,
    comic?.theme,
    comic?.summary,
    comic?.storage,
  ].filter(Boolean).join(" "));
}

function getComicCategory(comic) {
  const searchText = getComicSearchText(comic);
  const matchedCategory = historyCategories
    .filter((category) => category.id !== "all")
    .find((category) => category.keywords.some((keyword) => searchText.includes(normalizeSearchText(keyword))));

  return matchedCategory?.id || "";
}

function getHistoryCategoryLabel(categoryId) {
  return historyCategories.find((category) => category.id === categoryId)?.label || "全部";
}

function matchesHistoryCategory(comic) {
  if (activeHistoryCategory === "all") {
    return true;
  }

  return getComicCategory(comic) === activeHistoryCategory;
}

function matchesHistorySearch(comic) {
  const rawQuery = historySearchInput?.value || "";
  const queryTerms = getLooseSearchTerms(rawQuery);
  if (!queryTerms.length) {
    return true;
  }

  const searchText = getComicSearchText(comic);
  return queryTerms.some((term) => searchText.includes(term)) || hasLooseCharacterMatch(searchText, rawQuery);
}

function getVisibleComics(comics) {
  let visibleComics = comics;

  if (historyMode === "favorites") {
    const favoriteComics = loadFavoriteComics();
    visibleComics = visibleComics.filter((comic) => favoriteComics.includes(comic.filename));
  }

  return visibleComics
    .filter(matchesHistoryCategory)
    .filter(matchesHistorySearch);
}

function rerenderCurrentHistory() {
  const visibleComics = getVisibleComics(allComicsCache);
  renderComicHistory(visibleComics);
  const baseComics = historyMode === "favorites"
    ? allComicsCache.filter((comic) => loadFavoriteComics().includes(comic.filename))
    : allComicsCache;
  const filters = [];
  const query = historySearchInput?.value.trim();

  if (activeHistoryCategory !== "all") {
    filters.push(getHistoryCategoryLabel(activeHistoryCategory));
  }
  if (query) {
    filters.push(`搜尋「${query}」`);
  }

  historyStatus.textContent = baseComics.length
    ? `共 ${visibleComics.length} / ${baseComics.length} 張漫畫${filters.length ? `（${filters.join("、")}）` : ""}`
    : "";
}

function openHistoryDrawer(mode = "history") {
  setHistoryDrawerMode(mode);
  showMainView("library");
  loadComicHistory();
}

function closeHistoryDrawer() {
  document.body.classList.remove("history-drawer-open");
  historyDrawer.setAttribute("aria-hidden", "true");
  historyDrawer.classList.add("hidden");
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
  const isComicObject = comicOrFilename && typeof comicOrFilename === "object";
  const isDriveComic = isComicObject && comicOrFilename.storage === "drive";
  const filename = isComicObject ? comicOrFilename.filename : comicOrFilename;
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
  currentAnalysisError = "";
  rememberAnalysisComic(comic);

  if (shouldLoadComicStoryboard(comic)) {
    try {
      currentStoryboard = await loadComicStoryboard(comic);
      currentAnalysisError = "";
      imageUrl = comic.storage === "drive" ? imageUrl : currentStoryboard?.comic_scroll_url || imageUrl;
      renderAiAnalysis();
    } catch (error) {
      console.error(error);
      currentAnalysisError = error.message || "無法讀取 storyboard";
      historyStatus.textContent = error.message || "無法讀取漫畫編輯資料";
    }
  }

  summaryText.textContent = "已選取先前生成的漫畫。";
  showToast("已選取先前生成的漫畫。", "summary");
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

async function deleteHistoryComic(comicOrFilename) {
  const isComicObject = comicOrFilename && typeof comicOrFilename === "object";
  const filename = isComicObject ? comicOrFilename.filename : comicOrFilename;
  if (!filename) {
    return;
  }

  const shouldDelete = window.confirm(`確定要刪除 ${filename} 嗎？`);
  if (!shouldDelete) {
    return;
  }

  try {
    const isDriveComic = isComicObject && comicOrFilename.storage === "drive";
    let deleteUrl = `/api/comics/${encodeURIComponent(filename)}`;

    if (isDriveComic) {
      if (!comicOrFilename.drive_file_id) {
        throw new Error("這個 Google Drive 漫畫缺少檔案 ID，無法刪除。");
      }
      const params = new URLSearchParams();
      if (comicOrFilename.drive_storyboard_id) {
        params.set("storyboard_file_id", comicOrFilename.drive_storyboard_id);
      }
      deleteUrl = `/api/drive/files/${encodeURIComponent(comicOrFilename.drive_file_id)}${params.toString() ? `?${params}` : ""}`;
    }

    const response = await fetch(deleteUrl, {
      method: "DELETE",
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "刪除失敗"));
    }

    if (data.drive_delete_error) {
      historyStatus.textContent = `本機已刪除，但 Google Drive 刪除失敗：${data.drive_delete_error}`;
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
    window.alert(`已刪除 ${data.filename || filename}`);
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
    const categoryLabel = getHistoryCategoryLabel(getComicCategory(comic));
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

    const category = document.createElement("span");
    category.className = "history-card-category";
    category.textContent = categoryLabel;

    const date = document.createElement("time");
    const pageLabel = comic.page_count > 1 ? ` · ${comic.page_count} 頁` : "";
    const storageLabel = comic.storage === "drive" ? " · 雲端" : "";
    date.textContent = comic.editable
      ? `${formatComicDate(comic.created_at)} · 可編輯${pageLabel}${storageLabel}`
      : `${formatComicDate(comic.created_at)}${pageLabel}${storageLabel}`;

    meta.append(name);
    if (categoryLabel) {
      meta.append(category);
    }
    meta.append(date);
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
    const savedComic = findComicFromRef(allComicsCache, getSavedAnalysisComicRef());
    const currentComic = findComicFromRef(allComicsCache, currentAnalysisComic);
    const restorableComic = currentComic || savedComic || allComicsCache.find(shouldLoadComicStoryboard) || allComicsCache[0] || null;
    if (restorableComic && (!currentAnalysisComic || getComicKey(restorableComic) !== getComicKey(currentAnalysisComic))) {
      currentStoryboard = null;
      rememberAnalysisComic(restorableComic);
      ensureAnalysisStoryboard();
    }
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
    showToast("請先輸入文章或社群文案", "error");
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
    showToast(summaryText.textContent, "summary", 5200);
    currentStoryboard = data.storyboard || null;
    currentAnalysisError = "";
    const generatedImageUrl = data.comic_scroll_url || data.comic_image_url || currentStoryboard?.comic_scroll_url || currentStoryboard?.comic_page_url || "";
    if (generatedImageUrl) {
      rememberAnalysisComic({
        filename: getFilenameFromUrl(generatedImageUrl),
        url: generatedImageUrl,
        title: data.title || currentStoryboard?.title || "",
        storage: "local",
        editable: Boolean(currentStoryboard),
      });
    }
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
    showToast(errorMessage.textContent, "error", 5200);
    resultPlaceholder.classList.remove("hidden");
    resultPlaceholder.querySelector("p").textContent = "生成失敗，請調整輸入內容後再試一次。";
  } finally {
    finishProgress(didGenerate);
    setLoading(false);
  }
});

homeNavButton?.addEventListener("click", () => {
  showMainView("generate");
  setActiveMainNav(homeNavButton);
  window.scrollTo({ top: 0, behavior: "smooth" });
});
libraryNavButton?.addEventListener("click", () => {
  setActiveMainNav(libraryNavButton);
  openHistoryDrawer("history");
});
analysisNavButton?.addEventListener("click", () => showMainView("analysis"));
analysisBackButton?.addEventListener("click", () => showMainView("generate"));
openHistoryButton?.addEventListener("click", () => openHistoryDrawer("history"));
historyAllButton?.addEventListener("click", () => {
  setHistoryDrawerMode("history");
  rerenderCurrentHistory();
});
historyFavoritesButton?.addEventListener("click", () => {
  setHistoryDrawerMode("favorites");
  rerenderCurrentHistory();
});
toggleSettingsButton.addEventListener("click", () => {
  generationSettingsPanel.classList.toggle("hidden");
  toggleSettingsButton.classList.toggle(
    "is-active",
    !generationSettingsPanel.classList.contains("hidden")
  );
});
[stylePresetInput, imageModelInput].filter(Boolean).forEach((input) => {
  input.addEventListener("input", () => {
    syncStyleControls();
    saveGenerationSettings();
  });
  input.addEventListener("change", () => {
    syncStyleControls();
    saveGenerationSettings();
  });
});
sampleArticleButton.addEventListener("click", loadSampleArticle);
clearInputButton.addEventListener("click", () => {
  articleInput.value = "";
  setSampleSourceLink("");
  articleInput.focus();
  errorMessage.textContent = "";
});
favoriteResultButton?.addEventListener("click", () => {
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
previewAnalysisButton?.addEventListener("click", () => showMainView("analysis"));
comicImage.addEventListener("click", openCurrentResultPreview);
closeHistoryButton.addEventListener("click", () => showMainView("generate"));
historyOverlay.addEventListener("click", closeHistoryDrawer);
refreshHistoryButton.addEventListener("click", loadComicHistory);
historySearchInput?.addEventListener("input", rerenderCurrentHistory);
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
    deleteHistoryComic(contextComic);
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

    if (!historyDrawer.classList.contains("hidden")) {
      showMainView("generate");
    }
  }
});
mountHistoryAsMainView();
loadGenerationSettings();
syncStyleDescription();
attachPressFeedback();
renderHistoryCategoryTabs();
syncGoogleAuthStatus();
loadComicHistory();
