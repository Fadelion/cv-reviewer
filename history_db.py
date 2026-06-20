import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyses.db")

def init_db():
    """Initializes the SQLite database and creates the critiques table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS critiques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            filename TEXT NOT NULL,
            job_title TEXT,
            overall_score INTEGER NOT NULL,
            keyword_match INTEGER NOT NULL,
            cv_text TEXT,
            job_description TEXT,
            result_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_critique(filename: str, job_title: str, overall_score: int, keyword_match: int, 
                  cv_text: str, job_description: str, result_json_str: str) -> int:
    """Saves a critique session to the database and returns its new ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO critiques (filename, job_title, overall_score, keyword_match, cv_text, job_description, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (filename, job_title, overall_score, keyword_match, cv_text, job_description, result_json_str))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_history() -> List[Dict[str, Any]]:
    """Returns a list of all historical critiques summaries, sorted by newest first."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, filename, job_title, overall_score, keyword_match 
        FROM critiques 
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    history = [dict(row) for row in rows]
    conn.close()
    return history

def get_critique_by_id(critique_id: int) -> Optional[Dict[str, Any]]:
    """Returns the full details of a specific critique, including the raw LLM JSON response."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM critiques WHERE id = ?", (critique_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        res = dict(row)
        # Parse the JSON string into an object to return directly to the front-end
        try:
            res["result_json"] = json.loads(res["result_json"])
        except Exception:
            pass
        return res
    return None

def delete_critique(critique_id: int) -> bool:
    """Deletes a critique record from the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM critiques WHERE id = ?", (critique_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
    # Insert test row
    test_id = save_critique("test_cv.pdf", "Software Engineer", 75, 40, "John Doe CV...", "Job Description...", '{"overall_score": 75}')
    print(f"Inserted test row with ID: {test_id}")
    print("History summary list:")
    print(get_history())
    print("Retrieving test row:")
    print(get_critique_by_id(test_id))
    print("Deleting test row...")
    print(delete_critique(test_id))
