import { describe, expect, it } from 'vitest';
import { apiClient } from '@/shared/api/client';
import { ApiError } from '@/shared/api/errors';
import { tokenStore } from '@/shared/api/token';

describe('apiClient auth errors', () => {
  it('preserves login 401 message and does not treat it as session expiry', async () => {
    await expect(
      apiClient('/auth/login', {
        method: 'POST',
        auth: false,
        body: { email: 'employer@demo.ru', password: 'wrong' },
      }),
    ).rejects.toMatchObject({
      status: 401,
      message: 'Неверный email или пароль',
    } satisfies Partial<ApiError>);
    expect(tokenStore.get()).toBeNull();
  });
});
