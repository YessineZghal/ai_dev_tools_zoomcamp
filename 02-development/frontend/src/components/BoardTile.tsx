import { useState, type CSSProperties, type KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Pencil, Trash2 } from 'lucide-react';
import type { Board } from '../api';
import { accentFromId, formatRelativeDate } from '../utils/accentFromId';
import { KebabMenu } from './KebabMenu';

interface BoardTileProps {
  board: Board;
  onRename: (name: string) => void;
  onDelete: () => void;
}

export function BoardTile({ board, onRename, onDelete }: BoardTileProps) {
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(board.name);

  function commitRename() {
    const trimmed = draft.trim();
    setEditing(false);
    if (trimmed && trimmed !== board.name) {
      onRename(trimmed);
    } else {
      setDraft(board.name);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') commitRename();
    if (event.key === 'Escape') {
      setDraft(board.name);
      setEditing(false);
    }
  }

  const style = { '--tile-accent': accentFromId(board.id) } as CSSProperties;

  return (
    <div
      className="board-tile"
      style={style}
      onClick={() => !editing && navigate(`/boards/${board.id}`)}
      role="button"
      tabIndex={0}
    >
      <div className="board-tile-top">
        {editing ? (
          <input
            className="text-input"
            autoFocus
            value={draft}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commitRename}
            onKeyDown={handleKeyDown}
          />
        ) : (
          <span className="board-tile-name">{board.name}</span>
        )}
        <div onClick={(e) => e.stopPropagation()}>
          <KebabMenu
            items={[
              {
                label: 'Rename',
                icon: <Pencil />,
                onSelect: () => setEditing(true),
              },
              {
                label: 'Delete',
                icon: <Trash2 />,
                danger: true,
                onSelect: () => {
                  if (window.confirm(`Delete board "${board.name}"? This deletes all its columns and cards.`)) {
                    onDelete();
                  }
                },
              },
            ]}
          />
        </div>
      </div>
      <div className="board-tile-meta">Created {formatRelativeDate(board.created_at)}</div>
    </div>
  );
}
