"""Gate password configuration (SPEC-013).

Default: auth disabled (no gate password).
Override: environment variable ``SEE_THE_GROWTH_GATE_PASSWORD``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

GATE_PASSWORD_ENV_VAR = "SEE_THE_GROWTH_GATE_PASSWORD"


@dataclass(frozen=True)
class AuthConfig:
    gate_password: str | None

    def __post_init__(self) -> None:
        if self.gate_password is None:
            return
        stripped = self.gate_password.strip()
        if not stripped:
            object.__setattr__(self, "gate_password", None)
        elif stripped != self.gate_password:
            object.__setattr__(self, "gate_password", stripped)

    @property
    def enabled(self) -> bool:
        return self.gate_password is not None


def resolve_auth_config() -> AuthConfig:
    raw = os.environ.get(GATE_PASSWORD_ENV_VAR)
    if raw is None:
        return AuthConfig(gate_password=None)
    return AuthConfig(gate_password=raw)
