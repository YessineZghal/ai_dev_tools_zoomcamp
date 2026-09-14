import { useState, type FormEvent } from 'react';
import { Plus } from 'lucide-react';

interface NewColumnFormProps {
  onCreate: (name: string) => Promise<void>;
}

export function NewColumnForm({ onCreate }: NewColumnFormProps) {
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    try {
      await onCreate(trimmed);
      setName('');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="inline-form" style={{ width: 292, minWidth: 292 }} onSubmit={handleSubmit}>
      <span style={{ color: 'var(--text-tertiary)', display: 'flex', flexShrink: 0 }}>
        <Plus size={15} />
      </span>
      <input
        className="text-input"
        placeholder="Add a column"
        value={name}
        onChange={(e) => setName(e.target.value)}
        aria-label="New column name"
      />
    </form>
  );
}
