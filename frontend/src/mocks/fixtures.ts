import type {
  AdminAssessmentsResponse,
  AdminCategoriesResponse,
  AdminEvent,
  AppNotification,
  AuthUser,
  CandidateCompareResponse,
  CandidateMatch,
  CandidateProfile,
  FspAchievement,
  Offer,
  ProfileCompleteness,
  SkillRadar,
  Vacancy,
  VacancyParseResult,
} from '@/entities/types';

export const DEMO_PASSWORD = 'demo1234';

function seedUsers(): AuthUser[] {
  return [
    {
      id: 'user-cand-1',
      email: 'candidate@demo.ru',
      role: 'candidate',
      displayName: 'Анна Ковалёва',
    },
    {
      id: 'user-cand-2',
      email: 'maxim@demo.ru',
      role: 'candidate',
      displayName: 'Максим Орлов',
    },
    {
      id: 'user-cand-3',
      email: 'elena@demo.ru',
      role: 'candidate',
      displayName: 'Елена Ветрова',
    },
    {
      id: 'user-cand-4',
      email: 'denis@demo.ru',
      role: 'candidate',
      displayName: 'Денис Крылов',
    },
    {
      id: 'user-cand-5',
      email: 'sofia@demo.ru',
      role: 'candidate',
      displayName: 'София Белова',
    },
    {
      id: 'user-emp-1',
      email: 'employer@demo.ru',
      role: 'employer',
      displayName: 'Игорь Смирнов',
    },
    {
      id: 'user-emp-2',
      email: 'hr@demo.ru',
      role: 'employer',
      displayName: 'Мария Кузнецова',
    },
    {
      id: 'user-admin-1',
      email: 'admin@demo.ru',
      role: 'admin',
      displayName: 'Админ Resonance',
    },
  ];
}

/** Demo registration timestamps for admin user table. */
export const userCreatedAt: Record<string, string> = {
  'user-cand-1': '2026-08-12T09:00:00.000Z',
  'user-cand-2': '2026-08-20T11:30:00.000Z',
  'user-cand-3': '2026-09-01T14:15:00.000Z',
  'user-cand-4': '2026-09-10T08:40:00.000Z',
  'user-cand-5': '2026-09-22T16:20:00.000Z',
  'user-emp-1': '2026-08-05T10:00:00.000Z',
  'user-emp-2': '2026-09-18T12:00:00.000Z',
  'user-admin-1': '2026-07-01T08:00:00.000Z',
};

export const blockReasons: Record<string, string> = {};

function seedProfiles(): CandidateProfile[] {
  return [
    {
      id: 'cand-1',
      userId: 'user-cand-1',
      fullName: 'Анна Ковалёва',
      about: 'Frontend-разработчик с фокусом на React и доступность интерфейсов.',
      specialization: 'Frontend',
      claimedGrade: 'middle',
      confirmedGrade: 'middle',
      experienceYears: 4,
      experienceDescription: 'SPA, дизайн-системы, Code Review, менторство джунов.',
      skills: ['React', 'TypeScript', 'CSS', 'Vite', 'Redux'],
      desiredPosition: 'Frontend Engineer',
      salaryFrom: 250000,
      salaryTo: 320000,
      currency: 'RUB',
      city: 'Москва',
      workFormat: 'remote',
      readiness: 'open_to_offers',
      testResult: {
        score: 82,
        maxScore: 100,
        gradeConfirmed: true,
        completedAt: '2026-09-12T10:00:00.000Z',
      },
      fspSyncedAt: '2026-10-01T12:00:00.000Z',
      hasFspAchievements: true,
      profileCompleteness: 90,
    },
    {
      id: 'cand-2',
      userId: 'user-cand-2',
      fullName: 'Максим Орлов',
      about: 'Backend на Go и Python, хакатоны ФСП.',
      specialization: 'Backend',
      claimedGrade: 'senior',
      experienceYears: 6,
      skills: ['Go', 'Python', 'PostgreSQL', 'Kafka'],
      desiredPosition: 'Backend Engineer',
      salaryFrom: 300000,
      salaryTo: 400000,
      currency: 'RUB',
      city: 'Санкт-Петербург',
      workFormat: 'hybrid',
      readiness: 'actively_looking',
      hasFspAchievements: true,
      fspSyncedAt: '2026-09-20T09:00:00.000Z',
    },
    {
      id: 'cand-3',
      userId: 'user-cand-3',
      fullName: 'Елена Ветрова',
      specialization: 'Frontend',
      claimedGrade: 'junior',
      experienceYears: 1,
      skills: ['React', 'JavaScript', 'HTML', 'CSS'],
      desiredPosition: 'Junior Frontend',
      salaryFrom: 120000,
      salaryTo: 160000,
      currency: 'RUB',
      city: 'Казань',
      workFormat: 'office',
      readiness: 'actively_looking',
      hasFspAchievements: false,
    },
    {
      id: 'cand-4',
      userId: 'user-cand-4',
      fullName: 'Денис Крылов',
      specialization: 'Fullstack',
      claimedGrade: 'middle',
      experienceYears: 3,
      skills: ['React', 'TypeScript', 'Node.js', 'PostgreSQL'],
      desiredPosition: 'Fullstack Developer',
      salaryFrom: 220000,
      salaryTo: 280000,
      currency: 'RUB',
      city: 'Екатеринбург',
      workFormat: 'remote',
      readiness: 'open_to_offers',
      hasFspAchievements: true,
      fspSyncedAt: '2026-08-15T08:00:00.000Z',
    },
    {
      id: 'cand-5',
      userId: 'user-cand-5',
      fullName: 'София Белова',
      specialization: 'Frontend',
      claimedGrade: 'senior',
      experienceYears: 7,
      skills: ['React', 'TypeScript', 'Next.js', 'GraphQL', 'Jest'],
      desiredPosition: 'Senior Frontend',
      salaryFrom: 350000,
      salaryTo: 450000,
      currency: 'RUB',
      city: 'Москва',
      workFormat: 'hybrid',
      readiness: 'not_looking',
      hasFspAchievements: false,
    },
  ];
}

function seedFsp(): Record<string, FspAchievement[]> {
  return {
    'cand-1': [
      {
        id: 'fsp-1',
        title: 'Кубок ФСП по веб-разработке',
        discipline: 'Frontend',
        date: '2025-11-10',
        placeOrResult: '2 место',
        participantRole: 'Участник',
        sportRank: '1 разряд',
        verified: true,
      },
      {
        id: 'fsp-2',
        title: 'Хакатон Digital Breakthrough',
        discipline: 'Web',
        date: '2024-05-18',
        placeOrResult: 'Финалист',
        participantRole: 'Team Lead',
        verified: true,
      },
    ],
    'cand-2': [
      {
        id: 'fsp-3',
        title: 'ФСП Algorithms Open',
        discipline: 'Algorithms',
        date: '2025-03-02',
        placeOrResult: '1 место',
        participantRole: 'Участник',
        verified: true,
      },
    ],
    'cand-4': [
      {
        id: 'fsp-4',
        title: 'ФСП Fullstack Challenge',
        discipline: 'Fullstack',
        date: '2025-07-21',
        placeOrResult: '3 место',
        verified: true,
      },
    ],
  };
}

function seedVacancies(): Vacancy[] {
  return [
    {
      id: 'vac-1',
      employerId: 'user-emp-1',
      companyName: 'Resonance Labs',
      title: 'Frontend Engineer (React)',
      description:
        'Развиваем продукт обратного рекрутинга. Нужен сильный React/TS, опыт с дизайн-системами.',
      specialization: 'Frontend',
      requiredGrade: 'middle',
      requiredSkills: ['React', 'TypeScript'],
      niceToHaveSkills: ['Jest', 'Vite'],
      salaryFrom: 260000,
      salaryTo: 340000,
      currency: 'RUB',
      city: 'Москва',
      workFormat: 'remote',
      status: 'active',
      createdAt: '2026-09-01T10:00:00.000Z',
      updatedAt: '2026-09-15T10:00:00.000Z',
    },
    {
      id: 'vac-2',
      employerId: 'user-emp-1',
      companyName: 'Resonance Labs',
      title: 'Backend Engineer (Go)',
      description: 'API, интеграции ФСП, matching pipeline.',
      specialization: 'Backend',
      requiredGrade: 'senior',
      requiredSkills: ['Go', 'PostgreSQL'],
      niceToHaveSkills: ['Kafka'],
      salaryFrom: 320000,
      salaryTo: 420000,
      currency: 'RUB',
      city: 'Санкт-Петербург',
      workFormat: 'hybrid',
      status: 'active',
      createdAt: '2026-09-10T10:00:00.000Z',
      updatedAt: '2026-09-20T10:00:00.000Z',
    },
  ];
}

function seedOffers(): Offer[] {
  return [
    {
      id: 'offer-1',
      vacancyId: 'vac-1',
      candidateId: 'cand-1',
      employerId: 'user-emp-1',
      companyName: 'Resonance Labs',
      positionTitle: 'Frontend Engineer (React)',
      salaryFrom: 280000,
      salaryTo: 320000,
      currency: 'RUB',
      workFormat: 'remote',
      message: 'Нам близки ваш стек и опыт с ФСП. Готовы обсудить старт в ноябре.',
      status: 'new',
      createdAt: '2026-10-05T14:00:00.000Z',
    },
  ];
}

function seedContacts() {
  return {
    'cand-1': {
      email: 'anna.kovaleva@demo.ru',
      phone: '+7 999 111-22-33',
      telegram: '@anna_front',
    },
    'cand-2': {
      email: 'maxim.orlov@demo.ru',
      telegram: '@orlov_go',
    },
  } as Record<string, { email?: string; phone?: string; telegram?: string }>;
}

/** Mutable in-memory DB used by MSW. Reset between tests. */
export const users: AuthUser[] = seedUsers();
export const profiles: CandidateProfile[] = seedProfiles();
export const fspByCandidate: Record<string, FspAchievement[]> = seedFsp();
export const vacancies: Vacancy[] = seedVacancies();
export const offers: Offer[] = seedOffers();
export const shortlist: string[] = ['cand-2'];
export const contactsByCandidate = seedContacts();
/** Admin moderation: blocked user ids */
export const blockedUserIds: string[] = [];
/** candidateId → vacancyIds */
export const savedVacanciesByCandidate: Record<string, string[]> = { 'cand-1': [] };
/** candidateId → vacancyIds already applied */
export const applicationsByCandidate: Record<string, string[]> = { 'cand-1': [] };
/** userId → notification read overrides / extras */
export const notificationReadIds = new Set<string>();
export const extraNotifications: AppNotification[] = [];

export function resetMockDb() {
  users.splice(0, users.length, ...seedUsers());
  profiles.splice(0, profiles.length, ...structuredClone(seedProfiles()));
  vacancies.splice(0, vacancies.length, ...structuredClone(seedVacancies()));
  offers.splice(0, offers.length, ...structuredClone(seedOffers()));
  shortlist.splice(0, shortlist.length, 'cand-2');
  blockedUserIds.splice(0, blockedUserIds.length);
  for (const key of Object.keys(blockReasons)) delete blockReasons[key];
  notificationReadIds.clear();
  extraNotifications.splice(0, extraNotifications.length);

  for (const key of Object.keys(fspByCandidate)) delete fspByCandidate[key];
  Object.assign(fspByCandidate, structuredClone(seedFsp()));

  for (const key of Object.keys(contactsByCandidate)) delete contactsByCandidate[key];
  Object.assign(contactsByCandidate, seedContacts());

  for (const key of Object.keys(savedVacanciesByCandidate)) delete savedVacanciesByCandidate[key];
  savedVacanciesByCandidate['cand-1'] = [];

  for (const key of Object.keys(applicationsByCandidate)) delete applicationsByCandidate[key];
  applicationsByCandidate['cand-1'] = [];
}

/** Backend-owned completeness — frontend only renders. */
export function computeCompleteness(profile: CandidateProfile): ProfileCompleteness {
  const items = [
    {
      key: 'about',
      label: 'О себе',
      done: Boolean(profile.about && profile.about.length >= 20),
      weight: 10,
      href: '/candidate/profile/edit',
    },
    {
      key: 'skills',
      label: 'Навыки (минимум 3)',
      done: profile.skills.length >= 3,
      weight: 15,
      href: '/candidate/profile/edit',
    },
    {
      key: 'salary',
      label: 'Зарплатные ожидания',
      done: Boolean(profile.salaryFrom && profile.salaryTo),
      weight: 10,
      href: '/candidate/profile/edit',
    },
    {
      key: 'city',
      label: 'Город',
      done: Boolean(profile.city),
      weight: 5,
      href: '/candidate/profile/edit',
    },
    {
      key: 'format',
      label: 'Формат работы',
      done: Boolean(profile.workFormat),
      weight: 10,
      href: '/candidate/profile/edit',
    },
    {
      key: 'position',
      label: 'Желаемая должность',
      done: Boolean(profile.desiredPosition),
      weight: 10,
      href: '/candidate/profile/edit',
    },
    {
      key: 'experience',
      label: 'Опыт',
      done: Boolean(profile.experienceYears != null || profile.experienceDescription),
      weight: 10,
      href: '/candidate/profile/edit',
    },
    {
      key: 'fsp',
      label: 'Синхронизация ФСП',
      done: Boolean(profile.fspSyncedAt),
      weight: 15,
      href: '/candidate/fsp',
    },
    {
      key: 'test',
      label: 'Профессиональный тест',
      done: Boolean(profile.testResult),
      weight: 15,
      href: '/candidate/testing',
    },
  ];
  const total = items.reduce((sum, i) => sum + i.weight, 0);
  const earned = items.filter((i) => i.done).reduce((sum, i) => sum + i.weight, 0);
  const percent = Math.round((earned / total) * 100);
  return { percent, items };
}

export function buildNotificationsForUser(user: AuthUser): AppNotification[] {
  const derived: AppNotification[] = [];

  if (user.role === 'candidate') {
    const profile = profiles.find((p) => p.userId === user.id);
    if (profile) {
      offers
        .filter((o) => o.candidateId === profile.id)
        .forEach((o) => {
          if (o.status === 'new' || o.status === 'viewed') {
            derived.push({
              id: `notif-offer-${o.id}`,
              type: 'offer_new',
              title: 'Новое предложение',
              body: `${o.companyName}: ${o.positionTitle}`,
              createdAt: o.createdAt,
              read: notificationReadIds.has(`notif-offer-${o.id}`) || o.status === 'viewed',
              href: `/candidate/offers/${o.id}`,
            });
          }
        });
      if (profile.fspSyncedAt) {
        derived.push({
          id: `notif-fsp-${profile.id}`,
          type: 'fsp_synced',
          title: 'ФСП синхронизирован',
          body: 'Достижения обновлены и доступны работодателям.',
          createdAt: profile.fspSyncedAt,
          read: notificationReadIds.has(`notif-fsp-${profile.id}`),
          href: '/candidate/fsp',
        });
      }
    }
  }

  if (user.role === 'employer') {
    offers
      .filter((o) => o.employerId === user.id && (o.status === 'accepted' || o.status === 'declined'))
      .forEach((o) => {
        const id = `notif-resp-${o.id}`;
        derived.push({
          id,
          type: o.status === 'accepted' ? 'offer_accepted' : 'offer_declined',
          title: o.status === 'accepted' ? 'Оффер принят' : 'Оффер отклонён',
          body: `${o.positionTitle} · ${o.companyName}`,
          createdAt: o.respondedAt ?? o.createdAt,
          read: notificationReadIds.has(id),
          href: '/employer/offers',
        });
      });
  }

  const extras = extraNotifications.filter(
    (n) => n.id.startsWith(`user-${user.id}-`) || n.id.startsWith('global-'),
  );

  return [...extras, ...derived].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
}

/** Mock-backend matching only. Not used by UI production components. */
export function computeMatch(candidateId: string, vacancyId: string): CandidateMatch {
  const candidate = profiles.find((p) => p.id === candidateId)!;
  const vacancy = vacancies.find((v) => v.id === vacancyId)!;
  const matchedSkills = vacancy.requiredSkills.filter((s) =>
    candidate.skills.some((cs) => cs.toLowerCase() === s.toLowerCase()),
  );
  const missingInProfileSkills = [
    ...vacancy.requiredSkills,
    ...vacancy.niceToHaveSkills,
  ].filter(
    (s, i, arr) =>
      arr.indexOf(s) === i &&
      !candidate.skills.some((cs) => cs.toLowerCase() === s.toLowerCase()),
  );

  let score = 40;
  if (candidate.specialization === vacancy.specialization) score += 20;
  if (candidate.claimedGrade === vacancy.requiredGrade) score += 15;
  if (candidate.workFormat === vacancy.workFormat) score += 10;
  score += matchedSkills.length * 8;
  if (candidate.hasFspAchievements) score += 5;
  score = Math.min(98, score);

  const reasons = [
    {
      code: 'spec',
      label:
        candidate.specialization === vacancy.specialization
          ? `совпадает специализация ${vacancy.specialization}`
          : `специализация кандидата: ${candidate.specialization}`,
      positive: candidate.specialization === vacancy.specialization,
    },
    ...matchedSkills.map((s) => ({
      code: `skill-${s}`,
      label: `${s} указан в профиле`,
      positive: true,
    })),
    {
      code: 'format',
      label:
        candidate.workFormat === vacancy.workFormat
          ? `подходит формат ${vacancy.workFormat}`
          : `формат кандидата: ${candidate.workFormat ?? 'не указан'}`,
      positive: candidate.workFormat === vacancy.workFormat,
    },
  ];

  if (candidate.hasFspAchievements) {
    reasons.push({
      code: 'fsp',
      label: 'есть релевантные достижения ФСП',
      positive: true,
    });
  }

  return {
    candidateId,
    vacancyId,
    score,
    matchedSkills,
    missingInProfileSkills,
    reasons,
    relevantFsp: fspByCandidate[candidateId]?.slice(0, 2),
  };
}

/** Mock-backend skill radar. UI must not reimplement this. */
export function computeSkillRadar(candidateId: string): SkillRadar {
  const candidate = profiles.find((p) => p.id === candidateId);
  if (!candidate) return { candidateId, axes: [] };
  const base = candidate.claimedGrade === 'senior' || candidate.claimedGrade === 'lead' ? 78 : 62;
  const axes = candidate.skills.slice(0, 6).map((skill, index) => ({
    skill,
    score: Math.min(98, base + ((index * 7 + skill.length) % 20)),
  }));
  return { candidateId, axes };
}

export function computeCompare(ids: string[]): CandidateCompareResponse {
  const candidates = ids
    .map((id) => profiles.find((p) => p.id === id))
    .filter((p): p is CandidateProfile => Boolean(p));
  const skills = Array.from(new Set(candidates.flatMap((c) => c.skills)));
  const skillMatrix = skills.map((skill) => ({
    skill,
    values: Object.fromEntries(
      candidates.map((c) => {
        const has = c.skills.some((s) => s.toLowerCase() === skill.toLowerCase());
        if (!has) return [c.id, null];
        const radar = computeSkillRadar(c.id).axes.find((a) => a.skill === skill);
        return [c.id, radar?.score ?? 70];
      }),
    ) as Record<string, number | null>,
  }));
  return {
    candidates,
    skillMatrix,
    radars: candidates.map((c) => computeSkillRadar(c.id)),
  };
}

export function parseVacancyText(text: string): VacancyParseResult {
  const lower = text.toLowerCase();
  const skills = ['React', 'TypeScript', 'JavaScript', 'Node.js', 'Go', 'PostgreSQL', 'Jest', 'GraphQL']
    .filter((s) => lower.includes(s.toLowerCase()));
  const grade =
    lower.includes('senior') || lower.includes('сеньор')
      ? 'senior'
      : lower.includes('junior') || lower.includes('джун')
        ? 'junior'
        : 'middle';
  const workFormat = lower.includes('remote') || lower.includes('удал')
    ? 'remote'
    : lower.includes('hybrid') || lower.includes('гибрид')
      ? 'hybrid'
      : 'office';
  const salaryMatch = text.match(/(\d{2,3})\s*[–-]\s*(\d{2,3})\s*тыс/i);
  return {
    title: text.split('\n')[0]?.slice(0, 80) || 'Новая вакансия',
    description: text.slice(0, 600),
    specialization: lower.includes('backend') ? 'Backend' : 'Frontend',
    requiredGrade: grade,
    requiredSkills: skills.slice(0, 3).length ? skills.slice(0, 3) : ['React', 'TypeScript'],
    niceToHaveSkills: skills.slice(3),
    salaryFrom: salaryMatch ? Number(salaryMatch[1]) * 1000 : 250000,
    salaryTo: salaryMatch ? Number(salaryMatch[2]) * 1000 : 350000,
    workFormat,
    city: lower.includes('моск') ? 'Москва' : undefined,
  };
}

export const testQuestions = [
  {
    id: 'q1',
    text: 'Что делает ключ key в списках React?',
    options: [
      { id: 'a', text: 'Ускоряет CSS' },
      { id: 'b', text: 'Помогает reconciliation идентифицировать элементы' },
      { id: 'c', text: 'Включает Strict Mode' },
      { id: 'd', text: 'Заменяет useMemo' },
    ],
    correctOptionId: 'b',
  },
  {
    id: 'q2',
    text: 'Какой хук подходит для синхронизации с внешней системой?',
    options: [
      { id: 'a', text: 'useEffect' },
      { id: 'b', text: 'useId' },
      { id: 'c', text: 'useDebugValue' },
      { id: 'd', text: 'useReducer' },
    ],
    correctOptionId: 'a',
  },
  {
    id: 'q3',
    text: 'Что такое discriminated union в TypeScript?',
    options: [
      { id: 'a', text: 'Объединение через & с общим полем-дискриминатором' },
      { id: 'b', text: 'Union с общим литеральным полем для сужения типов' },
      { id: 'c', text: 'Только enum' },
      { id: 'd', text: 'Any alias' },
    ],
    correctOptionId: 'b',
  },
];

export function seedAdminEvents(): AdminEvent[] {
  return [
    {
      id: 'evt-1',
      type: 'test_completed',
      title: 'Кандидат завершил тестирование',
      description: 'Анна Ковалёва · Frontend / Middle',
      createdAt: '2026-10-10T15:20:00.000Z',
      href: '/admin/assessments',
    },
    {
      id: 'evt-2',
      type: 'offer_sent',
      title: 'Работодатель отправил приглашение',
      description: 'Resonance Labs → Frontend Engineer',
      createdAt: '2026-10-05T14:00:00.000Z',
      href: '/admin/offers',
    },
    {
      id: 'evt-3',
      type: 'user_registered',
      title: 'Зарегистрирован новый пользователь',
      description: 'София Белова · кандидат',
      createdAt: '2026-09-22T16:20:00.000Z',
      href: '/admin/users',
    },
    {
      id: 'evt-4',
      type: 'category_confirmed',
      title: 'Подтверждена профессиональная категория',
      description: 'Frontend / Middle',
      createdAt: '2026-09-12T10:05:00.000Z',
      href: '/admin/categories',
    },
  ];
}

export function seedAdminAssessments(): AdminAssessmentsResponse {
  return {
    catalog: [
      {
        id: 'test-fe-junior',
        specialization: 'Frontend',
        grade: 'junior',
        questionCount: 20,
        status: 'active',
        topics: [
          { name: 'HTML/CSS', difficulty: 'easy', count: 6 },
          { name: 'JavaScript', difficulty: 'medium', count: 8 },
          { name: 'React basics', difficulty: 'medium', count: 6 },
        ],
      },
      {
        id: 'test-fe-middle',
        specialization: 'Frontend',
        grade: 'middle',
        questionCount: 24,
        status: 'active',
        topics: [
          { name: 'React', difficulty: 'medium', count: 8 },
          { name: 'TypeScript', difficulty: 'medium', count: 8 },
          { name: 'Performance', difficulty: 'hard', count: 8 },
        ],
      },
      {
        id: 'test-be-middle',
        specialization: 'Backend',
        grade: 'middle',
        questionCount: 22,
        status: 'active',
        topics: [
          { name: 'API design', difficulty: 'medium', count: 8 },
          { name: 'SQL', difficulty: 'medium', count: 7 },
          { name: 'Concurrency', difficulty: 'hard', count: 7 },
        ],
      },
      {
        id: 'test-fs-senior',
        specialization: 'Fullstack',
        grade: 'senior',
        questionCount: 28,
        status: 'draft',
        topics: [
          { name: 'Architecture', difficulty: 'hard', count: 10 },
          { name: 'DevOps', difficulty: 'hard', count: 8 },
          { name: 'Frontend', difficulty: 'medium', count: 10 },
        ],
      },
    ],
    templates: [
      {
        id: 'tpl-1',
        specialization: 'Frontend',
        topic: 'React',
        difficulty: 'medium',
        parameterized: true,
        active: true,
        promptPreview: 'Что произойдёт при рендере списка без стабильного key?',
      },
      {
        id: 'tpl-2',
        specialization: 'Frontend',
        topic: 'TypeScript',
        difficulty: 'hard',
        parameterized: true,
        active: true,
        promptPreview: 'Как сузить union по discriminant field {{field}}?',
      },
      {
        id: 'tpl-3',
        specialization: 'Backend',
        topic: 'SQL',
        difficulty: 'medium',
        parameterized: false,
        active: true,
        promptPreview: 'Какой индекс ускорит поиск по (user_id, created_at)?',
      },
      {
        id: 'tpl-4',
        specialization: 'Backend',
        topic: 'Concurrency',
        difficulty: 'hard',
        parameterized: true,
        active: false,
        promptPreview: 'Выберите корректную модель изоляции для {{scenario}}.',
      },
    ],
    attempts: [
      {
        id: 'att-1',
        userId: 'user-cand-1',
        displayName: 'Анна Ковалёва',
        specialization: 'Frontend',
        grade: 'middle',
        score: 82,
        maxScore: 100,
        passed: true,
        completedAt: '2026-09-12T10:00:00.000Z',
        nextRetestAt: '2026-12-12T10:00:00.000Z',
      },
      {
        id: 'att-2',
        userId: 'user-cand-3',
        displayName: 'Елена Ветрова',
        specialization: 'Frontend',
        grade: 'junior',
        score: 54,
        maxScore: 100,
        passed: false,
        completedAt: '2026-10-01T09:30:00.000Z',
        nextRetestAt: '2026-10-15T09:30:00.000Z',
      },
      {
        id: 'att-3',
        userId: 'user-cand-4',
        displayName: 'Денис Крылов',
        specialization: 'Fullstack',
        grade: 'middle',
        score: 71,
        maxScore: 100,
        passed: true,
        completedAt: '2026-10-08T18:00:00.000Z',
        nextRetestAt: '2027-01-08T18:00:00.000Z',
      },
    ],
    stats: {
      successRate: 0.67,
      totalAttempts: 3,
      scoreDistribution: [
        { bucket: '0–49', count: 0 },
        { bucket: '50–69', count: 1 },
        { bucket: '70–84', count: 1 },
        { bucket: '85–100', count: 1 },
      ],
    },
  };
}

export function seedAdminCategories(): AdminCategoriesResponse {
  return {
    categories: [
      { id: 'cat-fe-junior', specialization: 'Frontend', grade: 'junior', confirmedCandidates: 0 },
      { id: 'cat-fe-middle', specialization: 'Frontend', grade: 'middle', confirmedCandidates: 1 },
      { id: 'cat-fe-senior', specialization: 'Frontend', grade: 'senior', confirmedCandidates: 0 },
      { id: 'cat-be-middle', specialization: 'Backend', grade: 'middle', confirmedCandidates: 0 },
      { id: 'cat-be-senior', specialization: 'Backend', grade: 'senior', confirmedCandidates: 0 },
      { id: 'cat-fs-middle', specialization: 'Fullstack', grade: 'middle', confirmedCandidates: 0 },
    ],
    specializations: [
      { id: 'spec-fe', name: 'Frontend' },
      { id: 'spec-be', name: 'Backend' },
      { id: 'spec-fs', name: 'Fullstack' },
      { id: 'spec-mobile', name: 'Mobile' },
      { id: 'spec-devops', name: 'DevOps' },
      { id: 'spec-ds', name: 'Data Science' },
      { id: 'spec-qa', name: 'QA' },
    ],
    grades: [
      { id: 'g-junior', code: 'junior', name: 'Junior' },
      { id: 'g-middle', code: 'middle', name: 'Middle' },
      { id: 'g-senior', code: 'senior', name: 'Senior' },
    ],
    skills: [
      { id: 'sk-react', name: 'React', aliases: ['React.js', 'ReactJS'] },
      { id: 'sk-ts', name: 'TypeScript', aliases: ['TS'] },
      { id: 'sk-go', name: 'Go', aliases: ['Golang'] },
      { id: 'sk-py', name: 'Python' },
      { id: 'sk-pg', name: 'PostgreSQL', aliases: ['Postgres'] },
      { id: 'sk-node', name: 'Node.js', aliases: ['Node'] },
    ],
    industries: [
      { id: 'ind-fintech', name: 'Финтех' },
      { id: 'ind-edtech', name: 'EdTech' },
      { id: 'ind-ecommerce', name: 'E-commerce' },
      { id: 'ind-gaming', name: 'Геймдев' },
      { id: 'ind-enterprise', name: 'Enterprise' },
    ],
  };
}
