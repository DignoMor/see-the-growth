"""Factories for default application wiring (SPEC-003)."""

from __future__ import annotations

from see_the_growth.db.config import ensure_db_parent_directory, resolve_db_path
from see_the_growth.db.sqlite_todo_repository import SqliteTodoRepository

from .todo_service import TodoService


def create_default_todo_service() -> TodoService:
    db_path = resolve_db_path()
    ensure_db_parent_directory(db_path)
    return TodoService(SqliteTodoRepository(db_path))
