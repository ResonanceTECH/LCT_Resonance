import '@testing-library/jest-dom/vitest';
import { afterAll, afterEach, beforeAll, beforeEach } from 'vitest';
import { server } from '@/mocks/server';
import { resetMockDb } from '@/mocks/fixtures';
import { resetTestSessions } from '@/mocks/handlers';
import { tokenStore } from '@/shared/api/token';

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

beforeEach(() => {
  resetMockDb();
  resetTestSessions();
  tokenStore.clear();
  sessionStorage.clear();
});

afterEach(() => {
  server.resetHandlers();
  tokenStore.clear();
});

afterAll(() => {
  server.close();
});
