import { useEffect, useState } from 'react';
import { LayoutGrid } from 'lucide-react';
import { api, type Board } from '../api';
import { BoardTile } from '../components/BoardTile';
import { NewBoardForm } from '../components/NewBoardForm';
import { EmptyState } from '../components/EmptyState';

type LoadState = 'loading' | 'ready' | 'error';

function BoardsSkeleton() {
  return (
    <div className="boards-skeleton-grid" aria-hidden="true">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="skeleton board-skeleton-tile" />
      ))}
    </div>
  );
}

export function BoardsPage() {
  const [boards, setBoards] = useState<Board[]>([]);
  const [state, setState] = useState<LoadState>('loading');

  function load() {
    setState('loading');
    api
      .listBoards()
      .then((result) => {
        setBoards(result);
        setState('ready');
      })
      .catch(() => setState('error'));
  }

  useEffect(load, []);

  async function handleCreate(name: string) {
    const board = await api.createBoard(name);
    setBoards((prev) => [...prev, board]);
  }

  function handleRename(id: string, name: string) {
    setBoards((prev) => prev.map((b) => (b.id === id ? { ...b, name } : b)));
    api.renameBoard(id, name).catch(load);
  }

  function handleDelete(id: string) {
    const previous = boards;
    setBoards((prev) => prev.filter((b) => b.id !== id));
    api.deleteBoard(id).catch(() => setBoards(previous));
  }

  return (
    <div className="boards-page">
      <div className="boards-page-header">
        <div>
          <h1>Your boards</h1>
          <p>Pick a board to open it, or start a new one.</p>
        </div>
        <NewBoardForm onCreate={handleCreate} />
      </div>

      {state === 'loading' && <BoardsSkeleton />}

      {state === 'error' && (
        <div className="error-banner">
          <span>Couldn't load boards.</span>
          <button className="btn btn-ghost" onClick={load}>
            Retry
          </button>
        </div>
      )}

      {state === 'ready' && boards.length === 0 && (
        <EmptyState
          icon={<LayoutGrid />}
          title="No boards yet"
          hint="Create your first board above."
        />
      )}

      {state === 'ready' && boards.length > 0 && (
        <div className="boards-grid">
          {boards.map((board) => (
            <BoardTile
              key={board.id}
              board={board}
              onRename={(name) => handleRename(board.id, name)}
              onDelete={() => handleDelete(board.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
