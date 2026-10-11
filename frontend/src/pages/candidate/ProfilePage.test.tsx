import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { DEMO_PASSWORD } from '@/mocks/fixtures';
import { server } from '@/mocks/server';
import { CandidateProfilePage } from '@/pages/candidate/ProfilePage';
import { authApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { renderWithProviders } from '@/test/test-utils';

async function authCandidate() {
  const res = await authApi.login({ email: 'candidate@demo.ru', password: DEMO_PASSWORD });
  tokenStore.set(res.accessToken);
}

describe('CandidateProfilePage passport card', () => {
  it('shows the readable passport link when it is published', async () => {
    await authCandidate();
    renderWithProviders(<CandidateProfilePage />);

    const url = await screen.findByTestId('passport-url');
    expect(url.textContent).toMatch(/\/p\/passport-/);
    const open = screen.getByRole('link', { name: 'Открыть паспорт' });
    expect(open.getAttribute('href')).toMatch(/^\/p\/passport-/);
    expect(screen.getByRole('button', { name: 'Скопировать ссылку' })).toBeInTheDocument();
  });

  it('explains a hidden passport and publishes it with the consent', async () => {
    await authCandidate();
    let published = false;
    const consents: unknown[] = [];
    server.use(
      http.get('/api/candidates/me/passport', () =>
        HttpResponse.json({
          slug: 'anna-kovaleva-k7m2q9xw',
          url: 'http://localhost:5173/p/anna-kovaleva-k7m2q9xw',
          published,
          reason: published ? null : 'CONSENT_REQUIRED',
        }),
      ),
      http.put('/api/candidates/me/consents', async ({ request }) => {
        consents.push(await request.json());
        published = true;
        return HttpResponse.json([]);
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<CandidateProfilePage />);

    expect(await screen.findByText(/нужно согласие на публикацию профиля/)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Опубликовать паспорт' }));

    await waitFor(() => {
      expect(screen.getByTestId('passport-url').textContent).toContain('/p/anna-kovaleva-k7m2q9xw');
    });
    expect(consents).toEqual([{ consents: [{ type: 'profile_publication', accepted: true }] }]);
  });
});
