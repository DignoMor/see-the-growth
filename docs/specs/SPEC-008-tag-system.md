# SPEC-008: Tag System and Tags Overview Page

## Status
Implemented

## Goal
Introduce a tag model so each visible todo can carry one or more labels, always including a built-in **task** tag, and add a left-hand navigation shell with a **Tags** page that summarizes tag metadata (including unfinished task counts).

## Scope
This spec adds persistence for tags, automatic tagging on todo create, a shared app layout with sidebar navigation, and a read-only tags overview page.

### In scope
- Many-to-many association between todos and tags.
- System tag **`task`**: created at database bootstrap if missing; every new todo is linked to it automatically.
- Service/repository APIs to associate additional tags with a todo (for tests and future UI).
- `GET /tags` page listing tags with metadata (at minimum: unfinished visible todo count per tag).
- Left-hand sidebar on web pages with links to **Todo** (`GET /`) and **Tags** (`GET /tags`).
- Shared Jinja base layout; existing todo page content unchanged in behavior aside from shell/navigation.
- SQLite schema bootstrap/migration for new tables.
- In-memory tag support on `TodoList` for deterministic API tests without SQLite.
- Presentation consistent with SPEC-005 (same stylesheet, BEM-style classes).

### Out of scope
- UI to assign or remove tags when creating or editing a todo (service layer only for extra tags in v1).
- Filtering or browsing todos by tag on the todo page.
- Tag CRUD in the UI (rename, delete, merge).
- Hard delete of tags or tag associations when todos are flushed (flushed todos retain tag rows in SQLite).
- Authentication, multi-user behavior, or per-user tag namespaces.
- JavaScript-heavy navigation, SPA routing, or real-time updates.
- Changes to Docker Compose topology (SPEC-004) or test runner (SPEC-007).

## Relationship to Prior Specs
- `SPEC-001` create/complete domain rules remain unchanged.
- `SPEC-002` todo routes (`GET /`, `POST /todos`, `POST /todos/<id>/complete`) remain; this spec adds `GET /tags`.
- `SPEC-003` persistence is extended with `tags` and `todo_tags` tables.
- `SPEC-005` presentation conventions apply; layout amends from single centered column to **sidebar + main content** shell.
- `SPEC-006` visible-todo semantics apply: tag counts on the tags page use only todos where `flushed = 0`.

## Domain Terms
- **Tag**: A long-lived named label stored once and reusable across many todos (for example `task`, `errand`). Tags persist independently of todo lifecycle; they are not removed when todos are completed or flushed.
- **System tag**: Tag with normalized name `task`; ensured at bootstrap and auto-linked on every todo create.
- **Todo–tag association**: A row linking one todo ID to one tag ID; a todo may have many associations. Associations on flushed todos remain in SQLite but do not affect tag metadata counts.
- **Visible todo**: Same as SPEC-006 — `flushed = 0`.
- **Unfinished todo**: A visible todo with `completed = 0`.
- **Finished task**: A completed and/or flushed todo — ephemeral from the user's working view (hidden after flush per SPEC-006) and excluded from tag unfinished counts.
- **Tags page**: HTML page at `GET /tags` showing tag metadata.
- **App shell**: Shared page frame with left sidebar navigation and a main content area.

## Data Model

### Table: `tags` (new)
| Column       | Type | Constraints                                      |
|-------------|------|--------------------------------------------------|
| `id`        | TEXT | PRIMARY KEY                                      |
| `name`      | TEXT | NOT NULL, UNIQUE (stored normalized)           |
| `created_at`| TEXT | NOT NULL, ISO-8601 UTC timestamp                 |

### Table: `todo_tags` (new)
| Column   | Type | Constraints                                                |
|----------|------|------------------------------------------------------------|
| `todo_id`| TEXT | NOT NULL, REFERENCES `todos(id)`                           |
| `tag_id` | TEXT | NOT NULL, REFERENCES `tags(id)`                            |
| —        | —    | PRIMARY KEY (`todo_id`, `tag_id`)                          |

### Bootstrap behavior
- Create `tags` and `todo_tags` if missing (idempotent).
- Ensure a tag row with normalized name `task` exists (insert if absent).
- Existing `todos` databases without tag tables gain them on next bootstrap; no backfill of `task` on pre-existing todo rows in v1 (see Decisions).

### Tag name normalization
- Trim leading/trailing whitespace.
- Collapse internal runs of whitespace to a single space (same spirit as title normalization).
- Store and compare names case-insensitively by persisting a lowercase form (normalization function documented in code/tests).
- Empty name after normalization is invalid (`TodoDomainError`).

## Functional Requirements

### FR-1 Automatic `task` Tag on Create
Every newly created todo must be associated with the `task` tag.

Behavior:
- `create_todo()` ensures the `task` tag exists (bootstrap or lazy ensure) and inserts a `todo_tags` row.
- Association is created in the same transaction as todo insert (SQLite repository).
- In-memory `TodoList` mirrors the same rule for API tests.

### FR-2 Associate Additional Tags (Service Layer)
The system must support linking extra tags to an existing visible todo without UI in v1.

Behavior:
- Service exposes `add_tags_to_todo(todo_id: str, tag_names: list[str]) -> None` (exact name may vary; documented in implementation).
- Each name is normalized; invalid empty names raise `TodoDomainError`.
- Unknown tag names cause tag rows to be created (upsert by normalized name) then linked.
- Duplicate associations are idempotent (no error, no duplicate rows).
- Unknown `todo_id` raises `TodoDomainError` (same semantics as complete).
- Flushed todos are not addressable for new associations in v1 (treat as not found).

### FR-3 List Tag Summaries for Tags Page
The system must expose tag metadata for the tags overview.

Behavior:
- Service/repository method returns **all** tags in the `tags` table, sorted by tag name ascending (case-insensitive).
- Each summary includes:
  - `name` — display name (normalized stored form),
  - `unfinished_count` — count of visible todos linked to the tag where `completed = 0`.
- Tags with `unfinished_count = 0` are still listed (long-lived tags remain visible even when no active work remains).
- Flushed and completed todos do not contribute to `unfinished_count`; tag rows are never removed when tasks finish.

### FR-4 Tags Page Route
The web app must serve a tags overview page.

Behavior:
- `GET /tags` returns 200 and HTML.
- Page title includes “Tags” (for example “See the Growth — Tags”).
- Body lists each tag summary with at least the tag name and unfinished count.
- Stable markup: container class `tags-page`, list class `tags-list`, item class `tags-item`, unfinished count class `tags-item__unfinished-count` (or equivalent documented selectors).
- Empty state: only when the `tags` table is empty (unlikely after bootstrap seeds `task`); show a short message (for example “No tags yet”).
- After bootstrap, `task` appears with `unfinished_count = 0` when no visible incomplete todos exist.

### FR-5 Sidebar Navigation Shell
Todo and Tags pages must share a left-hand navigation menu.

Behavior:
- Extract a base template (for example `base.html`) with:
  - `<nav class="app-nav">` containing links to `GET /` labeled **Todo** and `GET /tags` labeled **Tags**.
  - `<main class="app-content">` block for page body.
- `todo_page.html` extends the base; todo list/create/flush behavior unchanged.
- Active nav item: link to the current page includes class `app-nav__link--active` (or equivalent).
- Sidebar remains usable at 320px viewport width (stack or narrow column per SPEC-005 responsive baseline).

### FR-6 Todo Page Regression
SPEC-001 / SPEC-002 / SPEC-006 behavior on the todo page must not regress.

Behavior:
- Routes, status codes, validation, flush semantics unchanged.
- Todo page still lists visible todos in creation order with the same form actions and stable classes from SPEC-005/006.

## Non-Functional Requirements
- No new Python package dependencies.
- Tag persistence under `src/see_the_growth/db/`; orchestration on `TodoService` (or dedicated thin `TagService` if needed — prefer extending `TodoService` unless clarity suffers).
- Domain normalization/validation for tag names in `src/see_the_growth/domain/`.
- Deterministic `unittest` in `tests/unit/` and `tests/api/`.
- Bootstrap migrations safe to run repeatedly.
- Run tests via `docker compose run --rm --build test` (SPEC-007).

## Files Likely to Change
| File | Change |
|------|--------|
| `docs/specs/SPEC-008-tag-system.md` | This spec |
| `src/see_the_growth/domain/` | Tag name normalization; optional `Tag`/`TagSummary` types |
| `src/see_the_growth/db/bootstrap.py` | `tags`, `todo_tags` tables; seed `task` |
| `src/see_the_growth/db/sqlite_todo_repository.py` | Tag link on add; tag summary queries; protocol extension |
| `src/see_the_growth/services/todo_service.py` | `add_tags_to_todo`, `list_tag_summaries`; create hooks |
| `src/see_the_growth/domain/todo_list.py` | In-memory tag maps for tests |
| `src/see_the_growth/api/local_web_app.py` | `GET /tags`; pass summaries to template |
| `src/see_the_growth/api/templates/base.html` | App shell + sidebar (new) |
| `src/see_the_growth/api/templates/todo_page.html` | Extend base |
| `src/see_the_growth/api/templates/tags_page.html` | Tags overview (new) |
| `src/see_the_growth/api/static/todo.css` | Sidebar layout + tags list styles |
| `tests/unit/test_spec_008_tag_system.py` | Domain, repository, service tests |
| `tests/api/test_spec_008_tag_system.py` | HTTP, HTML, navigation tests |

## Test Plan

### `tests/unit/test_spec_008_tag_system.py`
- `test_spec_008_create_todo_auto_links_task_tag` — after create, todo has `task` association.
- `test_spec_008_tag_name_normalization` — whitespace/case normalization rules.
- `test_spec_008_add_tags_to_todo_creates_and_links` — new tag names create tag rows and link.
- `test_spec_008_add_tags_idempotent` — duplicate add does not error.
- `test_spec_008_add_tags_unknown_todo_raises` — missing/flushed todo fails.
- `test_spec_008_list_tag_summaries_unfinished_count` — counts only visible incomplete todos.
- `test_spec_008_list_tag_summaries_includes_zero_unfinished` — tag with no visible incomplete todos still appears with count 0.
- `test_spec_008_bootstrap_creates_tags_tables_and_task_tag` — fresh DB has schema + `task`.

### `tests/api/test_spec_008_tag_system.py`
- `test_spec_008_get_tags_page_returns_200` — `GET /tags` succeeds.
- `test_spec_008_tags_page_shows_unfinished_count` — create incomplete todo → `task` shows count ≥ 1.
- `test_spec_008_tags_page_shows_tag_with_zero_unfinished` — fresh app with no todos still lists `task` with unfinished count 0.
- `test_spec_008_tags_page_lists_tag_name` — body contains normalized tag name.
- `test_spec_008_todo_page_has_sidebar_nav` — `GET /` includes nav links Todo and Tags.
- `test_spec_008_tags_page_has_sidebar_nav` — `GET /tags` includes same nav.
- `test_spec_008_nav_active_state_todo` — on `/`, Todo link has active class.
- `test_spec_008_nav_active_state_tags` — on `/tags`, Tags link has active class.
- `test_spec_008_create_todo_still_works` — regression: POST create + redirect.

### Regression
All existing tests in `tests/unit/`, `tests/api/`, and `tests/e2e/` must pass.

## Implementation Phases

### Phase 1 — Persistence and domain
- Tag normalization helper.
- Bootstrap tables + seed `task`.
- Repository: link `task` on `add_todo`; `add_tags_for_todo`; `list_tag_summaries`.
- Service methods; in-memory `TodoList` parity.
- Unit tests green.

### Phase 2 — Web routes and templates
- `base.html` shell; refactor `todo_page.html`.
- `tags_page.html` + `GET /tags`.
- API tests green.

### Phase 3 — Presentation
- CSS for `.app-nav`, `.app-content`, tags list.
- Confirm SPEC-005/006 regression green at 320px width.

## Decisions
- **Storage**: Normalized lowercase `name` in `tags.name`; display uses stored form.
- **System tag**: Literal normalized name `task`; not user-deletable in v1.
- **Tag longevity**: Tags are long-lived entities. Todo completion and flush (SPEC-006) hide finished work from the todo page but do not delete tag rows or `todo_tags` associations.
- **Counts**: `unfinished_count` only — visible (`flushed = 0`) and `completed = 0`. No total, completed, or flushed counts on the tags page in v1.
- **Tags page listing**: Show **all** tags, including those with `unfinished_count = 0` (user decision).
- **Existing todos**: No automatic backfill of `task` on todos created before this spec; only new creates get associations.
- **Layout**: Sidebar + content replaces full-width centered card; todo content area keeps ~42rem max width inside main column.
- **Extra tags in v1**: Service API only; no create-form tag picker until a follow-up spec.
- **Tags on todo list rows**: None in v1 — tags page is the entry point for tag metadata.

### Resolved decisions (2026-06-06)
| Decision | Choice |
|----------|--------|
| Backfill `task` on existing todos | New creates only |
| Tags with zero unfinished todos | **Show** on tags page |
| Show tags on todo list rows | None in v1 |
| Tag assignment UI | Defer to follow-up spec |
| Tags page metadata | **Unfinished count only** |
| Tag vs task lifecycle | Tags long-lived; finished/flushed tasks ephemeral in UI |

## Change Log
- 2026-06-06: Implemented tag persistence, service APIs, in-memory parity, sidebar shell, and GET /tags page.
- 2026-06-06: User decisions locked — show all tags (including zero unfinished), unfinished-only metadata, tag longevity.
- 2026-06-06: Initial draft created.
