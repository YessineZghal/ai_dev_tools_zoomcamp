import { useState, type FormEvent, type KeyboardEvent } from 'react';
import { Plus } from 'lucide-react';

interface NewCardFormProps {
  onCreate: (title: string) => Promise<void>;
}

export function NewCardForm({ onCreate }: NewCardFormProps) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [submitting, setSubmitting] = useState(false);

  function close() {
    setOpen(false);
    setTitle('');
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = title.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    try {
      await onCreate(trimmed);
      setTitle('');
    } finally {
      setSubmitting(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
    if (event.key === 'Escape') close();
  }

  if (!open) {
    return (
      <div className="add-card-zone">
        <button className="add-card-trigger" onClick={() => setOpen(true)}>
          <Plus />
          Add a card
        </button>
      </div>
    );
  }

  return (
    <div className="add-card-zone">
      <form className="add-card-form" onSubmit={handleSubmit}>
        <textarea
          className="text-input"
          autoFocus
          rows={2}
          placeholder="Card title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => {
            if (!title.trim()) close();
          }}
        />
        <div className="add-card-form-actions">
          <button className="btn btn-primary" type="submit" disabled={!title.trim() || submitting}>
            Add card
          </button>
          <button type="button" className="btn btn-ghost" onClick={close}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
