import sqlite3
import pytest
from aggregate import median_repo_stars, max_repo_stars, aggregate_corpus
from lib.db import init_db

def test_median_repo_stars():
    assert median_repo_stars([]) == 0.0
    assert median_repo_stars([5]) == 5.0
    assert median_repo_stars([1, 5, 10]) == 5.0
    assert median_repo_stars([1, 3, 5, 7]) == 4.0
    assert median_repo_stars([10, 1, 5]) == 5.0  # Unsorted input

def test_max_repo_stars():
    assert max_repo_stars([]) == 0
    assert max_repo_stars([1, 10, 5]) == 10

@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()

def test_aggregate_corpus(db_conn):
    # Setup test data
    db_conn.execute("INSERT INTO seed_urls (url, domain, path, source, added_at) VALUES ('http://test.com/install', 'test.com', '/install', 'manual', '2023-01-01T00:00:00Z')")
    
    # 3 hits, 2 unique repos, 2 unique owners
    db_conn.execute("INSERT INTO raw_hits (seed_url, repo_full_name, file_path, crawled_at) VALUES ('http://test.com/install', 'owner1/repo1', 'README.md', '2023-01-02T10:00:00Z')")
    db_conn.execute("INSERT INTO raw_hits (seed_url, repo_full_name, file_path, crawled_at) VALUES ('http://test.com/install', 'owner1/repo1', 'install.sh', '2023-01-02T10:00:00Z')")
    db_conn.execute("INSERT INTO raw_hits (seed_url, repo_full_name, file_path, crawled_at) VALUES ('http://test.com/install', 'owner2/repo2', 'docs.md', '2023-01-02T10:00:00Z')")
    
    # Stars for repos
    db_conn.execute("INSERT INTO repos (full_name, owner, stars, fetched_at) VALUES ('owner1/repo1', 'owner1', 10, '2023-01-02T10:05:00Z')")
    db_conn.execute("INSERT INTO repos (full_name, owner, stars, fetched_at) VALUES ('owner2/repo2', 'owner2', 20, '2023-01-02T10:05:00Z')")
    db_conn.commit()
    
    # Run aggregation
    aggregate_corpus(db_conn)
    
    # Verify exact counts and stats
    cursor = db_conn.execute("SELECT occurrences, unique_repositories, unique_owners, median_repo_stars, max_repo_stars, first_seen, last_seen, truncated FROM corpus WHERE seed_url = 'http://test.com/install'")
    row = cursor.fetchone()
    assert row is not None
    occurrences, unique_repositories, unique_owners, median_repo_stars, max_repo_stars, first_seen, last_seen, truncated = row
    
    assert occurrences == 3
    assert unique_repositories == 2
    assert unique_owners == 2
    assert median_repo_stars == 15.0
    assert max_repo_stars == 20
    assert first_seen == '2023-01-02T10:00:00Z'
    assert last_seen == '2023-01-02T10:00:00Z'
    assert truncated == 0

def test_aggregate_corpus_update_timestamps(db_conn):
    # Setup initial corpus row
    db_conn.execute("INSERT INTO seed_urls (url) VALUES ('http://test.com/install')")
    db_conn.execute("INSERT INTO corpus (seed_url, first_seen, last_seen) VALUES ('http://test.com/install', '2023-01-01T00:00:00Z', '2023-01-01T00:00:00Z')")
    
    # New crawl
    db_conn.execute("INSERT INTO raw_hits (seed_url, repo_full_name, crawled_at) VALUES ('http://test.com/install', 'owner1/repo1', '2023-02-01T10:00:00Z')")
    db_conn.execute("INSERT INTO repos (full_name, owner, stars) VALUES ('owner1/repo1', 'owner1', 5)")
    db_conn.commit()
    
    aggregate_corpus(db_conn)
    
    cursor = db_conn.execute("SELECT first_seen, last_seen FROM corpus WHERE seed_url = 'http://test.com/install'")
    row = cursor.fetchone()
    
    assert row[0] == '2023-01-01T00:00:00Z' # Unchanged
    assert row[1] == '2023-02-01T10:00:00Z' # Updated
