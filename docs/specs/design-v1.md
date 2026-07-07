# Trusted Installer Corpus — v1 Design

## Goal

Prove the methodology: given a seed list of known-legitimate installer URLs,
build a pipeline that queries GitHub for occurrence evidence and produces a
trust-signal dataset (SQLite + JSON export). No auto-discovery, no scheduling,
no scoring model yet — just validate that "how widely is this URL referenced"
is a measurable, useful signal.

## Non-Goals (deferred to v2+)

- Broad pattern search / new-installer discovery (`curl | bash` style crawls)
- Scheduled/automated runs (GitHub Actions cron)
- Verified-org status, repo activity/maintenance signals, domain reputation
- Confidence scoring formula (corpus stores raw signals only, no combined score)

## Stack

- Python (requests + PyGithub)
- Auth via `gh auth token` (shell out to existing gh CLI auth, no separate PAT)
- SQLite for pipeline state, JSON export for consumers

## Architecture

```
seed_list.json          (manual + scraped candidates)
  |
crawler.py               per-URL exact Code Search query -> repo list
  |
enrich.py                fetch repo metadata (stars, owner) via REST API
  |
aggregate.py             compute occurrences/unique_repos/unique_owners
  |
corpus.db (SQLite)   ->   export.py -> corpus.json
```

Each stage is a separate script writing to shared SQLite state, not an
in-memory pipe. Any stage can be re-run independently without re-crawling.

## Seed List

Sources, both included:
1. Manually curated core list (~50-100 well-known installers, hand-picked)
2. Scraped from existing curated lists (e.g. awesome-cli, webinstall.dev)

Combined into `seed_list.json`:
```json
[{"url": "https://bun.sh/install", "domain": "bun.sh", "source": "manual"}]
```

## Data Flow

1. **Crawler**: for each seed URL, query `/search/code?q="<url>" in:file`
   (exact literal string match — GitHub REST Code Search does not support
   regex; confirmed regex chars are silently ignored by the API, only the
   web UI at cs.github.com supports it). Store raw hits (repo full_name,
   file_path) in `raw_hits`.
2. **Enrich**: pull distinct repo list from `raw_hits`, fetch stars/owner via
   `/repos/{owner}/{repo}`, cache in `repos` table (avoids re-fetching a repo
   referenced by multiple seed URLs).
3. **Aggregate**: join `raw_hits` + `repos`, compute `occurrences`,
   `unique_repositories`, `unique_owners`, `median_repo_stars`,
   `max_repo_stars` per seed URL, write to `corpus` table.
4. **Export**: dump `corpus` table to `corpus.json` matching the target
   dataset schema.

## Schema (SQLite)

```sql
seed_urls(url PK, domain, path, source, added_at)
raw_hits(id PK, seed_url FK, repo_full_name, file_path, crawled_at)
repos(full_name PK, owner, stars, fetched_at)
corpus(seed_url PK, occurrences, unique_repositories, unique_owners,
       median_repo_stars, max_repo_stars, first_seen, last_seen, truncated)
```

`truncated` flag: GitHub Code Search caps results at 1000 per query
(100/page x 10 pages). If a seed URL's `total_count` hits that cap, flag it
so the occurrence count is known to be a floor, not exact.

## Error Handling & Rate Limits

- Code Search REST endpoint: 10 req/min authenticated — the binding
  constraint. Crawler sleeps between calls and respects
  `X-RateLimit-Remaining`.
- Repo metadata endpoint: 5000 req/hr — generous, not a practical limit.
- On 403 / secondary rate limit: back off and retry.
- On network error / 5xx: retry 3x with exponential backoff, then log and
  skip — one bad seed URL doesn't kill the run.
- Script is resumable: re-running skips seed URLs already present in
  `raw_hits` for the current run, so a crash mid-run doesn't waste quota.

## Testing

- Unit tests: URL parsing (domain/path split), aggregation math
  (median/max), truncation flag logic — pure functions, no live API needed.
- Integration: manual run against 3-5 known seed URLs (bun.sh/install,
  sh.rustup.rs, get.docker.com), sanity-check output against known reality
  before running the full ~500-entry list.
- No API mocking framework for v1 — pipeline is small enough that a real
  subset run serves as the integration test.

## Execution Model

Local script, run manually. No CI/scheduling in v1 — success criteria is
"pipeline produces sane, evidence-backed numbers for known installers,"
not "it runs unattended."
