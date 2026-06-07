"""SPEC-010: Delete tags from tags page (API tests)."""

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


class TestSpec010TagDeletionApi(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(todo_list=TodoList())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_spec_010_tags_page_shows_delete_for_user_tag(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo = todo_list.create_todo("Sample")
        todo_list.add_tags_to_todo(todo.id, ["errand"])

        response = self.client.get("/tags")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('action="/tags/errand/delete"', body)
        self.assertIn("tags-item__delete-form", body)
        self.assertRegex(body, r'tags-item__delete-btn[^>]*>\s*Delete')

    def test_spec_010_tags_page_no_delete_for_task(self) -> None:
        response = self.client.get("/tags")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('action="/tags/task/delete"', body)
        self.assertNotRegex(
            body,
            r'tags-item[^>]*>[\s\S]*?task[\s\S]*?tags-item__delete-form',
        )

    def test_spec_010_post_delete_tag_redirects_and_removes(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo = todo_list.create_todo("Sample")
        todo_list.add_tags_to_todo(todo.id, ["errand"])

        response = self.client.post("/tags/errand/delete", follow_redirects=True)
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.path, "/tags")
        self.assertNotRegex(body, r'href="/\?tag=errand"')
        summaries = {item.name for item in todo_list.list_tag_summaries()}
        self.assertNotIn("errand", summaries)

    def test_spec_010_post_delete_tag_updates_todo_row(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Buy milk", tag_names=["errand"])

        self.client.post("/tags/errand/delete", follow_redirects=True)

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Buy milk", body)
        self.assertNotRegex(body, r'todo-item__tag[^>]*>[\s\S]*?errand')

    def test_spec_010_post_delete_task_returns_400(self) -> None:
        response = self.client.post("/tags/task/delete")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 400)
        self.assertIn("alert--error", body)
        self.assertIn("cannot be deleted", body.lower())

    def test_spec_010_post_delete_unknown_tag_returns_404(self) -> None:
        response = self.client.post("/tags/ghost/delete")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 404)
        self.assertIn("alert--error", body)
        self.assertIn("does not exist", body.lower())


if __name__ == "__main__":
    unittest.main()
