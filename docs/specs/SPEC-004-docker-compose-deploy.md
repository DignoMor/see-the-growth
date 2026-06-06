# SPEC-004: Docker Compose Deploy Strategy

## Status
Implemented

## Goal
Define Docker Compose as the standard way to run the todo web app, with persisted SQLite data at `data/todos.db` on the host (SPEC-003 default path via bind mount).

## Scope
This spec covers container packaging, orchestration with Docker Compose, persistent storage for the database, and operator documentation for run/stop workflows.

### In scope
- A `Dockerfile` that builds a runnable image for the Flask todo web app (`SPEC-002`) backed by SQLite (`SPEC-003`).
- A `docker-compose.yml` (Compose file format v2 or v3) defining one application service.
- Bind mount `./data:/app/data` so todos use the same `data/todos.db` path as SPEC-003 and survive container recreation.
- Environment-based configuration for database path and HTTP listen settings inside the container.
- `.dockerignore` to keep build context small and avoid leaking local artifacts.
- README (or linked docs) with copy-paste commands: build, up, down, logs, and data reset.

### Out of scope
- Kubernetes, Swarm, or other orchestrators beyond Compose on a single host.
- Managed or multi-container databases (PostgreSQL, MySQL, cloud DB services).
- TLS termination, reverse proxies (nginx, Traefik), or internet-facing production hardening.
- Image publishing to a container registry and CI/CD pipelines.
- Horizontal scaling and load balancing.
- Authentication, multi-user tenancy, or network isolation beyond default Docker bridge networking.
- Health-check endpoints beyond optional Compose `healthcheck` (may be added later).

## Relationship to Prior Specs
- `SPEC-001` domain behavior must be unchanged when running in a container.
- `SPEC-002` web routes, templates, and HTTP semantics remain authoritative for user-visible behavior.
- `SPEC-003` Database path convention is authoritative: default `data/todos.db` relative to working directory; Docker uses `WORKDIR` `/app` and bind mount `./data:/app/data` (host file `<repo>/data/todos.db`, container file `/app/data/todos.db`). Do not set `SEE_THE_GROWTH_DB_PATH` in the default Compose file.
- Unit and API tests run via Docker Compose (`docker compose run --rm --build test`; see SPEC-007), not via a host `.venv`.

## Domain Terms
- **Application Image**: OCI image built from the project `Dockerfile` containing app code and Python dependencies.
- **Compose Stack**: The set of services, networks, and volumes declared in `docker-compose.yml`.
- **Data bind mount**: Host `<repository-root>/data` mounted at `/app/data`; database file is `data/todos.db` per SPEC-003 (`<repo>/data/todos.db` on host, `/app/data/todos.db` in container).

## Architecture

### Topology
Single-service Compose stack:

```text
Host
  └── docker compose
        └── service: web
              ├── image: see-the-growth (built from Dockerfile)
              ├── port map: 127.0.0.1:7676 → container 5000
              ├── env: FLASK_APP, SEE_THE_GROWTH_PORT
              └── bind mount: ./data → /app/data
```

### Container layout
- **Working directory**: `/app` (project root inside the image).
- **Application code**: `src/see_the_growth/` installed or on `PYTHONPATH`.
- **Database file**: SPEC-003 default `data/todos.db` with `WORKDIR` `/app` → `/app/data/todos.db`; bind mount exposes the same file on the host at `<repo>/data/todos.db`.
- **HTTP server**: Flask development server or a minimal production WSGI server (see Decisions); must listen on `0.0.0.0` inside the container so port publishing works.

### Layering (unchanged from prior specs)
Container entrypoint invokes the same application factory as local development (`see_the_growth.api.local_web_app:create_app`). No SQL or domain logic in Docker-specific files beyond startup wiring.

## Functional Requirements

### FR-1 Build Application Image
The project must include a `Dockerfile` that produces an image capable of starting the web app.

Behavior:
- Base image: official Python slim (or equivalent) matching project Python version expectations.
- Install dependencies from `requirements.txt` during build.
- Copy only files needed to run the app and tests are not required at runtime (tests may be excluded via `.dockerignore`).
- `docker build` from the repository root must succeed without pre-existing `.venv` on the host.

### FR-2 Orchestrate with Docker Compose
The project must include `docker-compose.yml` defining the `web` service.

Behavior:
- `docker compose up --build` (or `docker-compose up --build`) starts the app and blocks until stopped.
- `docker compose up -d` runs detached.
- `docker compose down` stops and removes containers; `data/todos.db` on the host persists across restarts.
- Service `build` context is the repository root; `dockerfile` points to project `Dockerfile`.
- Publish container HTTP port `5000` to host `127.0.0.1:7676` using `127.0.0.1:7676:5000` (no all-interfaces host bind).

### FR-3 Persist Todo Data Across Container Restarts
SQLite data must survive container stop/start and use the SPEC-003 default path on the host.

Behavior:
- Bind mount `./data:/app/data` in `docker-compose.yml`.
- Do not set `SEE_THE_GROWTH_DB_PATH` in Compose unless overriding the default; the app uses `data/todos.db` relative to `/app`.
- Creating a todo, stopping the stack (`docker compose down`), and starting again (`docker compose up`) must show the same todos in `data/todos.db` on the host.
- Deleting `data/todos.db` (documented in README) is the intentional data-wipe operation.

### FR-4 Configure via Environment
Container runtime must honor existing and new environment variables.

Behavior:
| Variable | Required | Default (in container) | Purpose |
|----------|----------|--------------------------|---------|
| `SEE_THE_GROWTH_DB_PATH` | No | `data/todos.db` (under `/app`) | SQLite file location (`SPEC-003`); set only to override |
| `FLASK_APP` | Yes (set in Compose) | `see_the_growth.api.local_web_app:create_app` | Flask application factory |
| `SEE_THE_GROWTH_PORT` | No | `5000` | Listen port inside the container |

Host access is configured in `docker-compose.yml` via `ports: ["127.0.0.1:7676:5000"]`.

### FR-5 Document Operator Workflows
Project documentation must describe Docker Compose usage from the repository root.

Behavior:
- Document prerequisites: Docker Engine and Docker Compose v2 plugin.
- Document: build/up, detached up, view logs, stop, and reset data (`rm -f data/todos.db`).
- Document default URL: `http://127.0.0.1:7676/`.
- Document that `data/todos.db` on the host is the database (bind mount).
- Document optional `SEE_THE_GROWTH_DB_PATH` and host port overrides via Compose.

### FR-6 Preserve Application Behavior
Running via Compose must not change `SPEC-001`–`SPEC-003` behavior. Host exposure is loopback on port `7676` (SPEC-002 local-only intent).

Behavior:
- All existing unit and API tests pass unchanged via the SPEC-007 Docker test runner.
- Create, list, and complete todos over HTTP behave as in `SPEC-002`.
- Validation and error status codes remain the same.

## Non-Functional Requirements
- Image build time should remain reasonable for local iteration (use `.dockerignore` for `.venv`, `__pycache__`, `.git`, `data/`, etc.).
- Run container as a non-root user when practical.
- Pin base image to a major Python tag (for example `python:3.12-slim`); exact patch updates are acceptable.
- Compose file must be valid for Docker Compose v2 (`docker compose` CLI).
- No new application dependencies required solely for Docker unless a production WSGI server is chosen (see Decisions).

## Deliverables (implementation checklist)
| Artifact | Purpose |
|----------|---------|
| `Dockerfile` | Build runnable application image |
| `docker-compose.yml` | Single-service stack, port map, env, data bind mount |
| `.dockerignore` | Exclude dev artifacts from build context |
| `README.md` (section) | Operator commands and defaults |

## Test Plan (to implement before marking Implemented)

### Manual acceptance (required for v1)
Documented smoke script or checklist executed after `docker compose up --build`:
1. Open todo page at `http://127.0.0.1:7676/`; receive HTTP 200.
2. Create a todo via form; todo appears in list.
3. Mark todo complete; state updates in UI.
4. `docker compose down` then `docker compose up -d`; todo and completion state still present.
5. `docker compose down`, remove `data/todos.db`, then `docker compose up --build`; database is empty (fresh bootstrap).

### Automated (optional for v1, recommended later)
- `tests/e2e/test_spec_004_compose_smoke.py` — skip unless `RUN_SPEC_004_DOCKER_TESTS=1` and Docker CLI available; runs compose up, curls endpoints, compose down. Keeps default CI fast and deterministic.

### Regression
- Full existing `tests/unit/` and `tests/api/` suites pass via `docker compose run --rm --build test` (SPEC-007).

## Implementation Notes (non-normative)
- Entrypoint example: `python -m flask run --host=0.0.0.0 --port=${SEE_THE_GROWTH_PORT}` (host loopback enforced by Compose `ports`).
- Alternative: add `gunicorn` to `requirements.txt` and use `gunicorn -b 0.0.0.0:5000 'see_the_growth.api.local_web_app:create_app()'` for a slightly more production-like container process model.
- Ensure `ensure_db_parent_directory` runs on startup so `/app/data` exists when the bind mount is first created empty.
- Do not set `SEE_THE_GROWTH_DB_PATH` in the default `docker-compose.yml`; rely on SPEC-003 default `data/todos.db`.
- Consider a `compose.override.yml.example` for custom host ports; keep defaults minimal in the committed `docker-compose.yml`.

## Decisions
- **Orchestration**: Docker Compose v2, single `web` service.
- **Persistence**: Bind mount `./data:/app/data`; database file `data/todos.db` (SPEC-003 default).
- **Host publish**: `127.0.0.1:7676:5000`.
- **Default URL**: `http://127.0.0.1:7676/`.
- **In-container bind**: `0.0.0.0:5000` inside the container network namespace; local-only access enforced on the host via `127.0.0.1:7676`.
- **HTTP server (v1)**: Flask built-in server via `flask run` unless implementation adds `gunicorn` with an explicit follow-up note in the change log.
- **CI**: Docker smoke tests opt-in; default test runs use SPEC-007 Docker test runner when CI is added.

## Change Log
- 2026-06-02: Initial draft created.
- 2026-06-02: Implemented Docker Compose stack with `127.0.0.1:7676:5000` publish.
- 2026-06-02: Docker-first runtime; bind mount `./data` for shared `data/todos.db` with SPEC-003; removed named volume and default `SEE_THE_GROWTH_DB_PATH` override.
- 2026-06-02: Cross-referenced SPEC-003 Database path convention; clarified host vs container file locations.
