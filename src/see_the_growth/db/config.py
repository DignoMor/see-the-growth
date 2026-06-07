"""Database path configuration (SPEC-003).

Default: ``data/todos.db`` relative to the process working directory.
Docker (SPEC-004): ``WORKDIR`` ``/app`` and bind mount ``./data:/app/data``
→ host ``<repo>/data/todos.db``, container ``/app/data/todos.db``.
Override: environment variable ``SEE_THE_GROWTH_DB_PATH``.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB_PATH = Path("data/todos.db")
DB_PATH_ENV_VAR = "SEE_THE_GROWTH_DB_PATH"


def resolve_db_path() -> str:
    override = os.environ.get(DB_PATH_ENV_VAR)
    if override:
        return override
    return str(DEFAULT_DB_PATH)


def ensure_db_parent_directory(db_path: str) -> None:
    if db_path == ":memory:":
        return
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
