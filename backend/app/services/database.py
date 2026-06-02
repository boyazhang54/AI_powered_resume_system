import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import get_settings


def get_db_path() -> Path:
    return Path(get_settings().database_path)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS match_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resume_id TEXT NOT NULL,
                candidate_name TEXT NOT NULL,
                contact TEXT NOT NULL,
                job_title TEXT NOT NULL,
                score INTEGER NOT NULL,
                analysis_mode TEXT NOT NULL,
                job_description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_match_history_user_created ON match_history(user_id, created_at DESC)"
        )
