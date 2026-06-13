from __future__ import annotations

import re
from dataclasses import dataclass


SOURCE_LINE_RE = re.compile(
    r"^(民視|中時|中央社|聯合|自由時報|TVBS|三立|東森|中天|風傳媒|鏡週刊|Yahoo|NOWnews|ETtoday)"
)
DATE_LINE_RE = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日.*?(上午|下午|週|星期)")
CAPTION_RE = re.compile(r"[（(].{0,20}(圖|照片|翻攝|資料照|示意圖)[／/]")
BYLINE_RE = re.compile(r"^(政治|社會|生活|國際|財經|娛樂|體育|地方)?中心／")
RELATED_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$")
TITLE_SOURCE_SUFFIX_RE = re.compile(
    r"\s*[｜|]\s*(東森新聞|民視新聞|中時新聞網|中央社|聯合新聞網|自由時報|TVBS新聞網|三立新聞網|ETtoday新聞雲|Yahoo奇摩新聞|Google 新聞)\s*$"
)
STOP_SECTION_RE = re.compile(
    r"^(廣告\s*/|請繼續往下閱讀|查看完整報導|東森新聞\s*\d+\s*頻道|service@|東森電視事業股份有限公司)"
)
PROMO_LINE_RE = re.compile(
    r"(下載東森App|Copyright\s*©|Eastern Broadcasting|豪禮送不停|爆品\$|618年中盛典|線上直播|Google 新聞|Full Coverage|View Full Coverage)"
)


@dataclass(frozen=True)
class CleanedArticle:
    title: str
    content: str
    removed_lines: list[str]

    @property
    def text(self) -> str:
        return f"{self.title}\n\n{self.content}".strip()


def normalize_article_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\u3000", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_title(title: str) -> str:
    title = normalize_article_text(title)
    title = TITLE_SOURCE_SUFFIX_RE.sub("", title)
    return title.strip(" -｜|")


def is_noise_line(line: str, title: str = "") -> bool:
    compact = line.strip()
    if not compact:
        return True

    exact_noise = {
        "廣告",
        "延伸閱讀",
        "加入為 Google 偏好來源",
        "加入為Google偏好來源",
        "查看完整報導",
        "（另開新視窗）",
        "(另開新視窗)",
    }
    if compact in exact_noise:
        return True
    if STOP_SECTION_RE.search(compact):
        return True
    if PROMO_LINE_RE.search(compact):
        return True
    if compact.isdigit():
        return True
    if RELATED_DATE_RE.match(compact):
        return True
    if title and normalize_title(compact) == normalize_title(title):
        return True
    if CAPTION_RE.search(compact):
        return True
    if DATE_LINE_RE.search(compact):
        return True
    if SOURCE_LINE_RE.match(compact) and len(compact) <= 12:
        return True
    return False


def should_stop_at_line(lines: list[str], index: int, kept: list[str]) -> bool:
    line = lines[index].strip()
    if STOP_SECTION_RE.search(line):
        return True
    if line == "廣告" or line.startswith("廣告 /"):
        return True
    if index + 1 < len(lines) and RELATED_DATE_RE.match(lines[index + 1].strip()) and len(kept) >= 4:
        return True
    return False


def looks_like_article_line(line: str) -> bool:
    compact = line.strip()
    if not compact:
        return False
    return (
        len(compact) >= 55
        or "：「" in compact
        or BYLINE_RE.match(compact) is not None
        or compact.endswith("。")
    )


def clean_copied_news_article(raw_article: str) -> CleanedArticle:
    normalized = normalize_article_text(raw_article)
    raw_lines = [line.strip() for line in normalized.splitlines()]
    original_lines = [line for line in raw_lines if line]
    title = normalize_title(original_lines[0])[:80] if original_lines else "AI 新聞漫畫"

    kept: list[str] = []
    removed: list[str] = []
    skip_related_lines = 0

    for index, line in enumerate(original_lines):
        if index == 0:
            kept.append(title)
            continue

        if should_stop_at_line(original_lines, index, kept):
            removed.extend(original_lines[index:])
            break

        if line == "延伸閱讀":
            removed.append(line)
            skip_related_lines = 8
            continue

        if skip_related_lines > 0:
            if looks_like_article_line(line) and not is_noise_line(line, title):
                skip_related_lines = 0
            else:
                removed.append(line)
                skip_related_lines -= 1
                continue

        if is_noise_line(line, title):
            removed.append(line)
            continue

        kept.append(line)

    deduped: list[str] = []
    for line in kept:
        if deduped and line == deduped[-1]:
            removed.append(line)
            continue
        deduped.append(line)

    clean_title = deduped[0][:80] if deduped else title
    content_lines = deduped[1:] if deduped and deduped[0] == clean_title else deduped
    content = "\n".join(content_lines).strip()
    if len(content) < 10:
        content = f"{content}\n請根據這段文字整理成一則清楚的新聞漫畫。".strip()

    return CleanedArticle(
        title=clean_title or "AI 新聞漫畫",
        content=content,
        removed_lines=removed,
    )
