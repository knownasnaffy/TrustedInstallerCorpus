import sqlite3
import json

def export_corpus(db_path: str, json_path: str) -> None:
    """Export corpus table from SQLite to JSON."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM corpus")
    rows = cursor.fetchall()
    
    # Convert rows to dict and handle boolean for 'truncated'
    data = []
    for row in rows:
        row_dict = dict(row)
        if 'truncated' in row_dict:
            row_dict['truncated'] = bool(row_dict['truncated'])
        data.append(row_dict)
        
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    conn.close()

if __name__ == "__main__":
    export_corpus("corpus.db", "corpus.json")
