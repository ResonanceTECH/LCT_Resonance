import { describe, expect, it } from 'vitest';
import {
  authApi,
  candidateApi,
  notificationsApi,
  vacancyApi,
} from '@/shared/api/endpoints';
import { tokenStore } from '@/shared/api/token';
import { DEMO_PASSWORD } from '@/mocks/fixtures';

async function login(email: string) {
  const res = await authApi.login({ email, password: DEMO_PASSWORD });
  tokenStore.set(res.accessToken);
}

describe('P3 features — match-to-me / completeness / notifications / saved', () => {
  it('returns match-to-me for candidate vacancy without client scoring', async () => {
    await login('candidate@demo.ru');
    const list = await vacancyApi.publicList({ matchToMe: true });
    expect(list.length).toBeGreaterThan(0);
    expect(list[0].match?.score).toBeTypeOf('number');
    expect(list[0].match?.reasons.length).toBeGreaterThan(0);

    const match = await vacancyApi.matchToMe(list[0].id);
    expect(match.candidateId).toBe('cand-1');
    expect(match.vacancyId).toBe(list[0].id);
    expect(match.score).toBe(list[0].match?.score);
  });

  it('rejects match-to-me for employer', async () => {
    await login('employer@demo.ru');
    await expect(vacancyApi.matchToMe('vac-1')).rejects.toMatchObject({ status: 403 });
  });

  it('returns profile completeness checklist from backend', async () => {
    await login('candidate@demo.ru');
    const completeness = await candidateApi.completeness();
    expect(completeness.percent).toBeGreaterThan(0);
    expect(completeness.items.length).toBeGreaterThanOrEqual(5);
    expect(completeness.items.every((i) => typeof i.done === 'boolean')).toBe(true);
  });

  it('lists notifications and marks them read', async () => {
    await login('candidate@demo.ru');
    const before = await notificationsApi.list();
    expect(before.items.length).toBeGreaterThan(0);
    const unreadBefore = before.unread;
    expect(unreadBefore).toBeGreaterThan(0);

    await notificationsApi.markRead(before.items.find((n) => !n.read)!.id);
    const after = await notificationsApi.list();
    expect(after.unread).toBeLessThan(unreadBefore);

    await notificationsApi.markAllRead();
    const all = await notificationsApi.list();
    expect(all.unread).toBe(0);
  });

  it('saves and unsaves vacancies', async () => {
    await login('candidate@demo.ru');
    const list = await vacancyApi.publicList();
    const id = list[0].id;

    await vacancyApi.save(id);
    const saved = await vacancyApi.savedList();
    expect(saved.some((v) => v.id === id)).toBe(true);

    const withFlag = await vacancyApi.publicList({ savedOnly: true });
    expect(withFlag.every((v) => v.saved)).toBe(true);

    await vacancyApi.unsave(id);
    const empty = await vacancyApi.savedList();
    expect(empty.some((v) => v.id === id)).toBe(false);
  });

  it('tracks applications after apply', async () => {
    await login('candidate@demo.ru');
    const list = await vacancyApi.publicList();
    await vacancyApi.apply(list[0].id);
    const again = await vacancyApi.publicList();
    expect(again.find((v) => v.id === list[0].id)?.applied).toBe(true);
  });
});
