# see-the-growth
Tool for to-do list and time tracking

## Run the app

Requires Docker Engine and the Compose v2 plugin (`docker compose`).

From the project root:

```bash
# Build and run (foreground)
docker compose up --build

# Detached
docker compose up --build -d

# Logs
docker compose logs -f web

# Stop
docker compose down
```

Open the app at [http://127.0.0.1:7676/](http://127.0.0.1:7676/) (or `http://<server-host>:7676/` on a remote machine). Host port **7676** maps to container port **5000**. The todo page uses a small static stylesheet for layout and readability (SPEC-005).

Health probe: `GET /health` returns `{"status":"ok"}`.

### Database (`data/todos.db`)

Todos are stored at `data/todos.db` in the repository (SPEC-003 default). Docker bind-mounts `./data` to `/app/data` with container working directory `/app`, so the app opens the same file as `<repo>/data/todos.db` on the host and `/app/data/todos.db` in the container.

To use a different database file path, set `SEE_THE_GROWTH_DB_PATH` in `docker-compose.yml` (container path) or adjust the volume mount.

To reset todos:

```bash
docker compose down
rm -f data/todos.db
```

### Server deployment

Same commands as local — clone the repo on the server, run `docker compose up --build -d`, and open port **7676** in the host firewall if needed. TLS and reverse-proxy setup are left to the operator (out of scope).

## Development

### Project Structure

```text
see-the-growth/
  data/                     # SQLite database (gitignored; created at runtime)
  docs/
    specs/                  # Feature specs (source of truth)
  src/
    see_the_growth/
      domain/               # Core business logic
      api/                  # API routes and schemas
      db/                   # Persistence and repositories
      services/             # App orchestration/services
  tests/
    unit/                   # Fast logic tests
    api/                    # API contract tests
    e2e/                    # End-to-end user flows
  Dockerfile
  docker-compose.yml
  README.md
```

### Tests

Unit and API tests run in Docker (SPEC-007). Requires Docker Engine and the Compose v2 plugin, same as running the app:

```bash
docker compose run --rm --build test
```

The `test` service uses the Compose `test` profile and does not start with `docker compose up`. It bind-mounts `./src` and `./tests` so edits on the host are picked up without rebuilding the image (rebuild when `requirements.txt` changes).

### AI Assisted Development

This project uses `cursor` for AI-assisted development.
Cursor rules are defined in `.cursor/rules`.
