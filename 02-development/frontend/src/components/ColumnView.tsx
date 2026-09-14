import { useState, type KeyboardEvent } from 'react';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Pencil, Trash2 } from 'lucide-react';
import type { Card, Column } from '../api';
import { CardView } from './CardView';
import { NewCardForm } from './NewCardForm';
import { KebabMenu } from './KebabMenu';

interface ColumnViewProps {
  column: Column;
  cards: Card[];
  onRename: (name: string) => void;
  onDelete: () => void;
  onCreateCard: (title: string) => Promise<void>;
  onOpenCard: (card: Card) => void;
}

export function ColumnView({ column, cards, onRename, onDelete, onCreateCard, onOpenCard }: ColumnViewProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(column.name);

  const {
    attributes,
    listeners,
    setNodeRef: setColumnRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: column.id, data: { type: 'column' } });

  const { setNodeRef: setDroppableRef } = useDroppable({
    id: column.id,
    data: { type: 'column-body', columnId: column.id },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  function commitRename() {
    const trimmed = draft.trim();
    setEditing(false);
    if (trimmed && trimmed !== column.name) {
      onRename(trimmed);
    } else {
      setDraft(column.name);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') commitRename();
    if (event.key === 'Escape') {
      setDraft(column.name);
      setEditing(false);
    }
  }

  return (
    <div ref={setColumnRef} style={style} className={`column${isDragging ? ' is-dragging' : ''}`}>
      <div className="column-header">
        <span className="column-grip" {...attributes} {...listeners}>
          <GripVertical />
        </span>
        {editing ? (
          <input
            className="text-input column-title-input"
            autoFocus
            value={draft}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commitRename}
            onKeyDown={handleKeyDown}
          />
        ) : (
          <span className="column-title-input" onClick={() => setEditing(true)}>
            {column.name}
          </span>
        )}
        <span className="column-count">{cards.length}</span>
        <KebabMenu
          items={[
            { label: 'Rename', icon: <Pencil />, onSelect: () => setEditing(true) },
            {
              label: 'Delete',
              icon: <Trash2 />,
              danger: true,
              onSelect: () => {
                if (window.confirm(`Delete column "${column.name}"? This deletes all its cards.`)) {
                  onDelete();
                }
              },
            },
          ]}
        />
      </div>

      <SortableContext items={cards.map((c) => c.id)} strategy={verticalListSortingStrategy}>
        <div ref={setDroppableRef} className="column-card-list">
          {cards.map((card) => (
            <CardView key={card.id} card={card} onOpen={() => onOpenCard(card)} />
          ))}
        </div>
      </SortableContext>

      <NewCardForm onCreate={onCreateCard} />
    </div>
  );
}
