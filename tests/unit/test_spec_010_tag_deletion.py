"""SPEC-010: Delete tags from tags page (unit tests)."""

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

from see_the_growth.db.sqlite_todo_repository import SqliteTodoRepository
from see_the_growth.domain.todo_list import TodoDomainError, TodoList
from see_the_growth.services.todo_service import TodoService


def _make_service(db_path: str) -> TodoService:
    return TodoService(SqliteTodoRepository(db_path))


def _tag_exists(db_path: str, tag_name: str) -> bool:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT 1 FROM tags WHERE name = ?",
            (tag_name,),
        ).fetchone()
        return row is not None
    finally:
        connection.close()


def _todo_has_tag(db_path: str, todo_id: str, tag_name: str) -> bool:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            """
            SELECT 1
            FROM todo_tags
            JOIN tags ON tags.id = todo_tags.tag_id
            WHERE todo_tags.todo_id = ? AND tags.name = ?
            """,
            (todo_id, tag_name),
        ).fetchone()
        return row is not None
    finally:
        connection.close()


def _todo_is_flushed(db_path: str, todo_id: str) -> bool:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT flushed FROM todos WHERE id = ?",
            (todo_id,),
        ).fetchone()
        return row is not None and int(row[0]) == 1
    finally:
        connection.close()


class TestSpec010TagDeletionUnit(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmpdir.name) / "todos.db")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_spec_010_delete_tag_removes_tag_and_associations(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Tagged")
        service.add_tags_to_todo(todo.id, ["errand"])

        service.delete_tag("errand")

        summaries = {item.name for item in service.list_tag_summaries()}
        self.assertNotIn("errand", summaries)
        self.assertFalse(_tag_exists(self.db_path, "errand"))
        self.assertNotIn("errand", service.tags_for_todo(todo.id))

    def test_spec_010_delete_tag_leaves_todo_and_other_tags(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Keep me", tag_names=["errand", "home"])

        service.delete_tag("errand")

        self.assertEqual(service.list_todos()[0].title, "Keep me")
        self.assertEqual(set(service.tags_for_todo(todo.id)), {"home", "task"})

    def test_spec_010_delete_tag_removes_from_flushed_todo_associations(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Gone", tag_names=["errand"])
        service.complete_todo(todo.id)
        service.flush_completed()

        service.delete_tag("errand")

        self.assertTrue(_todo_is_flushed(self.db_path, todo.id))
        self.assertFalse(_todo_has_tag(self.db_path, todo.id, "errand"))
        self.assertFalse(_tag_exists(self.db_path, "errand"))

    def test_spec_010_delete_task_tag_raises(self) -> None:
        service = _make_service(self.db_path)

        with self.assertRaises(TodoDomainError) as ctx:
            service.delete_tag("task")

        self.assertIn("cannot be deleted", str(ctx.exception).lower())
        self.assertTrue(_tag_exists(self.db_path, "task"))

    def test_spec_010_delete_unknown_tag_raises(self) -> None:
        service = _make_service(self.db_path)

        with self.assertRaises(TodoDomainError) as ctx:
            service.delete_tag("missing")

        self.assertIn("does not exist", str(ctx.exception).lower())

    def test_spec_010_in_memory_delete_tag_parity(self) -> None:
        todo_list = TodoList()
        todo = todo_list.create_todo("Item", tag_names=["errand", "home"])

        todo_list.delete_tag("errand")

        summaries = {item.name for item in todo_list.list_tag_summaries()}
        self.assertNotIn("errand", summaries)
        self.assertEqual(set(todo_list.tags_for_todo(todo.id)), {"home", "task"})

        with self.assertRaises(TodoDomainError):
            todo_list.delete_tag("task")

        with self.assertRaises(TodoDomainError):
            todo_list.delete_tag("ghost")


if __name__ == "__main__":
    unittest.main()
