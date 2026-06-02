"""SPEC-006: Flush completed todos unit tests."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.db.bootstrap import bootstrap_database
from see_the_growth.db.sqlite_todo_repository import SqliteTodoRepository
from see_the_growth.domain.todo_list import TodoList
from see_the_growth.services.todo_service import TodoService


def _make_service(db_path: str) -> TodoService:
    return TodoService(SqliteTodoRepository(db_path))


def _todo_row_count(db_path: str) -> int:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM todos").fetchone()
        return int(row[0])
    finally:
        connection.close()


def _flushed_count(db_path: str) -> int:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT COUNT(*) FROM todos WHERE flushed = 1"
        ).fetchone()
        return int(row[0])
    finally:
        connection.close()


class TestSpec006FlushCompletedUnit(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmpdir.name) / "todos.db")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_spec_006_flush_completed_hides_completed_from_list(self) -> None:
        service = _make_service(self.db_path)
        first = service.create_todo("done one")
        second = service.create_todo("done two")
        service.complete_todo(first.id)
        service.complete_todo(second.id)

        service.flush_completed()

        titles = [todo.title for todo in service.list_todos()]
        self.assertEqual(titles, [])

    def test_spec_006_flush_completed_leaves_active_todos_visible(self) -> None:
        service = _make_service(self.db_path)
        active = service.create_todo("still open")
        done = service.create_todo("finished")
        service.complete_todo(done.id)

        service.flush_completed()

        todos = service.list_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0].id, active.id)
        self.assertEqual(todos[0].title, "still open")
        self.assertFalse(todos[0].completed)

    def test_spec_006_flush_completed_rows_remain_in_database(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("persisted")
        service.complete_todo(todo.id)

        service.flush_completed()

        self.assertEqual(_todo_row_count(self.db_path), 1)
        self.assertEqual(_flushed_count(self.db_path), 1)

    def test_spec_006_flush_completed_is_idempotent(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("once")
        service.complete_todo(todo.id)

        service.flush_completed()
        service.flush_completed()

        self.assertEqual(service.list_todos(), [])
        self.assertEqual(_flushed_count(self.db_path), 1)

    def test_spec_006_bootstrap_adds_flushed_column_to_existing_database(self) -> None:
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(
                """
                CREATE TABLE todos (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    completed INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

        bootstrap_database(self.db_path)

        connection = sqlite3.connect(self.db_path)
        try:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(todos)").fetchall()
            }
        finally:
            connection.close()

        self.assertIn("flushed", columns)


class TestSpec006InMemoryFlush(unittest.TestCase):
    def test_spec_006_in_memory_flush_hides_completed_only(self) -> None:
        todo_list = TodoList()
        active = todo_list.create_todo("active")
        done = todo_list.create_todo("done")
        todo_list.complete_todo(done.id)

        todo_list.flush_completed()

        visible = todo_list.list_todos()
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].id, active.id)


if __name__ == "__main__":
    unittest.main()
