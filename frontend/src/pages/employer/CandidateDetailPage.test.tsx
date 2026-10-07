import { screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { authApi, offerApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';
import { EmployerCandidateDetailPage } from '@/pages/employer/CandidateDetailPage';
import { renderWithProviders } from '@/test/test-utils';

async function login(email: string) {
  const res = await authApi.login({ email, password: DEMO_PASSWORD });
  tokenStore.set(res.accessToken);
  return res.user;
}

describe('EmployerCandidateDetailPage contacts gate', () => {
  it('shows hidden contacts state before accept', async () => {
    await login('employer@demo.ru');

    renderWithProviders(
      <Routes>
        <Route path="/employer/candidates/:id" element={<EmployerCandidateDetailPage />} />
      </Routes>,
      { route: '/employer/candidates/cand-1?vacancyId=vac-1' },
    );

    expect(await screen.findByText('Контактные данные скрыты')).toBeInTheDocument();
    expect(
      screen.getByText(/Контакты будут доступны после того/),
    ).toBeInTheDocument();
    expect(screen.queryByText('anna.kovaleva@demo.ru')).not.toBeInTheDocument();
  });

  it('reveals contacts only after API allows (post-accept)', async () => {
    await login('candidate@demo.ru');
    await offerApi.accept('offer-1');

    tokenStore.clear();
    await login('employer@demo.ru');

    renderWithProviders(
      <Routes>
        <Route path="/employer/candidates/:id" element={<EmployerCandidateDetailPage />} />
      </Routes>,
      { route: '/employer/candidates/cand-1' },
    );

    await waitFor(() => {
      expect(screen.getByText(/anna.kovaleva@demo.ru/)).toBeInTheDocument();
    });
    expect(screen.queryByText('Контактные данные скрыты')).not.toBeInTheDocument();
  });
});
