import { env } from '@/shared/config/env';
import { ApiError } from '@/shared/api/errors';
import { tokenStore } from '@/shared/api/token';

type RequestOptions = {
  method?: string;
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
  auth?: boolean;
};

function buildUrl(path: string, params?: RequestOptions['params']) {
  const base = env.apiBaseUrl.replace(/\/$/, '');
  const url = new URL(`${base}${path.startsWith('/') ? path : `/${path}`}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') return;
      url.searchParams.set(key, String(value));
    });
  }
  return url.pathname + url.search;
}

let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

export async function apiClient<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, params, auth = true } = options;
  const headers: Record<string, string> = {
    Accept: 'application/json',
  };

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  const hadToken = Boolean(tokenStore.get());
  if (auth) {
    const token = tokenStore.get();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildUrl(path, params), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const data = text ? (JSON.parse(text) as unknown) : null;

  if (response.status === 401) {
    // Only force logout when an authenticated session was rejected —
    // login/register 401 must keep the server message.
    if (auth && hadToken) {
      tokenStore.clear();
      onUnauthorized?.();
    }
    const message =
      typeof data === 'object' && data && 'message' in data
        ? String((data as { message: string }).message)
        : 'Требуется авторизация';
    throw new ApiError(message, 401, data);
  }

  if (!response.ok) {
    const message =
      typeof data === 'object' && data && 'message' in data
        ? String((data as { message: string }).message)
        : `Ошибка ${response.status}`;
    throw new ApiError(message, response.status, data);
  }

  return data as T;
}
