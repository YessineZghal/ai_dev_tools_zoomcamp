# Flowboard

A lightweight, shared Kanban board app — boards, columns, and cards, with
drag-and-drop. No login: everyone who opens the app shares the same data.

Built for Homework 2 of the [AI Dev Tools Zoomcamp](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/).

- Full spec: [`_docs/specs.md`](_docs/specs.md)
- Agent/contributor guide: [`AGENTS.md`](AGENTS.md)

## Project layout

```
02-development/
├── _docs/specs.md   # product spec
├── frontend/        # React + Vite + TypeScript UI
├── backend/         # FastAPI backend (uv-managed)
├── AGENTS.md
└── README.md
```

## Running it

### Backend

```bash
cd backend
uv sync
uv run fastapi dev app/main.py
```

The API serves at `http://127.0.0.1:8000` (interactive docs at `/docs`).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app serves at `http://localhost:5173` and talks to the backend above.

### Tests

```bash
cd backend
uv run pytest
```

## Status

All stages complete:

- ✅ Frontend prototype (React + Vite + TypeScript, `@dnd-kit` drag-and-drop,
  mocked backend centralized in `frontend/src/api/`)
- ✅ Backend (FastAPI + `uv`, 19 passing `pytest` tests, TDD)
- ✅ Frontend wired to the real backend (`frontend/src/api/httpClient.ts`,
  `VITE_API_BASE_URL`)
- ✅ Real database (SQLite via SQLAlchemy, `backend/app/sql_store.py`),
  database-agnostic via `DATABASE_URL`
- ✅ Professional visual design pass: refined color/typography system with
  light & dark mode (toggle in the header), Lucide icons, floating
  drag preview, skeleton loading states, kebab menus, reveal-to-add forms,
  and a modal for creating boards

Verified manually: create/rename/delete boards, columns, and cards;
drag-and-drop within and across columns; card detail editing; two browser
windows on the same board converge after a refresh; data survives a full
backend process restart (reads from `flowboard.db`, not memory).

Note: if port 8000 is already in use on your machine, run the backend with
`uv run fastapi dev app/main.py --port <free-port>` and set
`VITE_API_BASE_URL` in `frontend/.env` to match.
