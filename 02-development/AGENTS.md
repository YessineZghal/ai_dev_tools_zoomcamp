# AGENTS.md

Guidance for AI coding agents (and humans) working in this folder.

## What this is

Flowboard: a shared Kanban board app. Read [`_docs/specs.md`](_docs/specs.md)
first — it is the source of truth for scope and behavior. If a request
conflicts with the spec, flag the conflict rather than silently picking one.

## Stack & conventions

- **Frontend** (`frontend/`): React + Vite + TypeScript. All backend calls
  go through a single API module (currently `src/api/`) — never call
  `fetch`/`axios` directly from a component. This is what lets the backend
  be mocked, then swapped for the real one, without touching UI code.
- **Backend** (`backend/`): Python + FastAPI, managed with `uv` (not pip
  directly). Endpoints are covered by `pytest` tests written *before* the
  implementation (TDD) — keep that order when adding new endpoints.
- **Database**: SQLAlchemy models, kept database-agnostic (no
  database-specific SQL). SQLite is the default engine for local
  dev/tests.
- **Contract**: `backend/openapi.yaml` is the source of truth for the API
  shape. Update it before changing endpoint signatures.

## Running things

See [`README.md`](README.md) for exact commands (`uv sync` /
`uv run fastapi dev app/main.py` for the backend, `npm install` / `npm run
dev` for the frontend, `uv run pytest` for tests).

## Workflow expectations

- Don't `git commit` or `git push` unless explicitly asked to in the
  session — leave changes in the working tree for review.
- Keep the mock backend and real backend behaviorally identical (same
  request/response shapes) so the frontend never needs to change when the
  backend underneath it changes.
- Prefer small, focused commits/changes over large sweeping ones when the
  user does ask for a commit.
