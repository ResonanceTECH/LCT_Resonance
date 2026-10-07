import { screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { authApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';
import { EmployerComparePage } from '@/pages/employer/ComparePage';
import { renderWithProviders } from '@/test/test-utils';

describe('EmployerComparePage', () => {
  it('renders matrix with «не указан в профиле» and radars', async () => {
    const login = await authApi.login({
      email: 'employer@demo.ru',
      password: DEMO_PASSWORD,
    });
    tokenStore.set(login.accessToken);

    renderWithProviders(
      <Routes>
        <Route path="/employer/compare" element={<EmployerComparePage />} />
      </Routes>,
      { route: '/employer/compare?ids=cand-1,cand-2' },
    );

    expect(await screen.findByText('Сравнение кандидатов')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId('compare-matrix')).toBeInTheDocument();
    });
    expect(screen.getAllByText(/не указан в профиле/).length).toBeGreaterThan(0);
    expect(screen.getAllByTestId('skill-radar').length).toBe(2);
    expect(screen.queryByText(/не умеет/i)).not.toBeInTheDocument();
  });

  it('asks to select at least 2 candidates when ids missing', async () => {
    renderWithProviders(
      <Routes>
        <Route path="/employer/compare" element={<EmployerComparePage />} />
      </Routes>,
      { route: '/employer/compare' },
    );
    expect(await screen.findByText(/Выберите минимум 2 кандидатов/)).toBeInTheDocument();
  });
});
