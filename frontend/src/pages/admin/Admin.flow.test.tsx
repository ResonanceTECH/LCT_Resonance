import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { adminApi, authApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';
import { AdminOverviewPage } from '@/pages/admin/OverviewPage';
import { AdminUsersPage } from '@/pages/admin/UsersPage';
import { LoginPage } from '@/pages/auth/LoginPage';
import { renderWithProviders } from '@/test/test-utils';

async function loginAdmin() {
  const res = await authApi.login({ email: 'admin@demo.ru', password: DEMO_PASSWORD });
  tokenStore.set(res.accessToken);
  return res.user;
}

describe('Admin API + UI', () => {
  it('rejects non-admin overview', async () => {
    const emp = await authApi.login({ email: 'employer@demo.ru', password: DEMO_PASSWORD });
    tokenStore.set(emp.accessToken);
    await expect(adminApi.overview()).rejects.toMatchObject({ status: 403 });
  });

  it('shows overview stats for admin', async () => {
    await loginAdmin();
    renderWithProviders(
      <Routes>
        <Route path="/admin/overview" element={<AdminOverviewPage />} />
      </Routes>,
      { route: '/admin/overview' },
    );
    expect(await screen.findByTestId('admin-overview')).toBeInTheDocument();
    expect(screen.getByText('Кандидатов')).toBeInTheDocument();
    expect(screen.getByText('Работодателей')).toBeInTheDocument();
  });

  it('blocks user and prevents subsequent login', async () => {
    const user = userEvent.setup();
    await loginAdmin();
    renderWithProviders(
      <Routes>
        <Route path="/admin/users" element={<AdminUsersPage />} />
      </Routes>,
      { route: '/admin/users' },
    );

    expect(await screen.findByTestId('admin-users')).toBeInTheDocument();
    const blockButtons = await screen.findAllByRole('button', { name: 'Заблокировать' });
    await user.click(blockButtons[0]);

    await user.type(screen.getByLabelText('Причина блокировки'), 'Нарушение правил');
    const confirmButtons = screen.getAllByRole('button', { name: 'Заблокировать' });
    await user.click(confirmButtons[confirmButtons.length - 1]);

    await waitFor(async () => {
      const users = await adminApi.users();
      expect(users.some((u) => u.status === 'blocked')).toBe(true);
    });

    const blocked = (await adminApi.users()).find((u) => u.status === 'blocked')!;
    tokenStore.clear();
    await expect(
      authApi.login({ email: blocked.email, password: DEMO_PASSWORD }),
    ).rejects.toMatchObject({ status: 403, message: 'Аккаунт заблокирован' });
  });

  it('login redirects admin to /admin', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/admin" element={<div>Admin home</div>} />
      </Routes>,
      { route: '/login' },
    );

    await user.clear(screen.getByLabelText('Email'));
    await user.type(screen.getByLabelText('Email'), 'admin@demo.ru');
    await user.clear(screen.getByLabelText('Пароль'));
    await user.type(screen.getByLabelText('Пароль'), 'demo1234');
    await user.click(screen.getByRole('button', { name: 'Войти' }));

    await waitFor(() => {
      expect(screen.getByText('Admin home')).toBeInTheDocument();
    });
  });
});
