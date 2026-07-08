import sqlite3
import pytest
from lib.db import init_db
from enrich import get_distinct_repos, fetch_and_store_metadata

@pytest.fixture
def db():
    conn = init_db(":memory:")
    yield conn
    conn.close()

def test_distinct_repo_extraction(db):
    db.execute("INSERT INTO seed_urls (url) VALUES ('url1')")
    db.execute("INSERT INTO raw_hits (seed_url, repo_full_name) VALUES ('url1', 'owner/repo1')")
    db.execute("INSERT INTO raw_hits (seed_url, repo_full_name) VALUES ('url1', 'owner/repo1')")
    db.execute("INSERT INTO raw_hits (seed_url, repo_full_name) VALUES ('url1', 'owner/repo2')")
    
    repos = get_distinct_repos(db)
    assert repos == {'owner/repo1', 'owner/repo2'}

def test_repo_metadata_fetch_and_cache(db):
    db.execute("INSERT INTO repos (full_name, owner, stars, fetched_at) VALUES ('owner/repo1', 'owner', 10, '2023-01-01T00:00:00Z')")
    
    fetches = []
    def mock_fetch(repo_full_name, token, limiter):
        fetches.append(repo_full_name)
        return {"owner": {"login": repo_full_name.split('/')[0]}, "stargazers_count": 42}
        
    limiter = None
    fetch_and_store_metadata(db, 'owner/repo1', mock_fetch, 'dummy_token', limiter)
    fetch_and_store_metadata(db, 'owner/repo2', mock_fetch, 'dummy_token', limiter)
    
    assert fetches == ['owner/repo2']
    
    cur = db.execute("SELECT full_name, stars FROM repos ORDER BY full_name")
    rows = cur.fetchall()
    assert rows == [('owner/repo1', 10), ('owner/repo2', 42)]
