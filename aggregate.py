import sqlite3
import argparse
from typing import List
from lib.db import init_db

def median_repo_stars(stars: List[int]) -> float:
    if not stars:
        return 0.0
    sorted_stars = sorted(stars)
    n = len(sorted_stars)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_stars[mid - 1] + sorted_stars[mid]) / 2.0
    return float(sorted_stars[mid])

def max_repo_stars(stars: List[int]) -> int:
    if not stars:
        return 0
    return max(stars)

def aggregate_corpus(db_path_or_conn):
    if isinstance(db_path_or_conn, str):
        conn = init_db(db_path_or_conn)
    else:
        conn = db_path_or_conn
        
    cursor = conn.execute("SELECT url FROM seed_urls")
    seed_urls = [row[0] for row in cursor.fetchall()]
    
    for seed_url in seed_urls:
        hits_cursor = conn.execute('''
            SELECT rp.full_name, rp.owner, rp.stars, rh.crawled_at
            FROM raw_hits rh
            JOIN repos rp ON rh.repo_full_name = rp.full_name
            WHERE rh.seed_url = ?
        ''', (seed_url,))
        hits = hits_cursor.fetchall()
        
        if not hits:
            continue
            
        occurrences = len(hits)
        unique_repos = len(set(h[0] for h in hits))
        unique_owners = len(set(h[1] for h in hits))
        
        # Calculate stars only for unique repos to avoid skewing median
        unique_repo_stars = {}
        for h in hits:
            if h[0] not in unique_repo_stars and h[2] is not None:
                unique_repo_stars[h[0]] = h[2]
        
        stars = list(unique_repo_stars.values())
        med_stars = median_repo_stars(stars)
        max_stars = max_repo_stars(stars)
        
        crawled_ats = [h[3] for h in hits if h[3]]
        current_last_seen = max(crawled_ats) if crawled_ats else None
        current_first_seen = min(crawled_ats) if crawled_ats else None
        
        # Check existing corpus row to carry over truncated and first_seen
        existing = conn.execute("SELECT first_seen, truncated, last_seen FROM corpus WHERE seed_url = ?", (seed_url,)).fetchone()
        
        first_seen = current_first_seen
        truncated = 0
        last_seen = current_last_seen
        
        if existing:
            if existing[0]: # previous first_seen
                first_seen = existing[0]
            if existing[2] and current_last_seen and existing[2] > current_last_seen:
                last_seen = existing[2]
            truncated = existing[1]
            
        conn.execute('''
            INSERT INTO corpus (
                seed_url, occurrences, unique_repositories, unique_owners,
                median_repo_stars, max_repo_stars, first_seen, last_seen, truncated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(seed_url) DO UPDATE SET
                occurrences=excluded.occurrences,
                unique_repositories=excluded.unique_repositories,
                unique_owners=excluded.unique_owners,
                median_repo_stars=excluded.median_repo_stars,
                max_repo_stars=excluded.max_repo_stars,
                last_seen=excluded.last_seen,
                truncated=excluded.truncated
        ''', (
            seed_url, occurrences, unique_repos, unique_owners,
            med_stars, max_stars, first_seen, last_seen, truncated
        ))
    
    conn.commit()
    
    if isinstance(db_path_or_conn, str):
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregate crawler data into corpus stats.")
    parser.add_argument("--db", default="corpus.db", help="SQLite database path")
    args = parser.parse_args()
    aggregate_corpus(args.db)
