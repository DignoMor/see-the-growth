import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.api.auth import verify_gate_password
from see_the_growth.api.auth_config import AuthConfig, resolve_auth_config


class TestSpec013GatePasswordAuth(unittest.TestCase):
    def test_spec_013_auth_disabled_when_env_unset(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = resolve_auth_config()

        self.assertFalse(config.enabled)
        self.assertIsNone(config.gate_password)

    def test_spec_013_auth_disabled_when_env_empty_or_whitespace(self) -> None:
        with patch.dict(os.environ, {"SEE_THE_GROWTH_GATE_PASSWORD": ""}, clear=True):
            self.assertFalse(resolve_auth_config().enabled)

        with patch.dict(os.environ, {"SEE_THE_GROWTH_GATE_PASSWORD": "   "}, clear=True):
            self.assertFalse(resolve_auth_config().enabled)

    def test_spec_013_auth_enabled_when_env_set(self) -> None:
        with patch.dict(
            os.environ, {"SEE_THE_GROWTH_GATE_PASSWORD": "secret"}, clear=True
        ):
            config = resolve_auth_config()

        self.assertTrue(config.enabled)
        self.assertEqual(config.gate_password, "secret")

    def test_spec_013_auth_config_enabled_property(self) -> None:
        self.assertFalse(AuthConfig(gate_password=None).enabled)
        self.assertFalse(AuthConfig(gate_password="").enabled)
        self.assertFalse(AuthConfig(gate_password="   ").enabled)
        self.assertTrue(AuthConfig(gate_password="x").enabled)

    def test_spec_013_verify_password_accepts_matching_secret(self) -> None:
        self.assertTrue(verify_gate_password("secret", "secret"))

    def test_spec_013_verify_password_rejects_wrong_secret(self) -> None:
        self.assertFalse(verify_gate_password("wrong", "secret"))
        self.assertFalse(verify_gate_password("", "secret"))


if __name__ == "__main__":
    unittest.main()
