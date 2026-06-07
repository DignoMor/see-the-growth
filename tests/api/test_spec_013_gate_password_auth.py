import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.api.auth_config import AuthConfig
from see_the_growth.api.local_web_app import create_app
from see_the_growth.domain import TodoList


GATE_PASSWORD = "test-gate-secret"


class TestSpec013GatePasswordAuth(unittest.TestCase):
    def test_spec_013_auth_disabled_allows_todo_page_without_login(self) -> None:
        app = create_app(todo_list=TodoList(), auth_config=AuthConfig(gate_password=None))
        app.testing = True
        client = app.test_client()

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.content_type)

    def test_spec_013_auth_enabled_redirects_unauthenticated_to_login(self) -> None:
        app = create_app(
            todo_list=TodoList(),
            auth_config=AuthConfig(gate_password=GATE_PASSWORD),
        )
        app.testing = True
        client = app.test_client()

        response = client.get("/tags")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)
        self.assertIn("next=", response.location)

    def test_spec_013_auth_enabled_wrong_password_returns_401(self) -> None:
        app = create_app(
            todo_list=TodoList(),
            auth_config=AuthConfig(gate_password=GATE_PASSWORD),
        )
        app.testing = True
        client = app.test_client()

        response = client.post("/login", data={"password": "wrong-password"})

        self.assertEqual(response.status_code, 401)
        self.assertIn("Incorrect password", response.get_data(as_text=True))

    def test_spec_013_auth_enabled_correct_password_grants_access(self) -> None:
        app = create_app(
            todo_list=TodoList(),
            auth_config=AuthConfig(gate_password=GATE_PASSWORD),
        )
        app.testing = True
        client = app.test_client()

        login_response = client.post(
            "/login",
            data={"password": GATE_PASSWORD, "next": "/"},
            follow_redirects=False,
        )

        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.location, "/")

        todo_response = client.get("/")
        self.assertEqual(todo_response.status_code, 200)
        self.assertIn("Todo List", todo_response.get_data(as_text=True))

    def test_spec_013_health_accessible_without_auth_when_enabled(self) -> None:
        app = create_app(
            todo_list=TodoList(),
            auth_config=AuthConfig(gate_password=GATE_PASSWORD),
        )
        app.testing = True
        client = app.test_client()

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_spec_013_logout_clears_session(self) -> None:
        app = create_app(
            todo_list=TodoList(),
            auth_config=AuthConfig(gate_password=GATE_PASSWORD),
        )
        app.testing = True
        client = app.test_client()

        client.post(
            "/login",
            data={"password": GATE_PASSWORD},
            follow_redirects=True,
        )
        self.assertEqual(client.get("/").status_code, 200)

        logout_response = client.post("/logout", follow_redirects=False)
        self.assertEqual(logout_response.status_code, 302)
        self.assertIn("/login", logout_response.location)

        protected_response = client.get("/")
        self.assertEqual(protected_response.status_code, 302)
        self.assertIn("/login", protected_response.location)


if __name__ == "__main__":
    unittest.main()
