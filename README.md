# Trusted Installer Corpus

## Motivation

Build dataset of legitimate installer URLs. Goal: measure how wide URL referenced on GitHub. Output trust-signal dataset. Help security tools distinguish trusted install commands (`curl ... | bash`) from suspicious ones.

No auto-discovery. No scheduling. No scoring model yet. Just validate "how widely referenced" as useful signal.

## Architecture

Pipeline process seed list of known installer URLs.

1. **Crawler**: Query GitHub Code Search per URL exact match. Store hits.
2. **Enrich**: Fetch repo metadata (stars, owner) via REST API.
3. **Aggregate**: Join hits + repos. Compute occurrences, unique repos, unique owners, stars.
4. **Export**: Dump data to JSON.

Pipeline scripts write to shared SQLite state. Re-run stages independently.

## Tech Stack

- Python (requests, PyGithub)
- Auth via `gh auth token` (local gh CLI auth)
- SQLite (state) + JSON (export)

## Usage

1. Install deps:
```bash
pip install -r requirements.txt
```
2. Verify GitHub CLI auth:
```bash
gh auth status
```
3. Prepare seed list (manual + scraped):
```bash
python seed_sources/build_seed_list.py
```
4. Run pipeline stages:
```bash
python crawler.py
python enrich.py
python aggregate.py
python export.py
```

Result: `corpus.json` artifact.

Crawler rate limit: 10 req/min authenticated. Crawler sleep and backoff automatically. Scripts resumable.
