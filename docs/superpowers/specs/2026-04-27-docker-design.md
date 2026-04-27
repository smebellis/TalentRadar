# Docker Design — Job Search Agent

**Date:** 2026-04-27  
**Status:** Approved

---

## Goal

Containerize the job search pipeline and its PostgreSQL database so the app can be run identically in development and production with a single `docker compose` command.

---

## Interaction Model

```bash
# Start Postgres in the background
docker compose up db -d

# Run the pipeline once
docker compose run --rm app python cli.py full --cv /data/resume.pdf --keywords "Python"

# Drop into a shell for debugging
docker compose run --rm app bash
```

The `app` container is ephemeral — `--rm` removes it after each run. Postgres persists between runs via a named Docker volume (`pgdata`).

---

## Files

| File | Action |
|---|---|
| `Dockerfile` | Create — multi-stage build |
| `docker-compose.yml` | Create — app + db services |
| `.dockerignore` | Create — exclude venv, cache, .env |
| `.env.example` | Update — document `POSTGRES_HOST=db` for Docker |

No application code changes required. The Hydra database config already reads `POSTGRES_HOST` from the environment via `oc.env` interpolation.

---

## Dockerfile — Multi-Stage Build

**Stage 1 — `builder` (`python:3.12-slim`)**
- Install OS build deps: `gcc`, `libpq-dev` (required to compile `asyncpg`)
- `pip install --prefix=/install` from `requirements.txt`

**Stage 2 — `runtime` (`python:3.12-slim`)**
- Install OS runtime deps only: `libpq5`
- Copy `/install` from builder (compiled packages, no build tools)
- Copy source code to `/app`
- `WORKDIR /app`
- No `ENTRYPOINT` — container accepts arbitrary commands

Result: build tools stay out of the final image, keeping it lean.

---

## docker-compose.yml — Services

### `db` service
- Image: `postgres:16-alpine`
- Credentials via `.env`: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- Named volume `pgdata` for data persistence
- Healthcheck: `pg_isready` so `app` waits until Postgres is accepting connections

### `app` service
- Built from `Dockerfile`
- `depends_on: db` with `condition: service_healthy`
- `env_file: .env` — all secrets injected at runtime, never baked into the image
- Volume mounts:
  - `<your-resume-dir>:/data` — configurable bind mount; resume PDFs accessible at `/data/` inside the container
  - `./config:/app/config` — Hydra YAMLs mountable at runtime so config changes don't require a rebuild

---

## Environment / Config

The `.env` file drives all secrets and connection settings. One value differs between local and Docker:

| Key | Local value | Docker value |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | `db` |

All other keys are identical in both environments. The Hydra config reads `POSTGRES_HOST` via `${oc.env:POSTGRES_HOST,localhost}` — no code changes needed.

`.env.example` will be updated to document the Docker value alongside the local default.

---

## .dockerignore

Excludes: `.venv/`, `__pycache__/`, `*.pyc`, `.env`, `.git/`, `docs/`, `tests/`

---

## Testing the Setup

After building:

1. `docker compose up db -d` — Postgres starts healthy
2. `docker compose run --rm app python -c "import asyncpg; print('ok')"` — deps installed correctly
3. `docker compose run --rm app python cli.py --help` — CLI entry point reachable
