import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { LoginPage } from '@/pages/auth/LoginPage';
import { renderWithProviders } from '@/test/test-utils';

describe('LoginPage', () => {
  it('logs candidate in and redirects to /candidate', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/candidate" element={<div>Candidate home</div>} />
        <Route path="/employer" element={<div>Employer home</div>} />
      </Routes>,
      { route: '/login' },
    );

    await user.clear(screen.getByLabelText('Email'));
    await user.type(screen.getByLabelText('Email'), 'candidate@demo.ru');
    await user.clear(screen.getByLabelText('Пароль'));
    await user.type(screen.getByLabelText('Пароль'), 'demo1234');
    await user.click(screen.getByRole('button', { name: 'Войти' }));

    await waitFor(() => {
      expect(screen.getByText('Candidate home')).toBeInTheDocument();
    });
  });

  it('logs employer in and redirects to /employer', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/candidate" element={<div>Candidate home</div>} />
        <Route path="/employer" element={<div>Employer home</div>} />
      </Routes>,
      { route: '/login' },
    );

    await user.clear(screen.getByLabelText('Email'));
    await user.type(screen.getByLabelText('Email'), 'employer@demo.ru');
    await user.clear(screen.getByLabelText('Пароль'));
    await user.type(screen.getByLabelText('Пароль'), 'demo1234');
    await user.click(screen.getByRole('button', { name: 'Войти' }));

    await waitFor(() => {
      expect(screen.getByText('Employer home')).toBeInTheDocument();
    });
  });

  it('shows auth error on bad credentials', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, { route: '/login' });

    await user.clear(screen.getByLabelText('Email'));
    await user.type(screen.getByLabelText('Email'), 'employer@demo.ru');
    await user.clear(screen.getByLabelText('Пароль'));
    await user.type(screen.getByLabelText('Пароль'), 'bad-password');
    await user.click(screen.getByRole('button', { name: 'Войти' }));

    await waitFor(() => {
      expect(screen.getByText(/Неверный email или пароль|Не удалось войти/)).toBeInTheDocument();
    });
  });
});
