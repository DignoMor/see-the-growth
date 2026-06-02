# SPEC-005: UI Polish for Local Todo Web Interface

## Status
Implemented

## Goal
Improve the visual presentation and basic UX of the server-rendered todo page (`SPEC-002`) without changing domain behavior, routes, persistence, or deployment.

## Scope
This spec covers HTML structure hooks, CSS, and template layout for the existing create/list/complete flows.

### In scope
- Styled, readable todo page served at the same routes as `SPEC-002`.
- Static CSS served by the Flask app (no build step).
- Clear visual distinction between active and completed todos.
- Styled create form, complete actions, and error messages.
- Responsive layout for common phone and desktop viewport widths.
- Baseline accessibility for the existing controls (labels, focus, contrast, alert semantics).

### Out of scope
- **Clear completed / flush / bulk delete** of completed todos (separate future spec if desired).
- Authentication, multi-user behavior, and authorization.
- New todo features: edit, delete (single item), due dates, priorities, tags, search, or filtering.
- JavaScript-heavy UI, SPA frameworks, or real-time updates (websockets, polling).
- Public deployment hardening, CDN asset hosting, or image/asset pipelines beyond a small static folder.
- Changes to `SPEC-003` persistence or `SPEC-004` Docker Compose topology (runtime URL remains `http://127.0.0.1:7676/` per SPEC-004).
- Dark mode, theming systems, or user-selectable themes (unless added in a follow-up).

## Relationship to Prior Specs
- `SPEC-001` domain rules remain authoritative; no business-rule changes.
- `SPEC-002` remains authoritative for routes, HTTP status codes, form actions, and functional behavior; this spec amends **presentation only**.
- `SPEC-003` and `SPEC-004` are unchanged; optional one-line README note that appearance was improved is acceptable.
- `SPEC-002` FR-2 example (“CSS class” for completed state) is satisfied by this spec’s markup conventions.

## Domain Terms
- **Todo Page**: Same as SPEC-002 — the main HTML page at `GET /`.
- **Presentation Layer**: Jinja2 templates and static CSS under `src/see_the_growth/api/`.
- **Stable Selector**: A CSS class or `data-*` attribute on rendered elements that API tests can assert without parsing full computed styles.

## Functional Requirements

### FR-1 Page Shell and Static Assets
The todo page must load project CSS from a Flask static URL.

Behavior:
- `todo_page.html` must include `<link rel="stylesheet" href="...">` pointing at a project stylesheet (for example `static/todo.css` via `url_for('static', filename='todo.css')`).
- The page must retain `lang="en"` and a descriptive `<title>` (may remain “Todo List” or a minor copy tweak such as “See the Growth — Todos”).
- Body content must use a single main landmark (`<main>`) wrapping primary UI.

### FR-2 Layout and Typography
The page must present content in a centered, constrained layout readable on desktop and mobile.

Behavior:
- Primary content width must not exceed ~42rem on wide viewports (card or column layout).
- Page must use consistent vertical rhythm (heading, form, list spacing).
- Base font must use a system UI stack (no webfont CDN required for v1).
- Text and interactive targets must remain readable without horizontal scrolling at 320px viewport width.

### FR-3 Create Form Presentation
The create-todo form must be visually grouped and aligned with the list.

Behavior:
- Title field retains `id="title"`, `name="title"`, and associated `<label for="title">`.
- Submit control remains a `<button type="submit">` with visible label (copy may be “Add todo” for consistency).
- Form and button must have distinct focus styles (visible `:focus-visible` outline or equivalent).

### FR-4 Todo List and Completed State
Each todo must be listed with stable markup for active vs completed items.

Behavior:
- Each todo renders as a list item (`<li>`) with class `todo-item`.
- Completed items must include class `todo-item--completed` on the `<li>` (or equivalent BEM modifier documented in tests).
- Completed title text must be visually distinct via CSS (for example strikethrough and reduced opacity); the word “completed” as plain text is **not** required if the class and styling satisfy distinction.
- Active (incomplete) items must expose the existing POST complete form; layout may stack on narrow viewports.
- Todo titles must remain plain text in the DOM (no loss of content for screen readers).

### FR-5 Actions and Buttons
Primary and secondary actions must be visually differentiated.

Behavior:
- “Add todo” (or equivalent) uses a primary button style.
- “Complete” uses a secondary or subtle button style on each active row.
- Inline `style="..."` attributes on templates are removed in favor of CSS classes.

### FR-6 Error Message Presentation
Validation and not-found errors must remain user-visible and visually prominent.

Behavior:
- Error container retains `role="alert"` and displays `error_message` when present.
- Error block must use class `alert alert--error` (or equivalent documented stable selectors).
- Error copy and HTTP status behavior remain as defined in `SPEC-002` (4xx with message text in body).

### FR-7 No Behavioral Regression
All `SPEC-002` functional requirements must continue to hold.

Behavior:
- Routes: `GET /`, `POST /todos`, `POST /todos/<id>/complete` unchanged.
- POST-redirect-GET on successful mutations unchanged.
- Domain validation and 404 semantics unchanged.

## Non-Functional Requirements
- **Dependencies**: No new Python packages; no npm/webpack build step for v1.
- **CSS approach (v1 default)**: Hand-written CSS in `src/see_the_growth/api/static/` (single primary stylesheet). Third-party CSS frameworks (Bootstrap, Pico, etc.) are out of scope for v1 unless explicitly chosen in Decisions.
- **Accessibility baseline**:
  - Preserve existing labels and `role="alert"` on errors.
  - Focus indicators on all interactive elements.
  - Color contrast at least WCAG 2.1 AA for normal text and UI components where practical without a design system.
  - Do not rely on color alone to indicate completed state (use strikethrough and/or text style plus class).
- **Performance**: Single CSS file, total uncompressed size target under ~8 KB for v1.
- **Testing**: Deterministic `unittest` in `tests/api/`; no browser automation required for v1.
- **Code location**: Templates and static assets remain under `src/see_the_growth/api/`.

## Visual Direction (v1)
Practical “small local app” aesthetic — calm, minimal, not a marketing site.

| Area | Direction |
|------|-----------|
| Layout | Centered card on subtle neutral page background (`#f5f5f4` or similar); white card with light border/shadow |
| Typography | System stack (`system-ui, sans-serif`); `h1` ~1.5–1.75rem; body 1rem |
| Color | Neutral grays for text; one accent (e.g. teal or indigo `#0d9488` / `#4f46e5`) for primary button and focus ring |
| Completed | Muted text, strikethrough on title, hide or de-emphasize complete button (already absent when completed) |
| Errors | Light red background, dark red text, padding, rounded corners |
| Empty list | Optional short helper line (“No todos yet”) when `todos` is empty — copy-only, no new behavior |

## Files Likely to Change
| File | Change |
|------|--------|
| `docs/specs/SPEC-005-ui-polish.md` | This spec |
| `src/see_the_growth/api/templates/todo_page.html` | Structure, classes, static link, remove inline styles |
| `src/see_the_growth/api/static/todo.css` | New stylesheet |
| `tests/api/test_spec_005_ui_polish.py` | New presentation assertions |
| `docs/specs/SPEC-002-local-web-interface.md` | Change log cross-reference only (optional) |
| `README.md` | Optional one-line note under web UI section |

`local_web_app.py` should require **no** route changes if Flask default static handling is used.

## Test Plan

### Regression (must pass unchanged)
All existing tests in:
- `tests/api/test_spec_002_local_web_interface.py`
- `tests/e2e/test_spec_002_local_app_smoke.py` (if run)
- Full `tests/unit/` suite

Note: `test_spec_002_complete_todo_from_form_marks_item_completed` asserts `"completed"` in body (case-insensitive). Implementation must keep `todo-item--completed` or the substring `completed` in HTML (class name satisfies this).

### New (`tests/api/test_spec_005_ui_polish.py`)
- `test_spec_005_get_page_links_stylesheet` — `GET /` returns 200, body contains stylesheet URL or `todo.css`.
- `test_spec_005_page_has_main_landmark` — response HTML includes `<main`.
- `test_spec_005_active_todo_has_item_class` — incomplete todo `<li` includes `todo-item` without completed modifier.
- `test_spec_005_completed_todo_has_completed_class` — after complete flow, item includes `todo-item--completed`.
- `test_spec_005_error_renders_alert_classes` — empty title POST returns 4xx, body includes `role="alert"` and `alert--error` (or documented equivalent).
- `test_spec_005_template_has_no_inline_style_attributes` — `GET /` body does not contain `style="display:inline"` (guards against regression to inline styles).

Do **not** assert pixel-perfect rendering or computed colors in API tests.

### Manual acceptance (recommended)
After `docker compose up --build`, open `http://127.0.0.1:7676/`:
1. Page is visually centered and readable on desktop.
2. Resize to phone width; no horizontal scroll; buttons remain tappable.
3. Create todo; appears in styled list.
4. Complete todo; title shows completed styling.
5. Submit empty title; error banner visible.

## Implementation Phases

### Phase 1 — Static wiring and shell
- Add `static/todo.css` with reset/spacing and page shell.
- Update template: `<main>`, link stylesheet, remove inline styles.
- **Shippable**: Styled page frame; list may still look plain.

### Phase 2 — List and completed state
- Apply `todo-item` / `todo-item--completed` and completed title styling.
- Optional empty-state message.
- **Shippable**: Clear active vs done visual difference.

### Phase 3 — Forms, buttons, errors
- Style create form and complete buttons; style `alert--error`.
- **Shippable**: Full v1 polish.

### Phase 4 — Accessibility and responsive pass
- Focus-visible, contrast check, narrow viewport padding.
- Add `test_spec_005_*` suite; confirm SPEC-002 regression green.

## Decisions
- **Spec split**: UI polish lives in SPEC-005; SPEC-002 stays “Implemented” as the functional contract.
- **CSS (v1 default)**: Hand-written single file; no framework unless user overrides below.
- **Markup**: BEM-style classes (`todo-item`, `todo-item--completed`, `alert--error`) for test stability.
- **Completed indicator**: Class + CSS styling replaces `<strong>completed</strong>` text where tests still pass via class substring.

### Open decisions (user input)
| Decision | Options | Recommendation |
|----------|---------|----------------|
| CSS framework | None vs minimal classless (e.g. Pico CSS via static file) | None — keeps repo and Docker image simple |
| Accent color | User brand vs neutral-only | Single accent; default teal unless user specifies |
| Page title/branding | “Todo List” vs project name | “See the Growth” subtitle or title tweak — cosmetic |
| Empty state | Show helper line vs blank list | Short helper line |

## Change Log
- 2026-06-02: Implemented — template markup, `static/todo.css`, API tests.
- 2026-06-02: Initial draft created (presentation-only polish; excludes clear-completed).
