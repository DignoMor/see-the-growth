# SPEC-009: Assign Tags on Create and Filter Todos by Tag

## Status
Implemented

## Goal
Let users assign optional tags when creating todos and filter the todo list by tag, with tags visible on list rows and navigable links from the Tags page.

## Scope
This spec extends SPEC-008 with todo-page UX: tag input on create, tag display on rows, query-string filtering, and links from the tags overview.

### In scope
- Optional comma-separated tags on `POST /todos` (form field `tags`).
- `create_todo(title, tag_names=None)` links `task` plus any extra tags in one transaction (SQLite) or one operation (in-memory).
- Parse helper for comma-separated tag input (trim segments, skip empty segments, normalize each name).
- `list_todos(todo_filter=None)` filters visible todos using a `TodoFilter` value; `None` or inactive filter returns all visible todos.
- `tags_for_todo(todo_id)` returns sorted tag names for a visible todo (empty list when not found or flushed).
- `GET /?tag=<name>` renders filtered todo list; blank/whitespace-only query param is treated as no filter.
- Active filter banner on todo page with link to clear filter (`GET /`).
- Tags shown on each todo row; each tag links to `GET /?tag=<name>`.
- Tags page: tag name links to filtered todo view.
- Create form includes optional tags text field.
- POST-redirect-GET preserves active tag filter on create, complete, and flush.
- Presentation consistent with SPEC-005 (BEM-style classes, same stylesheet).

### Out of scope
- Edit or remove tags on existing todos.
- Multi-tag filter UI (see **SPEC-011**; query params already support multiple tags).
- Tag CRUD in the UI (rename, delete, merge).
- Autocomplete, multi-select, or JavaScript tag picker.
- Authentication or multi-user behavior.
- Changes to Docker Compose topology (SPEC-004) or test runner (SPEC-007).

## Relationship to Prior Specs
- `SPEC-001` / `SPEC-002` create/complete flows unchanged aside from optional tags field and filter query param.
- `SPEC-006` visible-todo semantics apply to filtered lists.
- `SPEC-008` tag model, normalization, and `task` auto-link remain; this spec adds UI and list/filter APIs.

## Domain Terms
- **Tag input**: Comma-separated string from the create form (for example `errand, home`).
- **Active filter**: A `TodoFilter` value derived from query params, used to restrict the todo list.
- **Todo row tags**: Tag names displayed beside each visible todo title.

## Functional Requirements

### FR-1 Create Todo with Optional Tags
Users may supply extra tags when creating a todo.

Behavior:
- Form field `tags` is optional; omitted or blank means only the system `task` tag is linked.
- Comma-separated values are split; empty segments after trim are skipped.
- Each segment is normalized per SPEC-008; invalid empty names raise `TodoDomainError`.
- Duplicate names in input are deduplicated before linking.
- Including `task` in input is idempotent (no error, single association).
- Extra tags are linked in the same transaction as todo insert (SQLite repository).

### FR-2 List Todos by Filter
The service must support optional filtering via a domain filter object.

Behavior:
- `list_todos()` or `list_todos(TodoFilter.none())` returns all visible todos in creation order.
- `list_todos(TodoFilter.for_single_tag("errand"))` returns visible todos linked to that tag.
- `TodoFilter.for_tags([...], match=TagMatchMode.ANY)` returns todos with **any** listed tag (OR).
- `TodoFilter.for_tags([...], match=TagMatchMode.ALL)` returns todos with **all** listed tags (AND).
- Unknown or unused tag names yield an empty list (not an error).
- Flushed todos are never included.
- `TodoFilter.matches(todo_tag_names)` implements the same semantics for in-memory lists.

Query-string mapping (HTTP layer):
- `GET /?tag=<name>` — single-tag filter (`TagMatchMode.ANY`).
- `GET /?tag=<name1>,<name2>` — multi-tag OR filter.
- `GET /?tag=<name1>,<name2>&tag_match=all` — multi-tag AND filter.
- Blank/whitespace-only `tag` param → no filter.

### FR-3 Tags for Todo
The service must expose tag names for display.

Behavior:
- `tags_for_todo(todo_id)` returns tag names sorted ascending (case-insensitive).
- Unknown or flushed todo IDs return an empty list.

### FR-4 Todo Page Filter and Display
The web app must support filtering and show tags on rows.

Behavior:
- `GET /?tag=<name>` lists only todos with that tag; whitespace-only param shows all todos.
- When a filter is active, show a banner (class `todo-filter`) naming the tag and linking to clear the filter.
- Each todo row shows tags (container `todo-item__tags`, item `todo-item__tag`); tag text links to `/?tag=<name>`.
- Create form includes label and input for tags (`name="tags"`, id `tags`).

### FR-5 Tags Page Links
Tag names on `GET /tags` link to the filtered todo view.

Behavior:
- Tag name element is a link to `GET /?tag=<name>` (class `tags-item__name` on the anchor).

### FR-6 Redirect Preservation
Successful POST actions preserve the active tag filter.

Behavior:
- After create, complete, or flush, redirect to `GET /` or `GET /?tag=<name>` when a filter was active.

## Non-Functional Requirements
- No new Python package dependencies.
- Deterministic `unittest` in `tests/unit/` and `tests/api/`.
- Run tests via `docker compose run --rm --build test` (SPEC-007).

## Files Likely to Change
| File | Change |
|------|--------|
| `docs/specs/SPEC-009-todo-tags-create-and-filter.md` | This spec |
| `src/see_the_growth/domain/todo_filter.py` | `TodoFilter`, `TagMatchMode`, query parsing |
| `src/see_the_growth/domain/todo_list.py` | create with tags; filter; `tags_for_todo` parity |
| `src/see_the_growth/db/sqlite_todo_repository.py` | create with extra tags; filter query; `tags_for_todo` |
| `src/see_the_growth/services/todo_service.py` | extended create/list/tags methods |
| `src/see_the_growth/api/local_web_app.py` | form parsing, filter query, template context |
| `src/see_the_growth/api/templates/todo_page.html` | tags field, filter banner, row tags |
| `src/see_the_growth/api/templates/tags_page.html` | linked tag names |
| `src/see_the_growth/api/static/todo.css` | filter banner and row tag styles |
| `tests/unit/test_spec_009_todo_tags_create_and_filter.py` | Domain, repository, service tests |
| `tests/api/test_spec_009_todo_tags_create_and_filter.py` | HTTP and HTML tests |

## Test Plan

### `tests/unit/test_spec_009_todo_tags_create_and_filter.py`
- `test_spec_009_parse_tag_names_splits_and_normalizes` — comma input, whitespace, dedupe.
- `test_spec_009_parse_tag_names_empty_returns_empty_list` — blank input.
- `test_spec_009_create_todo_with_extra_tags` — SQLite links `task` and extras.
- `test_spec_009_create_todo_invalid_tag_raises` — empty segment after normalize fails create.
- `test_spec_009_list_todos_filter_by_tag` — only matching visible todos returned.
- `test_spec_009_list_todos_filter_unknown_tag_returns_empty` — no error, empty list.
- `test_spec_009_tags_for_todo_returns_sorted_names` — sorted tag list for a todo.
- `test_spec_009_in_memory_create_and_filter` — `TodoList` parity.

### `tests/api/test_spec_009_todo_tags_create_and_filter.py`
- `test_spec_009_create_form_includes_tags_field` — input present on `GET /`.
- `test_spec_009_post_todos_with_tags_links_and_shows_tags` — POST with tags renders tag on row.
- `test_spec_009_get_with_tag_filters_todo_list` — `/?tag=` shows only matching todos.
- `test_spec_009_filter_banner_when_active` — banner with active class when filtered.
- `test_spec_009_tags_page_name_links_to_filter` — `href="/?tag=..."` on tags page.
- `test_spec_009_post_create_preserves_tag_filter_redirect` — redirect includes query param.

## Decisions
- **Tag input format**: Single comma-separated text field (no JS).
- **Filter model**: `TodoFilter` in domain layer; repositories and services accept it instead of ad hoc tag string params.
- **Filter**: Single-tag links use `?tag=<name>`; comma-separated values use OR; `tag_match=all` uses AND.
- **Blank filter param**: Treated as no filter.
- **Row display**: All tags including `task` shown on each row (consistent with filter semantics).

## Change Log
- 2026-06-07: Refactored filtering to domain `TodoFilter` with ANY/ALL multi-tag support.
- 2026-06-07: Initial draft and implementation.
