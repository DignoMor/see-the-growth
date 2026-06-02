"""SPEC-005: UI polish presentation assertions."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.api.local_web_app import create_app
from see_the_growth.domain import TodoList


class TestSpec005UiPolish(unittest.TestCase):
    """SPEC-005: HTML structure and stable selectors for styled todo page."""

    def setUp(self) -> None:
        self.app = create_app(todo_list=TodoList())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_spec_005_get_page_links_stylesheet(self) -> None:
        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("todo.css" in body or "/static/todo.css" in body)

    def test_spec_005_page_has_main_landmark(self) -> None:
        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("<main", body)

    def test_spec_005_active_todo_has_item_class(self) -> None:
        self.app.config["TODO_LIST"].create_todo("Active task")

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("todo-item", body)
        self.assertNotIn("todo-item--completed", body)

    def test_spec_005_completed_todo_has_completed_class(self) -> None:
        todo = self.app.config["TODO_LIST"].create_todo("Done task")

        response = self.client.post(
            f"/todos/{todo.id}/complete", follow_redirects=True
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("todo-item--completed", body)

    def test_spec_005_error_renders_alert_classes(self) -> None:
        response = self.client.post("/todos", data={"title": "   "})
        body = response.get_data(as_text=True)

        self.assertGreaterEqual(response.status_code, 400)
        self.assertLess(response.status_code, 500)
        self.assertIn('role="alert"', body)
        self.assertIn("alert--error", body)

    def test_spec_005_template_has_no_inline_style_attributes(self) -> None:
        self.app.config["TODO_LIST"].create_todo("Sample")

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('style="display:inline"', body)
        self.assertNotIn('style="', body)


if __name__ == "__main__":
    unittest.main()
