import { describe, expect, it } from 'vitest';
import { authApi, dashboardApi, testingApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD, testQuestions } from '@/mocks/fixtures';

async function login(email: string) {
  const res = await authApi.login({ email, password: DEMO_PASSWORD });
  tokenStore.set(res.accessToken);
}

async function completeTest(retest = false) {
  const session = await testingApi.start({
    specialization: 'Frontend',
    stack: ['React', 'TypeScript'],
    claimedGrade: 'middle',
    retest,
  });
  for (const q of testQuestions) {
    await testingApi.answer(session.id, {
      questionId: q.id,
      optionId: q.correctOptionId,
    });
  }
  return testingApi.finish(session.id);
}

describe('Employer analytics API', () => {
  it('returns funnel and conversion rates computed on backend', async () => {
    await login('employer@demo.ru');
    const analytics = await dashboardApi.employerAnalytics();
    expect(analytics.funnel.viewedCandidates).toBeGreaterThan(0);
    expect(analytics.conversion.shortlistRate).toBeGreaterThanOrEqual(0);
    expect(analytics.conversion.shortlistRate).toBeLessThanOrEqual(1);
    expect(analytics.bySpecialization.length).toBeGreaterThan(0);
    expect(analytics.topSkills.length).toBeGreaterThan(0);
    expect(analytics.avgMatchScore).toBeTypeOf('number');
  });
});

describe('Retest API', () => {
  it('keeps history and marks retest attempts', async () => {
    await login('candidate@demo.ru');

    const first = await completeTest(false);
    expect(first.isRetest).toBe(false);
    expect(first.score).toBe(100);

    const second = await completeTest(true);
    expect(second.isRetest).toBe(true);
    expect(second.score).toBe(100);

    const history = await testingApi.history();
    expect(history.length).toBeGreaterThanOrEqual(2);
    expect(history.some((h) => h.isRetest)).toBe(true);
    expect(history[0].sessionId).toBe(second.sessionId);
  });

  it('does not expose correct answers on question endpoint', async () => {
    await login('candidate@demo.ru');
    const session = await testingApi.start({
      specialization: 'Frontend',
      stack: ['React'],
      claimedGrade: 'middle',
      retest: true,
    });
    const question = await testingApi.question(session.id);
    expect(question).not.toHaveProperty('correctOptionId');
    expect(question.options.every((o) => Object.keys(o).sort().join() === 'id,text')).toBe(true);
  });
});
