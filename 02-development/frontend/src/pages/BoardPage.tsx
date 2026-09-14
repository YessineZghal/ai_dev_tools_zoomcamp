import { useEffect, useState, type CSSProperties, type KeyboardEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, LayoutGrid } from 'lucide-react';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';
import { SortableContext, arrayMove, horizontalListSortingStrategy } from '@dnd-kit/sortable';
import { api, type Board, type Card, type Column } from '../api';
import { ColumnView } from '../components/ColumnView';
import { NewColumnForm } from '../components/NewColumnForm';
import { CardDetailsPanel } from '../components/CardDetailsPanel';
import { EmptyState } from '../components/EmptyState';

type LoadState = 'loading' | 'ready' | 'error';

function ColumnsSkeleton() {
  return (
    <div className="columns-skeleton-row" aria-hidden="true">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="skeleton column-skeleton" />
      ))}
    </div>
  );
}

function sortedCardsIn(cards: Card[], columnId: string): Card[] {
  return cards.filter((c) => c.column_id === columnId).sort((a, b) => a.position - b.position);
}

function moveCardInList(cards: Card[], cardId: string, targetColumnId: string, targetPosition: number): Card[] {
  const moving = cards.find((c) => c.id === cardId);
  if (!moving) return cards;
  const sourceColumnId = moving.column_id;

  const remaining = cards.filter((c) => c.id !== cardId).map((c) => ({ ...c }));

  const targetList = sortedCardsIn(remaining, targetColumnId);
  const clamped = Math.max(0, Math.min(targetPosition, targetList.length));
  targetList.splice(clamped, 0, { ...moving, column_id: targetColumnId });
  targetList.forEach((c, i) => {
    c.position = i;
  });

  let sourceList: Card[] = [];
  if (sourceColumnId !== targetColumnId) {
    sourceList = sortedCardsIn(remaining, sourceColumnId);
    sourceList.forEach((c, i) => {
      c.position = i;
    });
  }

  const untouched = remaining.filter(
    (c) => c.column_id !== targetColumnId && c.column_id !== sourceColumnId
  );

  return [...untouched, ...sourceList, ...targetList];
}

export function BoardPage() {
  const { id } = useParams<{ id: string }>();
  const [board, setBoard] = useState<Board | null>(null);
  const [columns, setColumns] = useState<Column[]>([]);
  const [cards, setCards] = useState<Card[]>([]);
  const [state, setState] = useState<LoadState>('loading');
  const [activeCard, setActiveCard] = useState<Card | null>(null);
  const [draggingCard, setDraggingCard] = useState<Card | null>(null);
  const [renamingBoard, setRenamingBoard] = useState(false);
  const [boardNameDraft, setBoardNameDraft] = useState('');

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  function load() {
    if (!id) return;
    setState('loading');
    api
      .getBoard(id)
      .then((detail) => {
        setBoard(detail.board);
        setColumns(detail.columns);
        setCards(detail.cards);
        setBoardNameDraft(detail.board.name);
        setState('ready');
      })
      .catch(() => setState('error'));
  }

  useEffect(load, [id]);

  function commitBoardRename() {
    const trimmed = boardNameDraft.trim();
    setRenamingBoard(false);
    if (!board) return;
    if (trimmed && trimmed !== board.name) {
      setBoard({ ...board, name: trimmed });
      api.renameBoard(board.id, trimmed).catch(load);
    } else {
      setBoardNameDraft(board.name);
    }
  }

  function handleBoardNameKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') commitBoardRename();
    if (event.key === 'Escape') {
      setBoardNameDraft(board?.name ?? '');
      setRenamingBoard(false);
    }
  }

  async function handleCreateColumn(name: string) {
    if (!board) return;
    const column = await api.createColumn(board.id, name);
    setColumns((prev) => [...prev, column]);
  }

  function handleRenameColumn(columnId: string, name: string) {
    setColumns((prev) => prev.map((c) => (c.id === columnId ? { ...c, name } : c)));
    api.renameColumn(columnId, name).catch(load);
  }

  function handleDeleteColumn(columnId: string) {
    const previousColumns = columns;
    const previousCards = cards;
    setColumns((prev) => prev.filter((c) => c.id !== columnId));
    setCards((prev) => prev.filter((c) => c.column_id !== columnId));
    api.deleteColumn(columnId).catch(() => {
      setColumns(previousColumns);
      setCards(previousCards);
    });
  }

  async function handleCreateCard(columnId: string, title: string) {
    const card = await api.createCard(columnId, { title });
    setCards((prev) => [...prev, card]);
  }

  function handleSaveCard(cardId: string, data: Pick<Card, 'title' | 'description' | 'color_label'>) {
    setCards((prev) => prev.map((c) => (c.id === cardId ? { ...c, ...data } : c)));
    api.updateCard(cardId, data).catch(load);
  }

  function handleDeleteCard(cardId: string) {
    const previous = cards;
    setCards((prev) => prev.filter((c) => c.id !== cardId));
    api.deleteCard(cardId).catch(() => setCards(previous));
  }

  function handleDragStart(event: DragStartEvent) {
    if (event.active.data.current?.type === 'card') {
      const card = cards.find((c) => c.id === event.active.id) ?? null;
      setDraggingCard(card);
    }
  }

  function handleDragEnd(event: DragEndEvent) {
    setDraggingCard(null);
    const { active, over } = event;
    if (!over || !board) return;

    const activeType = active.data.current?.type;

    if (activeType === 'column') {
      if (active.id === over.id) return;
      const oldIndex = columns.findIndex((c) => c.id === active.id);
      const newIndex = columns.findIndex((c) => c.id === over.id);
      if (oldIndex === -1 || newIndex === -1) return;

      const previous = columns;
      const reordered = arrayMove(columns, oldIndex, newIndex).map((c, i) => ({ ...c, position: i }));
      setColumns(reordered);
      api.reorderColumns(board.id, reordered.map((c) => c.id)).catch(() => setColumns(previous));
      return;
    }

    if (activeType === 'card') {
      const cardId = active.id as string;
      const overType = over.data.current?.type;

      let targetColumnId: string;
      let targetPosition: number;

      if (overType === 'card') {
        targetColumnId = over.data.current?.columnId as string;
        const targetList = sortedCardsIn(cards, targetColumnId).filter((c) => c.id !== cardId);
        const index = targetList.findIndex((c) => c.id === over.id);
        targetPosition = index === -1 ? targetList.length : index;
      } else if (overType === 'column-body') {
        targetColumnId = over.data.current?.columnId as string;
        targetPosition = sortedCardsIn(cards, targetColumnId).filter((c) => c.id !== cardId).length;
      } else {
        return;
      }

      const previous = cards;
      setCards(moveCardInList(cards, cardId, targetColumnId, targetPosition));
      api.moveCard(cardId, targetColumnId, targetPosition).catch(() => setCards(previous));
    }
  }

  if (state === 'loading') {
    return (
      <div className="board-page">
        <div className="board-page-header">
          <div className="skeleton" style={{ width: 160, height: 28, borderRadius: 8 }} />
        </div>
        <ColumnsSkeleton />
      </div>
    );
  }

  if (state === 'error' || !board) {
    return (
      <div className="error-banner">
        <span>Couldn't load this board.</span>
        <Link className="btn btn-ghost" to="/">
          Back to boards
        </Link>
      </div>
    );
  }

  return (
    <div className="board-page">
      <div className="board-page-header">
        <div>
          <Link className="back-link" to="/">
            <ArrowLeft />
            All boards
          </Link>
          {renamingBoard ? (
            <input
              className="text-input board-name-input"
              autoFocus
              value={boardNameDraft}
              onChange={(e) => setBoardNameDraft(e.target.value)}
              onBlur={commitBoardRename}
              onKeyDown={handleBoardNameKeyDown}
            />
          ) : (
            <input
              className="board-name-input"
              value={board.name}
              readOnly
              onClick={() => setRenamingBoard(true)}
            />
          )}
        </div>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="columns-row">
          {columns.length === 0 && (
            <EmptyState
              icon={<LayoutGrid />}
              title="No columns yet"
              hint="Add your first column to start organizing work."
            />
          )}

          <SortableContext items={columns.map((c) => c.id)} strategy={horizontalListSortingStrategy}>
            {columns
              .slice()
              .sort((a, b) => a.position - b.position)
              .map((column) => (
                <ColumnView
                  key={column.id}
                  column={column}
                  cards={sortedCardsIn(cards, column.id)}
                  onRename={(name) => handleRenameColumn(column.id, name)}
                  onDelete={() => handleDeleteColumn(column.id)}
                  onCreateCard={(title) => handleCreateCard(column.id, title)}
                  onOpenCard={setActiveCard}
                />
              ))}
          </SortableContext>

          <NewColumnForm onCreate={handleCreateColumn} />
        </div>

        <DragOverlay>
          {draggingCard && (
            <div
              className="card drag-overlay-card"
              style={
                draggingCard.color_label
                  ? ({ '--card-accent': `var(--label-${draggingCard.color_label})` } as CSSProperties)
                  : undefined
              }
            >
              <div className="card-title">{draggingCard.title}</div>
            </div>
          )}
        </DragOverlay>
      </DndContext>

      {activeCard && (
        <CardDetailsPanel
          card={activeCard}
          onClose={() => setActiveCard(null)}
          onSave={(data) => handleSaveCard(activeCard.id, data)}
          onDelete={() => handleDeleteCard(activeCard.id)}
        />
      )}
    </div>
  );
}
