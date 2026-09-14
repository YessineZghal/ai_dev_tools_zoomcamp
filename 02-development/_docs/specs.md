# Flowboard — Product Spec

## Overview

Flowboard is a lightweight, shared Kanban board application for organizing
work into **boards → columns → cards**. There are no user accounts — anyone
who opens the app works against the same shared data, like a shared
whiteboard. Cards move between columns via drag-and-drop.

## Goals

- Let a user create boards to organize different projects or areas of work.
- Represent each board as a set of columns that stand for stages of work
  (e.g. To Do, In Progress, Done).
- Represent units of work as cards within columns; cards can be created,
  edited, deleted, and moved (including via drag-and-drop).
- Keep the interface fast, minimal, and pleasant to use.

## Non-goals (out of scope for this homework)

- User accounts / authentication / authorization.
- Multi-tenant workspaces or permissions.
- Real-time websocket sync (refresh / light polling is enough).
- File attachments, comments, or activity history.
- Structured assignees (a free-text label is enough, if included at all).

## Users & access

Single shared workspace, no login. Anyone with the URL can view and edit
every board. This intentionally matches the homework's demo scenario of two
browser windows seeing the same data.

## Core entities & data model

- **Board**: `id`, `name`, `created_at`
- **Column**: `id`, `board_id`, `name`, `position` (int, ordering), `created_at`
- **Card**: `id`, `column_id`, `title`, `description` (optional),
  `color_label` (optional, one of a fixed small palette), `position` (int,
  ordering within column), `created_at`, `updated_at`

Relationships: `Board 1—N Column 1—N Card`. Deleting a board cascades to its
columns and cards. Deleting a column cascades to its cards. Both deletions
require a confirmation step in the UI since they are destructive.

## Features (functional requirements)

1. **Boards list (home page)** — view all boards as tiles; create a new
   board (name only); rename a board; delete a board (with confirmation).
2. **Board view** — columns laid out left to right, each showing its cards.
3. **Column management** — add a column (name); rename a column; delete a
   column (with confirmation); reorder columns via drag-and-drop.
4. **Card management** — add a card to a column (title required,
   description and color optional); open a card to view/edit full details;
   delete a card; move a card via drag-and-drop, either reordering within a
   column or moving it to a different column.
5. **Empty states** — helpful messaging for: no boards yet, a board with no
   columns, a column with no cards.
6. **Persistence** — all changes persist across a page refresh (backed by a
   real database once the DB stage is complete).

## UX / interaction requirements

- Drag-and-drop feels responsive: optimistic UI update immediately, synced
  to the backend in the background, rolled back if the request fails.
- Clear affordances for draggable elements (grab cursor, drag preview,
  drop-target highlighting).
- Inline editing for quick renames (board/column names); a side panel or
  modal for full card details (title, description, color).
- Layout is responsive down to a typical laptop width; mobile support is a
  stretch goal, not required.
- Card color labels use a small fixed palette (gray, red, orange, yellow,
  green, blue, purple) shown as a small dot/bar on the card.

## API surface (high-level — formalized later as `openapi.yaml`)

- `GET /boards`, `POST /boards`
- `GET /boards/{id}`, `PATCH /boards/{id}`, `DELETE /boards/{id}`
- `POST /boards/{id}/columns`
- `PATCH /columns/{id}`, `DELETE /columns/{id}`, `PATCH /columns/{id}/reorder`
- `POST /columns/{id}/cards`
- `PATCH /cards/{id}`, `DELETE /cards/{id}`
- `PATCH /cards/{id}/move` (target column id + target position)

The frontend never calls these endpoints directly from components — every
call goes through a single API module so the mock/real backend can be
swapped in one place.

## Tech stack

- **Frontend**: React + Vite + TypeScript, `@dnd-kit` for drag-and-drop,
  plain CSS (no heavy component framework) for a clean, custom look.
- **Backend**: Python + FastAPI, managed with `uv`. Starts as an in-memory
  mock store; endpoints are covered by tests written before the
  implementation (TDD).
- **Database**: SQLite via SQLAlchemy. The app stays database-agnostic —
  swapping the SQLAlchemy engine URL should be the only change needed to
  point at a different database.
- **Contract**: `openapi.yaml`, written once the frontend prototype exists,
  becomes the source of truth the FastAPI backend is generated against.

## Success criteria

- A user can create a board, add columns, add cards, and drag cards across
  columns — all reflected instantly in the UI and still there after a
  refresh.
- Two browser windows open to the same board converge on the same data
  (via refresh or light polling — no websockets required).
- The backend has passing automated tests for every endpoint.
- Each stage works end-to-end before moving to the next: mocked frontend →
  real FastAPI backend (mock store) → real SQLite-backed database.

## Assumptions

- "Seeing another browser's change" is achieved via refresh or a light
  polling interval on the board view (e.g. every few seconds) — no
  websockets, per the homework's own demo guidance.
- Card `color_label` is one of a fixed 7-value enum (see palette above).
