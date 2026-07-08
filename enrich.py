import sqlite3
import sys
import logging
from datetime import datetime, timezone
from typing import Set, Callable
import requests
from lib.db import init_db
from lib.github_auth import get_token
from lib.rate_limit import GitHubRateLimiter

logging.basicConfig(level=logging.INFO)

def get_distinct_repos(conn: sqlite3.Connection) -> Set[str]:
    """Pull distinct repo full names from raw_hits."""
    cur = conn.execute("SELECT DISTINCT repo_full_name FROM raw_hits")
    return {row[0] for row in cur.fetchall()}

def default_fetch_repo_metadata(repo_full_name: str, token: str, limiter: GitHubRateLimiter) -> dict:
    url = f"https://api.github.com/repos/{repo_full_name}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    }
    resp = limiter.execute_with_retry(requests.get, url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def fetch_and_store_metadata(
    conn: sqlite3.Connection,
    repo_full_name: str,
    fetch_fn: Callable,
    token: str,
    limiter: GitHubRateLimiter
):
    """Fetch repo metadata and cache it in the repos table. Skip if already exists."""
    cur = conn.execute("SELECT 1 FROM repos WHERE full_name = ?", (repo_full_name,))
    if cur.fetchone():
        logging.info(f"Cache hit for {repo_full_name}")
        return

    logging.info(f"Fetching metadata for {repo_full_name}")
    try:
        data = fetch_fn(repo_full_name, token, limiter)
    except Exception as e:
        logging.error(f"Failed to fetch {repo_full_name}: {e}")
        return
        
    owner = data.get("owner", {}).get("login", "")
    stars = data.get("stargazers_count", 0)
    fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    conn.execute(
        "INSERT INTO repos (full_name, owner, stars, fetched_at) VALUES (?, ?, ?, ?)",
        (repo_full_name, owner, stars, fetched_at)
    )
    conn.commit()

def enrich():
    conn = init_db("corpus.db")
    token = get_token()
    if not token:
        logging.error("No GitHub token found.")
        sys.exit(1)
        
    repos = get_distinct_repos(conn)
    limiter = GitHubRateLimiter(calls_per_minute=80)  # Core API is 5000/hr
    for repo in repos:
        fetch_and_store_metadata(conn, repo, default_fetch_repo_metadata, token, limiter)

if __name__ == "__main__":
    enrich()
