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


class TestSpec002LocalAppSmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(todo_list=TodoList())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_spec_002_local_app_smoke_create_and_complete_flow(self) -> None:
        create_response = self.client.post("/todos", data={"title": "Plan week"}, follow_redirects=True)
        self.assertEqual(create_response.status_code, 200)
        self.assertIn("Plan week", create_response.get_data(as_text=True))

        todo = self.app.config["TODO_LIST"].list_todos()[0]
        complete_response = self.client.post(f"/todos/{todo.id}/complete", follow_redirects=True)
        complete_body = complete_response.get_data(as_text=True)

        self.assertEqual(complete_response.status_code, 200)
        self.assertIn("Plan week", complete_body)
        self.assertIn("completed", complete_body.lower())


if __name__ == "__main__":
    unittest.main()
