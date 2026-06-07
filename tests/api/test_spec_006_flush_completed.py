"""SPEC-006: Flush completed todos API tests."""

from __future__ import annotations

import os
import sqlite3
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
from see_the_growth.domain import TodoList


def _todo_row_count(db_path: str) -> int:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM todos").fetchone()
        return int(row[0])
    finally:
        connection.close()


class TestSpec006FlushCompletedApi(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(todo_list=TodoList())
        self.app.testing = True
        self.client = self.app.test_client()

    def test_spec_006_post_flush_completed_removes_completed_from_page(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        item = todo_list.create_todo("Old task")
        todo_list.complete_todo(item.id)

        response = self.client.post("/todos/flush-completed", follow_redirects=True)
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Old task", body)

    def test_spec_006_flush_completed_leaves_active_on_page(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        active = todo_list.create_todo("Keep me")
        done = todo_list.create_todo("Remove me")
        todo_list.complete_todo(done.id)

        response = self.client.post("/todos/flush-completed", follow_redirects=True)
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Keep me", body)
        self.assertNotIn("Remove me", body)

    def test_spec_006_flush_form_shown_when_completed_visible(self) -> None:
        todo_list = self.app.config["TODO_LIST"]
        item = todo_list.create_todo("Done")
        todo_list.complete_todo(item.id)

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("todo-flush-form", body)
        self.assertIn("Flush completed", body)
        self.assertIn("/todos/flush-completed", body)

    def test_spec_006_flush_form_hidden_when_no_completed_visible(self) -> None:
        self.app.config["TODO_LIST"].create_todo("Active only")

        response = self.client.get("/")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("todo-flush-form", body)
        self.assertNotIn("Flush completed", body)


class TestSpec006FlushCompletedPersistenceApi(unittest.TestCase):
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

    def test_spec_006_flushed_todos_hidden_after_app_restart(self) -> None:
        first_app = create_app()
        first_app.testing = True
        first_client = first_app.test_client()

        create_response = first_client.post(
            "/todos",
            data={"title": "Archived task"},
            follow_redirects=True,
        )
        self.assertEqual(create_response.status_code, 200)

        todo_id = first_app.config["TODO_LIST"].list_todos()[0].id
        first_client.post(f"/todos/{todo_id}/complete", follow_redirects=True)
        flush_response = first_client.post(
            "/todos/flush-completed",
            follow_redirects=True,
        )
        self.assertEqual(flush_response.status_code, 200)
        self.assertNotIn("Archived task", flush_response.get_data(as_text=True))
        self.assertEqual(_todo_row_count(self.db_path), 1)

        second_app = create_app()
        second_app.testing = True
        second_client = second_app.test_client()
        page_response = second_client.get("/")
        body = page_response.get_data(as_text=True)

        self.assertEqual(page_response.status_code, 200)
        self.assertNotIn("Archived task", body)


if __name__ == "__main__":
    unittest.main()
