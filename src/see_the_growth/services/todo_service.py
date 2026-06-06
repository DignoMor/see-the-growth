"""Todo application service backed by a repository (SPEC-003, SPEC-008)."""

from __future__ import annotations

from typing import Protocol
from uuid import uuid4

from see_the_growth.domain.tag import TagSummary, normalize_tag_name
from see_the_growth.domain.title import normalize_title
from see_the_growth.domain.todo_list import TodoDomainError, TodoItem


class TodoRepository(Protocol):
    def add_todo(self, todo: TodoItem) -> None:
        ...

    def list_todos(self) -> list[TodoItem]:
        ...

    def mark_completed(self, todo_id: str) -> bool:
        ...

    def flush_completed(self) -> None:
        ...

    def add_tags_for_todo(self, todo_id: str, tag_names: list[str]) -> None:
        ...

    def list_tag_summaries(self) -> list[TagSummary]:
        ...


class TodoService:
    def __init__(self, repository: TodoRepository) -> None:
        self._repository = repository

    def create_todo(self, title: str) -> TodoItem:
        normalized_title = normalize_title(title)
        if not normalized_title:
            raise TodoDomainError("Todo title must not be empty.")

        todo = TodoItem(id=str(uuid4()), title=normalized_title, completed=False)
        self._repository.add_todo(todo)
        return todo

    def list_todos(self) -> list[TodoItem]:
        return self._repository.list_todos()

    def complete_todo(self, todo_id: str) -> None:
        if not self._repository.mark_completed(str(todo_id)):
            raise TodoDomainError(f"Todo with id '{todo_id}' does not exist.")

    def flush_completed(self) -> None:
        self._repository.flush_completed()

    def add_tags_to_todo(self, todo_id: str, tag_names: list[str]) -> None:
        normalized_names = [normalize_tag_name(name) for name in tag_names]
        try:
            self._repository.add_tags_for_todo(str(todo_id), normalized_names)
        except ValueError as exc:
            raise TodoDomainError(str(exc)) from exc

    def list_tag_summaries(self) -> list[TagSummary]:
        return self._repository.list_tag_summaries()
