from __future__ import annotations

import random
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.services.article_fetcher import ArticleFetchError, fetch_news_article
from app.services.google_llm_service import generate_article_from_google_news_digest
from app.services.news_cleaner import clean_copied_news_article


GOOGLE_NEWS_TOP_STORIES_RSS = "https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
REQUEST_TIMEOUT_SECONDS = 12
MAX_RSS_BYTES = 1_000_000
MIN_FALLBACK_DIGEST_CHARS = 20


class GoogleNewsFetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoogleNewsItem:
    title: str
    link: str
    source: str
    published: str
    summary: str


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = normalize_space(data)
        if text:
            self._parts.append(text)

    def text(self) -> str:
        return "\n".join(self._parts)


class _GoogleNewsSummaryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_link = False
        self._in_font = False
        self._current_title: list[str] = []
        self._current_source: list[str] = []
        self.items: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._in_link = True
            self._current_title = []
        elif tag == "font":
            self._in_font = True
            self._current_source = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self._in_link = False
        elif tag == "font":
            self._in_font = False
        elif tag == "li":
            title = normalize_space(" ".join(self._current_title))
            source = normalize_space(" ".join(self._current_source))
            if title:
                self.items.append((title, source))
            self._current_title = []
            self._current_source = []

    def handle_data(self, data: str) -> None:
        text = normalize_space(data)
        if not text:
            return
        if self._in_link:
            self._current_title.append(text)
        elif self._in_font:
            self._current_source.append(text)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def normalize_google_news_title(title: str, source: str = "") -> str:
    title = normalize_space(title)
    source = normalize_space(source)
    if source and title.endswith(f" - {source}"):
        title = title[: -(len(source) + 3)].strip()
    title = re.sub(r"\s+-\s+(Google 新聞|Yahoo新聞|自由時報|中央社|UDN)$", "", title).strip()
    title = re.sub(r"\s*[｜|]\s*[^｜|]{1,12}\s*[｜|]\s*新聞\s*$", "", title).strip()
    title = re.sub(r"\s*[｜|]\s*新聞\s*$", "", title).strip()
    return title


def html_to_text(html: str) -> str:
    parser = _TextHTMLParser()
    parser.feed(html or "")
    return parser.text()


def clean_google_news_summary(summary_html: str, title: str, source: str) -> str:
    list_parser = _GoogleNewsSummaryParser()
    list_parser.feed(summary_html or "")
    normalized_title = normalize_google_news_title(title, source)
    if list_parser.items:
        related: list[str] = []
        seen_titles: set[str] = set()
        for item_title, item_source in list_parser.items:
            clean_title = normalize_google_news_title(item_title, item_source)
            if not clean_title or clean_title == normalized_title or clean_title in seen_titles:
                continue
            seen_titles.add(clean_title)
            related.append(f"相關報導：{clean_title}（{item_source}）" if item_source else f"相關報導：{clean_title}")
        return "\n".join(related)

    lines = [normalize_space(line) for line in html_to_text(summary_html).splitlines()]
    noise_fragments = (
        "Google 新聞",
        "查看完整報導",
        "加入為 Google 偏好來源",
        "加入為Google偏好來源",
        "Full Coverage",
        "View Full Coverage",
    )

    cleaned: list[str] = []
    seen: set[str] = set()
    normalized_source = normalize_space(source)

    for line in lines:
        if not line:
            continue
        if any(fragment in line for fragment in noise_fragments):
            continue
        if line in {normalized_title, normalized_source}:
            continue
        if line in seen:
            continue
        seen.add(line)
        cleaned.append(line)

    return "\n".join(cleaned)


def _read_google_news_rss() -> bytes:
    request = Request(
        GOOGLE_NEWS_TOP_STORIES_RSS,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; StudentComicGenerator/1.0)",
            "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            rss_bytes = response.read(MAX_RSS_BYTES + 1)
    except HTTPError as e:
        raise GoogleNewsFetchError(f"Google News returned HTTP {e.code}.") from e
    except URLError as e:
        raise GoogleNewsFetchError(f"Could not read Google News: {e.reason}") from e
    except TimeoutError as e:
        raise GoogleNewsFetchError("Google News request timed out.") from e

    if len(rss_bytes) > MAX_RSS_BYTES:
        raise GoogleNewsFetchError("Google News RSS response is too large.")
    return rss_bytes


def _find_text(element: ET.Element, name: str) -> str:
    child = element.find(name)
    return normalize_space(child.text or "") if child is not None else ""


def fetch_google_news_items() -> list[GoogleNewsItem]:
    rss_bytes = _read_google_news_rss()
    try:
        root = ET.fromstring(rss_bytes)
    except ET.ParseError as e:
        raise GoogleNewsFetchError("Google News RSS could not be parsed.") from e

    items: list[GoogleNewsItem] = []
    for item in root.findall("./channel/item"):
        title = _find_text(item, "title")
        link = _find_text(item, "link")
        description = _find_text(item, "description")
        published = _find_text(item, "pubDate")
        source_node = item.find("source")
        source = normalize_space(source_node.text or "") if source_node is not None else ""
        title = normalize_google_news_title(title, source)
        summary = clean_google_news_summary(description, title, source)

        if title and link:
            items.append(
                GoogleNewsItem(
                    title=title,
                    link=link,
                    source=source,
                    published=published,
                    summary=summary,
                )
            )

    if not items:
        raise GoogleNewsFetchError("Google News did not return any focus news items.")
    return items


def _fallback_article_from_item(item: GoogleNewsItem) -> dict | None:
    digest = "\n".join(line for line in [item.title, item.summary] if line).strip()
    if len(digest) < MIN_FALLBACK_DIGEST_CHARS:
        return None

    generated = generate_article_from_google_news_digest(item.title, item.source, digest)
    title = str(generated.get("title") or item.title).strip()
    article = str(generated.get("article") or "").strip()
    cleaned = clean_copied_news_article(f"{title}\n\n{article}")
    if len(cleaned.content) >= MIN_FALLBACK_DIGEST_CHARS:
        return {
            "title": cleaned.title,
            "article": cleaned.content,
            "removed_lines": cleaned.removed_lines,
        }
    return None


def fetch_random_google_focus_article(max_candidates: int = 8) -> dict:
    items = fetch_google_news_items()
    random.shuffle(items)

    fallback: dict | None = None
    fallback_item: GoogleNewsItem | None = None
    errors: list[str] = []

    for item in items[:max_candidates]:
        fallback = fallback or _fallback_article_from_item(item)
        fallback_item = fallback_item or (item if fallback else None)

        try:
            article = fetch_news_article(item.link)
        except ArticleFetchError as e:
            errors.append(f"{item.title}: {e}")
            continue

        cleaned = clean_copied_news_article(article.article_text)
        return {
            "title": cleaned.title,
            "article": cleaned.content,
            "source_url": article.url,
            "source_title": article.title or item.title,
            "source": item.source,
            "published": item.published,
            "removed_lines": cleaned.removed_lines,
            "source_type": "google_news_article",
        }

    if fallback and fallback_item:
        return {
            "title": fallback["title"],
            "article": fallback["article"],
            "source_url": fallback_item.link,
            "source_title": fallback_item.title,
            "source": fallback_item.source,
            "published": fallback_item.published,
            "removed_lines": fallback["removed_lines"],
            "source_type": "google_news_rss",
            "warnings": errors[:3],
        }

    detail = "; ".join(errors[:3]) if errors else "No usable Google News item was found."
    raise GoogleNewsFetchError(f"Could not fetch a usable Google News article. {detail}")
