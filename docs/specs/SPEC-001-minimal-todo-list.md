# SPEC-001: Minimal Todo List

## Status
Implemented

## Goal
Define the smallest useful todo list behavior for this project so implementation and tests can proceed incrementally.

## Scope
This spec covers only core todo task behavior and in-memory application flow.

### In scope
- Create a todo item with a non-empty title.
- List all todo items in creation order.
- Mark a todo item as completed.
- Keep todo data in memory for the initial implementation.

### Out of scope
- Persistent storage (database/files).
- User accounts, authentication, or multi-user support.
- Due dates, priorities, tags, or time tracking.
- Edit and delete operations.
- UI concerns (web/mobile rendering details).

## Domain Terms
- **TodoItem**: A single task with an ID, title, and completion status.
- **TodoList**: A collection of `TodoItem` objects with ordered retrieval.

## Functional Requirements

### FR-1 Create Todo
The system must allow creating a `TodoItem` with:
- a generated UUID ID,
- a title string,
- `completed = False` by default.

Validation:
- Title must be normalized by trimming leading/trailing whitespace.
- Title normalization must preserve internal repeated spaces (for example, double spaces).
- Title must not be empty after normalization.
- If title is invalid, creation must fail with a domain-level error.

### FR-2 List Todos
The system must return all created todos in insertion order.

### FR-3 Complete Todo
The system must allow marking an existing todo as completed.

Validation:
- If a todo ID does not exist, completion must fail with a domain-level error.
- Completing an already completed todo is allowed and must remain completed (idempotent behavior).

## Non-Functional Requirements
- Business rules should live in `src/see_the_growth/domain/`.
- Initial implementation should avoid external service dependencies.
- Behavior should be fully covered by deterministic `unittest` tests.

## Test Plan (to implement before code)
- `tests/unit/`:
  - `test_spec_001_create_todo_rejects_empty_title`
  - `test_spec_001_create_todo_defaults_to_incomplete`
  - `test_spec_001_list_todos_returns_in_creation_order`
  - `test_spec_001_complete_todo_marks_item_completed`
  - `test_spec_001_complete_unknown_todo_raises_error`
  - `test_spec_001_complete_todo_is_idempotent`

## Decisions
- IDs use UUID for v1.
- Title normalization trims leading/trailing whitespace and preserves internal repeated spaces.

## Change Log
- 2026-06-02: Initial draft created.
- 2026-06-02: Resolved v1 decisions for UUID IDs and title normalization rules.
- 2026-06-02: Implemented minimal in-memory todo domain and unit tests.
