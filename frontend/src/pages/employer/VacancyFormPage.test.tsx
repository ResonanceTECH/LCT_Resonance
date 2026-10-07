import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { authApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';
import { EmployerVacancyFormPage } from '@/pages/employer/VacancyFormPage';
import { renderWithProviders } from '@/test/test-utils';

describe('EmployerVacancyFormPage AI parse', () => {
  it('fills form fields from backend parse result', async () => {
    const login = await authApi.login({
      email: 'employer@demo.ru',
      password: DEMO_PASSWORD,
    });
    tokenStore.set(login.accessToken);
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route
          path="/employer/vacancies/new"
          element={<EmployerVacancyFormPage mode="create" />}
        />
      </Routes>,
      { route: '/employer/vacancies/new' },
    );

    expect(screen.getByTestId('ai-parse')).toBeInTheDocument();

    await user.type(
      screen.getByLabelText('Текст вакансии'),
      'Senior Frontend Engineer\nRemote\nReact TypeScript Jest\nЗарплата 300–400 тыс.',
    );
    await user.click(screen.getByRole('button', { name: /Заполнить форму из текста/i }));

    await waitFor(() => {
      expect(screen.getByText(/Черновик подставлен/)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect((screen.getByLabelText('Название') as HTMLInputElement).value).toMatch(
        /Senior Frontend/i,
      );
      expect((screen.getByLabelText('Грейд') as HTMLSelectElement).value).toBe('senior');
      expect((screen.getByLabelText('Формат') as HTMLSelectElement).value).toBe('remote');
    });
  });
});

