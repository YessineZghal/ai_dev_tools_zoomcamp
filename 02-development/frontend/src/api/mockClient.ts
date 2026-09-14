import type { Api, Board, Column, Card, ColorLabel } from './types';

// In-memory mock "database" for the frontend prototype. Replaced by
// httpClient.ts once the real backend exists (Task 11 of the plan).

let boards: Board[] = [
  { id: 'b1', name: 'Personal', created_at: new Date().toISOString() },
];

let columns: Column[] = [
  { id: 'c1', board_id: 'b1', name: 'To Do', position: 0 },
  { id: 'c2', board_id: 'b1', name: 'In Progress', position: 1 },
  { id: 'c3', board_id: 'b1', name: 'Done', position: 2 },
];

let cards: Card[] = [
  {
    id: 'k1',
    column_id: 'c1',
    title: 'Write the spec',
    description: 'Capture the app scope in _docs/specs.md',
    color_label: 'blue',
    position: 0,
  },
  {
    id: 'k2',
    column_id: 'c1',
    title: 'Sketch the UI',
    description: null,
    color_label: 'purple',
    position: 1,
  },
  {
    id: 'k3',
    column_id: 'c2',
    title: 'Build the frontend prototype',
    description: 'React + Vite + mocked backend',
    color_label: 'yellow',
    position: 0,
  },
  {
    id: 'k4',
    column_id: 'c3',
    title: 'Pick a project idea',
    description: null,
    color_label: 'green',
    position: 0,
  },
];

const delay = <T,>(value: T): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), 150));

const uid = (): string => Math.random().toString(36).slice(2, 10);

function reindex(items: { position: number }[]): void {
  items.forEach((item, index) => {
    item.position = index;
  });
}

export const mockClient: Api = {
  listBoards: () => delay([...boards]),

  createBoard: (name) => {
    const board: Board = { id: uid(), name, created_at: new Date().toISOString() };
    boards.push(board);
    return delay(board);
  },

  renameBoard: (id, name) => {
    const board = boards.find((b) => b.id === id);
    if (!board) return Promise.reject(new Error('Board not found'));
    board.name = name;
    return delay(board);
  },

  deleteBoard: (id) => {
    const colIds = columns.filter((c) => c.board_id === id).map((c) => c.id);
    cards = cards.filter((k) => !colIds.includes(k.column_id));
    columns = columns.filter((c) => c.board_id !== id);
    boards = boards.filter((b) => b.id !== id);
    return delay(undefined);
  },

  getBoard: (id) => {
    const board = boards.find((b) => b.id === id);
    if (!board) return Promise.reject(new Error('Board not found'));
    const boardColumns = columns
      .filter((c) => c.board_id === id)
      .sort((a, b) => a.position - b.position);
    const columnIds = new Set(boardColumns.map((c) => c.id));
    const boardCards = cards.filter((k) => columnIds.has(k.column_id));
    return delay({ board, columns: boardColumns, cards: boardCards });
  },

  createColumn: (boardId, name) => {
    const position = columns.filter((c) => c.board_id === boardId).length;
    const column: Column = { id: uid(), board_id: boardId, name, position };
    columns.push(column);
    return delay(column);
  },

  renameColumn: (id, name) => {
    const column = columns.find((c) => c.id === id);
    if (!column) return Promise.reject(new Error('Column not found'));
    column.name = name;
    return delay(column);
  },

  deleteColumn: (id) => {
    cards = cards.filter((k) => k.column_id !== id);
    columns = columns.filter((c) => c.id !== id);
    return delay(undefined);
  },

  reorderColumns: (boardId, orderedIds) => {
    orderedIds.forEach((id, index) => {
      const column = columns.find((c) => c.id === id);
      if (column) column.position = index;
    });
    return delay(
      columns.filter((c) => c.board_id === boardId).sort((a, b) => a.position - b.position)
    );
  },

  createCard: (columnId, data) => {
    const position = cards.filter((k) => k.column_id === columnId).length;
    const card: Card = {
      id: uid(),
      column_id: columnId,
      title: data.title,
      description: data.description ?? null,
      color_label: (data.color_label as ColorLabel) ?? null,
      position,
    };
    cards.push(card);
    return delay(card);
  },

  updateCard: (id, data) => {
    const card = cards.find((k) => k.id === id);
    if (!card) return Promise.reject(new Error('Card not found'));
    Object.assign(card, data);
    return delay(card);
  },

  deleteCard: (id) => {
    cards = cards.filter((k) => k.id !== id);
    return delay(undefined);
  },

  moveCard: (id, targetColumnId, targetPosition) => {
    const card = cards.find((k) => k.id === id);
    if (!card) return Promise.reject(new Error('Card not found'));

    card.column_id = targetColumnId;
    const siblings = cards
      .filter((k) => k.column_id === targetColumnId && k.id !== id)
      .sort((a, b) => a.position - b.position);
    const clampedPosition = Math.max(0, Math.min(targetPosition, siblings.length));
    siblings.splice(clampedPosition, 0, card);
    reindex(siblings);
    return delay(card);
  },
};
