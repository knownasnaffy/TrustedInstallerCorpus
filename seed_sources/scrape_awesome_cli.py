"""Scrape awesome-cli lists for installer-style URLs.

Fetches awesome-cli-apps and awesome-shell README files from GitHub,
parses markdown for URLs matching installer patterns, and returns
candidates tagged "scraped:awesome-cli".
"""

from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse

import requests

SOURCE_TAG = "scraped:awesome-cli"

SOURCES = [
    "https://raw.githubusercontent.com/agarrharr/awesome-cli-apps/master/readme.md",
    "https://raw.githubusercontent.com/alebcay/awesome-shell/master/README.md",
]

# Patterns in URL path that suggest an installer script
INSTALLER_PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"install\.sh", re.IGNORECASE),
    re.compile(r"/install(?:[/\b]|$)", re.IGNORECASE),
    re.compile(r"setup\.sh", re.IGNORECASE),
    re.compile(r"get\.", re.IGNORECASE),
    re.compile(r"\.sh$", re.IGNORECASE),
]

# Domains (or domain prefixes) known to serve install scripts
INSTALLER_DOMAIN_PREFIXES = ("get.", "install.", "webi.")

# URL regex — grab http(s) URLs from markdown
URL_RE = re.compile(r"https?://[^\s\)\]\>\"]+")


def _is_installer_url(url: str) -> bool:
    """Return True if URL looks like an installer script."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path

    # Check domain prefixes
    for prefix in INSTALLER_DOMAIN_PREFIXES:
        if domain.startswith(prefix):
            return True

    # Check path patterns
    for pat in INSTALLER_PATH_PATTERNS:
        if pat.search(path):
            return True

    return False


def _split_url(url: str) -> str:
    """Extract domain from URL. Raises on malformed URLs."""
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"No netloc in URL: {url}")
    return parsed.netloc.lower()


def _fetch_markdown(url: str) -> str:
    """Fetch markdown content. Returns empty string on failure."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        print(f"WARNING: failed to fetch {url}: {exc}", file=sys.stderr)
        return ""


def scrape() -> list[dict[str, str]]:
    """Scrape awesome-cli lists and return installer URL candidates."""
    seen: set[str] = set()
    candidates: list[dict[str, str]] = []

    for source_url in SOURCES:
        md = _fetch_markdown(source_url)
        if not md:
            continue

        urls = URL_RE.findall(md)
        for raw_url in urls:
            # Strip trailing punctuation that may have been grabbed
            url = raw_url.rstrip(".,;:'\")")
            if url in seen:
                continue

            if not _is_installer_url(url):
                continue

            try:
                domain = _split_url(url)
            except ValueError:
                continue

            seen.add(url)
            candidates.append({
                "url": url,
                "domain": domain,
                "source": SOURCE_TAG,
            })

    return candidates


if __name__ == "__main__":
    results = scrape()
    print(json.dumps(results, indent=2))
    print(f"\n# {len(results)} candidates found", file=sys.stderr)
