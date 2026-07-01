import importlib
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import history_db


def test_init_db_honors_env_override_path_and_creates_parent_dirs(monkeypatch, tmp_path):
    db_path = tmp_path / "nested" / "storage" / "analyses.db"
    monkeypatch.setenv("CV_REVIEWER_DB_PATH", str(db_path))

    importlib.reload(history_db)
    history_db.init_db()

    assert db_path.exists()

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='critiques'"
        ).fetchone()

    assert row is not None
