# AGENTS.md

## Project Overview

Dify is an open-source platform for developing LLM applications with an intuitive interface combining agentic AI workflows, RAG pipelines, agent capabilities, and model management.

The codebase is in `/home/fengchen/projects/Dify/dify-deploy/` and is split into:
- **Backend API** (`/api`): Python Flask application organized with Domain-Driven Design
- **Frontend Web** (`/web`): Next.js application using TypeScript and React
- **Docker deployment** (`/docker`): Containerized deployment configurations

---

## Build/Lint/Test Commands

### Setup Development Environment

```bash
cd /home/fengchen/projects/Dify/dify-deploy
make dev-setup              # Run all setup steps
make prepare-docker         # Set up Docker middleware (Redis, DB, etc.)
make prepare-web            # Set up web environment (pnpm install)
make prepare-api            # Set up API environment (uv sync + db upgrade)
```

### Backend Commands (Python/Flask)

Run commands through `uv run --project api <command>`:

```bash
cd /home/fengchen/projects/Dify/dify-deploy

# Format & Lint
make format                 # Format code with ruff
make check                  # Check code with ruff
make lint                   # Format, fix, and lint (ruff, imports, dotenv)

# Type Check
make type-check             # Run type checks (basedpyright, mypy, ty)

# Testing
make test                   # Run all backend unit tests
make test TARGET_TESTS=./api/tests/<path_to_test.py>  # Run single test
# Example: make test TARGET_TESTS=./api/tests/unit/core/workflow/test_node_executor.py
```

### Frontend Commands (TypeScript/Next.js)

```bash
cd /home/fengchen/projects/Dify/dify-deploy/web

pnpm install                # Install dependencies
pnpm dev                    # Start development server
pnpm build                  # Build for production
pnpm lint:fix               # Fix lint issues (preferred)
pnpm type-check:tsgo       # TypeScript type checking
```

### Docker Commands

```bash
cd /home/fengchen/projects/Dify/dify-deploy/docker

docker compose up -d                    # Start all services
docker compose down                      # Stop all services
docker compose -f docker-compose.middleware.yaml up -d  # Start middleware only
```

---

## Code Style Guidelines

### Python (Backend)

**Formatting & Linting:**
- Use Ruff for formatting and linting (follow `.ruff.toml`)
- Keep each line under 120 characters
- Run `make lint` before submitting

**Naming Conventions:**
- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`

**Typing:**
- Use modern typing forms: `list[str]`, `dict[str, int]`
- Avoid `Any` unless there's a strong reason
- Keep type hints on functions and attributes
- Implement relevant special methods (`__repr__`, `__str__`)

**Class Layout:**
```python
from datetime import datetime

class Example:
    user_id: str
    created_at: datetime

    def __init__(self, user_id: str, created_at: datetime) -> None:
        self.user_id = user_id
        self.created_at = created_at
```

**Error Handling:**
- Never use `print`; use `logger = logging.getLogger(__name__)`
- Raise domain-specific exceptions (`services/errors`, `core/errors`)
- Translate exceptions into HTTP responses in controllers
- Log retryable events at `warning`, terminal failures at `error`

**SQLAlchemy Patterns:**
- Models inherit from `models.base.TypeBase`
- Use context managers for sessions:
```python
with Session(db.engine, expire_on_commit=False) as session:
    stmt = select(Model).where(...)
    result = session.execute(stmt).scalar_one_or_none()
```
- Always scope queries by `tenant_id`

**Pydantic v2:**
- Define DTOs with Pydantic v2, forbid extras by default
- Use `@field_validator` / `@model_validator` for domain rules

### TypeScript/React (Frontend)

- Use strict TypeScript config
- Avoid `any` types
- Run `pnpm lint:fix` for auto-fixing
- Run `pnpm type-check:tsgo` for type checking

---

## Architecture & Patterns

### Backend (DDD + Clean Architecture)

```
controller → service → core/domain
```

- **Controllers**: Parse input via Pydantic, invoke services, return serialized responses; no business logic
- **Services**: Coordinate repositories, providers, background tasks; keep side effects explicit
- Use `configs.dify_config` for configuration—never read environment variables directly
- Maintain tenant awareness end-to-end; `tenant_id` must flow through every layer
- Queue async work through `services/async_workflow_service`; implement tasks under `tasks/`

### Frontend

- User-facing strings must use `web/i18n/en-US/`; avoid hardcoded text
- Follow the testing guidelines in `web/docs/test.md`

---

## Testing Practices

**Backend:**
- Follow TDD: red → green → refactor
- Use `pytest` with Arrange-Act-Assert structure
- Run single test: `make test TARGET_TESTS=./api/tests/<path>`

**Frontend:**
- Follow `./docs/test.md` for test generation
- Tests must comply with the `frontend-testing` skill

---

## General Practices

- Prefer editing existing files; add new documentation only when requested
- Inject dependencies through constructors
- Keep files below ~800 lines; split when necessary
- Write self-documenting code; only add comments that explain intent
- Read module/class/function docstrings before changing code—treat them as part of the spec
- If docstrings conflict with code, treat code as the source of truth and update docs

---

## Quick Reference

| Task | Command |
|------|---------|
| Format backend | `make format` |
| Lint backend | `make lint` |
| Type-check backend | `make type-check` |
| Run backend tests | `make test` |
| Run single test | `make test TARGET_TESTS=./api/tests/...` |
| Lint frontend | `pnpm lint:fix` |
| Type-check frontend | `pnpm type-check:tsgo` |
