import { httpClient } from './httpClient';
import type { Api } from './types';

export * from './types';

// Single place the whole app depends on for backend access. mockClient.ts
// is kept in the repo as a reference/fallback for offline frontend work,
// per the spec's "centralize and mock" requirement.
export const api: Api = httpClient;
