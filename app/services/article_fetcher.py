from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


MAX_ARTICLE_BYTES = 2_000_000
REQUEST_TIMEOUT_SECONDS = 12
URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)
CHARSET_RE = re.compile(r"charset=['\"]?([\w.-]+)", re.IGNORECASE)


class ArticleFetchError(ValueError):
    pass


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_news_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass(frozen=True)
class FetchedArticle:
    url: str
    title: str
    text: str

    @property
    def article_text(self) -> str:
        return f"{self.title}\n\n{self.text}".strip() if self.title else self.text


class _ArticleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._tag_stack: list[str] = []
        self._capture_stack: list[str] = []
        self._skip_depth = 0
        self._title_parts: list[str] = []
        self._text_blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self._tag_stack.append(tag)

        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return

        if self._skip_depth:
            return

        attr_map = {name.lower(): value or "" for name, value in attrs}
        semantic_hint = " ".join(
            [
                attr_map.get("id", ""),
                attr_map.get("class", ""),
                attr_map.get("itemprop", ""),
                attr_map.get("property", ""),
            ]
        ).lower()
        if tag in {"title", "h1", "h2", "p", "article", "main"} or any(
            hint in semantic_hint for hint in ("article", "content", "story", "entry", "post")
        ):
            self._capture_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._skip_depth and tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth -= 1

        if self._capture_stack and self._capture_stack[-1] == tag:
            self._capture_stack.pop()

        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return

        text = normalize_whitespace(data)
        if not text:
            return

        current_tag = self._tag_stack[-1] if self._tag_stack else ""
        if current_tag == "title":
            self._title_parts.append(text)
            return

        if self._capture_stack or current_tag in {"h1", "h2", "p"}:
            self._text_blocks.append(text)

    def parsed_article(self) -> tuple[str, str]:
        title = normalize_whitespace(" ".join(self._title_parts))
        blocks = dedupe_blocks(self._text_blocks)
        text = "\n".join(block for block in blocks if len(block) >= 12)
        return title, text


def normalize_whitespace(text: str) -> str:
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def dedupe_blocks(blocks: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for block in blocks:
        cleaned = normalize_whitespace(block)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def looks_like_url(text: str) -> bool:
    return URL_RE.match(text.strip()) is not None


def _is_public_hostname(hostname: str) -> bool:
    if not hostname:
        return False

    if hostname.lower() in {"localhost", "localhost.localdomain"}:
        return False

    try:
        addresses = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise ArticleFetchError(f"Cannot resolve news URL host: {e}") from e

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
    return True


def validate_public_news_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ArticleFetchError("News URL must start with http:// or https://.")
    if not parsed.hostname:
        raise ArticleFetchError("News URL is missing a hostname.")
    if not _is_public_hostname(parsed.hostname):
        raise ArticleFetchError("News URL must point to a public website.")
    return parsed.geturl()


def _detect_encoding(content_type: str, html_bytes: bytes) -> str:
    header_match = CHARSET_RE.search(content_type or "")
    if header_match:
        return header_match.group(1)

    sample = html_bytes[:4096].decode("ascii", errors="ignore")
    meta_match = CHARSET_RE.search(sample)
    return meta_match.group(1) if meta_match else "utf-8"


def fetch_news_article(url: str) -> FetchedArticle:
    safe_url = validate_public_news_url(url)
    request = Request(
        safe_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; StudentComicGenerator/1.0)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )

    try:
        opener = build_opener(_SafeRedirectHandler)
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type.lower() and "application/xhtml+xml" not in content_type.lower():
                raise ArticleFetchError("News URL did not return an HTML page.")
            html_bytes = response.read(MAX_ARTICLE_BYTES + 1)
    except HTTPError as e:
        raise ArticleFetchError(f"News URL returned HTTP {e.code}.") from e
    except URLError as e:
        raise ArticleFetchError(f"Could not read news URL: {e.reason}") from e
    except TimeoutError as e:
        raise ArticleFetchError("News URL timed out.") from e

    if len(html_bytes) > MAX_ARTICLE_BYTES:
        raise ArticleFetchError("News URL response is too large.")

    encoding = _detect_encoding(content_type, html_bytes)
    html = html_bytes.decode(encoding, errors="replace")
    parser = _ArticleHTMLParser()
    parser.feed(html)
    title, text = parser.parsed_article()

    if len(text) < 80:
        raise ArticleFetchError("Could not find enough article text on that page.")

    return FetchedArticle(url=safe_url, title=title[:120], text=text)
