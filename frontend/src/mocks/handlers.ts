import { http, HttpResponse, delay } from 'msw';
import type {
  AuthResponse,
  AuthUser,
  CreateOfferPayload,
  Grade,
  ReadinessStatus,
  RegisterPayload,
  Vacancy,
  WorkFormat,
} from '@/entities/types';
import {
  DEMO_PASSWORD,
  applicationsByCandidate,
  blockedUserIds,
  buildNotificationsForUser,
  computeCompare,
  computeCompleteness,
  computeMatch,
  computeSkillRadar,
  contactsByCandidate,
  fspByCandidate,
  notificationReadIds,
  offers,
  parseVacancyText,
  profiles,
  savedVacanciesByCandidate,
  shortlist,
  testQuestions,
  users,
  vacancies,
} from '@/mocks/fixtures';

const API = '/api';

function parseAuth(request: Request): AuthUser | null {
  const header = request.headers.get('Authorization');
  if (!header?.startsWith('Bearer ')) return null;
  const token = header.slice(7);
  const userId = token.replace('token-', '');
  return users.find((u) => u.id === userId) ?? null;
}

function requireUser(request: Request) {
  const user = parseAuth(request);
  if (!user) {
    return { error: HttpResponse.json({ message: 'Требуется авторизация' }, { status: 401 }) };
  }
  return { user };
}

let sessionAnswers: Record<string, Record<string, string>> = {};
let sessions: Record<
  string,
  {
    id: string;
    specialization: string;
    stack: string[];
    claimedGrade: Grade;
    currentIndex: number;
    totalQuestions: number;
    status: 'in_progress' | 'completed';
    userId: string;
    isRetest: boolean;
  }
> = {};
let testHistoryByUser: Record<
  string,
  {
    sessionId: string;
    score: number;
    maxScore: number;
    gradeConfirmed: boolean;
    completedAt: string;
    claimedGrade: Grade;
    specialization: string;
    isRetest?: boolean;
  }[]
> = {};

export function resetTestSessions() {
  sessionAnswers = {};
  sessions = {};
  testHistoryByUser = {};
}

export const handlers = [
  http.post(`${API}/auth/login`, async ({ request }) => {
    await delay(300);
    const body = (await request.json()) as { email: string; password: string };
    const user = users.find((u) => u.email === body.email);
    if (!user || body.password !== DEMO_PASSWORD) {
      return HttpResponse.json({ message: 'Неверный email или пароль' }, { status: 401 });
    }
    if (blockedUserIds.includes(user.id)) {
      return HttpResponse.json({ message: 'Аккаунт заблокирован' }, { status: 403 });
    }
    const payload: AuthResponse = { accessToken: `token-${user.id}`, user };
    return HttpResponse.json(payload);
  }),

  http.post(`${API}/auth/register`, async ({ request }) => {
    await delay(300);
    const body = (await request.json()) as RegisterPayload;
    if (users.some((u) => u.email === body.email)) {
      return HttpResponse.json({ message: 'Email уже зарегистрирован' }, { status: 409 });
    }
    const user: AuthUser = {
      id: `user-${crypto.randomUUID()}`,
      email: body.email,
      role: body.role,
      displayName: body.displayName,
    };
    users.push(user);
    if (body.role === 'candidate') {
      profiles.push({
        id: `cand-${crypto.randomUUID()}`,
        userId: user.id,
        fullName: body.displayName,
        specialization: 'Frontend',
        claimedGrade: 'junior',
        skills: [],
        currency: 'RUB',
        readiness: 'open_to_offers',
      });
    }
    return HttpResponse.json({ accessToken: `token-${user.id}`, user } satisfies AuthResponse);
  }),

  http.post(`${API}/auth/logout`, async () => {
    await delay(100);
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${API}/auth/me`, async ({ request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    return HttpResponse.json(auth.user);
  }),

  http.get(`${API}/candidates/me`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    return HttpResponse.json(profile);
  }),

  http.patch(`${API}/candidates/me`, async ({ request }) => {
    await delay(250);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const idx = profiles.findIndex((p) => p.userId === auth.user!.id);
    if (idx < 0) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    const body = (await request.json()) as Partial<(typeof profiles)[number]>;
    profiles[idx] = { ...profiles[idx], ...body, id: profiles[idx].id, userId: profiles[idx].userId };
    return HttpResponse.json(profiles[idx]);
  }),

  // Static /me/* routes MUST be registered before /:id/* or MSW treats "me" as an id.
  http.get(`${API}/candidates/me/fsp/achievements`, async ({ request }) => {
    await delay(250);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    return HttpResponse.json({
      achievements: fspByCandidate[profile.id] ?? [],
      syncedAt: profile.fspSyncedAt ?? null,
    });
  }),

  http.post(`${API}/candidates/me/fsp/sync`, async ({ request }) => {
    await delay(800);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    if (!fspByCandidate[profile.id]) {
      fspByCandidate[profile.id] = [
        {
          id: `fsp-${crypto.randomUUID()}`,
          title: 'ФСП Open Cup',
          discipline: profile.specialization,
          date: '2026-01-15',
          placeOrResult: 'Участник',
          verified: true,
        },
      ];
    }
    profile.fspSyncedAt = new Date().toISOString();
    profile.hasFspAchievements = (fspByCandidate[profile.id]?.length ?? 0) > 0;
    return HttpResponse.json({
      achievements: fspByCandidate[profile.id],
      syncedAt: profile.fspSyncedAt,
    });
  }),

  http.get(`${API}/candidates/:id`, async ({ params, request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    if (params.id === 'me') {
      return HttpResponse.json({ message: 'Используйте /candidates/me' }, { status: 404 });
    }
    const profile = profiles.find((p) => p.id === params.id);
    if (!profile) return HttpResponse.json({ message: 'Кандидат не найден' }, { status: 404 });
    return HttpResponse.json(profile);
  }),

  http.get(`${API}/candidates/:id/fsp/achievements`, async ({ params, request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const candidateId = String(params.id);
    if (candidateId === 'me') {
      return HttpResponse.json({ message: 'Используйте /candidates/me/fsp/achievements' }, { status: 404 });
    }
    const profile = profiles.find((p) => p.id === candidateId);
    if (!profile) return HttpResponse.json({ message: 'Кандидат не найден' }, { status: 404 });
    return HttpResponse.json({
      achievements: fspByCandidate[candidateId] ?? [],
      syncedAt: profile.fspSyncedAt ?? null,
    });
  }),

  http.get(`${API}/candidates/:id/contacts`, async ({ params, request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const candidateId = String(params.id);
    const accepted = offers.some(
      (o) =>
        o.candidateId === candidateId &&
        o.employerId === auth.user!.id &&
        o.status === 'accepted',
    );
    if (!accepted) {
      return HttpResponse.json(
        { message: 'Контакты доступны после принятия предложения' },
        { status: 403 },
      );
    }
    return HttpResponse.json(contactsByCandidate[candidateId] ?? {});
  }),

  http.get(`${API}/public/passports/:slug`, async ({ params }) => {
    await delay(200);
    const slug = String(params.slug);
    const profile = profiles.find(
      (p) => p.id === slug || p.fullName.toLowerCase().replace(/\s+/g, '-') === slug,
    );
    if (!profile) {
      return HttpResponse.json({ message: 'Паспорт не найден' }, { status: 404 });
    }
    return HttpResponse.json({
      profile,
      achievements: fspByCandidate[profile.id] ?? [],
      radar: computeSkillRadar(profile.id),
      publicUrl: `http://localhost:5173/p/${profile.id}`,
    });
  }),

  http.get(`${API}/candidates/:id/skill-radar`, async ({ params, request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const id = String(params.id);
    if (!profiles.some((p) => p.id === id)) {
      return HttpResponse.json({ message: 'Кандидат не найден' }, { status: 404 });
    }
    return HttpResponse.json(computeSkillRadar(id));
  }),

  http.get(`${API}/employer/candidates/compare`, async ({ request }) => {
    await delay(250);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const url = new URL(request.url);
    const ids = (url.searchParams.get('ids') ?? '').split(',').filter(Boolean);
    if (ids.length < 2) {
      return HttpResponse.json({ message: 'Нужно минимум 2 кандидата' }, { status: 400 });
    }
    return HttpResponse.json(computeCompare(ids));
  }),

  http.post(`${API}/vacancies/parse`, async ({ request }) => {
    await delay(400);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const body = (await request.json()) as { text?: string };
    if (!body.text || body.text.trim().length < 20) {
      return HttpResponse.json({ message: 'Слишком короткий текст вакансии' }, { status: 400 });
    }
    return HttpResponse.json(parseVacancyText(body.text));
  }),

  http.get(`${API}/candidates`, async ({ request }) => {
    await delay(300);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const url = new URL(request.url);
    const specialization = url.searchParams.get('specialization');
    const grade = url.searchParams.get('grade') as Grade | null;
    const skills = url.searchParams.get('skills');
    const workFormat = url.searchParams.get('workFormat') as WorkFormat | null;
    const salaryFrom = url.searchParams.get('salaryFrom');
    const salaryTo = url.searchParams.get('salaryTo');
    const fspDiscipline = url.searchParams.get('fspDiscipline');
    const hasFsp = url.searchParams.get('hasFspAchievements');
    const readiness = url.searchParams.get('readiness') as ReadinessStatus | null;
    const vacancyId = url.searchParams.get('vacancyId');
    const sort = url.searchParams.get('sort');
    const q = url.searchParams.get('q')?.toLowerCase();

    let items = [...profiles];

    if (specialization) items = items.filter((p) => p.specialization === specialization);
    if (grade) items = items.filter((p) => p.claimedGrade === grade);
    if (workFormat) items = items.filter((p) => p.workFormat === workFormat);
    if (readiness) items = items.filter((p) => p.readiness === readiness);
    if (hasFsp === 'true') items = items.filter((p) => p.hasFspAchievements);
    if (hasFsp === 'false') items = items.filter((p) => !p.hasFspAchievements);
    if (salaryFrom) items = items.filter((p) => (p.salaryTo ?? Infinity) >= Number(salaryFrom));
    if (salaryTo) items = items.filter((p) => (p.salaryFrom ?? 0) <= Number(salaryTo));
    if (skills) {
      const list = skills.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);
      items = items.filter((p) =>
        list.every((s) => p.skills.some((ps) => ps.toLowerCase().includes(s))),
      );
    }
    if (fspDiscipline) {
      items = items.filter((p) =>
        (fspByCandidate[p.id] ?? []).some((a) =>
          a.discipline?.toLowerCase().includes(fspDiscipline.toLowerCase()),
        ),
      );
    }
    if (q) {
      items = items.filter(
        (p) =>
          p.fullName.toLowerCase().includes(q) ||
          p.specialization.toLowerCase().includes(q) ||
          p.skills.some((s) => s.toLowerCase().includes(q)),
      );
    }

    const mapped = items.map((p) => ({
      ...p,
      match: vacancyId ? computeMatch(p.id, vacancyId) : undefined,
    }));

    if (vacancyId || sort === 'match') {
      mapped.sort((a, b) => (b.match?.score ?? 0) - (a.match?.score ?? 0));
    } else if (sort === 'name') {
      mapped.sort((a, b) => a.fullName.localeCompare(b.fullName, 'ru'));
    } else if (sort === 'salary') {
      mapped.sort((a, b) => (b.salaryTo ?? 0) - (a.salaryTo ?? 0));
    } else if (sort === 'grade') {
      const order = ['intern', 'junior', 'middle', 'senior', 'lead'];
      mapped.sort(
        (a, b) => order.indexOf(b.claimedGrade) - order.indexOf(a.claimedGrade),
      );
    }

    return HttpResponse.json({ items: mapped, total: mapped.length });
  }),

  http.get(`${API}/vacancies/:vacancyId/matches`, async ({ params, request }) => {
    await delay(250);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const vacancyId = String(params.vacancyId);
    const items = profiles
      .map((p) => ({ ...p, match: computeMatch(p.id, vacancyId) }))
      .sort((a, b) => (b.match?.score ?? 0) - (a.match?.score ?? 0));
    return HttpResponse.json({ items, total: items.length });
  }),

  http.get(`${API}/employer/vacancies`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    return HttpResponse.json(vacancies.filter((v) => v.employerId === auth.user!.id));
  }),

  http.post(`${API}/employer/vacancies`, async ({ request }) => {
    await delay(300);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const body = (await request.json()) as Omit<Vacancy, 'id' | 'employerId' | 'createdAt' | 'updatedAt'>;
    const now = new Date().toISOString();
    const vacancy: Vacancy = {
      ...body,
      id: `vac-${crypto.randomUUID()}`,
      employerId: auth.user!.id,
      createdAt: now,
      updatedAt: now,
    };
    vacancies.push(vacancy);
    return HttpResponse.json(vacancy, { status: 201 });
  }),

  http.get(`${API}/vacancies/:id`, async ({ params, request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const vacancy = vacancies.find((v) => v.id === params.id);
    if (!vacancy) return HttpResponse.json({ message: 'Вакансия не найдена' }, { status: 404 });
    return HttpResponse.json(vacancy);
  }),

  http.patch(`${API}/vacancies/:id`, async ({ params, request }) => {
    await delay(250);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const idx = vacancies.findIndex((v) => v.id === params.id && v.employerId === auth.user!.id);
    if (idx < 0) return HttpResponse.json({ message: 'Вакансия не найдена' }, { status: 404 });
    const body = (await request.json()) as Partial<Vacancy>;
    vacancies[idx] = {
      ...vacancies[idx],
      ...body,
      id: vacancies[idx].id,
      employerId: vacancies[idx].employerId,
      updatedAt: new Date().toISOString(),
    };
    return HttpResponse.json(vacancies[idx]);
  }),

  http.get(`${API}/vacancies`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const url = new URL(request.url);
    const specialization = url.searchParams.get('specialization');
    const matchToMe = url.searchParams.get('matchToMe') === 'true';
    const savedOnly = url.searchParams.get('savedOnly') === 'true';
    let items = vacancies.filter((v) => v.status === 'active');
    if (specialization) items = items.filter((v) => v.specialization === specialization);

    const profile =
      auth.user!.role === 'candidate'
        ? profiles.find((p) => p.userId === auth.user!.id)
        : undefined;
    const savedIds = profile ? (savedVacanciesByCandidate[profile.id] ?? []) : [];
    const appliedIds = profile ? (applicationsByCandidate[profile.id] ?? []) : [];

    if (savedOnly && profile) {
      items = items.filter((v) => savedIds.includes(v.id));
    }

    const mapped = items.map((v) => ({
      ...v,
      saved: profile ? savedIds.includes(v.id) : undefined,
      applied: profile ? appliedIds.includes(v.id) : undefined,
      match: matchToMe && profile ? computeMatch(profile.id, v.id) : undefined,
    }));

    if (matchToMe) {
      mapped.sort((a, b) => (b.match?.score ?? 0) - (a.match?.score ?? 0));
    }

    return HttpResponse.json(mapped);
  }),

  http.post(`${API}/offers`, async ({ request }) => {
    await delay(300);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const body = (await request.json()) as CreateOfferPayload;
    const offer = {
      id: `offer-${crypto.randomUUID()}`,
      ...body,
      employerId: auth.user!.id,
      status: 'new' as const,
      createdAt: new Date().toISOString(),
      respondedAt: null,
    };
    offers.unshift(offer);
    return HttpResponse.json(offer, { status: 201 });
  }),

  http.get(`${API}/candidate/offers`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json([]);
    return HttpResponse.json(offers.filter((o) => o.candidateId === profile.id));
  }),

  http.get(`${API}/employer/offers`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    return HttpResponse.json(offers.filter((o) => o.employerId === auth.user!.id));
  }),

  http.get(`${API}/offers/:id`, async ({ params, request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const offer = offers.find((o) => o.id === params.id);
    if (!offer) return HttpResponse.json({ message: 'Предложение не найдено' }, { status: 404 });
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    const isOwner =
      offer.employerId === auth.user!.id || (profile && offer.candidateId === profile.id);
    if (!isOwner) return HttpResponse.json({ message: 'Нет доступа' }, { status: 403 });
    if (profile && offer.candidateId === profile.id && offer.status === 'new') {
      offer.status = 'viewed';
    }
    return HttpResponse.json(offer);
  }),

  http.post(`${API}/offers/:id/accept`, async ({ params, request }) => {
    await delay(250);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const offer = offers.find((o) => o.id === params.id);
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!offer || !profile || offer.candidateId !== profile.id) {
      return HttpResponse.json({ message: 'Предложение не найдено' }, { status: 404 });
    }
    offer.status = 'accepted';
    offer.respondedAt = new Date().toISOString();
    return HttpResponse.json(offer);
  }),

  http.post(`${API}/offers/:id/decline`, async ({ params, request }) => {
    await delay(250);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const offer = offers.find((o) => o.id === params.id);
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!offer || !profile || offer.candidateId !== profile.id) {
      return HttpResponse.json({ message: 'Предложение не найдено' }, { status: 404 });
    }
    offer.status = 'declined';
    offer.respondedAt = new Date().toISOString();
    return HttpResponse.json(offer);
  }),

  http.get(`${API}/employer/shortlist`, async ({ request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const items = profiles.filter((p) => shortlist.includes(p.id));
    return HttpResponse.json(items);
  }),

  http.post(`${API}/employer/shortlist`, async ({ request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const body = (await request.json()) as { candidateId: string };
    if (!shortlist.includes(body.candidateId)) shortlist.push(body.candidateId);
    return HttpResponse.json({ ok: true });
  }),

  http.delete(`${API}/employer/shortlist/:candidateId`, async ({ params, request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const id = String(params.candidateId);
    const idx = shortlist.indexOf(id);
    if (idx >= 0) shortlist.splice(idx, 1);
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${API}/admin/overview`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    if (auth.user!.role !== 'admin') {
      return HttpResponse.json({ message: 'Только для администратора' }, { status: 403 });
    }
    return HttpResponse.json({
      usersTotal: users.filter((u) => u.role !== 'admin').length,
      candidates: users.filter((u) => u.role === 'candidate').length,
      employers: users.filter((u) => u.role === 'employer').length,
      vacanciesActive: vacancies.filter((v) => v.status === 'active').length,
      offersOpen: offers.filter((o) => o.status === 'new' || o.status === 'viewed').length,
      offersAccepted: offers.filter((o) => o.status === 'accepted').length,
      blockedUsers: blockedUserIds.length,
    });
  }),

  http.get(`${API}/admin/users`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    if (auth.user!.role !== 'admin') {
      return HttpResponse.json({ message: 'Только для администратора' }, { status: 403 });
    }
    return HttpResponse.json(
      users
        .filter((u) => u.role !== 'admin')
        .map((u) => ({
          ...u,
          status: blockedUserIds.includes(u.id) ? 'blocked' : 'active',
        })),
    );
  }),

  http.post(`${API}/admin/users/:userId/status`, async ({ params, request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    if (auth.user!.role !== 'admin') {
      return HttpResponse.json({ message: 'Только для администратора' }, { status: 403 });
    }
    const userId = String(params.userId);
    const user = users.find((u) => u.id === userId);
    if (!user || user.role === 'admin') {
      return HttpResponse.json({ message: 'Пользователь не найден' }, { status: 404 });
    }
    const body = (await request.json()) as { status: 'active' | 'blocked' };
    const idx = blockedUserIds.indexOf(userId);
    if (body.status === 'blocked' && idx < 0) blockedUserIds.push(userId);
    if (body.status === 'active' && idx >= 0) blockedUserIds.splice(idx, 1);
    return HttpResponse.json({
      ...user,
      status: blockedUserIds.includes(userId) ? 'blocked' : 'active',
    });
  }),

  http.get(`${API}/admin/offers`, async ({ request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    if (auth.user!.role !== 'admin') {
      return HttpResponse.json({ message: 'Только для администратора' }, { status: 403 });
    }
    return HttpResponse.json(offers);
  }),

  http.get(`${API}/admin/vacancies`, async ({ request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    if (auth.user!.role !== 'admin') {
      return HttpResponse.json({ message: 'Только для администратора' }, { status: 403 });
    }
    return HttpResponse.json(vacancies);
  }),

  http.get(`${API}/dashboard/candidate`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    const myOffers = offers.filter((o) => o.candidateId === profile?.id);
    const completeness = profile ? computeCompleteness(profile) : undefined;
    if (profile && completeness) profile.profileCompleteness = completeness.percent;
    const notifs = buildNotificationsForUser(auth.user!);
    return HttpResponse.json({
      profileViews: 42,
      offersReceived: myOffers.length,
      offersAccepted: myOffers.filter((o) => o.status === 'accepted').length,
      profileStatus: profile
        ? completeness && completeness.percent >= 80
          ? 'Заполнен'
          : 'Требует внимания'
        : 'Не создан',
      fspSyncStatus: profile?.fspSyncedAt
        ? `Синхронизировано ${new Date(profile.fspSyncedAt).toLocaleDateString('ru-RU')}`
        : 'Нет синхронизации',
      completeness,
      unreadNotifications: notifs.filter((n) => !n.read).length,
      savedVacanciesCount: profile ? (savedVacanciesByCandidate[profile.id] ?? []).length : 0,
      applicationsCount: profile ? (applicationsByCandidate[profile.id] ?? []).length : 0,
    });
  }),

  http.get(`${API}/dashboard/employer`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const myOffers = offers.filter((o) => o.employerId === auth.user!.id);
    const notifs = buildNotificationsForUser(auth.user!);
    return HttpResponse.json({
      candidatesFound: profiles.length,
      shortlistSize: shortlist.length,
      offersSent: myOffers.length,
      offersAccepted: myOffers.filter((o) => o.status === 'accepted').length,
      unreadNotifications: notifs.filter((n) => !n.read).length,
    });
  }),

  http.get(`${API}/candidates/me/completeness`, async ({ request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    const completeness = computeCompleteness(profile);
    profile.profileCompleteness = completeness.percent;
    return HttpResponse.json(completeness);
  }),

  http.get(`${API}/notifications`, async ({ request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const items = buildNotificationsForUser(auth.user!);
    return HttpResponse.json({
      items,
      unread: items.filter((n) => !n.read).length,
    });
  }),

  http.post(`${API}/notifications/:id/read`, async ({ params, request }) => {
    await delay(100);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    notificationReadIds.add(String(params.id));
    return HttpResponse.json({ ok: true });
  }),

  http.post(`${API}/notifications/read-all`, async ({ request }) => {
    await delay(100);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    buildNotificationsForUser(auth.user!).forEach((n) => notificationReadIds.add(n.id));
    return HttpResponse.json({ ok: true });
  }),

  http.get(`${API}/vacancies/:id/match-to-me`, async ({ params, request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    if (auth.user!.role !== 'candidate') {
      return HttpResponse.json({ message: 'Только для кандидатов' }, { status: 403 });
    }
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    const vacancyId = String(params.id);
    if (!vacancies.some((v) => v.id === vacancyId)) {
      return HttpResponse.json({ message: 'Вакансия не найдена' }, { status: 404 });
    }
    return HttpResponse.json(computeMatch(profile.id, vacancyId));
  }),

  http.get(`${API}/candidate/saved-vacancies`, async ({ request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    const ids = savedVacanciesByCandidate[profile.id] ?? [];
    return HttpResponse.json(vacancies.filter((v) => ids.includes(v.id)));
  }),

  http.post(`${API}/candidate/saved-vacancies/:vacancyId`, async ({ params, request }) => {
    await delay(120);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    const vacancyId = String(params.vacancyId);
    if (!vacancies.some((v) => v.id === vacancyId)) {
      return HttpResponse.json({ message: 'Вакансия не найдена' }, { status: 404 });
    }
    const list = savedVacanciesByCandidate[profile.id] ?? [];
    if (!list.includes(vacancyId)) list.push(vacancyId);
    savedVacanciesByCandidate[profile.id] = list;
    return HttpResponse.json({ ok: true, saved: true });
  }),

  http.delete(`${API}/candidate/saved-vacancies/:vacancyId`, async ({ params, request }) => {
    await delay(120);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    const vacancyId = String(params.vacancyId);
    savedVacanciesByCandidate[profile.id] = (savedVacanciesByCandidate[profile.id] ?? []).filter(
      (id) => id !== vacancyId,
    );
    return HttpResponse.json({ ok: true, saved: false });
  }),

  http.get(`${API}/dashboard/employer/analytics`, async ({ request }) => {
    await delay(250);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const myOffers = offers.filter((o) => o.employerId === auth.user!.id);
    const offersSent = myOffers.length;
    const offersAccepted = myOffers.filter((o) => o.status === 'accepted').length;
    const offersDeclined = myOffers.filter((o) => o.status === 'declined').length;
    const shortlisted = shortlist.length;
    const viewedCandidates = profiles.length;

    const bySpecializationMap = new Map<string, number>();
    const readinessMap = new Map<ReadinessStatus, number>();
    const skillMap = new Map<string, number>();
    profiles.forEach((p) => {
      bySpecializationMap.set(p.specialization, (bySpecializationMap.get(p.specialization) ?? 0) + 1);
      readinessMap.set(p.readiness, (readinessMap.get(p.readiness) ?? 0) + 1);
      p.skills.forEach((s) => skillMap.set(s, (skillMap.get(s) ?? 0) + 1));
    });

    const activeVacancy = vacancies.find((v) => v.employerId === auth.user!.id && v.status === 'active');
    let avgMatchScore: number | null = null;
    if (activeVacancy) {
      const scores = profiles.map((p) => computeMatch(p.id, activeVacancy.id).score);
      avgMatchScore = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
    }

    return HttpResponse.json({
      funnel: {
        viewedCandidates,
        shortlisted,
        offersSent,
        offersAccepted,
        offersDeclined,
      },
      conversion: {
        shortlistRate: viewedCandidates ? shortlisted / viewedCandidates : 0,
        offerAcceptRate: offersSent ? offersAccepted / offersSent : 0,
      },
      bySpecialization: Array.from(bySpecializationMap.entries()).map(([specialization, count]) => ({
        specialization,
        count,
      })),
      avgMatchScore,
      readinessBreakdown: Array.from(readinessMap.entries()).map(([readiness, count]) => ({
        readiness,
        count,
      })),
      topSkills: Array.from(skillMap.entries())
        .map(([skill, count]) => ({ skill, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 8),
    });
  }),

  http.get(`${API}/tests/history`, async ({ request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    return HttpResponse.json(testHistoryByUser[auth.user!.id] ?? []);
  }),

  http.post(`${API}/tests/sessions`, async ({ request }) => {
    await delay(200);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const body = (await request.json()) as {
      specialization: string;
      stack: string[];
      claimedGrade: Grade;
      retest?: boolean;
    };
    const id = `session-${crypto.randomUUID()}`;
    sessions[id] = {
      id,
      specialization: body.specialization,
      stack: body.stack,
      claimedGrade: body.claimedGrade,
      currentIndex: 0,
      totalQuestions: testQuestions.length,
      status: 'in_progress',
      userId: auth.user!.id,
      isRetest: Boolean(body.retest),
    };
    sessionAnswers[id] = {};
    return HttpResponse.json(sessions[id]);
  }),

  http.get(`${API}/tests/sessions/:id/question`, async ({ params, request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const session = sessions[String(params.id)];
    if (!session || session.userId !== auth.user!.id) {
      return HttpResponse.json({ message: 'Сессия не найдена' }, { status: 404 });
    }
    const q = testQuestions[session.currentIndex];
    if (!q) return HttpResponse.json({ message: 'Вопросы закончились' }, { status: 404 });
    return HttpResponse.json({
      id: q.id,
      text: q.text,
      options: q.options,
    });
  }),

  http.post(`${API}/tests/sessions/:id/answer`, async ({ params, request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const session = sessions[String(params.id)];
    if (!session || session.userId !== auth.user!.id) {
      return HttpResponse.json({ message: 'Сессия не найдена' }, { status: 404 });
    }
    const body = (await request.json()) as { questionId: string; optionId: string };
    sessionAnswers[session.id][body.questionId] = body.optionId;
    if (session.currentIndex < session.totalQuestions - 1) {
      session.currentIndex += 1;
    }
    return HttpResponse.json(session);
  }),

  http.post(`${API}/tests/sessions/:id/finish`, async ({ params, request }) => {
    await delay(300);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const session = sessions[String(params.id)];
    if (!session || session.userId !== auth.user!.id) {
      return HttpResponse.json({ message: 'Сессия не найдена' }, { status: 404 });
    }
    session.status = 'completed';
    const answers = sessionAnswers[session.id] ?? {};
    let correct = 0;
    testQuestions.forEach((q) => {
      if (answers[q.id] === q.correctOptionId) correct += 1;
    });
    const score = Math.round((correct / testQuestions.length) * 100);
    const result = {
      sessionId: session.id,
      score,
      maxScore: 100,
      gradeConfirmed: score >= 70,
      completedAt: new Date().toISOString(),
      claimedGrade: session.claimedGrade,
      isRetest: session.isRetest,
      specialization: session.specialization,
    };
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (profile) {
      profile.testResult = {
        score: result.score,
        maxScore: result.maxScore,
        gradeConfirmed: result.gradeConfirmed,
        completedAt: result.completedAt,
      };
      if (result.gradeConfirmed) profile.confirmedGrade = profile.claimedGrade;
    }
    const history = testHistoryByUser[auth.user!.id] ?? [];
    history.unshift(result);
    testHistoryByUser[auth.user!.id] = history;
    return HttpResponse.json(result);
  }),

  http.get(`${API}/tests/sessions/:id/result`, async ({ params, request }) => {
    await delay(150);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    const session = sessions[String(params.id)];
    if (!session || session.userId !== auth.user!.id || session.status !== 'completed') {
      return HttpResponse.json({ message: 'Результат недоступен' }, { status: 404 });
    }
    const fromHistory = (testHistoryByUser[auth.user!.id] ?? []).find(
      (h) => h.sessionId === session.id,
    );
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    return HttpResponse.json({
      sessionId: session.id,
      claimedGrade: session.claimedGrade,
      isRetest: session.isRetest,
      score: fromHistory?.score ?? profile?.testResult?.score ?? 0,
      maxScore: fromHistory?.maxScore ?? profile?.testResult?.maxScore ?? 100,
      gradeConfirmed:
        fromHistory?.gradeConfirmed ?? profile?.testResult?.gradeConfirmed ?? false,
      completedAt:
        fromHistory?.completedAt ??
        profile?.testResult?.completedAt ??
        new Date().toISOString(),
    });
  }),

  http.post(`${API}/vacancies/:id/apply`, async ({ params, request }) => {
    await delay(250);
    const auth = requireUser(request);
    if ('error' in auth && auth.error) return auth.error;
    if (auth.user!.role !== 'candidate') {
      return HttpResponse.json({ message: 'Только для кандидатов' }, { status: 403 });
    }
    const profile = profiles.find((p) => p.userId === auth.user!.id);
    if (!profile) return HttpResponse.json({ message: 'Профиль не найден' }, { status: 404 });
    const vacancyId = String(params.id);
    if (!vacancies.some((v) => v.id === vacancyId)) {
      return HttpResponse.json({ message: 'Вакансия не найдена' }, { status: 404 });
    }
    const list = applicationsByCandidate[profile.id] ?? [];
    if (!list.includes(vacancyId)) list.push(vacancyId);
    applicationsByCandidate[profile.id] = list;
    return HttpResponse.json({ ok: true, message: 'Отклик отправлен' });
  }),
];
