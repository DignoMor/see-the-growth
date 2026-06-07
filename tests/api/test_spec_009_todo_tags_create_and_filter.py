"""SPEC-009: Assign tags on create and filter todos by tag (API)."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.api.local_web_app import create_app
from see_the_growth.domain import TodoList


class TestSpec009TodoTagsCreateAndFilterApi(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(todo_list=TodoList())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_spec_009_create_form_includes_tags_field(self) -> None:
        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="tags"', body)
        self.assertIn('name="tags"', body)

    def test_spec_009_post_todos_with_tags_links_and_shows_tags(self) -> None:
        response = self.client.post(
            "/todos",
            data={"title": "Buy milk", "tags": "  Errand , home "},
            follow_redirects=True,
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Buy milk", body)
        self.assertRegex(body, r'todo-item__tag[^>]*>[\s\S]*?errand')
        self.assertRegex(body, r'todo-item__tag[^>]*>[\s\S]*?home')

    def test_spec_009_get_with_tag_filters_todo_list(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Errand item", tag_names=["errand"])
        todo_list.create_todo("Other item")

        response = self.client.get("/?tag=errand")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Errand item", body)
        self.assertNotIn("Other item", body)

    def test_spec_009_filter_banner_when_active(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Tagged", tag_names=["errand"])

        response = self.client.get("/?tag=errand")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('class="todo-filter"', body)
        self.assertIn("errand", body)

    def test_spec_009_tags_page_name_links_to_filter(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo = todo_list.create_todo("Sample")
        todo_list.add_tags_to_todo(todo.id, ["errand"])

        response = self.client.get("/tags")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertRegex(body, r'href="/\?tag=errand"')

    def test_spec_009_post_create_preserves_tag_filter_redirect(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Existing", tag_names=["errand"])

        response = self.client.post(
            "/todos?tag=errand",
            data={"title": "New errand", "tags": "errand"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("tag=errand", response.headers.get("Location", ""))


if __name__ == "__main__":
    unittest.main()
