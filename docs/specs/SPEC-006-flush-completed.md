# SPEC-006: Flush Completed Todos from Web View

## Status
Implemented

## Goal
Allow the user to clear all completed todos from the web interface while retaining them in the database for future use or inspection.

## Scope
This spec adds a flush action to the server-rendered todo page and the persistence layer needed to hide flushed items from list views.

### In scope
- A **Flush completed** control at the bottom of the todo list when at least one visible completed todo exists.
- `POST /todos/flush-completed` route that marks all completed, non-flushed todos as flushed.
- SQLite column `flushed` on `todos` (0 = visible, 1 = hidden from web list).
- Schema bootstrap/migration for existing databases (add column with default `0`).
- `list_todos()` returns only non-flushed todos (web-visible items).
- Flushed rows remain in the database; row count unchanged after flush.
- POST-redirect-GET on successful flush.
- In-memory `TodoList` flush support for deterministic API tests without SQLite.
- Presentation styling for the flush control consistent with SPEC-005.

### Out of scope
- Hard delete of todos from the database.
- Flush of individual items or incomplete todos.
- Undo / restore flushed todos in the UI.
- Authentication, multi-user behavior, or per-user flush state.
- JavaScript-heavy UI or confirmation dialogs (simple form POST only).
- Admin/reporting UI to browse flushed todos.
- Changes to Docker Compose topology (SPEC-004).

## Relationship to Prior Specs
- `SPEC-001` domain rules for create/complete remain unchanged.
- `SPEC-002` routes for create/complete remain; this spec adds one new route.
- `SPEC-003` `list_todos()` semantics are amended: the repository/service list operation returns **visible** (non-flushed) todos only. Direct SQL or future admin APIs may still read all rows.
- `SPEC-005` styling conventions apply to the flush button and form.

## Domain Terms
- **Flush**: Mark all completed, visible todos as hidden from the web list without deleting database rows.
- **Visible todo**: A todo row where `flushed = 0`.
- **Flushed todo**: A completed todo with `flushed = 1`; retained in SQLite but excluded from `list_todos()`.

## Data Model

### Table: `todos` (amended)
| Column       | Type    | Constraints                          |
|-------------|---------|--------------------------------------|
| `id`        | TEXT    | PRIMARY KEY                          |
| `title`     | TEXT    | NOT NULL                             |
| `completed` | INTEGER | NOT NULL, `0` = false, `1` = true    |
| `created_at`| TEXT    | NOT NULL, ISO-8601 UTC timestamp     |
| `flushed`   | INTEGER | NOT NULL, default `0`; `1` = hidden from web list |

Existing databases gain `flushed` via idempotent bootstrap migration (`ALTER TABLE ... ADD COLUMN` when missing).

## Functional Requirements

### FR-1 Flush Completed Todos
The system must hide all visible completed todos from the web list in one action.

Behavior:
- `POST /todos/flush-completed` sets `flushed = 1` for every row where `completed = 1` and `flushed = 0`.
- Incomplete todos are never flushed.
- Already-flushed todos are unchanged.
- Operation is idempotent: repeated flush with no visible completed todos succeeds without error.
- On success, redirect to `GET /` (POST-redirect-GET).

### FR-2 List Visible Todos Only
The web app must list only non-flushed todos.

Behavior:
- `list_todos()` on the service/repository returns rows where `flushed = 0`, in creation order (`created_at`, `id`).
- Create and complete flows operate on visible todos as today.
- Completing a todo then flushing removes it from the next page render.

### FR-3 Persist Flushed State
Flushed todos must remain in SQLite and stay hidden across restarts.

Behavior:
- After flush, `SELECT COUNT(*) FROM todos` is unchanged.
- A new app instance against the same database file does not show flushed todos on `GET /`.
- Flushed rows retain `completed = 1` and `flushed = 1`.

### FR-4 Flush Control on Todo Page
The todo page must expose flush when relevant.

Behavior:
- When the visible list includes at least one completed todo, render a form at the **bottom** of the list (after `<ul class="todo-list">`).
- Form: `method="post"`, `action="/todos/flush-completed"`, stable class `todo-flush-form`.
- Submit button label: **Flush completed** (or equivalent documented copy).
- When no visible completed todos exist, the flush form must not render.

### FR-5 No Regression on Existing Flows
SPEC-001 / SPEC-002 create and complete behavior must remain unchanged for visible todos.

Behavior:
- Empty title validation unchanged.
- Unknown todo complete still returns 404.
- SPEC-002 tests using in-memory `TodoList` continue to pass with flush support on the facade.

## Non-Functional Requirements
- No new Python package dependencies.
- Repository flush and list changes live under `src/see_the_growth/db/`.
- Service method `flush_completed()` on `TodoService` and in-memory `TodoList`.
- Deterministic `unittest` in `tests/unit/` and `tests/api/`.
- Bootstrap migration must be safe to run repeatedly.

## Files Likely to Change
| File | Change |
|------|--------|
| `docs/specs/SPEC-006-flush-completed.md` | This spec |
| `src/see_the_growth/db/bootstrap.py` | `flushed` column on create + migration |
| `src/see_the_growth/db/sqlite_todo_repository.py` | Filter list; `flush_completed()` |
| `src/see_the_growth/services/todo_service.py` | `flush_completed()`; protocol update |
| `src/see_the_growth/domain/todo_list.py` | In-memory flush for tests |
| `src/see_the_growth/api/local_web_app.py` | Route + facade protocol |
| `src/see_the_growth/api/templates/todo_page.html` | Flush form |
| `src/see_the_growth/api/static/todo.css` | Flush form styling |
| `tests/unit/test_spec_006_flush_completed.py` | Repository/service tests |
| `tests/api/test_spec_006_flush_completed.py` | HTTP and persistence tests |

## Test Plan

### `tests/unit/test_spec_006_flush_completed.py`
- `test_spec_006_flush_completed_hides_completed_from_list` — complete two, flush, list empty of those titles.
- `test_spec_006_flush_completed_leaves_active_todos_visible` — one active, one done; after flush only active listed.
- `test_spec_006_flush_completed_rows_remain_in_database` — row count unchanged; flushed flag set via SQL.
- `test_spec_006_flush_completed_is_idempotent` — second flush does not error or change visible list.
- `test_spec_006_bootstrap_adds_flushed_column_to_existing_database` — DB created without column gets migrated.

### `tests/api/test_spec_006_flush_completed.py`
- `test_spec_006_post_flush_completed_removes_completed_from_page` — HTTP flush + redirect; completed titles absent.
- `test_spec_006_flush_completed_leaves_active_on_page` — active todo still in body after flush.
- `test_spec_006_flush_form_shown_when_completed_visible` — completed todo present → flush form in HTML.
- `test_spec_006_flush_form_hidden_when_no_completed_visible` — only active todos → no flush form.
- `test_spec_006_flushed_todos_hidden_after_app_restart` — new `create_app()` + same DB; flushed item not shown.

### Regression
All existing tests in `tests/unit/`, `tests/api/`, and `tests/e2e/` must pass.

## Implementation Phases

### Phase 1 — Persistence
- Add `flushed` column and migration in bootstrap.
- Repository list filter and `flush_completed()`.
- Service and in-memory `TodoList` methods.
- Unit tests green.

### Phase 2 — Web route and template
- `POST /todos/flush-completed` with redirect.
- Template flush form at bottom of list.
- API tests green.

### Phase 3 — Presentation
- CSS for `todo-flush-form`; confirm SPEC-005 regression green.

## Decisions
- **Hide vs delete**: Soft-hide via `flushed` column; no `DELETE` statements.
- **List contract**: `list_todos()` means “visible todos” for app and web use.
- **Route**: `POST /todos/flush-completed` (collection action, consistent with REST-ish POST forms).
- **Idempotency**: Flush with zero targets returns 302 to `/` (success, no error).
- **UI placement**: Bottom of list, after todo items, before closing `</main>`.

## Change Log
- 2026-06-02: Implemented flush route, `flushed` column, repository/service, template, and tests.
- 2026-06-02: Initial draft created.
