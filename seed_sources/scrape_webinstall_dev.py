"""Scrape webinstall.dev / webi-installers for tool install URLs.

Fetches the webi-installers README from GitHub, extracts tool names,
and constructs webi.sh installer URLs for each. Returns candidates
tagged "scraped:webinstall_dev".
"""

from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse

import requests

SOURCE_TAG = "scraped:webinstall_dev"
WEBI_DOMAIN = "webi.sh"

README_URL = (
    "https://raw.githubusercontent.com/webinstall/webi-installers/master/README.md"
)
FALLBACK_URL = "https://webinstall.dev/"

# Match markdown links like [toolname](https://webinstall.dev/toolname)
WEBINSTALL_LINK_RE = re.compile(
    r"\[([^\]]+)\]\(https?://webinstall\.dev/([a-zA-Z0-9_\-\.]+)/?\)"
)

# Match directory-style tool names in table/list items: `| [tool](/tool) |`
# or lines like `- **tool** —`
TOOL_NAME_RE = re.compile(r"^\s*[-*|]\s*\[?([a-zA-Z0-9_\-\.]+)\]?", re.MULTILINE)

# Bare lines that look like tool directory entries in README
DIR_ENTRY_RE = re.compile(
    r"^\|\s*\[`?([a-zA-Z0-9_\-\.]+)`?\]\(/([a-zA-Z0-9_\-\.]+)/?\)",
    re.MULTILINE,
)


def _split_url(url: str) -> str:
    """Extract domain from URL. Raises on malformed URLs."""
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"No netloc in URL: {url}")
    return parsed.netloc.lower()


def _fetch(url: str) -> str:
    """Fetch URL content. Returns empty string on failure."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        print(f"WARNING: failed to fetch {url}: {exc}", file=sys.stderr)
        return ""


def _extract_tools_from_readme(md: str) -> set[str]:
    """Extract tool names from webi-installers README."""
    tools: set[str] = set()

    # Method 1: explicit webinstall.dev links
    for match in WEBINSTALL_LINK_RE.finditer(md):
        tool = match.group(2).strip().lower()
        if tool and len(tool) >= 2:
            tools.add(tool)

    # Method 2: directory-style table entries
    for match in DIR_ENTRY_RE.finditer(md):
        tool = match.group(1).strip().lower()
        if tool and len(tool) >= 2:
            tools.add(tool)

    return tools


def _extract_tools_from_html(html: str) -> set[str]:
    """Extract tool names from webinstall.dev HTML page."""
    tools: set[str] = set()
    # Look for links like href="/node" or href="/golang/"
    href_re = re.compile(r'href="/([a-zA-Z0-9_\-\.]+)/?\"')
    for match in href_re.finditer(html):
        tool = match.group(1).strip().lower()
        # Filter out generic page slugs
        if tool in ("about", "contact", "docs", "faq", "blog", "privacy", "terms"):
            continue
        if tool and len(tool) >= 2:
            tools.add(tool)
    return tools


def scrape() -> list[dict[str, str]]:
    """Scrape webinstall.dev tools and return installer URL candidates."""
    tools: set[str] = set()

    # Try README first
    md = _fetch(README_URL)
    if md:
        tools.update(_extract_tools_from_readme(md))

    # Fallback / supplement with HTML page
    html = _fetch(FALLBACK_URL)
    if html:
        tools.update(_extract_tools_from_html(html))

    if not tools:
        print("WARNING: no tools found from webinstall.dev sources", file=sys.stderr)
        return []

    candidates: list[dict[str, str]] = []
    for tool in sorted(tools):
        url = f"https://webi.sh/{tool}"
        try:
            _split_url(url)
        except ValueError:
            continue
        candidates.append({
            "url": url,
            "domain": WEBI_DOMAIN,
            "source": SOURCE_TAG,
        })

    return candidates


if __name__ == "__main__":
    results = scrape()
    print(json.dumps(results, indent=2))
    print(f"\n# {len(results)} candidates found", file=sys.stderr)
