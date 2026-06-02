"""SPEC-003: Database persistence API tests."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.api.local_web_app import create_app


class TestSpec003DatabasePersistenceApi(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self._tmpdir.name) / "todos.db")
        self._env_patch = patch.dict(
            os.environ,
            {"SEE_THE_GROWTH_DB_PATH": self.db_path},
            clear=False,
        )
        self._env_patch.start()

    def tearDown(self) -> None:
        self._env_patch.stop()
        self._tmpdir.cleanup()

    def test_spec_003_web_app_uses_persisted_store_by_default(self) -> None:
        app = create_app()
        app.testing = True
        client = app.test_client()

        response = client.post("/todos", data={"title": "Pay rent"}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Pay rent", response.get_data(as_text=True))
        self.assertTrue(Path(self.db_path).is_file())

    def test_spec_003_create_and_complete_via_http_survives_new_app_instance(self) -> None:
        first_app = create_app()
        first_app.testing = True
        first_client = first_app.test_client()

        create_response = first_client.post(
            "/todos",
            data={"title": "Buy milk"},
            follow_redirects=True,
        )
        self.assertEqual(create_response.status_code, 200)

        todo_id = first_app.config["TODO_LIST"].list_todos()[0].id
        complete_response = first_client.post(
            f"/todos/{todo_id}/complete",
            follow_redirects=True,
        )
        self.assertEqual(complete_response.status_code, 200)

        second_app = create_app()
        second_app.testing = True
        second_client = second_app.test_client()
        page_response = second_client.get("/")
        body = page_response.get_data(as_text=True)

        self.assertEqual(page_response.status_code, 200)
        self.assertIn("Buy milk", body)
        self.assertIn("completed", body.lower())


if __name__ == "__main__":
    unittest.main()
