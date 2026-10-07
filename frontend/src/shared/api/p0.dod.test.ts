/**
 * Definition of Done regresson for P0 (TECH_SPEC §12) against MSW mock backend.
 * These tests lock the API contract the UI relies on — not UI chrome.
 */
import { describe, expect, it } from 'vitest';
import {
  authApi,
  candidateApi,
  offerApi,
  vacancyApi,
} from '@/shared/api/endpoints';
import { ApiError } from '@/shared/api/errors';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';

async function loginAs(email: string) {
  const res = await authApi.login({ email, password: DEMO_PASSWORD });
  tokenStore.set(res.accessToken);
  return res.user;
}

describe('P0 Definition of Done (API + mock backend)', () => {
  it('1. registers and logs in candidate and employer', async () => {
    const candidate = await loginAs('candidate@demo.ru');
    expect(candidate.role).toBe('candidate');
    expect((await authApi.me()).email).toBe('candidate@demo.ru');

    tokenStore.clear();
    const employer = await loginAs('employer@demo.ru');
    expect(employer.role).toBe('employer');

    await expect(
      authApi.login({ email: 'employer@demo.ru', password: 'wrong' }),
    ).rejects.toMatchObject({ status: 401 });
  });

  it('2. candidate updates profile skills, grade, preferences, readiness', async () => {
    await loginAs('candidate@demo.ru');
    const updated = await candidateApi.updateMe({
      skills: ['React', 'TypeScript', 'Vite'],
      claimedGrade: 'middle',
      readiness: 'actively_looking',
      workFormat: 'remote',
      salaryFrom: 270000,
      salaryTo: 330000,
      desiredPosition: 'Senior Frontend Engineer',
    });
    expect(updated.skills).toEqual(['React', 'TypeScript', 'Vite']);
    expect(updated.readiness).toBe('actively_looking');
    expect(updated.desiredPosition).toBe('Senior Frontend Engineer');
  });

  it('3. candidate syncs FSP and gets verified achievements', async () => {
    await loginAs('candidate@demo.ru');
    const before = await candidateApi.fspAchievements();
    expect(before.achievements.every((a) => a.verified === true)).toBe(true);

    const synced = await candidateApi.fspSync();
    expect(synced.syncedAt).toBeTruthy();
    expect(synced.achievements.length).toBeGreaterThan(0);
    expect(synced.achievements.every((a) => a.verified)).toBe(true);
  });

  it('4. employer creates a vacancy', async () => {
    await loginAs('employer@demo.ru');
    const vacancy = await vacancyApi.create({
      title: 'Frontend Lead',
      description: 'Нужен сильный React/TS лид для продукта Resonance.',
      specialization: 'Frontend',
      requiredGrade: 'senior',
      requiredSkills: ['React', 'TypeScript'],
      niceToHaveSkills: ['GraphQL'],
      salaryFrom: 350000,
      salaryTo: 450000,
      currency: 'RUB',
      city: 'Москва',
      workFormat: 'hybrid',
      status: 'active',
      companyName: 'Resonance Labs',
    });
    expect(vacancy.id).toBeTruthy();
    expect(vacancy.title).toBe('Frontend Lead');
    const list = await vacancyApi.employerList();
    expect(list.some((v) => v.id === vacancy.id)).toBe(true);
  });

  it('5–6. talent pool filters and returns Match Score for vacancyId', async () => {
    await loginAs('employer@demo.ru');
    const filtered = await candidateApi.list({
      specialization: 'Frontend',
      readiness: 'open_to_offers',
    });
    expect(filtered.items.length).toBeGreaterThan(0);
    expect(filtered.items.every((c) => c.specialization === 'Frontend')).toBe(true);

    const ranked = await candidateApi.list({ vacancyId: 'vac-1' });
    expect(ranked.items[0].match).toBeDefined();
    expect(ranked.items[0].match!.score).toBeGreaterThan(0);
    expect(ranked.items[0].match!.missingInProfileSkills).toBeDefined();

    // ranking is descending by score (backend responsibility)
    for (let i = 1; i < ranked.items.length; i += 1) {
      expect(ranked.items[i - 1].match!.score).toBeGreaterThanOrEqual(
        ranked.items[i].match!.score,
      );
    }
  });

  it('7+10. contacts stay hidden until offer accepted, then API returns them', async () => {
    await loginAs('employer@demo.ru');

    await expect(candidateApi.contacts('cand-1')).rejects.toBeInstanceOf(ApiError);
    await expect(candidateApi.contacts('cand-1')).rejects.toMatchObject({ status: 403 });

    // accept as candidate
    tokenStore.clear();
    await loginAs('candidate@demo.ru');
    const accepted = await offerApi.accept('offer-1');
    expect(accepted.status).toBe('accepted');

    tokenStore.clear();
    await loginAs('employer@demo.ru');
    const contacts = await candidateApi.contacts('cand-1');
    expect(contacts.email).toBe('anna.kovaleva@demo.ru');
    expect(contacts.telegram).toBe('@anna_front');
  });

  it('8–9. employer sends offer with explicit salary; candidate can decline', async () => {
    await loginAs('employer@demo.ru');
    const offer = await offerApi.create({
      vacancyId: 'vac-1',
      candidateId: 'cand-3',
      companyName: 'Resonance Labs',
      positionTitle: 'Junior Frontend',
      salaryFrom: 140000,
      salaryTo: 170000,
      currency: 'RUB',
      workFormat: 'office',
      message: 'Присоединяйтесь к команде Frontend.',
    });
    expect(offer.salaryFrom).toBe(140000);
    expect(offer.salaryTo).toBe(170000);
    expect(offer.status).toBe('new');

    tokenStore.clear();
    await loginAs('candidate@demo.ru');
    // cand-3 is not the logged-in candidate — use cand-1's offer for decline path separately
    // create a fresh offer to cand-1 then decline
    tokenStore.clear();
    await loginAs('employer@demo.ru');
    const offer2 = await offerApi.create({
      vacancyId: 'vac-1',
      candidateId: 'cand-1',
      companyName: 'Resonance Labs',
      positionTitle: 'Frontend Engineer (React)',
      salaryFrom: 290000,
      salaryTo: 310000,
      currency: 'RUB',
      workFormat: 'remote',
      message: 'Второе предложение с явной вилкой.',
    });

    tokenStore.clear();
    await loginAs('candidate@demo.ru');
    const declined = await offerApi.decline(offer2.id);
    expect(declined.status).toBe('declined');
    expect(declined.respondedAt).toBeTruthy();
  });

  it('11. match payload comes from API response, not empty client stub', async () => {
    await loginAs('employer@demo.ru');
    const { items } = await candidateApi.list({ vacancyId: 'vac-1' });
    const anna = items.find((c) => c.id === 'cand-1');
    expect(anna?.match?.reasons.some((r) => r.label.includes('указан в профиле'))).toBe(true);
    expect(anna?.match?.missingInProfileSkills).toContain('Jest');
  });

  it('12. FSP achievements are verified=true; profile skills are not FSP entities', async () => {
    await loginAs('candidate@demo.ru');
    const profile = await candidateApi.me();
    const fsp = await candidateApi.fspAchievements();
    expect(profile.skills.length).toBeGreaterThan(0);
    expect(fsp.achievements.every((a) => a.verified === true)).toBe(true);
    // skills array has no verified flag — cannot be marked FSP Verified by type
    expect(profile.skills.every((s) => typeof s === 'string')).toBe(true);
  });
});
