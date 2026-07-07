import sqlite3
import json
import os
from export import export_corpus

def test_export_corpus(tmp_path):
    db_path = tmp_path / "test.db"
    json_path = tmp_path / "test_corpus.json"
    
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE corpus (seed_url TEXT PRIMARY KEY, occurrences INTEGER, unique_repositories INTEGER, unique_owners INTEGER, median_repo_stars REAL, max_repo_stars INTEGER, first_seen TEXT, last_seen TEXT, truncated BOOLEAN)")
    
    conn.execute(
        "INSERT INTO corpus VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("https://bun.sh/install", 50, 10, 8, 100.5, 5000, "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z", 1)
    )
    conn.execute(
        "INSERT INTO corpus VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("https://sh.rustup.rs", 100, 20, 15, 200.0, 10000, "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z", 0)
    )
    conn.commit()
    conn.close()

    export_corpus(str(db_path), str(json_path))

    assert os.path.exists(json_path)
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]["seed_url"] == "https://bun.sh/install"
    assert data[0]["occurrences"] == 50
    assert data[0]["median_repo_stars"] == 100.5
    assert data[0]["truncated"] is True
    
    assert data[1]["seed_url"] == "https://sh.rustup.rs"
    assert data[1]["truncated"] is False
