# SPEC-003: Database Persistence for Todo List

## Status
Implemented

## Goal
Replace in-memory todo storage with a local database so todos survive process restarts while preserving all behavior defined in `SPEC-001` and `SPEC-002`.

## Scope
This spec covers persistence, storage schema, and the application wiring needed to use a database as the system of record for todos.

### In scope
- Persist todos in a local SQLite database.
- Preserve `SPEC-001` domain rules (title validation, UUID IDs, creation order, completion semantics).
- Preserve `SPEC-002` web behavior when backed by the database.
- Initialize database schema on application startup when missing.
- Configure database file location for local development.
- Deterministic tests using isolated database instances (in-memory or temporary files).

### Out of scope
- Multi-user tenancy, authentication, or authorization.
- Remote or managed databases (PostgreSQL, MySQL, cloud-hosted DB).
- Schema migration tooling beyond simple v1 bootstrap (for example, Alembic).
- Edit and delete operations (still deferred from `SPEC-001`).
- Due dates, priorities, tags, search, or filtering.
- Backup, restore, or replication features.
- Performance tuning beyond correctness for a single-user local app.

## Relationship to Prior Specs
- `SPEC-001` domain behavior remains authoritative for business rules.
- `SPEC-001` in-memory storage is superseded for runtime use by this spec; domain tests may continue using fast in-memory fakes where appropriate.
- `SPEC-002` web routes and templates remain unchanged in user-visible behavior; only the backing store changes.

## Domain Terms
- **Todo Repository**: Persistence boundary that stores and retrieves `TodoItem` records.
- **Todo Service**: Application façade that applies `SPEC-001` rules and delegates storage to a repository (successor to the current in-memory `TodoList` orchestration).
- **Database Bootstrap**: One-time creation of required tables/indexes when the database is first used.

## Architecture

### Layering
- **Domain** (`src/see_the_growth/domain/`): `TodoItem`, `TodoDomainError`, and title normalization/validation rules. No SQL or storage details.
- **Database** (`src/see_the_growth/db/`): schema definition, connection handling, and `TodoRepository` implementation(s).
- **Services** (`src/see_the_growth/services/`): `TodoService` (or equivalent) coordinating domain validation with repository calls.
- **API** (`src/see_the_growth/api/`): continues to depend on the todo application façade, not on SQL directly.

### Repository Contract
The repository must support the operations required by `SPEC-001`:
- `add_todo(todo: TodoItem) -> None` — persist a new item.
- `list_todos() -> list[TodoItem]` — return all items in creation order.
- `mark_completed(todo_id: str) -> bool` — set `completed = True` for the given ID; return `False` if the ID does not exist, `True` if updated (including already-completed items).

The service layer maps repository `False` on complete to `TodoDomainError` to preserve existing error semantics.

## Data Model

### Table: `todos`
| Column       | Type    | Constraints                          |
|-------------|---------|--------------------------------------|
| `id`        | TEXT    | PRIMARY KEY                          |
| `title`     | TEXT    | NOT NULL                             |
| `completed` | INTEGER | NOT NULL, `0` = false, `1` = true    |
| `created_at`| TEXT    | NOT NULL, ISO-8601 UTC timestamp     |

Ordering for `list_todos()` must use `created_at` ascending, with `id` as a stable tiebreaker when timestamps collide.

## Functional Requirements

### FR-1 Persist Todos
The system must store each created todo in SQLite.

Behavior:
- Creating a todo must insert a row before the operation is considered successful.
- Listing todos must read from the database, not from a process-local list.
- Completing a todo must update the corresponding row.

### FR-2 Preserve SPEC-001 Behavior
All `SPEC-001` functional requirements must continue to pass when the todo façade is backed by SQLite.

Behavior:
- Title normalization and validation rules are unchanged.
- IDs remain UUID strings generated at creation time.
- `list_todos()` returns insertion (creation) order.
- `complete_todo()` remains idempotent for already-completed items.
- Unknown IDs still raise `TodoDomainError`.

### FR-3 Survive Process Restart
Todos must remain available after the application process exits and restarts.

Behavior:
- A todo created in one process run must appear in a subsequent run against the same database file.
- Completion state must persist across restarts.

### FR-4 Bootstrap Schema
The system must create required schema automatically when the database is uninitialized.

Behavior:
- On first use of a database path, create the `todos` table (and indexes if defined).
- Bootstrap must be safe to run repeatedly (idempotent; no error if schema already exists).
- Bootstrap failures must surface as explicit application errors (not silent corruption).

### FR-5 Configure Database Location
The system must allow selecting the SQLite database file for local runs.

Behavior:
- Default database path: `data/todos.db` relative to the project working directory.
- Override via environment variable `SEE_THE_GROWTH_DB_PATH`.
- The parent directory for the database file must be created if it does not exist.
- Documentation must describe how to run the app with the default and custom paths.

### FR-6 Preserve SPEC-002 Web Integration
The local web app must use the persisted todo façade by default.

Behavior:
- `create_app()` without injection uses the configured SQLite-backed service.
- Tests may inject an isolated repository/service (for example, temporary file or `:memory:` database) to remain deterministic.
- HTTP status codes and user-visible error messages remain as defined in `SPEC-002`.

## Non-Functional Requirements
- Use Python standard library `sqlite3` for v1 (no new required database ORM dependency).
- Repository and connection code live under `src/see_the_growth/db/`.
- Service orchestration lives under `src/see_the_growth/services/`.
- Tests must not share writable database files across parallel test cases.
- Prefer `:memory:` SQLite or per-test temporary files in unit/API tests.
- E2E smoke tests may use a temporary database file in a test-specific directory.

## Test Plan (to implement before code)

### `tests/unit/`
- `test_spec_003_create_todo_persists_to_database`
- `test_spec_003_list_todos_reads_from_database_in_creation_order`
- `test_spec_003_complete_todo_updates_database_row`
- `test_spec_003_complete_unknown_todo_raises_domain_error`
- `test_spec_003_complete_todo_is_idempotent_in_database`
- `test_spec_003_todos_survive_service_reinstantiation` (new connection/service instance, same DB file)
- `test_spec_003_bootstrap_is_idempotent`
- `test_spec_003_repository_list_todos_works_from_other_thread` (thread-safe access for multi-threaded HTTP servers)
- `test_spec_003_spec_001_domain_rules_still_hold_with_sqlite_backend` (regression guard; may reuse/adapt existing SPEC-001 cases against SQLite)

### `tests/api/`
- `test_spec_003_web_app_uses_persisted_store_by_default`
- `test_spec_003_create_and_complete_via_http_survives_new_app_instance` (new `create_app()` + same DB path)

### `tests/e2e/` (minimal smoke)
- `test_spec_003_persisted_create_and_complete_flow` (optional if covered adequately by API test above)

Existing `SPEC-001` and `SPEC-002` tests must continue to pass after implementation (updated setup where injection is required).

## Implementation Notes (non-normative)
- Refactor current `TodoList` so domain validation is separate from storage; the public methods (`create_todo`, `list_todos`, `complete_todo`) can remain on `TodoService` for minimal API churn.
- Keep an in-memory repository implementation only if useful for focused domain tests; runtime and integration paths should use SQLite.
- Use a thread-local connection per repository instance for v1 so Flask's multi-threaded dev server can share one repository across request threads; connection lifecycle is owned by the repository or a small `Database` helper in `db/`.

## Decisions
- **Database engine**: SQLite for v1.
- **Driver**: Python `sqlite3` standard library.
- **Default path**: `data/todos.db`, overridable with `SEE_THE_GROWTH_DB_PATH`.
- **Ordering key**: `created_at` UTC timestamp at insert time.
- **Schema versioning**: implicit v1 bootstrap only; no migration framework in v1.

## Change Log
- 2026-06-02: Initial draft created.
- 2026-06-02: Implemented SQLite persistence, repository/service layering, and web app wiring.
- 2026-06-02: Repository uses thread-local SQLite connections for multi-threaded Flask runtime.
