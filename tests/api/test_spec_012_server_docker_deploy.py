import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.api.local_web_app import create_app
from see_the_growth.domain import TodoList


class TestSpec012ServerDockerDeploy(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(todo_list=TodoList())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_spec_012_health_returns_ok_json(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
