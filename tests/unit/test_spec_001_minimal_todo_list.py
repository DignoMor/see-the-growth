import sys
import unittest
from pathlib import Path
from uuid import UUID


# Ensure src-layout imports work when tests are run from repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from see_the_growth.domain.todo_list import TodoDomainError, TodoList


class TestSpec001MinimalTodoList(unittest.TestCase):
    def setUp(self) -> None:
        self.todo_list = TodoList()

    def test_spec_001_create_todo_rejects_empty_title(self) -> None:
        with self.assertRaises(TodoDomainError):
            self.todo_list.create_todo("   ")

    def test_spec_001_create_todo_defaults_to_incomplete(self) -> None:
        todo = self.todo_list.create_todo("  Buy milk  ")

        # UUID format required by SPEC-001.
        parsed_id = UUID(str(todo.id))
        self.assertEqual(str(parsed_id), str(todo.id))
        self.assertEqual(todo.title, "Buy milk")
        self.assertFalse(todo.completed)

    def test_spec_001_list_todos_returns_in_creation_order(self) -> None:
        first = self.todo_list.create_todo("first")
        second = self.todo_list.create_todo("second")
        third = self.todo_list.create_todo("third")

        todos = self.todo_list.list_todos()
        self.assertEqual([todo.id for todo in todos], [first.id, second.id, third.id])

    def test_spec_001_complete_todo_marks_item_completed(self) -> None:
        todo = self.todo_list.create_todo("write tests")

        self.todo_list.complete_todo(todo.id)

        todos = self.todo_list.list_todos()
        self.assertTrue(todos[0].completed)

    def test_spec_001_complete_unknown_todo_raises_error(self) -> None:
        with self.assertRaises(TodoDomainError):
            self.todo_list.complete_todo("a8f4f8ab-b6e4-4f4d-8f5a-5ed206f8b0d5")

    def test_spec_001_complete_todo_is_idempotent(self) -> None:
        todo = self.todo_list.create_todo("idempotent completion")

        self.todo_list.complete_todo(todo.id)
        self.todo_list.complete_todo(todo.id)

        todos = self.todo_list.list_todos()
        self.assertTrue(todos[0].completed)


if __name__ == "__main__":
    unittest.main()
