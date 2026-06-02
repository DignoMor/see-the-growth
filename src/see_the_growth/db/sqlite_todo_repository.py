"""SQLite-backed todo repository (SPEC-003)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from see_the_growth.domain.todo_list import TodoItem

from .bootstrap import bootstrap_database


class SqliteTodoRepository:
    def __init__(self, db_path: str) -> None:
        bootstrap_database(db_path)
        self._db_path = db_path
        self._connection = sqlite3.connect(db_path)

    def add_todo(self, todo: TodoItem) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        self._connection.execute(
            """
            INSERT INTO todos (id, title, completed, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (todo.id, todo.title, int(todo.completed), created_at),
        )
        self._connection.commit()

    def list_todos(self) -> list[TodoItem]:
        rows = self._connection.execute(
            """
            SELECT id, title, completed
            FROM todos
            ORDER BY created_at ASC, id ASC
            """
        ).fetchall()
        return [
            TodoItem(id=row[0], title=row[1], completed=bool(row[2]))
            for row in rows
        ]

    def mark_completed(self, todo_id: str) -> bool:
        row = self._connection.execute(
            "SELECT id FROM todos WHERE id = ?",
            (str(todo_id),),
        ).fetchone()
        if row is None:
            return False

        self._connection.execute(
            "UPDATE todos SET completed = 1 WHERE id = ?",
            (str(todo_id),),
        )
        self._connection.commit()
        return True
