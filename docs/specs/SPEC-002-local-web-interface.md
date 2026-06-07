# SPEC-002: Local Web Interface for Todo List

## Status
Implemented

## Goal
Define a minimal local web interface so a user can run the todo list as an app in a browser and perform the core todo actions from `SPEC-001`.

## Scope
This spec covers a local-only web app interface backed by the existing todo domain behavior.

### In scope
- Run the app locally and access it from a browser on the same machine.
- Render a todo page that shows existing todos and their completion state.
- Submit a new todo title from the UI.
- Mark a todo as completed from the UI.
- Show user-facing validation and not-found errors for failed actions.

### Out of scope
- Authentication, authorization, and multi-user behavior.
- Persistent storage and database file paths (see `SPEC-003`; runtime via `SPEC-004`).
- Edit, delete, due date, priority, tag, or filtering features.
- Styling complexity beyond basic readable HTML.
- Real-time updates (websockets, polling, push).
- Public deployment and internet-facing hardening.

## Domain Terms
- **Local Web App**: The process running on localhost that serves HTTP endpoints and HTML for todo interactions.
- **Todo Page**: The main HTML page containing create/list/complete UI controls.
- **Form Submission**: Browser request triggered by user interaction for create/complete actions.

## Relationship to Later Specs
- `SPEC-003` defines persistence at default path `data/todos.db` (see SPEC-003 Database path convention).
- `SPEC-004` runs this web app via Docker Compose; the same `data/todos.db` file is used on the host and in the container.

## Functional Requirements

### FR-1 Run Locally
The system must provide an application entrypoint that starts an HTTP server locally.

Behavior:
- The app must bind to localhost by default.
- The app must provide a default port with optional override via configuration (for example, environment variable or CLI argument).
- The app startup instructions must be documented in project docs (Docker Compose per SPEC-004; URL `http://127.0.0.1:7676/`).

### FR-2 Render Todo Page
The system must provide a route that returns HTML for the todo interface.

Behavior:
- The page must display all todos in insertion order.
- Each listed todo must display title and completion state.
- Completed todos must be distinguishable in rendered output (for example, label or CSS class).

### FR-3 Create Todo via UI
The system must allow creating a todo from the todo page.

Behavior:
- A create form submission with a valid title must create a new todo using `SPEC-001` domain rules.
- After successful creation, the response must allow the user to observe the new todo in the list (redirect or direct render are both acceptable).

Validation:
- Empty or whitespace-only titles must fail with a user-visible error message.
- Validation must rely on domain behavior, not duplicated business rules in UI layer.

### FR-4 Complete Todo via UI
The system must allow marking an existing todo as completed from the todo page.

Behavior:
- Completing a valid todo ID must update state using `SPEC-001` rules.
- After success, the response must allow the user to observe completed state in the list.

Validation:
- If a todo ID does not exist, the system must provide a user-visible error response.
- Re-completing an already completed todo remains idempotent.

### FR-5 Error Handling and Response Contract
The web layer must provide deterministic responses for expected failures.

Behavior:
- Domain validation failures must map to HTTP 4xx responses.
- Not-found completion attempts must map to HTTP 404.
- Error responses must include a readable message for UI display.

## Non-Functional Requirements
- Web routing and schemas should live in `src/see_the_growth/api/`.
- Business rules must remain in `src/see_the_growth/domain/` and be reused by the web layer.
- HTML rendering must use Jinja2 templates in v1.
- Test coverage should prioritize deterministic `unittest` tests in `tests/api/` and targeted integration/e2e tests.
- The app should run without external services.

## Test Plan (to implement before code)
- `tests/api/`:
  - `test_spec_002_get_todo_page_returns_html_and_lists_todos`
  - `test_spec_002_create_todo_from_form_succeeds_and_renders_new_item`
  - `test_spec_002_create_todo_from_form_rejects_empty_title_with_4xx`
  - `test_spec_002_complete_todo_from_form_marks_item_completed`
  - `test_spec_002_complete_unknown_todo_returns_404`
  - `test_spec_002_domain_errors_are_exposed_as_user_visible_messages`
- `tests/e2e/` (minimal smoke):
  - `test_spec_002_local_app_smoke_create_and_complete_flow`

## Decisions
- Web interface is server-rendered HTML for v1 (no SPA requirement).
- Jinja2 is the templating engine for server-rendered HTML in v1.
- POST-redirect-GET is recommended for successful mutations to avoid duplicate form submission, but direct render is acceptable if behavior remains deterministic.

## Change Log
- 2026-06-02: Initial draft created.
- 2026-06-02: Selected Jinja2 as the v1 templating engine.
- 2026-06-02: Implemented local Flask/Jinja2 web interface with API and e2e tests.
