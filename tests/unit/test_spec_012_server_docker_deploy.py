import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = PROJECT_ROOT / "docker-compose.yml"


class TestSpec012ServerDockerDeploy(unittest.TestCase):
    def test_spec_012_compose_declares_gunicorn_healthcheck_and_port_7676(self) -> None:
        compose_text = COMPOSE_PATH.read_text()

        self.assertIn("gunicorn", compose_text.lower())
        self.assertIn("healthcheck:", compose_text)
        self.assertIn("unless-stopped", compose_text)
        self.assertIn("7676:5000", compose_text)
