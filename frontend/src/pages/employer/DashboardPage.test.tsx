import { screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { authApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';
import { EmployerDashboardPage } from '@/pages/employer/DashboardPage';
import { renderWithProviders } from '@/test/test-utils';

describe('EmployerDashboardPage advanced analytics', () => {
  it('renders funnel, conversion and avg match from backend analytics', async () => {
    const login = await authApi.login({
      email: 'employer@demo.ru',
      password: DEMO_PASSWORD,
    });
    tokenStore.set(login.accessToken);

    renderWithProviders(
      <Routes>
        <Route path="/employer" element={<EmployerDashboardPage />} />
      </Routes>,
      { route: '/employer' },
    );

    expect(await screen.findByTestId('employer-analytics')).toBeInTheDocument();
    expect(screen.getByText(/Расширенная аналитика/)).toBeInTheDocument();
    expect(screen.getByText(/Воронка/)).toBeInTheDocument();
    expect(screen.getByText(/Конверсия в shortlist/)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId('avg-match').textContent).toMatch(/%|—/);
    });
    expect(screen.getByText(/Топ навыков в пуле/)).toBeInTheDocument();
    expect(screen.getByText(/Frontend:/)).toBeInTheDocument();
  });
});
