import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { authApi, testingApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD, testQuestions } from '@/mocks/fixtures';
import { CandidateTestingPage } from '@/pages/candidate/TestingPage';
import { renderWithProviders } from '@/test/test-utils';

async function seedCompletedTest() {
  const login = await authApi.login({
    email: 'candidate@demo.ru',
    password: DEMO_PASSWORD,
  });
  tokenStore.set(login.accessToken);
  const session = await testingApi.start({
    specialization: 'Frontend',
    stack: ['React'],
    claimedGrade: 'middle',
  });
  for (const q of testQuestions) {
    await testingApi.answer(session.id, { questionId: q.id, optionId: q.correctOptionId });
  }
  await testingApi.finish(session.id);
}

describe('CandidateTestingPage retest', () => {
  it('shows last result/history and starts retest session', async () => {
    await seedCompletedTest();
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route path="/candidate/testing" element={<CandidateTestingPage />} />
        <Route path="/candidate/testing/:sessionId" element={<div>Session running</div>} />
      </Routes>,
      { route: '/candidate/testing?retest=1' },
    );

    expect(await screen.findByTestId('last-test-result')).toBeInTheDocument();
    expect(await screen.findByTestId('test-history')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Пройти повторно' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Пройти повторно' }));
    await waitFor(() => {
      expect(screen.getByText('Session running')).toBeInTheDocument();
    });
  });
});
