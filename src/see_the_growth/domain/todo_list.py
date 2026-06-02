from dataclasses import dataclass
from uuid import uuid4

from .title import normalize_title


class TodoDomainError(ValueError):
    """Raised when todo domain validation fails."""


@dataclass
class TodoItem:
    id: str
    title: str
    completed: bool = False


class TodoList:
    """In-memory todo collection for SPEC-001 behavior."""

    def __init__(self) -> None:
        self._todos: list[TodoItem] = []
        self._flushed_ids: set[str] = set()

    def create_todo(self, title: str) -> TodoItem:
        normalized_title = normalize_title(title)
        if not normalized_title:
            raise TodoDomainError("Todo title must not be empty.")

        todo = TodoItem(id=str(uuid4()), title=normalized_title, completed=False)
        self._todos.append(todo)
        return todo

    def list_todos(self) -> list[TodoItem]:
        return [todo for todo in self._todos if todo.id not in self._flushed_ids]

    def complete_todo(self, todo_id: str) -> None:
        for todo in self._todos:
            if todo.id == str(todo_id):
                todo.completed = True
                return
        raise TodoDomainError(f"Todo with id '{todo_id}' does not exist.")

    def flush_completed(self) -> None:
        for todo in self._todos:
            if todo.completed:
                self._flushed_ids.add(todo.id)
