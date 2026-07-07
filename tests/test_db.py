"""Tests for lib.db — init_db public seam."""

import sqlite3

from lib.db import init_db


def test_init_db_creates_all_tables():
    conn = init_db(":memory:")
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = sorted(row[0] for row in cursor.fetchall())
    assert tables == ["corpus", "raw_hits", "repos", "seed_urls"]
    conn.close()


def test_init_db_is_idempotent(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn1 = init_db(db_path)
    conn1.close()
    conn2 = init_db(db_path)
    cursor = conn2.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = sorted(row[0] for row in cursor.fetchall())
    assert tables == ["corpus", "raw_hits", "repos", "seed_urls"]
    conn2.close()


def test_seed_urls_schema_has_correct_columns():
    conn = init_db(":memory:")
    conn.execute(
        "INSERT INTO seed_urls (url, domain, path, source, added_at) "
        "VALUES ('https://x.com', 'x.com', '/', 'manual', '2025-01-01T00:00:00Z')"
    )
    row = conn.execute("SELECT * FROM seed_urls").fetchone()
    assert row == ("https://x.com", "x.com", "/", "manual", "2025-01-01T00:00:00Z")
    cols = [desc[0] for desc in conn.execute("SELECT * FROM seed_urls").description]
    assert cols == ["url", "domain", "path", "source", "added_at"]
    conn.close()


def test_raw_hits_schema_has_correct_columns():
    conn = init_db(":memory:")
    # Need seed_url FK target
    conn.execute(
        "INSERT INTO seed_urls (url, domain, path, source, added_at) "
        "VALUES ('https://x.com', 'x.com', '/', 'manual', '2025-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO raw_hits (seed_url, repo_full_name, file_path, crawled_at) "
        "VALUES ('https://x.com', 'owner/repo', 'README.md', '2025-01-02T00:00:00Z')"
    )
    row = conn.execute("SELECT * FROM raw_hits").fetchone()
    assert row == (1, "https://x.com", "owner/repo", "README.md", "2025-01-02T00:00:00Z")
    cols = [desc[0] for desc in conn.execute("SELECT * FROM raw_hits").description]
    assert cols == ["id", "seed_url", "repo_full_name", "file_path", "crawled_at"]
    conn.close()


def test_repos_schema_has_correct_columns():
    conn = init_db(":memory:")
    conn.execute(
        "INSERT INTO repos (full_name, owner, stars, fetched_at) "
        "VALUES ('owner/repo', 'owner', 42, '2025-01-01T00:00:00Z')"
    )
    row = conn.execute("SELECT * FROM repos").fetchone()
    assert row == ("owner/repo", "owner", 42, "2025-01-01T00:00:00Z")
    cols = [desc[0] for desc in conn.execute("SELECT * FROM repos").description]
    assert cols == ["full_name", "owner", "stars", "fetched_at"]
    conn.close()


def test_corpus_schema_has_correct_columns():
    conn = init_db(":memory:")
    # Need seed_url FK target
    conn.execute(
        "INSERT INTO seed_urls (url, domain, path, source, added_at) "
        "VALUES ('https://x.com', 'x.com', '/', 'manual', '2025-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO corpus (seed_url, occurrences, unique_repositories, unique_owners, "
        "median_repo_stars, max_repo_stars, first_seen, last_seen, truncated) "
        "VALUES ('https://x.com', 10, 5, 3, 100.5, 500, "
        "'2025-01-01T00:00:00Z', '2025-06-01T00:00:00Z', 0)"
    )
    row = conn.execute("SELECT * FROM corpus").fetchone()
    assert row == (
        "https://x.com", 10, 5, 3, 100.5, 500,
        "2025-01-01T00:00:00Z", "2025-06-01T00:00:00Z", 0,
    )
    cols = [desc[0] for desc in conn.execute("SELECT * FROM corpus").description]
    assert cols == [
        "seed_url", "occurrences", "unique_repositories", "unique_owners",
        "median_repo_stars", "max_repo_stars", "first_seen", "last_seen", "truncated",
    ]
    conn.close()
