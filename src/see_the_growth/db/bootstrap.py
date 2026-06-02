"""SQLite schema bootstrap (SPEC-003)."""

from __future__ import annotations

import sqlite3

from .config import ensure_db_parent_directory

_CREATE_TODOS_TABLE = """
CREATE TABLE IF NOT EXISTS todos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    completed INTEGER NOT NULL,
    created_at TEXT NOT NULL
)
"""


def bootstrap_database(db_path: str) -> None:
    ensure_db_parent_directory(db_path)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(_CREATE_TODOS_TABLE)
        connection.commit()
    finally:
        connection.close()
