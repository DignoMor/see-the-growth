# SPEC-012: Server Docker Deploy

## Status
Implemented

## Goal
Enable deploying the todo web app on a remote server with Docker Compose, using a production WSGI server and network-accessible HTTP while preserving SQLite data on the host.

## Scope
This spec extends SPEC-004 using the same `docker-compose.yml` for local dev and server deploy — no extra compose file or `.env` file.

### In scope
- Unified `docker-compose.yml` for local dev and server deploy.
- Fixed host port **7676** → container port **5000**.
- Gunicorn as the in-container HTTP server.
- `GET /health` endpoint returning HTTP 200 for load balancers and Compose health checks.
- README note that server deploy uses the same commands as local.
- Gunicorn added to `requirements.txt`.

### Out of scope
- TLS termination, reverse proxies (nginx, Caddy, Traefik), or certificate management.
- Image publishing to a container registry and CI/CD pipelines.
- Authentication, multi-user tenancy, or internet-facing hardening beyond default Docker port publishing.
- Kubernetes, Swarm, or multi-host orchestration.
- `.env` files or environment-based port overrides.

## Relationship to Prior Specs
- `SPEC-004` compose file is extended in place; host port remains **7676**.
- `SPEC-003` database path and bind mount `./data:/app/data` apply unchanged.
- `SPEC-007` test runner continues to use the same `Dockerfile`; all unit and API tests must pass.

## Domain Terms
- **Health check**: HTTP probe against `GET /health` inside the container.

## Architecture

### Topology
Same Compose stack for local and server:

```text
Host
  └── docker compose
        └── service: web
              ├── image: built from Dockerfile (gunicorn)
              ├── port map: 7676 → container 5000
              ├── env: FLASK_APP, SEE_THE_GROWTH_PORT
              ├── bind mount: ./data → /app/data
              ├── restart: unless-stopped
              └── healthcheck: GET /health on container port 5000
```

### Layering
Application factory and domain logic are unchanged. Compose controls restart, healthcheck, and Gunicorn command.

## Functional Requirements

### FR-1 Unified Compose File
The project must use a single `docker-compose.yml` for local dev and server deployment.

Behavior:
- `docker compose up --build -d` starts the app detached (same command locally and on a server).
- Publish container port `5000` to host port **7676**.
- Bind mount `./data:/app/data` (same as SPEC-004).
- `restart: unless-stopped`.
- Service command runs Gunicorn bound to `0.0.0.0:${SEE_THE_GROWTH_PORT}` inside the container.

### FR-2 Production WSGI Server
Gunicorn must serve the Flask application in the compose stack.

Behavior:
- Add `gunicorn` to `requirements.txt`.
- Compose command uses Gunicorn with the app factory (`see_the_growth.api.local_web_app:create_app()`).
- Default worker count: `2` (sufficient for a small single-host deploy).
- Dockerfile default `CMD` also uses Gunicorn.

### FR-3 Health Endpoint
The web app must expose a health check route.

Behavior:
- `GET /health` returns HTTP **200**.
- Response body is JSON: `{"status": "ok"}`.
- No authentication required.
- Route does not touch the database (liveness only).

### FR-4 Compose Health Check
Compose must define a container health check probing `/health`.

Behavior:
- Probe targets `http://127.0.0.1:5000/health` inside the container.
- Uses Compose `healthcheck` with reasonable interval, timeout, and retries.
- `docker compose ps` shows `healthy` after startup.

### FR-5 Environment Configuration
Container runtime honors existing environment variables.

Behavior:
| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SEE_THE_GROWTH_PORT` | No | `5000` | Listen port inside the container |
| `FLASK_APP` | Yes (set in compose) | `see_the_growth.api.local_web_app:create_app` | Application factory |

Host port **7676** is fixed in `docker-compose.yml`; no `.env` file is required.

### FR-6 Document Server Deploy Workflow
README must describe server deployment from the repository root.

Behavior:
- Server deploy uses the same `docker compose up --build -d` as local dev.
- URL pattern: `http://<server-host>:7676/`.
- Note that firewall and TLS/reverse proxy are operator responsibility (out of scope).

### FR-7 Preserve Application Behavior
Server deployment must not change SPEC-001–SPEC-011 user-visible behavior.

Behavior:
- All existing unit and API tests pass via SPEC-007 test runner.
- Todo create, list, complete, tags, and filters behave as before over HTTP.

## Non-Functional Requirements
- Compose file must be valid for Docker Compose v2.
- Health endpoint must respond quickly without database I/O.

## Deliverables (implementation checklist)
| Artifact | Purpose |
|----------|---------|
| `docker-compose.yml` | Unified stack: gunicorn, port 7676, restart, healthcheck |
| `requirements.txt` | Add `gunicorn` |
| `GET /health` route | Liveness probe |
| `README.md` (section) | Server deploy uses same commands |

## Test Plan

### Automated
- `tests/api/test_spec_012_server_docker_deploy.py` — `GET /health` returns 200 and JSON body.
- `tests/unit/test_spec_012_server_docker_deploy.py` — `docker-compose.yml` declares gunicorn, healthcheck, and `7676:5000`.

### Manual acceptance
After `docker compose up --build -d` on a server:
1. `curl http://<host>:7676/health` returns `{"status":"ok"}`.
2. Open todo page; create and complete a todo.
3. `docker compose down` then up again; todos persist in `./data/todos.db`.
4. `docker compose ps` shows service `healthy`.

### Regression
- Full `tests/unit/` and `tests/api/` pass via `docker compose run --rm --build test`.

## Decisions
- **Single compose file**: Same file and commands for local and server; no `.env` overrides.
- **Host port**: **7676** (matches SPEC-004; works for server deploy).
- **Workers**: `2` Gunicorn workers for v1.
- **Health response**: JSON `{"status":"ok"}` for easy parsing by probes.
- **TLS**: Out of scope; document that operators add a reverse proxy when needed.

## Change Log
- 2026-06-07: Initial draft created.
- 2026-06-07: Implemented Gunicorn, `/health`, and README server section.
- 2026-06-07: Consolidated to single `docker-compose.yml`; removed `docker-compose.prod.yml`.
- 2026-06-07: Dropped `.env` and `SEE_THE_GROWTH_PUBLISH`; fixed port `7676:5000`.
