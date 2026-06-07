"""SQLite-backed todo repository (SPEC-003, SPEC-008)."""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from uuid import uuid4

from see_the_growth.domain.tag import TagSummary
from see_the_growth.domain.todo_filter import TagMatchMode, TodoFilter
from see_the_growth.domain.todo_list import TodoItem

from .bootstrap import bootstrap_database


class SqliteTodoRepository:
    def __init__(self, db_path: str) -> None:
        bootstrap_database(db_path)
        self._db_path = db_path
        self._local = threading.local()

    @property
    def _connection(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = sqlite3.connect(self._db_path)
            self._local.connection = connection
        return connection

    def add_todo(
        self, todo: TodoItem, extra_tag_names: list[str] | None = None
    ) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        connection = self._connection
        try:
            connection.execute("BEGIN")
            connection.execute(
                """
                INSERT INTO todos (id, title, completed, created_at, flushed)
                VALUES (?, ?, ?, ?, 0)
                """,
                (todo.id, todo.title, int(todo.completed), created_at),
            )
            tag_names = ["task"]
            if extra_tag_names:
                for tag_name in extra_tag_names:
                    if tag_name != "task":
                        tag_names.append(tag_name)
            for tag_name in tag_names:
                tag_id = self._get_or_create_tag_id(connection, tag_name)
                connection.execute(
                    """
                    INSERT OR IGNORE INTO todo_tags (todo_id, tag_id)
                    VALUES (?, ?)
                    """,
                    (todo.id, tag_id),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def list_todos(self, todo_filter: TodoFilter | None = None) -> list[TodoItem]:
        if todo_filter is None or not todo_filter.is_active:
            rows = self._connection.execute(
                """
                SELECT id, title, completed
                FROM todos
                WHERE flushed = 0
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        elif todo_filter.tag_match == TagMatchMode.ALL:
            rows = self._list_todos_matching_all_tags(todo_filter.tag_names)
        else:
            rows = self._list_todos_matching_any_tag(todo_filter.tag_names)
        return [
            TodoItem(id=row[0], title=row[1], completed=bool(row[2]))
            for row in rows
        ]

    def _list_todos_matching_any_tag(
        self, tag_names: tuple[str, ...]
    ) -> list[tuple[str, str, int]]:
        placeholders = ", ".join("?" for _ in tag_names)
        return self._connection.execute(
            f"""
            SELECT DISTINCT todos.id, todos.title, todos.completed
            FROM todos
            INNER JOIN todo_tags ON todo_tags.todo_id = todos.id
            INNER JOIN tags ON tags.id = todo_tags.tag_id
            WHERE todos.flushed = 0 AND tags.name IN ({placeholders})
            ORDER BY todos.created_at ASC, todos.id ASC
            """,
            tag_names,
        ).fetchall()

    def _list_todos_matching_all_tags(
        self, tag_names: tuple[str, ...]
    ) -> list[tuple[str, str, int]]:
        placeholders = ", ".join("?" for _ in tag_names)
        return self._connection.execute(
            f"""
            SELECT todos.id, todos.title, todos.completed
            FROM todos
            WHERE todos.flushed = 0
            AND todos.id IN (
                SELECT todo_tags.todo_id
                FROM todo_tags
                INNER JOIN tags ON tags.id = todo_tags.tag_id
                WHERE tags.name IN ({placeholders})
                GROUP BY todo_tags.todo_id
                HAVING COUNT(DISTINCT tags.name) = ?
            )
            ORDER BY todos.created_at ASC, todos.id ASC
            """,
            (*tag_names, len(tag_names)),
        ).fetchall()

    def tags_for_todo(self, todo_id: str) -> list[str]:
        rows = self._connection.execute(
            """
            SELECT tags.name
            FROM tags
            INNER JOIN todo_tags ON todo_tags.tag_id = tags.id
            INNER JOIN todos ON todos.id = todo_tags.todo_id
            WHERE todo_tags.todo_id = ? AND todos.flushed = 0
            ORDER BY tags.name ASC
            """,
            (str(todo_id),),
        ).fetchall()
        return [str(row[0]) for row in rows]

    def flush_completed(self) -> None:
        self._connection.execute(
            """
            UPDATE todos
            SET flushed = 1
            WHERE completed = 1 AND flushed = 0
            """
        )
        self._connection.commit()

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

    def add_tags_for_todo(self, todo_id: str, tag_names: list[str]) -> None:
        if not self._is_todo_visible(todo_id):
            raise ValueError(f"Todo with id '{todo_id}' does not exist.")

        connection = self._connection
        try:
            connection.execute("BEGIN")
            for tag_name in tag_names:
                tag_id = self._get_or_create_tag_id(connection, tag_name)
                connection.execute(
                    """
                    INSERT OR IGNORE INTO todo_tags (todo_id, tag_id)
                    VALUES (?, ?)
                    """,
                    (str(todo_id), tag_id),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def list_tag_summaries(self) -> list[TagSummary]:
        rows = self._connection.execute(
            """
            SELECT
                tags.name,
                COUNT(
                    CASE
                        WHEN todos.flushed = 0 AND todos.completed = 0 THEN 1
                    END
                ) AS unfinished_count
            FROM tags
            LEFT JOIN todo_tags ON todo_tags.tag_id = tags.id
            LEFT JOIN todos ON todos.id = todo_tags.todo_id
            GROUP BY tags.id, tags.name
            ORDER BY tags.name ASC
            """
        ).fetchall()
        return [
            TagSummary(name=row[0], unfinished_count=int(row[1]))
            for row in rows
        ]

    def delete_tag(self, tag_name: str) -> None:
        connection = self._connection
        try:
            connection.execute("BEGIN")
            row = connection.execute(
                "SELECT id FROM tags WHERE name = ?",
                (tag_name,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Tag '{tag_name}' does not exist.")
            tag_id = str(row[0])
            connection.execute(
                "DELETE FROM todo_tags WHERE tag_id = ?",
                (tag_id,),
            )
            connection.execute(
                "DELETE FROM tags WHERE id = ?",
                (tag_id,),
            )
            connection.commit()
        except ValueError:
            connection.rollback()
            raise
        except Exception:
            connection.rollback()
            raise

    def _is_todo_visible(self, todo_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM todos WHERE id = ? AND flushed = 0",
            (str(todo_id),),
        ).fetchone()
        return row is not None

    def _get_or_create_tag_id(
        self, connection: sqlite3.Connection, tag_name: str
    ) -> str:
        row = connection.execute(
            "SELECT id FROM tags WHERE name = ?",
            (tag_name,),
        ).fetchone()
        if row is not None:
            return str(row[0])

        tag_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        connection.execute(
            """
            INSERT INTO tags (id, name, created_at)
            VALUES (?, ?, ?)
            """,
            (tag_id, tag_name, created_at),
        )
        return tag_id
