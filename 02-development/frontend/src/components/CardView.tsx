import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { CSSProperties } from 'react';
import type { Card } from '../api';

interface CardViewProps {
  card: Card;
  onOpen: () => void;
}

export function CardView({ card, onOpen }: CardViewProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: card.id,
    data: { type: 'card', columnId: card.column_id },
  });

  const style: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    ...(card.color_label ? { '--card-accent': `var(--label-${card.color_label})` } : {}),
  } as CSSProperties;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`card${isDragging ? ' is-dragging' : ''}`}
      onClick={onOpen}
    >
      <div className="card-title">{card.title}</div>
    </div>
  );
}
