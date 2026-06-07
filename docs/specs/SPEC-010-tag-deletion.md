# SPEC-010: Delete Tags from Tags Page

## Status
Implemented

## Goal
Let users delete user-created tags from the Tags page, removing the tag and all todo associations while leaving todos intact.

## Scope
This spec adds tag deletion UI and service/repository support on `GET /tags`, extending SPEC-008 tag longevity with an explicit user-initiated delete path.

### In scope
- `delete_tag(tag_name)` on the service/repository layer.
- `POST /tags/<name>/delete` route with POST-redirect-GET back to `GET /tags`.
- Delete control on each deletable tag row on the tags page.
- Remove the tag row from `tags` and all `todo_tags` associations for that tag (visible and flushed todos).
- Todos remain; they lose only the deleted tag (other tags, including `task`, unchanged).
- System tag **`task`** cannot be deleted (error surfaced on the tags page).
- Unknown tag name on delete raises `TodoDomainError` (same not-found semantics as `complete_todo`).
- In-memory `TodoList` parity for deterministic API tests.
- Presentation consistent with SPEC-005 (BEM-style classes, same stylesheet).

### Out of scope
- Rename, merge, or bulk-delete tags.
- Remove tags from individual todos without deleting the tag entity.
- Confirmation dialogs or JavaScript (simple form POST only).
- Undo / restore deleted tags.
- Authentication or multi-user behavior.
- Changes to Docker Compose topology (SPEC-004) or test runner (SPEC-007).

## Relationship to Prior Specs
- `SPEC-008` tag model, normalization, and tags page listing remain; this spec amends longevity with user-initiated delete for non-system tags.
- `SPEC-009` todo-page tag display and filtering continue; deleted tags disappear from rows and filter results.
- `SPEC-006` flushed todos retain rows; deleting a tag removes associations on flushed todos too but does not delete todo rows.

## Domain Terms
- **Deletable tag**: Any tag except the system tag `task`.
- **Tag deletion**: Remove the tag entity and all `todo_tags` links; todos are not deleted.
- **System tag**: Normalized name `task`; always present after bootstrap; not deletable.

## Functional Requirements

### FR-1 Delete Tag (Service Layer)
The system must support deleting a tag by normalized name.

Behavior:
- `delete_tag(tag_name: str) -> None` normalizes `tag_name` per SPEC-008.
- Deleting normalized name `task` raises `TodoDomainError` with a clear message (for example “The task tag cannot be deleted.”).
- Unknown tag name raises `TodoDomainError` (for example “Tag '…' does not exist.”).
- On success:
  - The `tags` row for that name is removed.
  - All `todo_tags` rows for that tag are removed.
  - Visible todos no longer show the tag on list rows or match it in filters.
  - Flushed todos lose the association in SQLite but remain flushed.
- Operation is idempotent only in the sense that a second delete of the same name fails as not found (not silent success).

### FR-2 SQLite Repository
Tag deletion must run in a single transaction.

Behavior:
- Resolve tag by normalized `name`; if missing, raise `ValueError` (service maps to `TodoDomainError`).
- `DELETE FROM todo_tags WHERE tag_id = ?` then `DELETE FROM tags WHERE id = ?`.
- Commit atomically; rollback on failure.

### FR-3 In-Memory Parity
`TodoList` must mirror delete semantics for API tests.

Behavior:
- Remove the name from `_all_tags`.
- Remove the name from every entry in `_todo_tags`.
- Reject delete of `task` and unknown names with `TodoDomainError`.

### FR-4 Delete Route
The web app must accept tag deletion via POST.

Behavior:
- `POST /tags/<name>/delete` where `<name>` is the normalized tag name (URL-encoded in forms).
- On success: redirect to `GET /tags` (303/302 per existing POST patterns).
- On `TodoDomainError`: re-render tags page with `error_message` and current summaries; status **400** for validation errors (system tag), **404** for unknown tag (match `complete_todo` split).
- Tags page lists summaries after failed delete (unchanged data except for successful deletes).

### FR-5 Tags Page Delete Control
Each deletable tag row must expose a delete action.

Behavior:
- System tag `task`: no delete control (row shows name and unfinished count only).
- Other tags: inline form `method="post"` `action="/tags/<name>/delete"` with submit button labeled **Delete** (class `btn btn--secondary`, form class `tags-item__delete-form`, button class `tags-item__delete-btn` or equivalent documented selectors).
- Existing tag name link to `GET /?tag=<name>` and unfinished count remain unchanged.
- Error banner on tags page when delete fails (reuse `alert alert--error` pattern from todo page).

### FR-6 Regression
SPEC-008 / SPEC-009 behavior must not regress aside from deleted tags disappearing.

Behavior:
- `GET /tags` still lists all remaining tags with unfinished counts.
- Create, complete, flush, filter, and tag-on-create flows unchanged.
- `task` always remains after bootstrap.

## Non-Functional Requirements
- No new Python package dependencies.
- Deterministic `unittest` in `tests/unit/` and `tests/api/`.
- Run tests via `docker compose run --rm --build test` (SPEC-007).

## Files Likely to Change
| File | Change |
|------|--------|
| `docs/specs/SPEC-010-tag-deletion.md` | This spec |
| `src/see_the_growth/db/sqlite_todo_repository.py` | `delete_tag` |
| `src/see_the_growth/services/todo_service.py` | `delete_tag`; protocol extension |
| `src/see_the_growth/domain/todo_list.py` | In-memory `delete_tag` |
| `src/see_the_growth/api/local_web_app.py` | `POST /tags/<name>/delete`; error context on tags page |
| `src/see_the_growth/api/templates/tags_page.html` | Delete forms; error alert |
| `src/see_the_growth/api/static/todo.css` | Delete button layout on tag rows |
| `tests/unit/test_spec_010_tag_deletion.py` | Domain, repository, service tests |
| `tests/api/test_spec_010_tag_deletion.py` | HTTP and HTML tests |

## Test Plan

### `tests/unit/test_spec_010_tag_deletion.py`
- `test_spec_010_delete_tag_removes_tag_and_associations` — after delete, tag absent from summaries and todo `tags_for_todo`.
- `test_spec_010_delete_tag_leaves_todo_and_other_tags` — todo remains with `task` and other tags.
- `test_spec_010_delete_tag_removes_from_flushed_todo_associations` — SQLite: flushed todo loses link; row still flushed.
- `test_spec_010_delete_task_tag_raises` — `TodoDomainError` for `task`.
- `test_spec_010_delete_unknown_tag_raises` — missing name fails.
- `test_spec_010_in_memory_delete_tag_parity` — `TodoList` matches SQLite semantics.

### `tests/api/test_spec_010_tag_deletion.py`
- `test_spec_010_tags_page_shows_delete_for_user_tag` — deletable tag has delete form/button.
- `test_spec_010_tags_page_no_delete_for_task` — `task` row has no delete control.
- `test_spec_010_post_delete_tag_redirects_and_removes` — POST delete → redirect `/tags`; tag name gone.
- `test_spec_010_post_delete_tag_updates_todo_row` — todo no longer shows deleted tag on `GET /`.
- `test_spec_010_post_delete_task_returns_400` — error message on tags page.
- `test_spec_010_post_delete_unknown_tag_returns_404` — error message on tags page.

### Regression
All existing tests in `tests/unit/`, `tests/api/`, and `tests/e2e/` must pass.

## Implementation Phases

### Phase 1 — Domain and persistence
- Repository `delete_tag`; service method; `TodoList` parity.
- Unit tests green.

### Phase 2 — Web route and template
- `POST /tags/<name>/delete`; tags page forms and error display.
- API tests green.

### Phase 3 — Presentation
- CSS for delete control on tag rows; confirm layout at 320px width.

## Decisions
- **Delete vs hide**: Hard delete of `tags` and `todo_tags` rows (unlike todo flush). Todos are never deleted.
- **System tag**: `task` is not deletable; no delete UI on that row.
- **Todos with unfinished work**: Tag may be deleted even when `unfinished_count > 0`; associations are removed and todos stay visible with remaining tags.
- **Route shape**: `POST /tags/<name>/delete` with URL-encoded normalized name (consistent with per-item POST routes).
- **Errors**: 400 for protected system tag; 404 for unknown tag (align with `complete_todo`).
- **Success feedback**: Redirect only; no flash message in v1.

## Change Log
- 2026-06-07: Implemented delete_tag service, POST route, tags page UI, and tests.
- 2026-06-07: Initial draft.
