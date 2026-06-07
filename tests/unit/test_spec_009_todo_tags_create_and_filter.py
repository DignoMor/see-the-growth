"""SPEC-009: Assign tags on create and filter todos by tag."""

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
from see_the_growth.domain.todo_filter import TagMatchMode, TodoFilter
from see_the_growth.domain.todo_list import TodoDomainError, TodoList
from see_the_growth.services.todo_service import TodoService


def _make_service(db_path: str) -> TodoService:
    return TodoService(SqliteTodoRepository(db_path))


def _import_parse_tag_names():
    try:
        from see_the_growth.domain.tag import parse_tag_names
    except ImportError as exc:
        raise AssertionError("parse_tag_names not implemented (SPEC-009)") from exc
    return parse_tag_names


class TestSpec009ParseTagNames(unittest.TestCase):
    def test_spec_009_parse_tag_names_splits_and_normalizes(self) -> None:
        parse_tag_names = _import_parse_tag_names()

        self.assertEqual(parse_tag_names("  Errand , HOME , errand "), ["errand", "home"])

    def test_spec_009_parse_tag_names_empty_returns_empty_list(self) -> None:
        parse_tag_names = _import_parse_tag_names()

        self.assertEqual(parse_tag_names(""), [])
        self.assertEqual(parse_tag_names("   "), [])
        self.assertEqual(parse_tag_names(", ,,"), [])


class TestSpec009CreateAndFilterService(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmpdir.name) / "todos.db")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_spec_009_create_todo_with_extra_tags(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Shop", tag_names=["  Errand  ", "errand"])

        tags = service.tags_for_todo(todo.id)

        self.assertEqual(tags, ["errand", "task"])

    def test_spec_009_create_todo_invalid_tag_raises(self) -> None:
        service = _make_service(self.db_path)

        with self.assertRaises(TodoDomainError):
            service.create_todo("Bad tags", tag_names=["   "])

    def test_spec_009_list_todos_filter_by_tag(self) -> None:
        service = _make_service(self.db_path)
        service.create_todo("Errand one", tag_names=["errand"])
        service.create_todo("Home task", tag_names=["home"])
        service.create_todo("Plain task")

        errand_todos = service.list_todos(TodoFilter.for_single_tag("errand"))
        home_todos = service.list_todos(TodoFilter.for_single_tag("home"))
        all_todos = service.list_todos()

        self.assertEqual([todo.title for todo in errand_todos], ["Errand one"])
        self.assertEqual([todo.title for todo in home_todos], ["Home task"])
        self.assertEqual(len(all_todos), 3)

    def test_spec_009_list_todos_filter_unknown_tag_returns_empty(self) -> None:
        service = _make_service(self.db_path)
        service.create_todo("Only task")

        self.assertEqual(
            service.list_todos(TodoFilter.for_single_tag("missing")),
            [],
        )

    def test_spec_009_list_todos_filter_any_of_multiple_tags(self) -> None:
        service = _make_service(self.db_path)
        service.create_todo("Errand only", tag_names=["errand"])
        service.create_todo("Home only", tag_names=["home"])
        service.create_todo("Both", tag_names=["errand", "home"])

        filtered = service.list_todos(
            TodoFilter.for_tags(["errand", "home"], match=TagMatchMode.ANY)
        )

        self.assertEqual(
            {todo.title for todo in filtered},
            {"Errand only", "Home only", "Both"},
        )

    def test_spec_009_list_todos_filter_all_of_multiple_tags(self) -> None:
        service = _make_service(self.db_path)
        service.create_todo("Errand only", tag_names=["errand"])
        service.create_todo("Both", tag_names=["errand", "home"])

        filtered = service.list_todos(
            TodoFilter.for_tags(["errand", "home"], match=TagMatchMode.ALL)
        )

        self.assertEqual([todo.title for todo in filtered], ["Both"])

    def test_spec_009_tags_for_todo_returns_sorted_names(self) -> None:
        service = _make_service(self.db_path)
        todo = service.create_todo("Tagged", tag_names=["zebra", "alpha"])

        self.assertEqual(service.tags_for_todo(todo.id), ["alpha", "task", "zebra"])

    def test_spec_009_tags_for_todo_unknown_returns_empty(self) -> None:
        service = _make_service(self.db_path)

        self.assertEqual(service.tags_for_todo("missing-id"), [])


class TestSpec009TodoFilter(unittest.TestCase):
    def test_spec_009_todo_filter_matches_any(self) -> None:
        todo_filter = TodoFilter.for_tags(["errand", "home"], match=TagMatchMode.ANY)

        self.assertTrue(todo_filter.matches({"errand", "task"}))
        self.assertTrue(todo_filter.matches({"home"}))
        self.assertFalse(todo_filter.matches({"task"}))

    def test_spec_009_todo_filter_matches_all(self) -> None:
        todo_filter = TodoFilter.for_tags(["errand", "home"], match=TagMatchMode.ALL)

        self.assertTrue(todo_filter.matches({"errand", "home", "task"}))
        self.assertFalse(todo_filter.matches({"errand", "task"}))

    def test_spec_009_parse_todo_filter_from_query(self) -> None:
        from see_the_growth.domain.todo_filter import parse_todo_filter_from_query

        self.assertEqual(
            parse_todo_filter_from_query("errand, home").tag_names,
            ("errand", "home"),
        )
        self.assertEqual(
            parse_todo_filter_from_query("errand", "all").tag_match,
            TagMatchMode.ALL,
        )
        self.assertFalse(parse_todo_filter_from_query("").is_active)


class TestSpec009InMemoryCreateAndFilter(unittest.TestCase):
    def test_spec_009_in_memory_create_and_filter(self) -> None:
        todo_list = TodoList()
        todo_list.create_todo("Errand item", tag_names=["errand"])
        todo_list.create_todo("Other")

        filtered = todo_list.list_todos(TodoFilter.for_single_tag("errand"))

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Errand item")
        self.assertEqual(todo_list.tags_for_todo(filtered[0].id), ["errand", "task"])


if __name__ == "__main__":
    unittest.main()
