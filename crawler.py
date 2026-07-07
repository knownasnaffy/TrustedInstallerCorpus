import sys
import json
import logging
from datetime import datetime, timezone
import requests
from lib.db import init_db
from lib.github_auth import get_token
from lib.rate_limit import GitHubRateLimiter

logging.basicConfig(level=logging.INFO)

def build_query(url: str) -> str:
    """Build exact-literal-match query for seed URL."""
    escaped_url = url.replace('"', '\\"')
    return f'"{escaped_url}" in:file'

def is_truncated(total_count: int) -> bool:
    """Check if result hit the pagination cap (1000)."""
    return total_count >= 1000

def has_been_crawled(conn, seed_url: str) -> bool:
    """Check if the seed URL already has rows in raw_hits."""
    cur = conn.execute("SELECT 1 FROM raw_hits WHERE seed_url = ? LIMIT 1", (seed_url,))
    return cur.fetchone() is not None

def fetch_page(limiter: GitHubRateLimiter, query: str, page: int, token: str) -> requests.Response:
    url = "https://api.github.com/search/code"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    }
    params = {
        "q": query,
        "per_page": 100,
        "page": page
    }
    return limiter.execute_with_retry(requests.get, url, headers=headers, params=params)

def crawl():
    conn = init_db("corpus.db")
    token = get_token()
    if not token:
        logging.error("No GitHub token found.")
        sys.exit(1)
        
    with open("seed_list.json") as f:
        seed_list = json.load(f)
        
    limiter = GitHubRateLimiter()
    
    from lib.url_utils import split_url
    for seed in seed_list:
        seed_url = seed["url"]
        domain, path = split_url(seed_url)
        added_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        conn.execute(
            "INSERT INTO seed_urls (url, domain, path, source, added_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(url) DO NOTHING",
            (seed_url, seed.get("domain", domain), path, seed.get("source", "unknown"), added_at)
        )
        conn.commit()
        if has_been_crawled(conn, seed_url):
            logging.info(f"Skipping already crawled: {seed_url}")
            continue
            
        logging.info(f"Crawling: {seed_url}")
        query = build_query(seed_url)
        
        for page in range(1, 11):
            try:
                resp = fetch_page(limiter, query, page, token)
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to fetch {seed_url} page {page}: {e}")
                break
                
            data = resp.json()
            items = data.get("items", [])
            
            crawled_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            for item in items:
                repo_full_name = item["repository"]["full_name"]
                file_path = item["path"]
                conn.execute(
                    "INSERT INTO raw_hits (seed_url, repo_full_name, file_path, crawled_at) VALUES (?, ?, ?, ?)",
                    (seed_url, repo_full_name, file_path, crawled_at)
                )
            conn.commit()
            
            if len(items) < 100:
                break

if __name__ == "__main__":
    crawl()
