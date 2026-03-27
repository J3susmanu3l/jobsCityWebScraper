from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse
import requests


EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}")
LIKELY_CONTACT_PATHS = (
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
)


def _normalize_site_url(site_url: str) -> str:
    if not site_url.startswith(("http://", "https://")):
        return f"https://{site_url}"
    return site_url


def _same_host(base: str, maybe_url: str) -> bool:
    return urlparse(base).netloc == urlparse(maybe_url).netloc


def _extract_first_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def find_email_from_website(site_url: str, timeout_seconds: int = 15) -> str | None:
    try:
        normalized = _normalize_site_url(site_url)
        response = requests.get(
            normalized,
            timeout=timeout_seconds,
            headers={"User-Agent": "Mozilla/5.0 JobsScraper/1.0"},
        )
        response.raise_for_status()
        email = _extract_first_email(response.text)
        if email:
            return email

        for path in LIKELY_CONTACT_PATHS:
            url = urljoin(normalized, path)
            if not _same_host(normalized, url):
                continue

            page_response = requests.get(
                url,
                timeout=timeout_seconds,
                headers={"User-Agent": "Mozilla/5.0 JobsScraper/1.0"},
            )
            if page_response.ok:
                email = _extract_first_email(page_response.text)
                if email:
                    return email
    except requests.RequestException:
        return None
    return None

