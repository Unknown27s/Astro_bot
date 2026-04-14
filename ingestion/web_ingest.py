"""
IMS AstroBot — Official Site Ingestion Helpers
Fetches and cleans public website pages for local indexing.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import OFFICIAL_SITE_ALLOWED_DOMAINS, OFFICIAL_SITE_TIMEOUT_SECONDS, OFFICIAL_SITE_USER_AGENT


def _normalize_domain(hostname: str) -> str:
    return (hostname or "").strip().lower().removeprefix("www.")


def _is_private_host(hostname: str) -> bool:
    if not hostname:
        return True

    if hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
        return True

    try:
        ip_addr = ipaddress.ip_address(hostname)
        return ip_addr.is_private or ip_addr.is_loopback or ip_addr.is_link_local
    except ValueError:
        pass

    try:
        for addr_info in socket.getaddrinfo(hostname, None):
            sockaddr = addr_info[4][0]
            try:
                ip_addr = ipaddress.ip_address(sockaddr)
            except ValueError:
                continue
            if ip_addr.is_private or ip_addr.is_loopback or ip_addr.is_link_local:
                return True
    except socket.gaierror:
        return True

    return False


def _is_allowed_domain(hostname: str, allowed_domains: list[str] | None = None) -> bool:
    normalized = _normalize_domain(hostname)
    if not normalized or _is_private_host(normalized):
        return False

    domain_allowlist = [
        _normalize_domain(domain)
        for domain in (allowed_domains if allowed_domains is not None else OFFICIAL_SITE_ALLOWED_DOMAINS)
        if domain
    ]
    if not domain_allowlist:
        return True

    for allowed in domain_allowlist:
        if normalized == allowed or normalized.endswith(f".{allowed}"):
            return True
    return False


def _clean_html_text(html_bytes: bytes) -> tuple[str, str]:
    soup = BeautifulSoup(html_bytes, "lxml")

    for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        element.decompose()

    page_title = ""
    if soup.title and soup.title.string:
        page_title = " ".join(soup.title.string.split()).strip()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines), page_title


def fetch_official_site_page(url: str, allowed_domains: list[str] | None = None, timeout: int | None = None) -> dict:
    """Fetch and clean a public web page for local indexing."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return {"ok": False, "error": "Only http and https URLs are supported"}

    domain = _normalize_domain(parsed.hostname or "")
    if not _is_allowed_domain(domain, allowed_domains):
        return {"ok": False, "error": f"Domain not allowed for ingestion: {domain or 'unknown'}"}

    request_timeout = timeout or OFFICIAL_SITE_TIMEOUT_SECONDS
    headers = {"User-Agent": OFFICIAL_SITE_USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=request_timeout, allow_redirects=True)
        response.raise_for_status()
    except Exception as exc:
        return {"ok": False, "error": f"Failed to fetch URL: {exc}"}

    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type and "text" not in content_type:
        return {"ok": False, "error": f"Unsupported content type: {content_type or 'unknown'}"}

    try:
        text, page_title = _clean_html_text(response.content)
    except Exception as exc:
        return {"ok": False, "error": f"Failed to parse HTML: {exc}"}

    if not text.strip():
        return {"ok": False, "error": "No text could be extracted from the page"}

    return {
        "ok": True,
        "url": response.url,
        "domain": domain,
        "title": page_title or domain or url,
        "text": text.strip(),
        "file_size": len(response.content),
    }