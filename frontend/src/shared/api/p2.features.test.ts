import { describe, expect, it } from 'vitest';
import { authApi, candidateApi, vacancyApi } from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';

async function login(email: string) {
  const res = await authApi.login({ email, password: DEMO_PASSWORD });
  tokenStore.set(res.accessToken);
}

describe('P2 features (API contract)', () => {
  it('returns skill radar from backend for a candidate', async () => {
    await login('employer@demo.ru');
    const radar = await candidateApi.skillRadar('cand-1');
    expect(radar.candidateId).toBe('cand-1');
    expect(radar.axes.length).toBeGreaterThan(0);
    expect(radar.axes.every((a) => a.score >= 0 && a.score <= 100)).toBe(true);
  });

  it('compares candidates with matrix wording for missing skills', async () => {
    await login('employer@demo.ru');
    const result = await candidateApi.compare(['cand-1', 'cand-2']);
    expect(result.candidates).toHaveLength(2);
    expect(result.radars).toHaveLength(2);
    expect(result.skillMatrix.length).toBeGreaterThan(0);
    const missingCell = result.skillMatrix
      .flatMap((row) => Object.values(row.values))
      .some((v) => v === null);
    expect(missingCell).toBe(true);
  });

  it('rejects compare with fewer than 2 ids', async () => {
    await login('employer@demo.ru');
    await expect(candidateApi.compare(['cand-1'])).rejects.toMatchObject({ status: 400 });
  });

  it('parses vacancy text on backend and returns draft fields', async () => {
    await login('employer@demo.ru');
    const draft = await vacancyApi.parseAi(`
Senior Frontend Engineer
Remote, Москва
Нужен React, TypeScript, Jest. Зарплата 300–400 тыс.
`);
    expect(draft.requiredGrade).toBe('senior');
    expect(draft.workFormat).toBe('remote');
    expect(draft.requiredSkills?.some((s) => s.toLowerCase() === 'react')).toBe(true);
    expect(draft.salaryFrom).toBe(300000);
    expect(draft.salaryTo).toBe(400000);
  });

  it('sorts talent pool by name on backend', async () => {
    await login('employer@demo.ru');
    const { items } = await candidateApi.list({ sort: 'name' });
    const names = items.map((i) => i.fullName);
    const sorted = [...names].sort((a, b) => a.localeCompare(b, 'ru'));
    expect(names).toEqual(sorted);
  });
});
