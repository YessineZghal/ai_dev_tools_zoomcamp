import type { Api } from './types';

// Real backend implementation of Api, matching backend/openapi.yaml.
// Swapped in via index.ts once the FastAPI backend exists (see plan Task 11).

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${path}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export const httpClient: Api = {
  listBoards: () => request('/boards'),

  createBoard: (name) =>
    request('/boards', { method: 'POST', body: JSON.stringify({ name }) }),

  renameBoard: (id, name) =>
    request(`/boards/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),

  deleteBoard: (id) => request(`/boards/${id}`, { method: 'DELETE' }),

  getBoard: (id) => request(`/boards/${id}`),

  createColumn: (boardId, name) =>
    request(`/boards/${boardId}/columns`, { method: 'POST', body: JSON.stringify({ name }) }),

  renameColumn: (id, name) =>
    request(`/columns/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),

  deleteColumn: (id) => request(`/columns/${id}`, { method: 'DELETE' }),

  reorderColumns: (_boardId, orderedIds) =>
    request(`/columns/${orderedIds[0]}/reorder`, {
      method: 'PATCH',
      body: JSON.stringify({ ordered_ids: orderedIds }),
    }),

  createCard: (columnId, data) =>
    request(`/columns/${columnId}/cards`, { method: 'POST', body: JSON.stringify(data) }),

  updateCard: (id, data) =>
    request(`/cards/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  deleteCard: (id) => request(`/cards/${id}`, { method: 'DELETE' }),

  moveCard: (id, targetColumnId, targetPosition) =>
    request(`/cards/${id}/move`, {
      method: 'PATCH',
      body: JSON.stringify({
        target_column_id: targetColumnId,
        target_position: targetPosition,
      }),
    }),
};
