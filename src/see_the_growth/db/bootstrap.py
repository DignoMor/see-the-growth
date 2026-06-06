"""SQLite schema bootstrap (SPEC-003, SPEC-008)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from .config import ensure_db_parent_directory

_CREATE_TODOS_TABLE = """
CREATE TABLE IF NOT EXISTS todos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    completed INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    flushed INTEGER NOT NULL DEFAULT 0
)
"""

_CREATE_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
)
"""

_CREATE_TODO_TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS todo_tags (
    todo_id TEXT NOT NULL REFERENCES todos(id),
    tag_id TEXT NOT NULL REFERENCES tags(id),
    PRIMARY KEY (todo_id, tag_id)
)
"""


def _ensure_flushed_column(connection: sqlite3.Connection) -> None:
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(todos)").fetchall()
    }
    if "flushed" not in columns:
        connection.execute(
            "ALTER TABLE todos ADD COLUMN flushed INTEGER NOT NULL DEFAULT 0"
        )


def _ensure_task_tag(connection: sqlite3.Connection) -> None:
    row = connection.execute(
        "SELECT id FROM tags WHERE name = 'task'"
    ).fetchone()
    if row is not None:
        return

    created_at = datetime.now(timezone.utc).isoformat()
    connection.execute(
        "INSERT INTO tags (id, name, created_at) VALUES (?, 'task', ?)",
        (str(uuid4()), created_at),
    )


def bootstrap_database(db_path: str) -> None:
    ensure_db_parent_directory(db_path)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(_CREATE_TODOS_TABLE)
        _ensure_flushed_column(connection)
        connection.execute(_CREATE_TAGS_TABLE)
        connection.execute(_CREATE_TODO_TAGS_TABLE)
        _ensure_task_tag(connection)
        connection.commit()
    finally:
        connection.close()
