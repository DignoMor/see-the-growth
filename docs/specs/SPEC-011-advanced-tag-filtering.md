# SPEC-011: Advanced Tag Filtering (Multi-Tag Selection)

## Status
Implemented

## Goal
Let users filter the todo list by selecting multiple tags and choosing whether todos must match **any** or **all** selected tags, using server-rendered controls on the todo page.

## Scope
This spec adds multi-tag filter UI on `GET /`, extending SPEC-009 single-tag links and query-string filtering with an explicit tag-picker form. Domain filtering (`TodoFilter`, ANY/ALL semantics) already exists; this spec focuses on HTTP query parsing for HTML forms and presentation.

### In scope
- Tag filter panel on the todo page: checkbox per known tag, match-mode control, **Apply filter** (GET submit).
- Pre-select checkboxes and match mode from the active filter on page load.
- Support repeated `tag` query params from checkbox forms (`?tag=home&tag=errand`) in addition to SPEC-009 comma-separated `tag` param.
- Merge and dedupe tag names from both query styles; blank/whitespace-only values ignored.
- Match mode via `tag_match` query param (`any` default, `all` for AND) — unchanged semantics from SPEC-009.
- Active filter banner continues to describe multi-tag filters (existing `TodoFilter.display_label`).
- POST-redirect-GET on create, complete, and flush preserves the active multi-tag filter (existing `to_query_string()` behavior).
- Filter panel lists tags from `list_tag_summaries()` (same set as Tags page), sorted by name ascending (case-insensitive).
- Presentation consistent with SPEC-005 (BEM-style classes, same stylesheet, no JavaScript).

### Out of scope
- JavaScript, autocomplete, drag-and-drop, or client-side filter preview.
- Changing row or Tags-page tag links to append to an active multi-tag filter (links remain single-tag quick filters: `GET /?tag=<name>`).
- Edit or remove tags on existing todos.
- Saving named filter presets or filter history.
- Filter todos from the Tags page (Tags page links stay single-tag shortcuts to the todo list).
- Authentication or multi-user behavior.
- Changes to Docker Compose topology (SPEC-004) or test runner (SPEC-007).
- Repository or service API changes beyond what SPEC-009 already provides (unless required for query parsing).

## Relationship to Prior Specs
- `SPEC-009` defines `TodoFilter`, `TagMatchMode`, comma-separated `tag` query param, filter banner, and redirect preservation; this spec adds UI and repeated-`tag` query support.
- `SPEC-010` tag deletion removes tags from summaries; filter checkboxes reflect the current tag list after delete.
- `SPEC-008` tag normalization applies when parsing query params (via existing `parse_tag_names` / filter helpers).

## Domain Terms
- **Tag filter panel**: Server-rendered GET form on the todo page for choosing tags and match mode.
- **Quick filter link**: Existing single-tag anchor on a todo row or Tags page (`/?tag=<name>`), replacing the active filter with one tag.
- **Match mode**: `any` (OR — todo has at least one selected tag) or `all` (AND — todo has every selected tag).
- **Active filter**: Current `TodoFilter` derived from request query params, unchanged from SPEC-009.

## Functional Requirements

### FR-1 Query Parameter Parsing
The HTTP layer must accept tag filters from both link-style and form-style query strings.

Behavior:
- `GET /?tag=<name>` — single-tag filter (`TagMatchMode.ANY`); unchanged from SPEC-009.
- `GET /?tag=<name1>,<name2>` — multi-tag OR filter; unchanged from SPEC-009.
- `GET /?tag=<name1>&tag=<name2>` — multi-tag OR filter (checkbox form output); equivalent to comma-separated form after merge.
- When both repeated `tag` params and comma-separated values appear, collect all names, normalize per SPEC-008, dedupe preserving first-seen order, then apply filter.
- `GET /?tag=<name1>,<name2>&tag_match=all` or repeated tags with `tag_match=all` — multi-tag AND filter.
- Blank or whitespace-only `tag` values are skipped; if no valid tag names remain, treat as no filter.
- Unknown `tag_match` values raise `TodoDomainError` (400 on todo page); unchanged from SPEC-009.
- `TodoFilter.to_query_string()` continues to emit comma-separated `tag` and optional `tag_match` for redirects and form actions (canonical serialized form).

### FR-2 Tag Filter Panel (Todo Page)
The todo page must expose controls to build a multi-tag filter.

Behavior:
- Panel appears below the page heading and above the create form (or above the active-filter banner when both are shown — banner stays directly under heading per SPEC-009).
- `<form method="get" action="/" class="todo-tag-filter">` contains:
  - Fieldset or labeled group `todo-tag-filter__tags` with one checkbox per tag from `list_tag_summaries()`.
  - Each checkbox: `name="tag"`, `value="<normalized tag name>"`, id `filter-tag-<name>` (URL-safe id; use same normalized name with characters safe for HTML id, or index-based ids documented in tests).
  - Label text is the tag display name.
  - Match mode: radio group `name="tag_match"`, values `any` (default) and `all`, classes `todo-tag-filter__match`.
  - Submit button labeled **Apply filter** (class `btn btn--secondary`).
- When `active_filter.is_active`, checkboxes for tags in `active_filter.tag_names` are `checked`; match radio reflects `active_filter.tag_match`.
- When no filter is active, no checkboxes checked; `any` selected by default.
- Submitting with zero checkboxes selected navigates to `GET /` with no tag filter (equivalent to clear filter).
- Panel visible even when the tag list is empty (show empty helper text, no checkboxes); Apply still submits to unfiltered list.

### FR-3 Active Filter Banner
The existing filter banner must remain accurate for multi-tag filters.

Behavior:
- When `active_filter.is_active`, show banner (class `todo-filter`) with `active_filter.display_label` (quoted tag names; `(all)` suffix when AND mode).
- **Show all** link (`todo-filter__clear`) clears filter (`GET /`).
- Banner and filter panel may both be visible when a filter is active (panel reflects current selection).

### FR-4 Quick Filter Links (Unchanged)
Single-tag links remain the fast path for one-tag filtering.

Behavior:
- Todo row tags and Tags page names link to `GET /?tag=<name>` (replaces active filter with single tag, ANY mode).
- Quick links do not pre-check other tags in the filter panel beyond what the new URL implies on reload.

### FR-5 Redirect and Form Action Preservation
POST flows must preserve multi-tag filters.

Behavior:
- Create, complete, and flush forms append `active_filter_query` when a filter is active — unchanged from SPEC-009.
- After successful POST, redirect URL uses `TodoFilter.to_query_string()` so multi-tag AND filters keep `tag_match=all`.

### FR-6 Template Context
The todo page render path must supply data for the filter panel.

Behavior:
- Pass `tag_summaries` (from `list_tag_summaries()`) to `todo_page.html` in addition to existing context.
- Sort order for checkboxes: tag name ascending, case-insensitive (match Tags page listing order).

## Non-Functional Requirements
- No new Python package dependencies.
- No JavaScript required for filter interaction.
- Deterministic `unittest` in `tests/unit/` and `tests/api/`.
- Run tests via `docker compose run --rm --build test` (SPEC-007).
- Filter panel usable at 320px viewport width without horizontal scroll (wrap checkboxes or stack vertically).

## Files Likely to Change
| File | Change |
|------|--------|
| `docs/specs/SPEC-011-advanced-tag-filtering.md` | This spec |
| `src/see_the_growth/domain/todo_filter.py` | Parse repeated `tag` query values; optional helper for Flask request args |
| `src/see_the_growth/api/local_web_app.py` | Pass `tag_summaries`; wire repeated-tag query parsing |
| `src/see_the_growth/api/templates/todo_page.html` | Tag filter panel markup |
| `src/see_the_growth/api/static/todo.css` | Filter panel layout and checkbox grouping |
| `tests/unit/test_spec_011_advanced_tag_filtering.py` | Query parsing and filter merge tests |
| `tests/api/test_spec_011_advanced_tag_filtering.py` | HTML panel, GET submit, multi-tag list results |

## Test Plan

### `tests/unit/test_spec_011_advanced_tag_filtering.py`
- `test_spec_011_parse_repeated_tag_params` — `tag=a&tag=b` → `TodoFilter.for_tags(["a","b"], ANY)`.
- `test_spec_011_parse_merges_comma_and_repeated_tags` — `tag=a,b&tag=c` dedupes and preserves order.
- `test_spec_011_parse_repeated_tags_with_match_all` — AND mode with repeated params.
- `test_spec_011_parse_empty_repeated_tags_returns_no_filter` — all blank → `TodoFilter.none()`.
- `test_spec_011_to_query_string_unchanged_for_multi_tag` — regression on canonical redirect string.

### `tests/api/test_spec_011_advanced_tag_filtering.py`
- `test_spec_011_todo_page_shows_tag_filter_panel` — form `todo-tag-filter`, checkboxes per tag.
- `test_spec_011_filter_panel_reflects_active_filter` — GET with multi-tag filter checks correct boxes and `all` radio.
- `test_spec_011_get_apply_filter_any_shows_matching_todos` — submit two tags, ANY, only matching rows.
- `test_spec_011_get_apply_filter_all_shows_intersection` — submit two tags, ALL, stricter result.
- `test_spec_011_apply_filter_no_checkboxes_clears_filter` — submit empty selection → unfiltered list, no banner.
- `test_spec_011_post_create_preserves_multi_tag_filter_redirect` — redirect includes comma-separated tags and `tag_match=all` when active.
- `test_spec_011_filter_banner_multi_tag_all_mode` — banner shows `(all)` in label.

### Regression
All existing tests in `tests/unit/`, `tests/api/`, and `tests/e2e/` must pass.

## Implementation Phases

### Phase 1 — Query parsing
- Extend `parse_todo_filter_from_query` (or companion) to accept a list of tag param strings.
- Unit tests green.

### Phase 2 — Todo page panel
- Template markup, `tag_summaries` context, GET form wiring.
- API tests for panel presence and filter submission.

### Phase 3 — Presentation
- CSS for checkbox group and match-mode row; verify mobile layout.

## Decisions
- **UI pattern**: GET form with checkboxes (`name="tag"`) rather than a comma-separated text field — clearer multi-select without JavaScript.
- **Query canonical form**: Redirects and POST hidden query continue using comma-separated `tag` in `to_query_string()`; repeated params are accepted on input only.
- **Quick links vs panel**: Row and Tags page links keep single-tag replace semantics; multi-tag composition is via the panel only (avoids ambiguous “add to filter” URL rules in v1).
- **Tag source**: Filter checkboxes use `list_tag_summaries()` so counts stay consistent with Tags page; include all tags (including `task`).
- **Clear filter**: **Show all** in banner and submitting the panel with no boxes checked both resolve to unfiltered list.
- **Match mode default**: `any` when param omitted or radio not explicitly set to `all`.

## Change Log
- 2026-06-07: Implemented filter panel, repeated-tag query parsing, and tests.
- 2026-06-07: Initial draft.
