"""SPEC-008: Tag system API tests."""

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


class TestSpec008TagSystemApi(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(todo_list=TodoList())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_spec_008_get_tags_page_returns_200(self) -> None:
        response = self.client.get("/tags")

        self.assertEqual(response.status_code, 200)

    def test_spec_008_tags_page_shows_unfinished_count(self) -> None:
        self.app.config["TODO_LIST"].create_todo("Active work")

        response = self.client.get("/tags")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("tags-item__unfinished-count", body)
        self.assertRegex(body, r"tags-item__unfinished-count[^>]*>\s*[1-9]")

    def test_spec_008_tags_page_shows_tag_with_zero_unfinished(self) -> None:
        response = self.client.get("/tags")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("task", body)
        self.assertRegex(
            body,
            r"tags-item[^>]*>[\s\S]*?task[\s\S]*?tags-item__unfinished-count[^>]*>\s*0",
        )

    def test_spec_008_tags_page_lists_tag_name(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo = todo_list.create_todo("Sample")
        todo_list.add_tags_to_todo(todo.id, ["  Errand  "])

        response = self.client.get("/tags")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("errand", body)

    def test_spec_008_todo_page_has_sidebar_nav(self) -> None:
        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('class="app-nav"', body)
        self.assertIn("Todo", body)
        self.assertIn("Tags", body)
        self.assertIn('href="/tags"', body)

    def test_spec_008_tags_page_has_sidebar_nav(self) -> None:
        response = self.client.get("/tags")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('class="app-nav"', body)
        self.assertIn("Todo", body)
        self.assertIn("Tags", body)

    def test_spec_008_nav_active_state_todo(self) -> None:
        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            body,
            r'<a[^>]*app-nav__link--active[^>]*>[\s\S]*?Todo',
        )

    def test_spec_008_nav_active_state_tags(self) -> None:
        response = self.client.get("/tags")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            body,
            r'<a[^>]*app-nav__link--active[^>]*>[\s\S]*?Tags',
        )

    def test_spec_008_create_todo_still_works(self) -> None:
        response = self.client.post(
            "/todos",
            data={"title": "Regression item"},
            follow_redirects=True,
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Regression item", body)


if __name__ == "__main__":
    unittest.main()
