"""
IMS AstroBot — Official Site Fetching and Full-Site Crawler

Provides a single-page fetch helper plus a BFS site crawler that expands
same-domain links from a seed URL.

Each returned dict has the same shape as fetch_official_site_page():
    {
        "ok":        True,
        "url":       str,
        "domain":    str,
        "title":     str,
        "text":      str,
        "file_size": int,
        "depth":     int,   # extra field added by crawler
    }

Pages that fail (ok=False) are silently skipped.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from config import (
    OFFICIAL_SITE_ALLOWED_DOMAINS,
    OFFICIAL_SITE_TIMEOUT_SECONDS,
    OFFICIAL_SITE_USER_AGENT,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class CrawlConfig:
    """
    Controls how deep and how wide the crawler goes.

    Attributes:
        max_pages:        Hard cap on total pages fetched.
        max_depth:        BFS depth limit (seed URL = depth 0).
        delay_seconds:    Polite delay between requests (seconds).
        allowed_domains:  Forwarded to fetch_official_site_page().
                          None = use the value from config.py.
        timeout:          Per-request timeout forwarded to fetcher.
        skip_extensions:  File extensions to ignore (images, PDFs, etc.).
    """
    max_pages: int = 200
    max_depth: int = 4
    delay_seconds: float = 0.5
    allowed_domains: list[str] | None = None
    timeout: int | None = None
    skip_extensions: frozenset[str] = field(default_factory=lambda: frozenset({
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
        ".mp4", ".mp3", ".zip", ".rar", ".tar", ".gz",
        ".css", ".js", ".ico", ".woff", ".woff2", ".ttf",
        ".xls", ".xlsx", ".doc", ".docx", ".ppt", ".pptx",
    }))


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    """
    Strip fragments and trailing slashes so that:
        https://example.com/about#team  →  https://example.com/about
        https://example.com/about/     →  https://example.com/about
    This prevents the same page from being queued twice under different keys.
    """
    parsed = urlparse(url)
    clean = parsed._replace(fragment="")
    path = clean.path.rstrip("/") or "/"
    return urlunparse(clean._replace(path=path))


def _same_domain(url: str, seed_domain: str) -> bool:
    """Return True if `url` belongs to the same registered domain as the seed."""
    host = urlparse(url).hostname or ""
    host = host.lower().removeprefix("www.")
    return host == seed_domain or host.endswith(f".{seed_domain}")


def _should_skip(url: str, config: CrawlConfig) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in config.skip_extensions)


def _extract_text_from_html(html_bytes: bytes) -> tuple[str, str]:
    """Return a cleaned title/text pair from HTML bytes."""
    try:
        soup = BeautifulSoup(html_bytes, "lxml")
    except Exception:
        return "", ""

    for node in soup(["script", "style", "noscript"]):
        node.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = " ".join(soup.title.string.split())

    text = "\n".join(line.strip() for line in soup.get_text(separator="\n").splitlines())
    text = "\n".join(line for line in text.splitlines() if line)
    return title, text


def fetch_official_site_page(
    url: str,
    allowed_domains: list[str] | None = None,
    timeout: int | None = None,
) -> dict:
    """Fetch and clean a single public page from the official site."""
    url = _normalize_url(url.strip())
    parsed = urlparse(url)
    domain = (parsed.hostname or "").lower().removeprefix("www.")

    if not parsed.scheme or parsed.scheme not in {"http", "https"}:
        return {"ok": False, "url": url, "domain": domain, "error": "Invalid URL scheme"}

    effective_allowed = allowed_domains if allowed_domains is not None else OFFICIAL_SITE_ALLOWED_DOMAINS
    effective_allowed = [item.strip().lower().removeprefix("www.") for item in effective_allowed if item.strip()]
    if effective_allowed and not any(domain == allowed or domain.endswith(f".{allowed}") for allowed in effective_allowed):
        return {
            "ok": False,
            "url": url,
            "domain": domain,
            "error": f"URL domain '{domain}' is not in the allowed domains list",
        }

    try:
        import requests

        response = requests.get(
            url,
            headers={"User-Agent": OFFICIAL_SITE_USER_AGENT},
            timeout=timeout or OFFICIAL_SITE_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        response.raise_for_status()
        final_url = _normalize_url(response.url)
        final_domain = (urlparse(final_url).hostname or domain).lower().removeprefix("www.")
        title, text = _extract_text_from_html(response.content)
        if not title:
            title = parsed.path.strip("/").replace("/", " > ") or final_domain or url
        return {
            "ok": True,
            "url": final_url,
            "domain": final_domain,
            "title": title,
            "text": text,
            "file_size": len(response.content),
        }
    except Exception as exc:
        logger.debug("fetch_official_site_page failed for %s: %s", url, exc)
        return {"ok": False, "url": url, "domain": domain, "error": str(exc)}


def _extract_links(html_bytes: bytes, base_url: str) -> list[str]:
    """
    Parse raw HTML and return absolute URLs found in <a href> attributes.
    Only http/https links are returned; relative URLs are resolved against
    `base_url`.
    """
    try:
        soup = BeautifulSoup(html_bytes, "lxml")
    except Exception:
        return []

    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        href = str(tag["href"]).strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme in {"http", "https"}:
            links.append(_normalize_url(absolute))

    return links


# ---------------------------------------------------------------------------
# Crawler
# ---------------------------------------------------------------------------

def crawl_site(
    seed_url: str,
    config: CrawlConfig | None = None,
) -> list[dict]:
    """
    Crawl `seed_url` and every same-domain link found on the way.

    Args:
        seed_url: The starting URL (e.g. "https://www.imscolleges.com").
        config:   CrawlConfig instance; uses sensible defaults if omitted.

    Returns:
        List of page dicts (same schema as fetch_official_site_page())
        plus an extra "depth" key.  Failed pages are not included.
    """
    if config is None:
        config = CrawlConfig()

    seed_url = _normalize_url(seed_url.strip())
    seed_domain = (urlparse(seed_url).hostname or "").lower().removeprefix("www.")
    if not seed_domain:
        logger.error("crawl_site: cannot determine domain from %s", seed_url)
        return []

    # BFS state
    queue: deque[tuple[str, int]] = deque([(seed_url, 0)])
    visited: set[str] = {seed_url}
    results: list[dict] = []

    logger.info("Starting crawl of %s (max_pages=%d, max_depth=%d)",
                seed_url, config.max_pages, config.max_depth)

    while queue and len(results) < config.max_pages:
        url, depth = queue.popleft()

        if depth > config.max_depth:
            continue

        if _should_skip(url, config):
            logger.debug("Skipping (extension): %s", url)
            continue

        logger.debug("Fetching depth=%d  %s", depth, url)

        # Delegate all fetching, security checks, and HTML cleaning to the
        # existing helper — we do not duplicate any of that logic here.
        result = fetch_official_site_page(
            url,
            allowed_domains=config.allowed_domains,
            timeout=config.timeout,
        )

        if not result.get("ok"):
            logger.debug("Skipping (fetch failed): %s — %s", url, result.get("error"))
            # Still rate-limit even on failures to avoid hammering the server
            if config.delay_seconds > 0:
                time.sleep(config.delay_seconds)
            continue

        result["depth"] = depth
        results.append(result)

        logger.info(
            "[%d/%d] depth=%d  %s  (%d chars)",
            len(results), config.max_pages, depth,
            result["url"], len(result.get("text", "")),
        )

        # Extract and enqueue links only if we haven't hit the depth limit
        if depth < config.max_depth:
            # We need the raw HTML to extract links; re-fetch is wasteful so
            # we make a second lightweight request here.  A production system
            # should cache the raw bytes inside fetch_official_site_page and
            # return them alongside the cleaned text.
            try:
                import requests
                from config import OFFICIAL_SITE_USER_AGENT, OFFICIAL_SITE_TIMEOUT_SECONDS
                raw = requests.get(
                    result["url"],
                    headers={"User-Agent": OFFICIAL_SITE_USER_AGENT},
                    timeout=config.timeout or OFFICIAL_SITE_TIMEOUT_SECONDS,
                    allow_redirects=True,
                )
                raw.raise_for_status()
                raw_bytes = raw.content
            except Exception as exc:
                logger.debug("Could not re-fetch for link extraction: %s", exc)
                raw_bytes = b""

            new_links = _extract_links(raw_bytes, result["url"])
            enqueued = 0
            for link in new_links:
                if (
                    link not in visited
                    and _same_domain(link, seed_domain)
                    and not _should_skip(link, config)
                ):
                    visited.add(link)
                    queue.append((link, depth + 1))
                    enqueued += 1

            logger.debug("Enqueued %d new links from %s", enqueued, result["url"])

        if config.delay_seconds > 0:
            time.sleep(config.delay_seconds)

    logger.info(
        "Crawl complete: %d pages fetched, %d URLs visited",
        len(results), len(visited),
    )
    return results


# ---------------------------------------------------------------------------
# Convenience: crawl and format for the ingestion pipeline
# ---------------------------------------------------------------------------

def crawl_site_for_ingestion(
    seed_url: str,
    config: CrawlConfig | None = None,
) -> list[dict]:
    """
    Thin wrapper around crawl_site() that adds the `source_type` and
    `source_url` metadata fields expected by the ingestion pipeline.

    Returns only successfully crawled pages with non-empty text.
    """
    pages = crawl_site(seed_url, config)
    ingestion_ready = []
    for page in pages:
        if not page.get("text", "").strip():
            continue
        ingestion_ready.append({
            **page,
            "source_type": "official_site",
            "source_url": page["url"],
            "source": page.get("title") or page["url"],
        })
    return ingestion_ready