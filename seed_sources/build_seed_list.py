"""Build seed_list.json from manual and scraped sources.

Merges manual seed list with scraped candidates, dedupes by exact URL,
validates schema, and writes combined JSON array.
"""

import json
import sys
from pathlib import Path

from seed_sources.scrape_awesome_cli import scrape as scrape_awesome
from seed_sources.scrape_webinstall_dev import scrape as scrape_webinstall

ROOT_DIR = Path(__file__).parent.parent
MANUAL_FILE = ROOT_DIR / "seed_sources" / "manual_seed_list.json"
OUT_FILE = ROOT_DIR / "seed_list.json"


def build() -> None:
    """Build seed_list.json from all sources."""
    try:
        with open(MANUAL_FILE, "r") as f:
            manual = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {MANUAL_FILE} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(manual)} manual entries.", file=sys.stderr)

    print("Running awesome-cli scraper...", file=sys.stderr)
    awesome = scrape_awesome()
    print(f"Found {len(awesome)} awesome-cli entries.", file=sys.stderr)

    print("Running webinstall scraper...", file=sys.stderr)
    webinstall = scrape_webinstall()
    print(f"Found {len(webinstall)} webinstall entries.", file=sys.stderr)

    combined = []
    seen = set()
    counts = {"manual": 0, "scraped:awesome-cli": 0, "scraped:webinstall_dev": 0}

    def add_entries(entries: list[dict[str, str]]) -> None:
        for e in entries:
            url = e["url"]
            if url not in seen:
                seen.add(url)
                combined.append(e)
                source = e["source"]
                counts[source] = counts.get(source, 0) + 1

    # Manual takes precedence if URLs duplicate
    add_entries(manual)
    add_entries(awesome)
    add_entries(webinstall)

    # Validate schema
    for e in combined:
        assert "url" in e, f"Missing url in {e}"
        assert "domain" in e, f"Missing domain in {e}"
        assert "source" in e, f"Missing source in {e}"
        assert e["domain"], f"Empty domain in {e}"

    with open(OUT_FILE, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"\nWrote {len(combined)} total entries to {OUT_FILE}", file=sys.stderr)
    print("Breakdown:", file=sys.stderr)
    for src, count in counts.items():
        if count > 0:
            print(f"  {src}: {count}", file=sys.stderr)


if __name__ == "__main__":
    build()
