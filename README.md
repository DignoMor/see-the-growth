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

Open the app at [http://127.0.0.1:7676/](http://127.0.0.1:7676/). The service is published on the host loopback only (`127.0.0.1:7676` → container port `5000`), so it is not reachable from other machines on your network.

### Database (`data/todos.db`)

Todos are stored at `data/todos.db` in the repository (SPEC-003 default). Docker bind-mounts `./data` to `/app/data` with container working directory `/app`, so the app opens the same file as `<repo>/data/todos.db` on the host and `/app/data/todos.db` in the container.

To use a different database file path, set `SEE_THE_GROWTH_DB_PATH` in `docker-compose.yml` (container path) or adjust the volume mount.

To reset todos:

```bash
docker compose down
rm -f data/todos.db
```

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

Unit and API tests run on the host with a local virtual environment (they do not require Docker):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests/unit -s tests/api -p 'test_*.py' -v
```

### AI Assisted Development

This project uses `cursor` for AI-assisted development.
Cursor rules are defined in `.cursor/rules`.
