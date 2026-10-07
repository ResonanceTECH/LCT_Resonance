import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { authApi, offerApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';
import { CandidateOfferDetailPage } from '@/pages/candidate/OfferDetailPage';
import { renderWithProviders } from '@/test/test-utils';

async function authCandidate() {
  const res = await authApi.login({
    email: 'candidate@demo.ru',
    password: DEMO_PASSWORD,
  });
  tokenStore.set(res.accessToken);
}

describe('CandidateOfferDetailPage', () => {
  it('accepts offer and updates status without leaving the flow', async () => {
    await authCandidate();
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route path="/candidate/offers/:id" element={<CandidateOfferDetailPage />} />
      </Routes>,
      { route: '/candidate/offers/offer-1' },
    );

    expect(await screen.findByText('Frontend Engineer (React)')).toBeInTheDocument();
    expect(screen.getByText(/280/)).toBeInTheDocument();

    await user.click(await screen.findByRole('button', { name: 'Принять' }));

    await waitFor(() => {
      expect(screen.getByText(/Действие уже выполнено/)).toBeInTheDocument();
    });

    const offer = await offerApi.byId('offer-1');
    expect(offer.status).toBe('accepted');
  });

  it('declines offer and persists declined status', async () => {
    await authCandidate();
    const created = await (async () => {
      // create via employer then switch back
      tokenStore.clear();
      const emp = await authApi.login({
        email: 'employer@demo.ru',
        password: DEMO_PASSWORD,
      });
      tokenStore.set(emp.accessToken);
      const offer = await offerApi.create({
        vacancyId: 'vac-1',
        candidateId: 'cand-1',
        companyName: 'Resonance Labs',
        positionTitle: 'Temp Offer',
        salaryFrom: 200000,
        salaryTo: 220000,
        currency: 'RUB',
        workFormat: 'remote',
        message: 'Временное предложение для decline-теста.',
      });
      tokenStore.clear();
      await authCandidate();
      return offer;
    })();

    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/candidate/offers/:id" element={<CandidateOfferDetailPage />} />
      </Routes>,
      { route: `/candidate/offers/${created.id}` },
    );

    await user.click(await screen.findByRole('button', { name: 'Отклонить' }));
    await waitFor(() => {
      expect(screen.getByText(/Действие уже выполнено/)).toBeInTheDocument();
    });

    const offer = await offerApi.byId(created.id);
    expect(offer.status).toBe('declined');
  });
});
