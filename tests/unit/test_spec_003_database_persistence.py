"""SPEC-003: Database persistence unit tests."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import UUID


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.db.bootstrap import bootstrap_database
from see_the_growth.db.sqlite_todo_repository import SqliteTodoRepository
from see_the_growth.domain.todo_list import TodoDomainError, TodoItem
from see_the_growth.services.todo_service import TodoService


def _todo_row_count(db_path: str) -> int:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM todos").fetchone()
        return int(row[0])
    finally:
        connection.close()


def _todo_completed(db_path: str, todo_id: str) -> bool:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT completed FROM todos WHERE id = ?",
            (todo_id,),
        ).fetchone()
        if row is None:
            raise AssertionError(f"Todo {todo_id} not found in database.")
        return bool(row[0])
    finally:
        connection.close()


def _make_service(db_path: str) -> TodoService:
    repository = SqliteTodoRepository(db_path)
    return TodoService(repository)


class TestSpec003DatabasePersistence(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmpdir.name) / "todos.db")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_spec_003_create_todo_persists_to_database(self) -> None:
        service = _make_service(self.db_path)

        service.create_todo("Buy milk")

        self.assertEqual(_todo_row_count(self.db_path), 1)

    def test_spec_003_list_todos_reads_from_database_in_creation_order(self) -> None:
        service = _make_service(self.db_path)
        first = service.create_todo("first")
        second = service.create_todo("second")
        third = service.create_todo("third")

        reloaded = _make_service(self.db_path)
        todos = reloaded.list_todos()

        self.assertEqual([todo.id for todo in todos], [first.id, second.id, third.id])

    def test_spec_003_complete_todo_updates_database_row(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("write tests")

        service.complete_todo(todo.id)

        self.assertTrue(_todo_completed(self.db_path, todo.id))
        self.assertTrue(service.list_todos()[0].completed)

    def test_spec_003_complete_unknown_todo_raises_domain_error(self) -> None:
        service = _make_service(self.db_path)

        with self.assertRaises(TodoDomainError):
            service.complete_todo("a8f4f8ab-b6e4-4f4d-8f5a-5ed206f8b0d5")

    def test_spec_003_complete_todo_is_idempotent_in_database(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("idempotent completion")

        service.complete_todo(todo.id)
        service.complete_todo(todo.id)

        self.assertTrue(_todo_completed(self.db_path, todo.id))
        self.assertTrue(service.list_todos()[0].completed)

    def test_spec_003_todos_survive_service_reinstantiation(self) -> None:
        first_service = _make_service(self.db_path)
        todo = first_service.create_todo("survive restart")
        first_service.complete_todo(todo.id)

        second_service = _make_service(self.db_path)
        todos = second_service.list_todos()

        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0].id, todo.id)
        self.assertEqual(todos[0].title, "survive restart")
        self.assertTrue(todos[0].completed)

    def test_spec_003_bootstrap_is_idempotent(self) -> None:
        bootstrap_database(self.db_path)
        bootstrap_database(self.db_path)

        connection = sqlite3.connect(self.db_path)
        try:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'todos'"
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(len(tables), 1)

    def test_spec_003_spec_001_domain_rules_still_hold_with_sqlite_backend(self) -> None:
        """Regression guard: SPEC-001 behavior via SQLite-backed TodoService."""
        service = _make_service(self.db_path)

        with self.assertRaises(TodoDomainError):
            service.create_todo("   ")

        todo = service.create_todo("  Buy milk  ")
        parsed_id = UUID(str(todo.id))
        self.assertEqual(str(parsed_id), str(todo.id))
        self.assertEqual(todo.title, "Buy milk")
        self.assertFalse(todo.completed)

        first = service.create_todo("first")
        second = service.create_todo("second")
        third = service.create_todo("third")
        todos = service.list_todos()
        self.assertEqual(
            [item.id for item in todos],
            [todo.id, first.id, second.id, third.id],
        )

        service.complete_todo(todo.id)
        self.assertTrue(service.list_todos()[0].completed)


class TestSpec003SqliteTodoRepository(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmpdir.name) / "todos.db")
        bootstrap_database(self.db_path)
        self.repository = SqliteTodoRepository(self.db_path)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_spec_003_repository_add_and_list_persist_rows(self) -> None:
        first = TodoItem(id="11111111-1111-4111-8111-111111111111", title="one")
        second = TodoItem(id="22222222-2222-4222-8222-222222222222", title="two")

        self.repository.add_todo(first)
        self.repository.add_todo(second)

        reloaded = SqliteTodoRepository(self.db_path)
        todos = reloaded.list_todos()

        self.assertEqual([todo.id for todo in todos], [first.id, second.id])

    def test_spec_003_repository_mark_completed_returns_false_for_unknown_id(self) -> None:
        updated = self.repository.mark_completed("a8f4f8ab-b6e4-4f4d-8f5a-5ed206f8b0d5")

        self.assertFalse(updated)


if __name__ == "__main__":
    unittest.main()
