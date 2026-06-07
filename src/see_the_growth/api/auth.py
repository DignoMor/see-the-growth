"""Gate password session helpers (SPEC-013)."""

from __future__ import annotations

import hashlib
import secrets

SESSION_AUTHENTICATED_KEY = "gate_authenticated"


def secret_key_for_gate_password(gate_password: str) -> str:
    digest = hashlib.sha256(f"see-the-growth-gate:{gate_password}".encode())
    return digest.hexdigest()


def verify_gate_password(submitted: str, gate_password: str) -> bool:
    return secrets.compare_digest(submitted, gate_password)


def is_authenticated(session) -> bool:
    return session.get(SESSION_AUTHENTICATED_KEY) is True


def mark_authenticated(session) -> None:
    session[SESSION_AUTHENTICATED_KEY] = True


def clear_authentication(session) -> None:
    session.pop(SESSION_AUTHENTICATED_KEY, None)


def safe_redirect_target(next_param: str | None) -> str:
    if not next_param:
        return "/"
    if not next_param.startswith("/") or next_param.startswith("//"):
        return "/"
    return next_param
