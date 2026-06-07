import sys
import unittest
from pathlib import Path


# Ensure src-layout imports work when tests are run from repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.api.local_web_app import create_app
from see_the_growth.domain import TodoList


class TestSpec002LocalWebInterface(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(todo_list=TodoList())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_spec_002_get_todo_page_returns_html_and_lists_todos(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        todo_list.create_todo("Pay rent")
        todo_list.create_todo("Read book")

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)
        self.assertIn("Pay rent", body)
        self.assertIn("Read book", body)

    def test_spec_002_create_todo_from_form_succeeds_and_renders_new_item(self) -> None:
        response = self.client.post("/todos", data={"title": "  Buy milk  "}, follow_redirects=True)
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Buy milk", body)

    def test_spec_002_create_todo_from_form_rejects_empty_title_with_4xx(self) -> None:
        response = self.client.post("/todos", data={"title": "   "})
        body = response.get_data(as_text=True)

        self.assertGreaterEqual(response.status_code, 400)
        self.assertLess(response.status_code, 500)
        self.assertIn("must not be empty", body)

    def test_spec_002_complete_todo_from_form_marks_item_completed(self) -> None:
        todo = self.app.config["TODO_LIST"].create_todo("Write docs")

        response = self.client.post(f"/todos/{todo.id}/complete", follow_redirects=True)
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Write docs", body)
        self.assertIn("completed", body.lower())

    def test_spec_002_complete_unknown_todo_returns_404(self) -> None:
        unknown_id = "a8f4f8ab-b6e4-4f4d-8f5a-5ed206f8b0d5"

        response = self.client.post(f"/todos/{unknown_id}/complete")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 404)
        self.assertIn("does not exist", body)

    def test_spec_002_domain_errors_are_exposed_as_user_visible_messages(self) -> None:
        response = self.client.post("/todos", data={"title": ""})
        body = response.get_data(as_text=True)

        self.assertGreaterEqual(response.status_code, 400)
        self.assertIn("Todo title must not be empty", body)


if __name__ == "__main__":
    unittest.main()
