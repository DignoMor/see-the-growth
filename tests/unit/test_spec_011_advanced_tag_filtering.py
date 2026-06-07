"""SPEC-011: Advanced tag filtering (multi-tag selection)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.domain.todo_filter import TagMatchMode, TodoFilter
from see_the_growth.domain.todo_filter import parse_todo_filter_from_query


class TestSpec011ParseTodoFilterFromQuery(unittest.TestCase):
    def test_spec_011_parse_repeated_tag_params(self) -> None:
        todo_filter = parse_todo_filter_from_query(["a", "b"])

        self.assertEqual(todo_filter.tag_names, ("a", "b"))
        self.assertEqual(todo_filter.tag_match, TagMatchMode.ANY)

    def test_spec_011_parse_merges_comma_and_repeated_tags(self) -> None:
        todo_filter = parse_todo_filter_from_query(["a,b", "c", "a"])

        self.assertEqual(todo_filter.tag_names, ("a", "b", "c"))

    def test_spec_011_parse_repeated_tags_with_match_all(self) -> None:
        todo_filter = parse_todo_filter_from_query(["errand", "home"], "all")

        self.assertEqual(todo_filter.tag_names, ("errand", "home"))
        self.assertEqual(todo_filter.tag_match, TagMatchMode.ALL)

    def test_spec_011_parse_empty_repeated_tags_returns_no_filter(self) -> None:
        self.assertFalse(parse_todo_filter_from_query([]).is_active)
        self.assertFalse(parse_todo_filter_from_query(["", "   "]).is_active)

    def test_spec_011_to_query_string_unchanged_for_multi_tag(self) -> None:
        todo_filter = TodoFilter.for_tags(["errand", "home"], match=TagMatchMode.ALL)

        self.assertEqual(
            todo_filter.to_query_string(),
            "tag=errand%2Chome&tag_match=all",
        )


if __name__ == "__main__":
    unittest.main()
