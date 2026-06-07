"""SPEC-011: Advanced tag filtering (multi-tag selection) (API)."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.api.local_web_app import create_app
from see_the_growth.domain import TodoList


class TestSpec011AdvancedTagFilteringApi(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(todo_list=TodoList())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_spec_011_todo_page_shows_tag_filter_panel(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Sample", tag_names=["errand", "home"])

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('class="todo-tag-filter"', body)
        self.assertIn('class="todo-tag-filter__tags"', body)
        self.assertIn('name="tag"', body)
        self.assertIn('value="errand"', body)
        self.assertIn('value="home"', body)
        self.assertIn('value="task"', body)
        self.assertIn("Apply filter", body)

    def test_spec_011_filter_panel_reflects_active_filter(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Sample", tag_names=["errand", "home"])

        response = self.client.get("/?tag=errand&tag=home&tag_match=all")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            body,
            r'<input[^>]*name="tag"[^>]*value="errand"[^>]*checked',
        )
        self.assertRegex(
            body,
            r'<input[^>]*name="tag"[^>]*value="home"[^>]*checked',
        )
        self.assertRegex(
            body,
            r'<input[^>]*type="radio"[^>]*name="tag_match"[^>]*value="all"[^>]*checked',
        )

    def test_spec_011_get_apply_filter_any_shows_matching_todos(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Errand only", tag_names=["errand"])
        todo_list.create_todo("Home only", tag_names=["home"])
        todo_list.create_todo("Plain")

        response = self.client.get("/?tag=errand&tag=home&tag_match=any")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Errand only", body)
        self.assertIn("Home only", body)
        self.assertNotIn("Plain", body)

    def test_spec_011_get_apply_filter_all_shows_intersection(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Errand only", tag_names=["errand"])
        todo_list.create_todo("Both", tag_names=["errand", "home"])
        todo_list.create_todo("Home only", tag_names=["home"])

        response = self.client.get("/?tag=errand&tag=home&tag_match=all")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Both", body)
        self.assertNotIn("Errand only", body)
        self.assertNotIn("Home only", body)

    def test_spec_011_apply_filter_no_checkboxes_clears_filter(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Tagged", tag_names=["errand"])
        todo_list.create_todo("Other")

        response = self.client.get("/?tag_match=any")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('class="todo-filter"', body)
        self.assertIn("Tagged", body)
        self.assertIn("Other", body)

    def test_spec_011_post_create_preserves_multi_tag_filter_redirect(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Existing", tag_names=["errand", "home"])

        response = self.client.post(
            "/todos?tag=errand%2Chome&tag_match=all",
            data={"title": "New item", "tags": "errand"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        location = response.headers.get("Location", "")
        query = parse_qs(urlparse(location).query)
        self.assertEqual(query.get("tag"), ["errand,home"])
        self.assertEqual(query.get("tag_match"), ["all"])

    def test_spec_011_filter_banner_multi_tag_all_mode(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Both", tag_names=["errand", "home"])

        response = self.client.get("/?tag=errand&tag=home&tag_match=all")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('class="todo-filter"', body)
        self.assertIn("(all)", body)
        self.assertIn("errand", body)
        self.assertIn("home", body)


if __name__ == "__main__":
    unittest.main()
