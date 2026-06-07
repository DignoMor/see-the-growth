# SPEC-007: Docker Test Runner

## Status
Implemented

## Goal
Run unit and API tests inside Docker so developers and agents do not need a host `.venv`.

## Scope

### In scope
- A Compose `test` service (profile `test`) that runs `tests/unit/` and `tests/api/` in the application image.
- Bind-mount `./src` and `./tests` so test runs use working-tree code without rebuilding for every edit.
- README and agent rules documenting the Docker test command as the standard workflow.
- Deprecate host `.venv` as the documented test path (`.gitignore` entry may remain for optional local use).

### Out of scope
- CI pipeline configuration (no GitHub Actions in repo yet).
- E2E tests that require a running `web` service (see SPEC-004 optional smoke tests).
- Changing test assertions or application behavior.

## Functional Requirements

### FR-1 Compose test service
`docker-compose.yml` must define a `test` service with profile `test`.

Behavior:
- Uses the same `Dockerfile` build as `web`.
- Sets `PYTHONPATH=/app/src` and `working_dir: /app`.
- Mounts `./src:/app/src:ro` and `./tests:/app/tests:ro`.
- Does not start when running `docker compose up` (profile isolation).
- Default command runs unit then API suites via `unittest discover`.

### FR-2 Document operator command
README must document:

```bash
docker compose run --rm --build test
```

Behavior:
- Exit code 0 when all unit and API tests pass.
- Non-zero exit code on failure.
- `--build` ensures dependencies from `requirements.txt` are present in the image.

### FR-3 Preserve test coverage
All existing tests under `tests/unit/` and `tests/api/` must pass unchanged when run via the `test` service.

## Non-Functional Requirements
- Test runs must not require a pre-existing host `.venv`.
- Test service must not bind-mount `./data` or mutate host application database files.

## Test Plan
1. `docker compose run --rm --build test` exits 0 on a clean checkout.
2. `docker compose up --build` still starts only `web` (no `test` service without profile).

## Change Log
- 2026-06-06: Initial draft and implementation.
