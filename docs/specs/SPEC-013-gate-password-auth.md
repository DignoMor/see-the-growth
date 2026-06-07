# SPEC-013: Gate Password Authentication

## Status
Implemented

## Goal
Protect the todo web app behind a single shared gate password so a server deployment (SPEC-012) is not fully open on the network, while keeping local development simple when auth is disabled.

## Scope
This spec adds optional, app-wide authentication using one shared password configured at deploy time.

### In scope
- Optional gate password via environment variable.
- Login page with password form.
- Session cookie after successful login.
- Redirect unauthenticated browser requests to login.
- Preserve access to `GET /health` without authentication.
- Allow static assets (`/static/*`) without authentication so the login page is styled.
- Logout action clearing the session.
- Backward-compatible default: no password configured → auth disabled, existing behavior unchanged.

### Out of scope
- Multi-user accounts, roles, or per-user data isolation.
- OAuth, SSO, or third-party identity providers.
- Password hashing at rest (the configured value is the gate secret itself).
- Rate limiting, CAPTCHA, or brute-force protection.
- API tokens or HTTP Basic Auth.
- TLS, reverse proxies, or network-level security (SPEC-012 out of scope).

## Relationship to Prior Specs
- `SPEC-012` server deploy exposes port **7676** on the network; this spec is the minimal auth layer for that scenario.
- `SPEC-007` test runner must continue to pass with auth disabled (default in tests).
- All SPEC-001–SPEC-011 user-visible behavior is unchanged once authenticated.

## Domain Terms
- **Gate password**: The single shared secret required to access the app.
- **Auth enabled**: Gate password is configured (non-empty); all protected routes require a session.
- **Auth disabled**: No gate password configured; app behaves as before SPEC-013.

## Functional Requirements

### FR-1 Configuration
The app must read gate password configuration from the environment.

Behavior:
| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SEE_THE_GROWTH_GATE_PASSWORD` | No | unset (auth disabled) | Shared gate password; non-empty value enables auth |

- Whitespace-only values are treated as disabled.
- Configuration logic lives in `src/see_the_growth/api/auth_config.py`.

### FR-2 Login Page
When auth is enabled, the app must provide a login route.

Behavior:
- `GET /login` returns HTML with a password field and submit control.
- Unauthenticated requests to protected routes redirect to `/login`, preserving the original path in a `next` query parameter when safe (same-origin relative path starting with `/`, not `//`).
- `POST /login` with the correct password establishes an authenticated session and redirects to `next` or `/`.
- `POST /login` with a wrong or empty password re-renders the login page with a user-visible error (HTTP 401).

### FR-3 Session Authentication
Successful login must persist authentication across requests.

Behavior:
- Flask signed session cookie stores authenticated state.
- Session signing key is derived deterministically from the gate password when auth is enabled (stable across Gunicorn workers).
- `POST /logout` clears the session and redirects to `/login`.

### FR-4 Protected Routes
When auth is enabled, all application routes except public endpoints require an authenticated session.

Public (no auth required):
- `GET /health`
- `GET /static/*`
- `GET /login`, `POST /login`

Protected (auth required when enabled):
- Todo, tags, and all other existing routes from SPEC-002–SPEC-011.

When auth is disabled, no route requires a session.

### FR-5 Navigation
When auth is enabled and the user is authenticated, the app shell must offer a logout control.

Behavior:
- Logout is a form POST to `/logout` visible in the main navigation.

## Non-Functional Requirements
- Password comparison must use constant-time comparison (`secrets.compare_digest`).
- Auth routing and session helpers live in `src/see_the_growth/api/`.
- Tests must not depend on real cookies from external services; use Flask test client.
- `create_app` accepts an optional `auth_config` override for deterministic tests.

## Deliverables (implementation checklist)
| Artifact | Purpose |
|----------|---------|
| `docs/specs/SPEC-013-gate-password-auth.md` | This spec |
| `src/see_the_growth/api/auth_config.py` | Env-based auth configuration |
| `src/see_the_growth/api/auth.py` | Session helpers and password verification |
| `src/see_the_growth/api/local_web_app.py` | Login/logout routes and auth gate |
| `src/see_the_growth/api/templates/login_page.html` | Login form UI |
| `src/see_the_growth/api/templates/base.html` | Logout control when auth enabled |
| `tests/unit/test_spec_013_gate_password_auth.py` | Config and pure auth logic |
| `tests/api/test_spec_013_gate_password_auth.py` | HTTP auth flow |
| `README.md` | Document `SEE_THE_GROWTH_GATE_PASSWORD` |

## Test Plan

### Unit (`tests/unit/test_spec_013_gate_password_auth.py`)
- `test_spec_013_auth_disabled_when_env_unset`
- `test_spec_013_auth_disabled_when_env_empty_or_whitespace`
- `test_spec_013_auth_enabled_when_env_set`
- `test_spec_013_verify_password_uses_constant_time_comparison`

### API (`tests/api/test_spec_013_gate_password_auth.py`)
- `test_spec_013_auth_disabled_allows_todo_page_without_login`
- `test_spec_013_auth_enabled_redirects_unauthenticated_to_login`
- `test_spec_013_auth_enabled_wrong_password_returns_401`
- `test_spec_013_auth_enabled_correct_password_grants_access`
- `test_spec_013_health_accessible_without_auth_when_enabled`
- `test_spec_013_logout_clears_session`

### Regression
- Full `tests/unit/` and `tests/api/` pass via `docker compose run --rm --build test` with auth disabled (default).

## Decisions
- **Single password, not users**: One shared secret for the whole app; no user table.
- **Env-only config**: Matches `SEE_THE_GROWTH_DB_PATH` pattern; no `.env` file in repo.
- **Opt-in**: Auth disabled by default so local dev and CI need no extra setup.
- **Session cookie**: Browser-friendly; no Authorization headers for HTML forms.

## Change Log
- 2026-06-07: Initial draft.
- 2026-06-07: Implemented gate password auth, login/logout, and tests.
