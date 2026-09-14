import { useState, type FormEvent } from 'react';
import { Plus } from 'lucide-react';

interface NewBoardFormProps {
  onCreate: (name: string) => Promise<void>;
}

export function NewBoardForm({ onCreate }: NewBoardFormProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  function close() {
    setOpen(false);
    setName('');
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    try {
      await onCreate(trimmed);
      close();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <button className="btn btn-primary new-board-trigger" onClick={() => setOpen(true)}>
        <Plus />
        New board
      </button>

      {open && (
        <div className="modal-backdrop" onClick={close}>
          <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
            <h2>New board</h2>
            <input
              className="text-input"
              autoFocus
              placeholder="e.g. Product launch"
              value={name}
              onChange={(e) => setName(e.target.value)}
              aria-label="New board name"
            />
            <div className="modal-actions">
              <button type="button" className="btn btn-ghost" onClick={close}>
                Cancel
              </button>
              <button className="btn btn-primary" type="submit" disabled={!name.trim() || submitting}>
                Create board
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
