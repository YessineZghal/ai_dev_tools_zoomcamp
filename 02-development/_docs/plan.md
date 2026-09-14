# Flowboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Flowboard, a shared Kanban board app, end-to-end: a mocked
React frontend, then a FastAPI backend (TDD, mock store), wired together,
then backed by a real SQLite database via SQLAlchemy.

**Architecture:** React + Vite + TypeScript SPA talks to a FastAPI backend
over HTTP through one centralized API module (`frontend/src/api/`). The
backend exposes REST endpoints matching `backend/openapi.yaml`, starting
with an in-memory store and ending with a SQLAlchemy/SQLite-backed store
behind the same repository interface, so swapping storage never changes
the API contract or the frontend.

**Tech Stack:** React 18, Vite, TypeScript, `@dnd-kit`, `react-router-dom`;
Python, FastAPI, `uv`, Pydantic, `pytest`, SQLAlchemy, SQLite.

**Spec:** [`02-development/_docs/specs.md`](specs.md)

## Global Constraints

- No authentication; single shared workspace (spec: "Users & access").
- Frontend never calls the network directly from components — every call
  goes through the API module (spec: "API surface").
- Backend: mock in-memory store first; endpoints get `pytest` tests
  *before* implementation (spec: "Tech stack"; homework Q5).
- Database must stay swappable via SQLAlchemy engine URL — no
  database-specific SQL (spec: "Tech stack").
- Card `color_label` is one of: `gray, red, orange, yellow, green, blue,
  purple` (spec: "UX / interaction requirements").
- Do not run `git commit` / `git push` without the user explicitly asking
  in-session (AGENTS.md).

---

## Task 1: Frontend foundation — scaffold + types + mock API client

**Files:**
- Create: `frontend/` (via `npm create vite@latest frontend -- --template react-ts`)
- Create: `frontend/src/api/types.ts`
- Create: `frontend/src/api/mockClient.ts`
- Create: `frontend/src/api/index.ts`
- Test: manual (`npm run dev`, check console has no errors) — no automated
  frontend tests required by the spec; correctness here is verified by the
  UI tasks that consume this module.

**Interfaces:**
- Produces (used by every later frontend task):
  ```ts
  export type ColorLabel = 'gray'|'red'|'orange'|'yellow'|'green'|'blue'|'purple';
  export interface Board { id: string; name: string; created_at: string; }
  export interface Column { id: string; board_id: string; name: string; position: number; }
  export interface Card {
    id: string; column_id: string; title: string;
    description: string | null; color_label: ColorLabel | null; position: number;
  }
  export interface Api {
    listBoards(): Promise<Board[]>;
    createBoard(name: string): Promise<Board>;
    renameBoard(id: string, name: string): Promise<Board>;
    deleteBoard(id: string): Promise<void>;
    getBoard(id: string): Promise<{ board: Board; columns: Column[]; cards: Card[] }>;
    createColumn(boardId: string, name: string): Promise<Column>;
    renameColumn(id: string, name: string): Promise<Column>;
    deleteColumn(id: string): Promise<void>;
    reorderColumns(boardId: string, orderedIds: string[]): Promise<Column[]>;
    createCard(columnId: string, data: { title: string; description?: string; color_label?: ColorLabel }): Promise<Card>;
    updateCard(id: string, data: Partial<Pick<Card,'title'|'description'|'color_label'>>): Promise<Card>;
    deleteCard(id: string): Promise<void>;
    moveCard(id: string, targetColumnId: string, targetPosition: number): Promise<Card>;
  }
  export const api: Api; // from src/api/index.ts
  ```

- [ ] **Step 1: Scaffold the Vite project**

  Run: `cd 02-development && npm create vite@latest frontend -- --template react-ts`
  Then: `cd frontend && npm install`
  Expected: `frontend/` contains a runnable Vite React+TS app; `npm run dev`
  serves it on `http://localhost:5173`.

- [ ] **Step 2: Add `@dnd-kit` and `react-router-dom` dependencies**

  Run: `cd frontend && npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities react-router-dom`

- [ ] **Step 3: Write `src/api/types.ts`**

  Add the `ColorLabel`, `Board`, `Column`, `Card`, and `Api` type
  definitions exactly as listed in "Interfaces" above.

- [ ] **Step 4: Write `src/api/mockClient.ts`**

  In-memory implementation of `Api`. Key shape (fill in each method
  following this pattern — every method mutates the module-level arrays
  and resolves after a small artificial delay to mimic network latency):

  ```ts
  import { Api, Board, Column, Card, ColorLabel } from './types';

  let boards: Board[] = [
    { id: 'b1', name: 'Personal', created_at: new Date().toISOString() },
  ];
  let columns: Column[] = [
    { id: 'c1', board_id: 'b1', name: 'To Do', position: 0 },
    { id: 'c2', board_id: 'b1', name: 'In Progress', position: 1 },
    { id: 'c3', board_id: 'b1', name: 'Done', position: 2 },
  ];
  let cards: Card[] = [
    { id: 'k1', column_id: 'c1', title: 'Write the spec', description: null, color_label: 'blue', position: 0 },
  ];

  const delay = <T,>(value: T) => new Promise<T>(resolve => setTimeout(() => resolve(value), 150));
  const uid = () => Math.random().toString(36).slice(2, 10);

  export const mockClient: Api = {
    listBoards: () => delay([...boards]),
    createBoard: (name) => {
      const board: Board = { id: uid(), name, created_at: new Date().toISOString() };
      boards.push(board);
      return delay(board);
    },
    renameBoard: (id, name) => {
      const board = boards.find(b => b.id === id)!;
      board.name = name;
      return delay(board);
    },
    deleteBoard: (id) => {
      const colIds = columns.filter(c => c.board_id === id).map(c => c.id);
      cards = cards.filter(k => !colIds.includes(k.column_id));
      columns = columns.filter(c => c.board_id !== id);
      boards = boards.filter(b => b.id !== id);
      return delay(undefined);
    },
    getBoard: (id) => delay({
      board: boards.find(b => b.id === id)!,
      columns: columns.filter(c => c.board_id === id).sort((a, b) => a.position - b.position),
      cards: cards.filter(k => columns.some(c => c.board_id === id && c.id === k.column_id)),
    }),
    createColumn: (boardId, name) => {
      const position = columns.filter(c => c.board_id === boardId).length;
      const column: Column = { id: uid(), board_id: boardId, name, position };
      columns.push(column);
      return delay(column);
    },
    renameColumn: (id, name) => {
      const column = columns.find(c => c.id === id)!;
      column.name = name;
      return delay(column);
    },
    deleteColumn: (id) => {
      cards = cards.filter(k => k.column_id !== id);
      columns = columns.filter(c => c.id !== id);
      return delay(undefined);
    },
    reorderColumns: (boardId, orderedIds) => {
      orderedIds.forEach((id, index) => {
        const column = columns.find(c => c.id === id);
        if (column) column.position = index;
      });
      return delay(columns.filter(c => c.board_id === boardId).sort((a, b) => a.position - b.position));
    },
    createCard: (columnId, data) => {
      const position = cards.filter(k => k.column_id === columnId).length;
      const card: Card = {
        id: uid(), column_id: columnId, title: data.title,
        description: data.description ?? null, color_label: (data.color_label as ColorLabel) ?? null,
        position,
      };
      cards.push(card);
      return delay(card);
    },
    updateCard: (id, data) => {
      const card = cards.find(k => k.id === id)!;
      Object.assign(card, data);
      return delay(card);
    },
    deleteCard: (id) => {
      cards = cards.filter(k => k.id !== id);
      return delay(undefined);
    },
    moveCard: (id, targetColumnId, targetPosition) => {
      const card = cards.find(k => k.id === id)!;
      card.column_id = targetColumnId;
      const siblings = cards.filter(k => k.column_id === targetColumnId && k.id !== id)
        .sort((a, b) => a.position - b.position);
      siblings.splice(targetPosition, 0, card);
      siblings.forEach((k, index) => { k.position = index; });
      return delay(card);
    },
  };
  ```

- [ ] **Step 5: Write `src/api/index.ts`**

  ```ts
  import { mockClient } from './mockClient';
  import { Api } from './types';

  export * from './types';
  export const api: Api = mockClient; // swapped for the real client in Task 11
  ```

- [ ] **Step 6: Verify it compiles and runs**

  Run: `cd frontend && npm run dev`
  Expected: dev server starts with no TypeScript errors (Vite overlay
  clean); visiting `http://localhost:5173` still shows the default Vite
  template (UI is built in Task 2+).

- [ ] **Step 7: Commit reminder**

  Do not commit. Note the change for the end-of-session review.

---

## Task 2: Boards list page (home)

**Files:**
- Create: `frontend/src/pages/BoardsPage.tsx`
- Create: `frontend/src/components/BoardTile.tsx`
- Create: `frontend/src/components/NewBoardForm.tsx`
- Modify: `frontend/src/App.tsx` (router setup: `/` → `BoardsPage`, `/boards/:id` → placeholder for Task 3)
- Modify: `frontend/src/main.tsx` (wrap `App` in `BrowserRouter`)
- Create: `frontend/src/styles.css` (shared base styles: resets, color tokens, layout)

**Interfaces:**
- Consumes: `api.listBoards()`, `api.createBoard()`, `api.renameBoard()`, `api.deleteBoard()` from Task 1.
- Produces: route `/boards/:id` (consumed by Task 3), CSS custom properties for the palette (consumed by Task 3-5), e.g. `--color-accent`, `--color-danger`, `--space-1..4`.

- [ ] **Step 1: Add routing shell**

  In `main.tsx`, wrap `<App />` in `<BrowserRouter>`. In `App.tsx`, define
  `<Routes>` with `<Route path="/" element={<BoardsPage />} />` and a
  `<Route path="/boards/:id" element={<div>Board view (Task 3)</div>} />`.

- [ ] **Step 2: Implement `BoardsPage.tsx`**

  On mount, call `api.listBoards()` into state; show a loading state while
  pending. Render a grid of `BoardTile` for each board plus a
  `NewBoardForm`. Handle delete with a `window.confirm` before calling
  `api.deleteBoard`. Handle create by pushing the new board from
  `api.createBoard(name)` into local state (no full refetch).

- [ ] **Step 3: Implement `BoardTile.tsx`**

  Props: `{ board: Board; onRename: (name: string) => void; onDelete: () => void }`.
  Clicking the tile navigates (via `useNavigate`) to `/boards/${board.id}`.
  Rename is inline: a text field that appears on a small edit icon click,
  commits on blur/Enter.

- [ ] **Step 4: Implement `NewBoardForm.tsx`**

  A small form: text input + "Create board" button, disabled while the
  name is empty or a request is in flight.

- [ ] **Step 5: Manual verification**

  Run `npm run dev`. In the browser: create two boards, rename one,
  delete one, confirm the empty state message shows when zero boards
  remain, then create one more.

---

## Task 3: Board view — columns and cards (no drag-and-drop yet)

**Files:**
- Create: `frontend/src/pages/BoardPage.tsx`
- Create: `frontend/src/components/ColumnView.tsx`
- Create: `frontend/src/components/CardView.tsx`
- Create: `frontend/src/components/NewColumnForm.tsx`
- Create: `frontend/src/components/NewCardForm.tsx`
- Create: `frontend/src/components/CardDetailsPanel.tsx`
- Modify: `frontend/src/App.tsx` (point `/boards/:id` at `BoardPage`)

**Interfaces:**
- Consumes: `api.getBoard(id)`, `api.createColumn`, `api.renameColumn`,
  `api.deleteColumn`, `api.createCard`, `api.updateCard`, `api.deleteCard`
  from Task 1.
- Produces: `ColumnView` and `CardView` components with props
  `{ column: Column; cards: Card[]; ... }` and `{ card: Card; onOpen: () => void }`
  respectively — reused unmodified (only wrapped) by Task 4's drag-and-drop.

- [ ] **Step 1: Implement `BoardPage.tsx`**

  Read `id` from `useParams()`. On mount and whenever it changes, call
  `api.getBoard(id)` to load `{ board, columns, cards }` into state.
  Render the board name (editable inline, reusing the rename pattern from
  Task 2), a horizontally-scrollable row of `ColumnView` (one per column,
  sorted by `position`), and a `NewColumnForm` at the end of the row.

- [ ] **Step 2: Implement `ColumnView.tsx`**

  Renders the column name (inline-editable), a delete button (confirm
  before calling `api.deleteColumn`), the list of `CardView` for that
  column (sorted by `position`), and a `NewCardForm` pinned to the bottom.

- [ ] **Step 3: Implement `CardView.tsx`**

  Shows the card title and, if set, a small color swatch for
  `color_label`. Clicking anywhere on the card opens `CardDetailsPanel`.

- [ ] **Step 4: Implement `NewColumnForm.tsx` and `NewCardForm.tsx`**

  Same minimal-form pattern as `NewBoardForm` from Task 2: a text input
  plus a submit button/Enter-to-submit, calling `api.createColumn` /
  `api.createCard` and appending the result to local state.

- [ ] **Step 5: Implement `CardDetailsPanel.tsx`**

  A side panel (not a blocking modal) with fields for title, description
  (textarea), and a 7-swatch color picker for `color_label`. Saves via
  `api.updateCard` on close/blur; has a "Delete card" button that confirms
  then calls `api.deleteCard`.

- [ ] **Step 6: Manual verification**

  In the browser: open a board, add a column, add two cards to it, open a
  card and edit its title/description/color, delete a card, delete a
  column, confirm the "no columns yet" / "no cards yet" empty states
  render correctly.

---

## Task 4: Drag-and-drop for cards and columns

**Files:**
- Modify: `frontend/src/pages/BoardPage.tsx` (wrap in `DndContext`, handle `onDragEnd`)
- Modify: `frontend/src/components/ColumnView.tsx` (wrap card list in `SortableContext`, make column header a drag handle via `useSortable`)
- Modify: `frontend/src/components/CardView.tsx` (make draggable via `useSortable`)

**Interfaces:**
- Consumes: `api.moveCard(id, targetColumnId, targetPosition)`,
  `api.reorderColumns(boardId, orderedIds)` from Task 1.
- Produces: no new interfaces — this task only changes how existing state
  updates are triggered (drag events instead of button clicks).

- [ ] **Step 1: Wrap `BoardPage` content in `DndContext`**

  ```tsx
  import { DndContext, DragEndEvent, closestCenter } from '@dnd-kit/core';

  <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
    {/* columns row */}
  </DndContext>
  ```

- [ ] **Step 2: Make columns sortable (reordering the row)**

  Wrap the columns row in
  `<SortableContext items={columns.map(c => c.id)} strategy={horizontalListSortingStrategy}>`.
  In `ColumnView`, call `useSortable({ id: column.id })` and spread
  `attributes`/`listeners` onto the column header (the drag handle) and
  `style`/`transform`/`transition` onto the column's root element.

- [ ] **Step 3: Make cards sortable within and across columns**

  Wrap each column's card list in
  `<SortableContext items={cardsInColumn.map(k => k.id)} strategy={verticalListSortingStrategy}>`.
  In `CardView`, call `useSortable({ id: card.id, data: { columnId: card.column_id } })`
  and spread the same props onto the card root.

- [ ] **Step 4: Implement `handleDragEnd` with optimistic update + rollback**

  ```tsx
  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    if (isColumnDrag(active)) {
      const newOrder = reorderArray(columnIds, active.id, over.id);
      setColumns(applyOrder(columns, newOrder)); // optimistic
      api.reorderColumns(board.id, newOrder).catch(() => {
        setColumns(previousColumns); // rollback on failure
      });
      return;
    }

    const targetColumnId = resolveTargetColumn(over);
    const targetPosition = resolveTargetPosition(over, cards);
    const previousCards = cards;
    setCards(moveCardLocally(cards, active.id as string, targetColumnId, targetPosition)); // optimistic
    api.moveCard(active.id as string, targetColumnId, targetPosition).catch(() => {
      setCards(previousCards); // rollback on failure
    });
  }
  ```

  Implement the small helpers (`isColumnDrag`, `reorderArray`,
  `applyOrder`, `resolveTargetColumn`, `resolveTargetPosition`,
  `moveCardLocally`) as plain functions in the same file — each is a
  short array manipulation over the `columns`/`cards` state already held
  by `BoardPage`.

- [ ] **Step 5: Manual verification**

  In the browser: drag a card to a different position within its column,
  drag a card into a different column, drag a column to reorder it.
  Confirm the UI updates immediately and a page refresh preserves the new
  order (state lives in `mockClient` module scope, so it survives a
  refresh within the same dev-server session, but not a full reload of
  the JS bundle — note this is expected until Task 11 connects a real
  backend process).

---

## Task 5: Polish pass — empty states, loading/error states, responsive layout

**Files:**
- Modify: `frontend/src/styles.css` (design tokens, responsive breakpoints)
- Modify: `frontend/src/pages/BoardsPage.tsx`, `frontend/src/pages/BoardPage.tsx` (loading/error/empty states)
- Create: `frontend/src/components/EmptyState.tsx`

**Interfaces:**
- Produces: `EmptyState` component with props `{ title: string; hint?: string }`, reused by both pages.

- [ ] **Step 1: Add a small shared design-token base to `styles.css`**

  Define CSS custom properties for spacing, radius, and the 7-color card
  palette (matching the spec's list exactly:
  gray/red/orange/yellow/green/blue/purple), plus light/dark-friendly
  neutral background/text colors.

- [ ] **Step 2: Implement `EmptyState.tsx` and use it in both pages**

  `BoardsPage`: "No boards yet" + "Create your first board above." when
  `boards.length === 0`. `BoardPage`: "No columns yet" when
  `columns.length === 0`; each `ColumnView` shows "No cards yet" when its
  card list is empty.

- [ ] **Step 3: Add loading and error states**

  While the initial `api.listBoards()` / `api.getBoard()` call is
  pending, show a simple loading placeholder instead of an empty list
  (avoids a flash of the empty state). If the call rejects, show an
  inline error message with a "Retry" button that re-runs the fetch.

- [ ] **Step 4: Responsive layout pass**

  Ensure the boards grid wraps at narrow widths and the columns row
  scrolls horizontally with visible scroll affordance rather than
  overflowing the page, down to ~1024px wide.

- [ ] **Step 5: Manual verification**

  Resize the browser window narrow and wide; delete all boards to see the
  empty state; use browser devtools to throttle network and confirm the
  loading state is visible before data appears.

---

## Task 6: OpenAPI contract

**Files:**
- Create: `backend/openapi.yaml`

**Interfaces:**
- Produces: the REST contract every backend task (7-10) implements against,
  and that Task 11 points the real frontend client at.

- [ ] **Step 1: Write `backend/openapi.yaml`**

  Author an OpenAPI 3.0 document with paths and schemas matching the
  spec's "API surface" section and the frontend's `Api` type from Task 1
  one-to-one: `Board`, `Column`, `Card` schemas (matching the TS
  interfaces' fields exactly, snake_case as already used); paths
  `GET/POST /boards`, `GET/PATCH/DELETE /boards/{board_id}`,
  `GET /boards/{board_id}` returning `{ board, columns, cards }`,
  `POST /boards/{board_id}/columns`, `PATCH/DELETE /columns/{column_id}`,
  `PATCH /columns/{column_id}/reorder` (body: `{ ordered_ids: string[] }`),
  `POST /columns/{column_id}/cards`, `PATCH/DELETE /cards/{card_id}`,
  `PATCH /cards/{card_id}/move` (body: `{ target_column_id: string, target_position: int }`).

- [ ] **Step 2: Sanity-check the document**

  Run: `npx @redocly/cli lint backend/openapi.yaml` (via `npx`, no
  install needed)
  Expected: no errors (warnings about missing `info.description` etc. are
  fine to leave).

---

## Task 7: Backend foundation — uv + FastAPI scaffold, schemas, in-memory store

**Files:**
- Create: `backend/pyproject.toml` (via `uv init`)
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/schemas.py`
- Create: `backend/app/store.py`
- Test: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `app.store.Store` — the in-memory repository class every
  endpoint task (8-10) reads/writes through, and the interface Task 12's
  SQLAlchemy-backed store must also satisfy:
  ```python
  class Store:
      def list_boards(self) -> list[Board]: ...
      def create_board(self, name: str) -> Board: ...
      def get_board(self, board_id: str) -> Board | None: ...
      def rename_board(self, board_id: str, name: str) -> Board | None: ...
      def delete_board(self, board_id: str) -> bool: ...
      def list_columns(self, board_id: str) -> list[Column]: ...
      def list_cards_for_board(self, board_id: str) -> list[Card]: ...
      def create_column(self, board_id: str, name: str) -> Column: ...
      def rename_column(self, column_id: str, name: str) -> Column | None: ...
      def delete_column(self, column_id: str) -> bool: ...
      def reorder_columns(self, board_id: str, ordered_ids: list[str]) -> list[Column]: ...
      def create_card(self, column_id: str, title: str, description: str | None, color_label: str | None) -> Card: ...
      def update_card(self, card_id: str, **fields) -> Card | None: ...
      def delete_card(self, card_id: str) -> bool: ...
      def move_card(self, card_id: str, target_column_id: str, target_position: int) -> Card | None: ...
  ```
  `app.main.app` — the FastAPI instance later tasks add routes to.

- [ ] **Step 1: Initialize the uv project**

  Run: `cd 02-development && uv init backend --package`
  Run: `cd backend && uv add fastapi 'uvicorn[standard]' pydantic`
  Run: `uv add --dev pytest httpx`

- [ ] **Step 2: Write the failing health-check test**

  ```python
  # backend/tests/test_health.py
  from fastapi.testclient import TestClient
  from app.main import app

  client = TestClient(app)

  def test_health_check_returns_ok():
      response = client.get("/health")
      assert response.status_code == 200
      assert response.json() == {"status": "ok"}
  ```

- [ ] **Step 3: Run it and confirm it fails**

  Run: `uv run pytest tests/test_health.py -v`
  Expected: FAIL (import error — `app.main` doesn't exist yet).

- [ ] **Step 4: Write `app/schemas.py` (Pydantic models matching openapi.yaml)**

  Define `Board`, `Column`, `Card` (response models) and
  `BoardCreate`, `BoardUpdate`, `ColumnCreate`, `ColumnUpdate`,
  `ColumnReorder`, `CardCreate`, `CardUpdate`, `CardMove` (request
  models) with fields matching Task 6's `openapi.yaml` exactly.

- [ ] **Step 5: Write `app/store.py` (in-memory `Store` implementation)**

  Implement the `Store` class from "Interfaces" above using
  module-private lists/dicts and `uuid4().hex` ids, seeded empty (no
  demo data — unlike the frontend mock, the real backend starts clean).

- [ ] **Step 6: Write `app/main.py` with CORS and the health endpoint**

  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.store import Store

  app = FastAPI(title="Flowboard API")
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:5173"],
      allow_methods=["*"],
      allow_headers=["*"],
  )
  store = Store()

  @app.get("/health")
  def health_check():
      return {"status": "ok"}
  ```

- [ ] **Step 7: Run the test again and confirm it passes**

  Run: `uv run pytest tests/test_health.py -v`
  Expected: PASS.

- [ ] **Step 8: Verify the dev server boots**

  Run: `uv run fastapi dev app/main.py`
  Expected: server starts on `http://127.0.0.1:8000`; `/docs` loads
  Swagger UI; `/health` returns `{"status": "ok"}`.

---

## Task 8: Backend — Boards endpoints (TDD)

**Files:**
- Create: `backend/tests/test_boards.py`
- Modify: `backend/app/main.py` (add board routes)

**Interfaces:**
- Consumes: `Store` methods `list_boards`, `create_board`, `get_board`,
  `rename_board`, `delete_board`, `list_columns`, `list_cards_for_board`
  from Task 7.

- [ ] **Step 1: Write the failing tests**

  ```python
  # backend/tests/test_boards.py
  from fastapi.testclient import TestClient
  from app.main import app

  client = TestClient(app)

  def test_create_and_list_boards():
      response = client.post("/boards", json={"name": "Personal"})
      assert response.status_code == 201
      board = response.json()
      assert board["name"] == "Personal"
      assert "id" in board

      response = client.get("/boards")
      assert response.status_code == 200
      assert any(b["id"] == board["id"] for b in response.json())

  def test_get_board_returns_columns_and_cards():
      board = client.post("/boards", json={"name": "Work"}).json()
      response = client.get(f"/boards/{board['id']}")
      assert response.status_code == 200
      body = response.json()
      assert body["board"]["id"] == board["id"]
      assert body["columns"] == []
      assert body["cards"] == []

  def test_get_missing_board_returns_404():
      response = client.get("/boards/does-not-exist")
      assert response.status_code == 404

  def test_rename_board():
      board = client.post("/boards", json={"name": "Old name"}).json()
      response = client.patch(f"/boards/{board['id']}", json={"name": "New name"})
      assert response.status_code == 200
      assert response.json()["name"] == "New name"

  def test_delete_board():
      board = client.post("/boards", json={"name": "Temp"}).json()
      response = client.delete(f"/boards/{board['id']}")
      assert response.status_code == 204
      assert client.get(f"/boards/{board['id']}").status_code == 404
  ```

- [ ] **Step 2: Run and confirm all fail**

  Run: `uv run pytest tests/test_boards.py -v`
  Expected: FAIL (404 "Not Found" from FastAPI's default router — routes
  don't exist yet).

- [ ] **Step 3: Implement the routes in `app/main.py`**

  ```python
  from fastapi import HTTPException
  from app.schemas import Board, BoardCreate, BoardUpdate, BoardDetail

  @app.get("/boards", response_model=list[Board])
  def list_boards():
      return store.list_boards()

  @app.post("/boards", response_model=Board, status_code=201)
  def create_board(payload: BoardCreate):
      return store.create_board(payload.name)

  @app.get("/boards/{board_id}", response_model=BoardDetail)
  def get_board(board_id: str):
      board = store.get_board(board_id)
      if board is None:
          raise HTTPException(status_code=404, detail="Board not found")
      return BoardDetail(
          board=board,
          columns=store.list_columns(board_id),
          cards=store.list_cards_for_board(board_id),
      )

  @app.patch("/boards/{board_id}", response_model=Board)
  def rename_board(board_id: str, payload: BoardUpdate):
      board = store.rename_board(board_id, payload.name)
      if board is None:
          raise HTTPException(status_code=404, detail="Board not found")
      return board

  @app.delete("/boards/{board_id}", status_code=204)
  def delete_board(board_id: str):
      if not store.delete_board(board_id):
          raise HTTPException(status_code=404, detail="Board not found")
  ```

  Add the corresponding `BoardDetail` schema (`board: Board`,
  `columns: list[Column]`, `cards: list[Card]`) to `app/schemas.py`.

- [ ] **Step 4: Run and confirm all pass**

  Run: `uv run pytest tests/test_boards.py -v`
  Expected: PASS (5 tests).

---

## Task 9: Backend — Columns endpoints (TDD)

**Files:**
- Create: `backend/tests/test_columns.py`
- Modify: `backend/app/main.py` (add column routes)

**Interfaces:**
- Consumes: `Store` methods `create_column`, `rename_column`,
  `delete_column`, `reorder_columns` from Task 7.

- [ ] **Step 1: Write the failing tests**

  ```python
  # backend/tests/test_columns.py
  from fastapi.testclient import TestClient
  from app.main import app

  client = TestClient(app)

  def _make_board():
      return client.post("/boards", json={"name": "Board"}).json()

  def test_create_column():
      board = _make_board()
      response = client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"})
      assert response.status_code == 201
      column = response.json()
      assert column["name"] == "To Do"
      assert column["board_id"] == board["id"]
      assert column["position"] == 0

  def test_second_column_gets_next_position():
      board = _make_board()
      client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"})
      response = client.post(f"/boards/{board['id']}/columns", json={"name": "Done"})
      assert response.json()["position"] == 1

  def test_rename_and_delete_column():
      board = _make_board()
      column = client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"}).json()

      renamed = client.patch(f"/columns/{column['id']}", json={"name": "Doing"})
      assert renamed.status_code == 200
      assert renamed.json()["name"] == "Doing"

      deleted = client.delete(f"/columns/{column['id']}")
      assert deleted.status_code == 204

  def test_reorder_columns():
      board = _make_board()
      first = client.post(f"/boards/{board['id']}/columns", json={"name": "A"}).json()
      second = client.post(f"/boards/{board['id']}/columns", json={"name": "B"}).json()

      response = client.patch(
          f"/columns/{first['id']}/reorder",
          json={"ordered_ids": [second["id"], first["id"]]},
      )
      assert response.status_code == 200
      by_id = {c["id"]: c["position"] for c in response.json()}
      assert by_id[second["id"]] == 0
      assert by_id[first["id"]] == 1
  ```

  Note: the reorder route lives at `/columns/{column_id}/reorder` for URL
  symmetry with the other column routes, but its body carries the full
  `ordered_ids` list for the board — `column_id` in the path is not used
  by the handler beyond routing convention. (This matches `openapi.yaml`
  from Task 6.)

- [ ] **Step 2: Run and confirm all fail**

  Run: `uv run pytest tests/test_columns.py -v`
  Expected: FAIL (404s — routes don't exist yet).

- [ ] **Step 3: Implement the routes in `app/main.py`**

  ```python
  from app.schemas import Column, ColumnCreate, ColumnUpdate, ColumnReorder

  @app.post("/boards/{board_id}/columns", response_model=Column, status_code=201)
  def create_column(board_id: str, payload: ColumnCreate):
      if store.get_board(board_id) is None:
          raise HTTPException(status_code=404, detail="Board not found")
      return store.create_column(board_id, payload.name)

  @app.patch("/columns/{column_id}", response_model=Column)
  def rename_column(column_id: str, payload: ColumnUpdate):
      column = store.rename_column(column_id, payload.name)
      if column is None:
          raise HTTPException(status_code=404, detail="Column not found")
      return column

  @app.delete("/columns/{column_id}", status_code=204)
  def delete_column(column_id: str):
      if not store.delete_column(column_id):
          raise HTTPException(status_code=404, detail="Column not found")

  @app.patch("/columns/{column_id}/reorder", response_model=list[Column])
  def reorder_columns(column_id: str, payload: ColumnReorder):
      column = store.get_column(column_id)
      if column is None:
          raise HTTPException(status_code=404, detail="Column not found")
      return store.reorder_columns(column.board_id, payload.ordered_ids)
  ```

  Add a `get_column(self, column_id: str) -> Column | None` method to
  `Store` (Task 7's class) if not already present — needed here to look
  up `board_id` from a `column_id`.

- [ ] **Step 4: Run and confirm all pass**

  Run: `uv run pytest tests/test_columns.py -v`
  Expected: PASS (4 tests).

---

## Task 10: Backend — Cards endpoints (TDD)

**Files:**
- Create: `backend/tests/test_cards.py`
- Modify: `backend/app/main.py` (add card routes)

**Interfaces:**
- Consumes: `Store` methods `create_card`, `update_card`, `delete_card`,
  `move_card` from Task 7.

- [ ] **Step 1: Write the failing tests**

  ```python
  # backend/tests/test_cards.py
  from fastapi.testclient import TestClient
  from app.main import app

  client = TestClient(app)

  def _make_column():
      board = client.post("/boards", json={"name": "Board"}).json()
      return client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"}).json()

  def test_create_card():
      column = _make_column()
      response = client.post(
          f"/columns/{column['id']}/cards",
          json={"title": "Write tests", "description": None, "color_label": "blue"},
      )
      assert response.status_code == 201
      card = response.json()
      assert card["title"] == "Write tests"
      assert card["column_id"] == column["id"]
      assert card["position"] == 0

  def test_update_card():
      column = _make_column()
      card = client.post(f"/columns/{column['id']}/cards", json={"title": "Draft"}).json()
      response = client.patch(f"/cards/{card['id']}", json={"title": "Final", "color_label": "green"})
      assert response.status_code == 200
      body = response.json()
      assert body["title"] == "Final"
      assert body["color_label"] == "green"

  def test_delete_card():
      column = _make_column()
      card = client.post(f"/columns/{column['id']}/cards", json={"title": "Temp"}).json()
      response = client.delete(f"/cards/{card['id']}")
      assert response.status_code == 204

  def test_move_card_to_another_column():
      column_a = _make_column()
      board_id = column_a["board_id"]
      column_b = client.post(f"/boards/{board_id}/columns", json={"name": "Done"}).json()
      card = client.post(f"/columns/{column_a['id']}/cards", json={"title": "Ship it"}).json()

      response = client.patch(
          f"/cards/{card['id']}/move",
          json={"target_column_id": column_b["id"], "target_position": 0},
      )
      assert response.status_code == 200
      assert response.json()["column_id"] == column_b["id"]

  def test_create_card_requires_title():
      column = _make_column()
      response = client.post(f"/columns/{column['id']}/cards", json={"title": ""})
      assert response.status_code == 422
  ```

- [ ] **Step 2: Run and confirm all fail**

  Run: `uv run pytest tests/test_cards.py -v`
  Expected: FAIL (404s — routes don't exist yet).

- [ ] **Step 3: Implement the routes in `app/main.py`, add title validation**

  ```python
  from pydantic import Field
  from app.schemas import Card, CardCreate, CardUpdate, CardMove

  @app.post("/columns/{column_id}/cards", response_model=Card, status_code=201)
  def create_card(column_id: str, payload: CardCreate):
      if store.get_column(column_id) is None:
          raise HTTPException(status_code=404, detail="Column not found")
      return store.create_card(column_id, payload.title, payload.description, payload.color_label)

  @app.patch("/cards/{card_id}", response_model=Card)
  def update_card(card_id: str, payload: CardUpdate):
      card = store.update_card(card_id, **payload.model_dump(exclude_unset=True))
      if card is None:
          raise HTTPException(status_code=404, detail="Card not found")
      return card

  @app.delete("/cards/{card_id}", status_code=204)
  def delete_card(card_id: str):
      if not store.delete_card(card_id):
          raise HTTPException(status_code=404, detail="Card not found")

  @app.patch("/cards/{card_id}/move", response_model=Card)
  def move_card(card_id: str, payload: CardMove):
      card = store.move_card(card_id, payload.target_column_id, payload.target_position)
      if card is None:
          raise HTTPException(status_code=404, detail="Card not found")
      return card
  ```

  In `app/schemas.py`, give `CardCreate.title` the constraint
  `title: str = Field(min_length=1)` so an empty title returns FastAPI's
  standard 422 validation error (this is what `test_create_card_requires_title` checks).

- [ ] **Step 4: Run and confirm all pass**

  Run: `uv run pytest tests/test_cards.py -v`
  Expected: PASS (5 tests).

- [ ] **Step 5: Run the full backend test suite**

  Run: `uv run pytest -v`
  Expected: all tests across `test_health.py`, `test_boards.py`,
  `test_columns.py`, `test_cards.py` pass.

---

## Task 11: Connect frontend to the real backend

**Files:**
- Create: `frontend/src/api/httpClient.ts`
- Create: `frontend/.env` (`VITE_API_BASE_URL=http://127.0.0.1:8000`)
- Modify: `frontend/src/api/index.ts` (select `httpClient` instead of `mockClient`)

**Interfaces:**
- Consumes: `backend/openapi.yaml` paths (Tasks 6, 8-10) and the frontend's
  own `Api` type (Task 1) — `httpClient` implements the same `Api`
  interface as `mockClient`, so no UI code changes.

- [ ] **Step 1: Write `httpClient.ts` implementing `Api` over `fetch`**

  ```ts
  import { Api, Board, Column, Card } from './types';

  const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    });
    if (!response.ok) throw new Error(`Request failed: ${response.status} ${path}`);
    if (response.status === 204) return undefined as T;
    return response.json();
  }

  export const httpClient: Api = {
    listBoards: () => request('/boards'),
    createBoard: (name) => request('/boards', { method: 'POST', body: JSON.stringify({ name }) }),
    renameBoard: (id, name) => request(`/boards/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
    deleteBoard: (id) => request(`/boards/${id}`, { method: 'DELETE' }),
    getBoard: (id) => request(`/boards/${id}`),
    createColumn: (boardId, name) => request(`/boards/${boardId}/columns`, { method: 'POST', body: JSON.stringify({ name }) }),
    renameColumn: (id, name) => request(`/columns/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
    deleteColumn: (id) => request(`/columns/${id}`, { method: 'DELETE' }),
    reorderColumns: (_boardId, orderedIds) => request(`/columns/${orderedIds[0]}/reorder`, { method: 'PATCH', body: JSON.stringify({ ordered_ids: orderedIds }) }),
    createCard: (columnId, data) => request(`/columns/${columnId}/cards`, { method: 'POST', body: JSON.stringify(data) }),
    updateCard: (id, data) => request(`/cards/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    deleteCard: (id) => request(`/cards/${id}`, { method: 'DELETE' }),
    moveCard: (id, targetColumnId, targetPosition) => request(`/cards/${id}/move`, { method: 'PATCH', body: JSON.stringify({ target_column_id: targetColumnId, target_position: targetPosition }) }),
  };
  ```

- [ ] **Step 2: Swap the exported client**

  In `src/api/index.ts`, change the export to
  `export const api: Api = httpClient;` (delete or comment out the
  `mockClient` import — keep `mockClient.ts` in the repo as a reference/
  fallback, per the spec's "centralize and mock" requirement).

- [ ] **Step 3: Start both servers**

  Run: `cd backend && uv run fastapi dev app/main.py` (terminal 1)
  Run: `cd frontend && npm run dev` (terminal 2)

- [ ] **Step 4: Manual + browser verification**

  Open `http://localhost:5173` in the browser. Create a board, add
  columns/cards, drag a card. Check the Network tab (or backend terminal
  log) to confirm requests hit `http://127.0.0.1:8000`. Refresh the page
  and confirm the data is still there (now persisted in the backend
  process, not just the frontend module). Open a second browser tab to
  the same URL and confirm it shows the same board after a refresh.

- [ ] **Step 5: Fix CORS or shape mismatches if they appear**

  If the browser console shows a CORS error, confirm
  `allow_origins` in `app/main.py` includes `http://localhost:5173`. If a
  response shape mismatch appears (e.g. a field name typo between
  `openapi.yaml` and `httpClient.ts`), fix the client to match the
  backend's actual response, then re-verify.

---

## Task 12: Real database — SQLAlchemy + SQLite

**Files:**
- Create: `backend/app/db.py`
- Create: `backend/app/models.py`
- Create: `backend/app/sql_store.py`
- Modify: `backend/app/main.py` (use `SqlStore` instead of the in-memory `Store`)
- Modify: `backend/tests/test_health.py`, `test_boards.py`, `test_columns.py`, `test_cards.py` (use a per-test database)
- Create: `backend/tests/conftest.py`

**Interfaces:**
- Produces: `SqlStore`, a drop-in implementation of the same `Store`
  interface from Task 7 — every method signature listed there is
  reimplemented against a SQLAlchemy session, so `app/main.py`'s route
  handlers do not change.

- [ ] **Step 1: Add SQLAlchemy dependency**

  Run: `cd backend && uv add sqlalchemy`

- [ ] **Step 2: Write `app/db.py` (engine/session factory, swappable URL)**

  ```python
  import os
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker, declarative_base

  DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./flowboard.db")
  connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
  engine = create_engine(DATABASE_URL, connect_args=connect_args)
  SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
  Base = declarative_base()
  ```

- [ ] **Step 3: Write `app/models.py` (ORM models)**

  ```python
  import uuid
  from sqlalchemy import Column as SAColumn, String, Integer, ForeignKey, DateTime
  from sqlalchemy.orm import relationship
  from sqlalchemy.sql import func
  from app.db import Base

  def _id():
      return uuid.uuid4().hex

  class BoardModel(Base):
      __tablename__ = "boards"
      id = SAColumn(String, primary_key=True, default=_id)
      name = SAColumn(String, nullable=False)
      created_at = SAColumn(DateTime(timezone=True), server_default=func.now())
      columns = relationship("ColumnModel", cascade="all, delete-orphan", back_populates="board")

  class ColumnModel(Base):
      __tablename__ = "columns"
      id = SAColumn(String, primary_key=True, default=_id)
      board_id = SAColumn(String, ForeignKey("boards.id"), nullable=False)
      name = SAColumn(String, nullable=False)
      position = SAColumn(Integer, nullable=False, default=0)
      board = relationship("BoardModel", back_populates="columns")
      cards = relationship("CardModel", cascade="all, delete-orphan", back_populates="column")

  class CardModel(Base):
      __tablename__ = "cards"
      id = SAColumn(String, primary_key=True, default=_id)
      column_id = SAColumn(String, ForeignKey("columns.id"), nullable=False)
      title = SAColumn(String, nullable=False)
      description = SAColumn(String, nullable=True)
      color_label = SAColumn(String, nullable=True)
      position = SAColumn(Integer, nullable=False, default=0)
      column = relationship("ColumnModel", back_populates="cards")
  ```

- [ ] **Step 4: Write `app/sql_store.py` implementing the `Store` interface**

  Same method set as Task 7's `Store`, each method opening a session from
  `SessionLocal`, operating on the ORM models, and mapping results back
  to the `app.schemas` Pydantic types (e.g. `Board.model_validate(row,
  from_attributes=True)`). `move_card` and `reorder_columns` reuse the
  exact same position-shifting logic already written for the in-memory
  `Store` (Task 7), just reading/writing rows instead of list items —
  port that logic rather than redesigning it.

- [ ] **Step 5: Write `tests/conftest.py` for a per-test database**

  ```python
  import pytest
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  from app.db import Base
  import app.main as main_module
  from app.sql_store import SqlStore

  @pytest.fixture(autouse=True)
  def isolated_db(monkeypatch):
      engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
      Base.metadata.create_all(engine)
      TestSession = sessionmaker(bind=engine)
      monkeypatch.setattr(main_module, "store", SqlStore(TestSession))
      yield
  ```

  This swaps `app.main.store` for a fresh in-memory-SQLite-backed
  `SqlStore` before every test, so each test starts from a clean
  database and the existing `test_boards.py` / `test_columns.py` /
  `test_cards.py` files (Tasks 8-10) need no changes beyond this fixture.

- [ ] **Step 6: Point `app/main.py` at `SqlStore` for real runs**

  ```python
  from app.db import SessionLocal, engine, Base
  from app.sql_store import SqlStore

  Base.metadata.create_all(engine)
  store = SqlStore(SessionLocal)
  ```

- [ ] **Step 7: Run the full test suite and confirm everything still passes**

  Run: `uv run pytest -v`
  Expected: same tests as Task 10 Step 5, all passing, now running
  against `SqlStore` via the `conftest.py` fixture instead of the
  in-memory `Store`.

- [ ] **Step 8: Add a cascade-delete regression test**

  ```python
  # backend/tests/test_cascade_delete.py
  from fastapi.testclient import TestClient
  from app.main import app

  client = TestClient(app)

  def test_deleting_board_cascades_to_columns_and_cards():
      board = client.post("/boards", json={"name": "Temp"}).json()
      column = client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"}).json()
      client.post(f"/columns/{column['id']}/cards", json={"title": "Card"})

      client.delete(f"/boards/{board['id']}")

      assert client.patch(f"/columns/{column['id']}", json={"name": "x"}).status_code == 404
  ```

  Run: `uv run pytest tests/test_cascade_delete.py -v`
  Expected: PASS — confirms the SQLAlchemy `cascade="all, delete-orphan"`
  relationships from Step 3 actually delete dependent rows.

- [ ] **Step 9: Verify the real (non-test) database file works end-to-end**

  Run: `rm -f backend/flowboard.db && cd backend && uv run fastapi dev app/main.py`
  In the browser (frontend still running from Task 11): create a board,
  add data, then stop and restart the backend process. Refresh the
  frontend and confirm the data is still there (proves it's reading from
  `flowboard.db`, not memory).

---

## Task 13: Final verification and docs update

**Files:**
- Modify: `02-development/README.md` (status section)

**Interfaces:** none — this task only verifies and documents prior work.

- [ ] **Step 1: Run the full backend test suite one more time**

  Run: `cd backend && uv run pytest -v`
  Expected: all tests pass.

- [ ] **Step 2: Two-browser end-to-end check**

  With both servers running, open the same board in two separate browser
  windows. In window A, add a card. In window B, refresh and confirm the
  new card appears. In window A, refresh the whole page and confirm
  nothing is lost.

- [ ] **Step 3: Update the README status section**

  Replace the "Status" section placeholder in `02-development/README.md`
  with a short summary: frontend prototype done, backend done (list test
  count), connected, SQLite database in place — plus the exact commands
  to run each part (already documented above it) so the file is
  submission-ready.

- [ ] **Step 4: Do not commit**

  Leave everything in the working tree. Ask the user whether to stage,
  commit, and push before touching git, per `AGENTS.md`.
