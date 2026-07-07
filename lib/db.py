"""Database initialisation — SQLite with WAL + foreign keys."""

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS seed_urls (
    url       TEXT PRIMARY KEY,
    domain    TEXT,
    path      TEXT,
    source    TEXT,
    added_at  TEXT
);

CREATE TABLE IF NOT EXISTS raw_hits (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_url       TEXT REFERENCES seed_urls(url),
    repo_full_name TEXT,
    file_path      TEXT,
    crawled_at     TEXT
);

CREATE TABLE IF NOT EXISTS repos (
    full_name  TEXT PRIMARY KEY,
    owner      TEXT,
    stars      INTEGER,
    fetched_at TEXT
);

CREATE TABLE IF NOT EXISTS corpus (
    seed_url            TEXT PRIMARY KEY REFERENCES seed_urls(url),
    occurrences         INTEGER,
    unique_repositories INTEGER,
    unique_owners       INTEGER,
    median_repo_stars   REAL,
    max_repo_stars      INTEGER,
    first_seen          TEXT,
    last_seen           TEXT,
    truncated           BOOLEAN
);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    """Create/connect SQLite DB, enable WAL + FKs, create tables."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA)
    return conn
