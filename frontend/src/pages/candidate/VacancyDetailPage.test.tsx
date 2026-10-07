import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { authApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';
import { renderWithProviders } from '@/test/test-utils';
import { CandidateVacancyDetailPage } from './VacancyDetailPage';

describe('CandidateVacancyDetailPage', () => {
  it('shows match-to-me and toggles saved vacancy', async () => {
    const user = userEvent.setup();
    const res = await authApi.login({ email: 'candidate@demo.ru', password: DEMO_PASSWORD });
    tokenStore.set(res.accessToken);

    renderWithProviders(
      <Routes>
        <Route path="/candidate/vacancies/:id" element={<CandidateVacancyDetailPage />} />
      </Routes>,
      { route: '/candidate/vacancies/vac-1' },
    );

    expect(await screen.findByTestId('match-to-me')).toBeInTheDocument();
    expect(screen.getByText(/Match \d+%/)).toBeInTheDocument();

    const saveBtn = await screen.findByTestId('save-vacancy');
    await user.click(saveBtn);
    expect(await screen.findByText('Убрать из избранного')).toBeInTheDocument();
  });
});
