import { useState, type CSSProperties } from 'react';
import { Check, Trash2, X } from 'lucide-react';
import { COLOR_LABELS, type Card, type ColorLabel } from '../api';

interface CardDetailsPanelProps {
  card: Card;
  onClose: () => void;
  onSave: (data: { title: string; description: string | null; color_label: ColorLabel | null }) => void;
  onDelete: () => void;
}

export function CardDetailsPanel({ card, onClose, onSave, onDelete }: CardDetailsPanelProps) {
  const [title, setTitle] = useState(card.title);
  const [description, setDescription] = useState(card.description ?? '');
  const [colorLabel, setColorLabel] = useState<ColorLabel | null>(card.color_label);

  function handleClose() {
    const trimmedTitle = title.trim() || card.title;
    onSave({
      title: trimmedTitle,
      description: description.trim() ? description.trim() : null,
      color_label: colorLabel,
    });
    onClose();
  }

  return (
    <div className="panel-overlay" onClick={handleClose}>
      <div className="panel" onClick={(e) => e.stopPropagation()}>
        <div className="panel-header">
          <h2>Card details</h2>
          <button className="icon-btn" onClick={handleClose} title="Close" aria-label="Close">
            <X />
          </button>
        </div>

        <div className="panel-field">
          <label htmlFor="card-title">Title</label>
          <input
            id="card-title"
            className="text-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div className="panel-field">
          <label htmlFor="card-description">Description</label>
          <textarea
            id="card-description"
            className="text-input"
            rows={5}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add more detail (optional)"
          />
        </div>

        <div className="panel-field">
          <label>Color label</label>
          <div className="color-picker">
            <button
              type="button"
              className={`color-swatch none${colorLabel === null ? ' selected' : ''}`}
              title="No color"
              onClick={() => setColorLabel(null)}
            >
              {colorLabel === null && <Check />}
            </button>
            {COLOR_LABELS.map((color) => (
              <button
                type="button"
                key={color}
                className={`color-swatch${colorLabel === color ? ' selected' : ''}`}
                style={{ background: `var(--label-${color})`, '--color-swatch-ring': `var(--label-${color})` } as CSSProperties}
                title={color}
                onClick={() => setColorLabel(color)}
              >
                {colorLabel === color && <Check />}
              </button>
            ))}
          </div>
        </div>

        <div className="panel-footer">
          <button
            className="btn btn-danger-ghost"
            onClick={() => {
              if (window.confirm('Delete this card?')) {
                onDelete();
                onClose();
              }
            }}
          >
            <Trash2 />
            Delete card
          </button>
          <button className="btn btn-primary" onClick={handleClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
