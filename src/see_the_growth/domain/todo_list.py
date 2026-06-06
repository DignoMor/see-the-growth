from dataclasses import dataclass
from uuid import uuid4

from .tag import TagSummary, normalize_tag_name
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
        self._todo_tags: dict[str, set[str]] = {}
        self._all_tags: set[str] = {"task"}

    def create_todo(self, title: str) -> TodoItem:
        normalized_title = normalize_title(title)
        if not normalized_title:
            raise TodoDomainError("Todo title must not be empty.")

        todo = TodoItem(id=str(uuid4()), title=normalized_title, completed=False)
        self._todos.append(todo)
        self._todo_tags[todo.id] = {"task"}
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

    def tags_for_todo(self, todo_id: str) -> list[str]:
        return sorted(self._todo_tags.get(str(todo_id), set()))

    def add_tags_to_todo(self, todo_id: str, tag_names: list[str]) -> None:
        todo_key = str(todo_id)
        if not self._is_todo_addressable(todo_key):
            raise TodoDomainError(f"Todo with id '{todo_id}' does not exist.")

        normalized_names = [normalize_tag_name(name) for name in tag_names]
        tags = self._todo_tags.setdefault(todo_key, set())
        for name in normalized_names:
            self._all_tags.add(name)
            tags.add(name)

    def list_tag_summaries(self) -> list[TagSummary]:
        visible_todos = {
            todo.id: todo
            for todo in self._todos
            if todo.id not in self._flushed_ids
        }
        summaries: list[TagSummary] = []
        for tag_name in sorted(self._all_tags, key=str.lower):
            unfinished_count = sum(
                1
                for todo_id, tag_names in self._todo_tags.items()
                if tag_name in tag_names
                and todo_id in visible_todos
                and not visible_todos[todo_id].completed
            )
            summaries.append(
                TagSummary(name=tag_name, unfinished_count=unfinished_count)
            )
        return summaries

    def _is_todo_addressable(self, todo_id: str) -> bool:
        if todo_id in self._flushed_ids:
            return False
        return any(todo.id == todo_id for todo in self._todos)
