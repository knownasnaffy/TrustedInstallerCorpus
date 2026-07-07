import pytest
from crawler import build_query, is_truncated

def test_build_query_simple():
    url = "bun.sh/install"
    assert build_query(url) == '"bun.sh/install" in:file'

def test_build_query_escapes_quotes():
    url = 'bun.sh/install"hack'
    # GitHub code search doesn't support regex, but escaping quotes is good
    # For now, let's just assert it escapes them or we just assume the url is clean
    # The spec says "escaping quotes in URLs, if any".
    # so we should replace " with \"
    assert build_query(url) == '"bun.sh/install\\"hack" in:file'

def test_is_truncated():
    assert is_truncated(999) == False
    assert is_truncated(1000) == True
    assert is_truncated(1001) == True

def test_has_been_crawled():
    import sqlite3
    from crawler import has_been_crawled
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE raw_hits (seed_url TEXT)")
    
    assert has_been_crawled(conn, "bun.sh/install") == False
    
    conn.execute("INSERT INTO raw_hits (seed_url) VALUES (?)", ("bun.sh/install",))
    assert has_been_crawled(conn, "bun.sh/install") == True

