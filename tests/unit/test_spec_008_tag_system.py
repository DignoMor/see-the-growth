"""SPEC-008: Tag system unit tests."""

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
from see_the_growth.domain.todo_list import TodoDomainError, TodoList
from see_the_growth.services.todo_service import TodoService


def _make_service(db_path: str) -> TodoService:
    return TodoService(SqliteTodoRepository(db_path))


def _table_exists(db_path: str, table_name: str) -> bool:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (table_name,),
        ).fetchone()
        return row is not None
    finally:
        connection.close()


def _task_tag_name(db_path: str) -> str | None:
    connection = sqlite3.connect(db_path)
    try:
        if not _table_exists(db_path, "tags"):
            return None
        row = connection.execute(
            "SELECT name FROM tags WHERE name = 'task'"
        ).fetchone()
        return None if row is None else str(row[0])
    finally:
        connection.close()


def _todo_has_tag(db_path: str, todo_id: str, tag_name: str) -> bool:
    connection = sqlite3.connect(db_path)
    try:
        if not _table_exists(db_path, "todo_tags"):
            return False
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


def _import_normalize_tag_name():
    try:
        from see_the_growth.domain.tag import normalize_tag_name
    except ImportError as exc:
        raise AssertionError(
            "normalize_tag_name not implemented (SPEC-008)"
        ) from exc
    return normalize_tag_name


class TestSpec008TagSystemUnit(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmpdir.name) / "todos.db")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_spec_008_create_todo_auto_links_task_tag(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Tagged item")

        self.assertTrue(
            _todo_has_tag(self.db_path, todo.id, "task"),
            "expected create_todo to link new todo to task tag",
        )

    def test_spec_008_tag_name_normalization(self) -> None:
        normalize_tag_name = _import_normalize_tag_name()

        self.assertEqual(normalize_tag_name("  Errand  "), "errand")
        self.assertEqual(normalize_tag_name("FOO   BAR"), "foo bar")
        self.assertEqual(normalize_tag_name("Task"), "task")

        with self.assertRaises(TodoDomainError):
            normalize_tag_name("   ")

    def test_spec_008_add_tags_to_todo_creates_and_links(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Multi-tag")

        service.add_tags_to_todo(todo.id, ["  Errand  ", "ERRAND"])

        self.assertTrue(_todo_has_tag(self.db_path, todo.id, "errand"))
        connection = sqlite3.connect(self.db_path)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM tags WHERE name = 'errand'"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(int(count[0]), 1)

    def test_spec_008_add_tags_idempotent(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Stable tags")

        service.add_tags_to_todo(todo.id, ["errand"])
        service.add_tags_to_todo(todo.id, ["errand"])

        connection = sqlite3.connect(self.db_path)
        try:
            link_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM todo_tags
                JOIN tags ON tags.id = todo_tags.tag_id
                WHERE todo_tags.todo_id = ? AND tags.name = 'errand'
                """,
                (todo.id,),
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(int(link_count[0]), 1)

    def test_spec_008_add_tags_unknown_todo_raises(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Will flush")
        service.complete_todo(todo.id)
        service.flush_completed()

        with self.assertRaises(TodoDomainError):
            service.add_tags_to_todo(todo.id, ["errand"])

        with self.assertRaises(TodoDomainError):
            service.add_tags_to_todo("missing-id", ["errand"])

    def test_spec_008_list_tag_summaries_unfinished_count(self) -> None:
        service = _make_service(self.db_path)
        open_todo = service.create_todo("Open")
        done_todo = service.create_todo("Done")
        service.complete_todo(done_todo.id)
        service.add_tags_to_todo(open_todo.id, ["errand"])
        service.add_tags_to_todo(done_todo.id, ["errand"])

        summaries = {item.name: item for item in service.list_tag_summaries()}

        self.assertEqual(summaries["errand"].unfinished_count, 1)
        self.assertEqual(summaries["task"].unfinished_count, 1)

    def test_spec_008_list_tag_summaries_includes_zero_unfinished(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Only task")
        service.add_tags_to_todo(todo.id, ["orphan"])
        service.complete_todo(todo.id)

        summaries = {item.name: item for item in service.list_tag_summaries()}

        self.assertIn("orphan", summaries)
        self.assertEqual(summaries["orphan"].unfinished_count, 0)
        self.assertIn("task", summaries)

    def test_spec_008_bootstrap_creates_tags_tables_and_task_tag(self) -> None:
        bootstrap_database(self.db_path)

        self.assertTrue(_table_exists(self.db_path, "tags"))
        self.assertTrue(_table_exists(self.db_path, "todo_tags"))
        self.assertEqual(_task_tag_name(self.db_path), "task")


class TestSpec008InMemoryTags(unittest.TestCase):
    def test_spec_008_in_memory_create_todo_auto_links_task_tag(self) -> None:
        todo_list = TodoList()
        todo = todo_list.create_todo("In memory")

        tags = todo_list.tags_for_todo(todo.id)

        self.assertIn("task", tags)


if __name__ == "__main__":
    unittest.main()
