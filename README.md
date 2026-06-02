# see-the-growth
Tool for to-do list and time tracking

## Development

### Project Structure

```text
see-the-growth/
  docs/
    specs/                    # Feature specs (source of truth)
  src/
    see_the_growth/
      domain/                 # Core business logic
      api/                    # API routes and schemas
      db/                     # Persistence and repositories
      services/               # App orchestration/services
      __init__.py
  tests/
    unit/                     # Fast logic tests
    api/                      # API contract tests
    e2e/                      # End-to-end user flows
  .cursor/
    rules/                    # Cursor agent rules
  README.md
```

### AI Assisted Development

This project uses `cursor` for AI-assisted development.
Cursor rules are defined in `.cursor/rules`.

### Local Web App and Database

Run the local todo web app from the project root (with dependencies installed in `.venv`):

```bash
.venv/bin/python -m flask --app see_the_growth.api.local_web_app:create_app run
```

By default, todos are stored in `data/todos.db` (the `data/` directory is created automatically).

Use a custom database file path:

```bash
export SEE_THE_GROWTH_DB_PATH=/path/to/my-todos.db
.venv/bin/python -m flask --app see_the_growth.api.local_web_app:create_app run
```
