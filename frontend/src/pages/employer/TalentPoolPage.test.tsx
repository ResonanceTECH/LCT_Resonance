import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { authApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';
import { EmployerTalentPoolPage } from '@/pages/employer/TalentPoolPage';
import { renderWithProviders } from '@/test/test-utils';

describe('EmployerTalentPoolPage', () => {
  it('lists candidates and shows Match Score when vacancy selected', async () => {
    const login = await authApi.login({
      email: 'employer@demo.ru',
      password: DEMO_PASSWORD,
    });
    tokenStore.set(login.accessToken);
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route path="/employer/talent-pool" element={<EmployerTalentPoolPage />} />
      </Routes>,
      { route: '/employer/talent-pool' },
    );

    expect(await screen.findByText('Анна Ковалёва')).toBeInTheDocument();
    expect(screen.getByText('Максим Орлов')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('Вакансия для Match'), 'vac-1');

    await waitFor(() => {
      expect(screen.getAllByText(/Match \d+%/).length).toBeGreaterThan(0);
    });
  });

  it('shows empty state when filters match nobody', async () => {
    const login = await authApi.login({
      email: 'employer@demo.ru',
      password: DEMO_PASSWORD,
    });
    tokenStore.set(login.accessToken);
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route path="/employer/talent-pool" element={<EmployerTalentPoolPage />} />
      </Routes>,
      { route: '/employer/talent-pool' },
    );

    await screen.findByText('Анна Ковалёва');
    await user.selectOptions(screen.getByLabelText('Специализация'), 'DevOps');

    expect(await screen.findByText('Подходящие кандидаты не найдены')).toBeInTheDocument();
  });
});
