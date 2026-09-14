export type ColorLabel =
  | 'gray'
  | 'red'
  | 'orange'
  | 'yellow'
  | 'green'
  | 'blue'
  | 'purple';

export const COLOR_LABELS: ColorLabel[] = [
  'gray',
  'red',
  'orange',
  'yellow',
  'green',
  'blue',
  'purple',
];

export interface Board {
  id: string;
  name: string;
  created_at: string;
}

export interface Column {
  id: string;
  board_id: string;
  name: string;
  position: number;
}

export interface Card {
  id: string;
  column_id: string;
  title: string;
  description: string | null;
  color_label: ColorLabel | null;
  position: number;
}

export interface BoardDetail {
  board: Board;
  columns: Column[];
  cards: Card[];
}

export interface Api {
  listBoards(): Promise<Board[]>;
  createBoard(name: string): Promise<Board>;
  renameBoard(id: string, name: string): Promise<Board>;
  deleteBoard(id: string): Promise<void>;
  getBoard(id: string): Promise<BoardDetail>;
  createColumn(boardId: string, name: string): Promise<Column>;
  renameColumn(id: string, name: string): Promise<Column>;
  deleteColumn(id: string): Promise<void>;
  reorderColumns(boardId: string, orderedIds: string[]): Promise<Column[]>;
  createCard(
    columnId: string,
    data: { title: string; description?: string | null; color_label?: ColorLabel | null }
  ): Promise<Card>;
  updateCard(
    id: string,
    data: Partial<Pick<Card, 'title' | 'description' | 'color_label'>>
  ): Promise<Card>;
  deleteCard(id: string): Promise<void>;
  moveCard(id: string, targetColumnId: string, targetPosition: number): Promise<Card>;
}
