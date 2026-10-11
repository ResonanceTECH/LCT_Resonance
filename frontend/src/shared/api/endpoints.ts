import { apiClient } from '@/shared/api/client';
import type {
  AdminAssessmentsResponse,
  AdminCategoriesResponse,
  AdminOverview,
  AdminUserRow,
  AppNotification,
  AuthResponse,
  AuthUser,
  CandidateCompareResponse,
  CandidateContacts,
  CandidateDashboard,
  CandidateMatch,
  CandidatePassport,
  CandidateProfile,
  Consent,
  ConsentType,
  CreateOfferPayload,
  EmployerAnalytics,
  EmployerDashboard,
  FspAchievementsResponse,
  Grade,
  LoginPayload,
  Offer,
  ProfileCompleteness,
  PublicPassport,
  RegisterPayload,
  SkillRadar,
  TalentPoolFilters,
  TalentPoolResponse,
  TestHistoryItem,
  TestQuestion,
  TestResult,
  TestSession,
  Vacancy,
  VacancyParseResult,
  VacancyWithMatch,
} from '@/entities/types';

export const authApi = {
  login: (payload: LoginPayload) =>
    apiClient<AuthResponse>('/auth/login', { method: 'POST', body: payload, auth: false }),
  register: (payload: RegisterPayload) =>
    apiClient<AuthResponse>('/auth/register', { method: 'POST', body: payload, auth: false }),
  logout: () => apiClient<void>('/auth/logout', { method: 'POST' }),
  me: () => apiClient<AuthUser>('/auth/me'),
  resendVerification: () =>
    apiClient<{ ok: boolean }>('/auth/resend-verification', { method: 'POST' }),
};

export const candidateApi = {
  me: () => apiClient<CandidateProfile>('/candidates/me'),
  updateMe: (payload: Partial<CandidateProfile>) =>
    apiClient<CandidateProfile>('/candidates/me', { method: 'PATCH', body: payload }),
  byId: (id: string) => apiClient<CandidateProfile>(`/candidates/${id}`),
  contacts: (id: string) => apiClient<CandidateContacts>(`/candidates/${id}/contacts`),
  fspAchievements: () => apiClient<FspAchievementsResponse>('/candidates/me/fsp/achievements'),
  fspByCandidateId: (id: string) =>
    apiClient<FspAchievementsResponse>(`/candidates/${id}/fsp/achievements`),
  fspSync: () =>
    apiClient<FspAchievementsResponse>('/candidates/me/fsp/sync', { method: 'POST' }),
  list: (filters: TalentPoolFilters = {}) =>
    apiClient<TalentPoolResponse>('/candidates', {
      params: filters as Record<string, string | number | boolean | undefined | null>,
    }),
  skillRadar: (id: string) => apiClient<SkillRadar>(`/candidates/${id}/skill-radar`),
  compare: (ids: string[]) =>
    apiClient<CandidateCompareResponse>('/employer/candidates/compare', {
      params: { ids: ids.join(',') },
    }),
  completeness: () => apiClient<ProfileCompleteness>('/candidates/me/completeness'),
  consents: () => apiClient<Consent[]>('/candidates/me/consents'),
  updateConsents: (consents: { type: ConsentType; accepted: boolean }[]) =>
    apiClient<Consent[]>('/candidates/me/consents', { method: 'PUT', body: { consents } }),
  passport: () => apiClient<CandidatePassport>('/candidates/me/passport'),
};

export const publicApi = {
  passport: (slug: string) =>
    apiClient<PublicPassport>(`/public/passports/${encodeURIComponent(slug)}`, { auth: false }),
};

export const vacancyApi = {
  employerList: () => apiClient<Vacancy[]>('/employer/vacancies'),
  create: (payload: Omit<Vacancy, 'id' | 'employerId' | 'createdAt' | 'updatedAt'>) =>
    apiClient<Vacancy>('/employer/vacancies', { method: 'POST', body: payload }),
  byId: (id: string) => apiClient<Vacancy>(`/vacancies/${id}`),
  update: (id: string, payload: Partial<Vacancy>) =>
    apiClient<Vacancy>(`/vacancies/${id}`, { method: 'PATCH', body: payload }),
  publicList: (params?: {
    specialization?: string;
    matchToMe?: boolean;
    savedOnly?: boolean;
  }) =>
    apiClient<VacancyWithMatch[]>('/vacancies', {
      params: {
        specialization: params?.specialization,
        matchToMe: params?.matchToMe ? 'true' : undefined,
        savedOnly: params?.savedOnly ? 'true' : undefined,
      },
    }),
  matchToMe: (id: string) => apiClient<CandidateMatch>(`/vacancies/${id}/match-to-me`),
  apply: (id: string) =>
    apiClient<{ ok: boolean; message: string }>(`/vacancies/${id}/apply`, { method: 'POST' }),
  parseAi: (text: string) =>
    apiClient<VacancyParseResult>('/vacancies/parse', { method: 'POST', body: { text } }),
  savedList: () => apiClient<Vacancy[]>('/candidate/saved-vacancies'),
  save: (id: string) =>
    apiClient<{ ok: boolean; saved: boolean }>(`/candidate/saved-vacancies/${id}`, {
      method: 'POST',
    }),
  unsave: (id: string) =>
    apiClient<{ ok: boolean; saved: boolean }>(`/candidate/saved-vacancies/${id}`, {
      method: 'DELETE',
    }),
};

export const notificationsApi = {
  list: () =>
    apiClient<{ items: AppNotification[]; unread: number }>('/notifications'),
  markRead: (id: string) =>
    apiClient<{ ok: boolean }>(`/notifications/${id}/read`, { method: 'POST' }),
  markAllRead: () =>
    apiClient<{ ok: boolean }>('/notifications/read-all', { method: 'POST' }),
};

export const offerApi = {
  create: (payload: CreateOfferPayload) =>
    apiClient<Offer>('/offers', { method: 'POST', body: payload }),
  candidateList: () => apiClient<Offer[]>('/candidate/offers'),
  employerList: () => apiClient<Offer[]>('/employer/offers'),
  byId: (id: string) => apiClient<Offer>(`/offers/${id}`),
  accept: (id: string) => apiClient<Offer>(`/offers/${id}/accept`, { method: 'POST' }),
  decline: (id: string) => apiClient<Offer>(`/offers/${id}/decline`, { method: 'POST' }),
};

export const shortlistApi = {
  list: () => apiClient<CandidateProfile[]>('/employer/shortlist'),
  add: (candidateId: string) =>
    apiClient<{ ok: boolean }>('/employer/shortlist', {
      method: 'POST',
      body: { candidateId },
    }),
  remove: (candidateId: string) =>
    apiClient<void>(`/employer/shortlist/${candidateId}`, { method: 'DELETE' }),
};

export const dashboardApi = {
  candidate: () => apiClient<CandidateDashboard>('/dashboard/candidate'),
  employer: () => apiClient<EmployerDashboard>('/dashboard/employer'),
  employerAnalytics: () => apiClient<EmployerAnalytics>('/dashboard/employer/analytics'),
};

export const adminApi = {
  overview: () => apiClient<AdminOverview>('/admin/overview'),
  users: () => apiClient<AdminUserRow[]>('/admin/users'),
  setUserStatus: (
    userId: string,
    status: 'active' | 'blocked',
    reason?: string,
  ) =>
    apiClient<AdminUserRow>(`/admin/users/${userId}/status`, {
      method: 'POST',
      body: { status, reason },
    }),
  offers: () => apiClient<Offer[]>('/admin/offers'),
  vacancies: () => apiClient<Vacancy[]>('/admin/vacancies'),
  assessments: () => apiClient<AdminAssessmentsResponse>('/admin/assessments'),
  categories: () => apiClient<AdminCategoriesResponse>('/admin/categories'),
};

export const testingApi = {
  start: (payload: {
    specialization: string;
    stack: string[];
    claimedGrade: Grade;
    retest?: boolean;
  }) => apiClient<TestSession>('/tests/sessions', { method: 'POST', body: payload }),
  question: (sessionId: string) =>
    apiClient<TestQuestion>(`/tests/sessions/${sessionId}/question`),
  answer: (sessionId: string, payload: { questionId: string; optionId: string }) =>
    apiClient<TestSession>(`/tests/sessions/${sessionId}/answer`, {
      method: 'POST',
      body: payload,
    }),
  finish: (sessionId: string) =>
    apiClient<TestResult>(`/tests/sessions/${sessionId}/finish`, { method: 'POST' }),
  result: (sessionId: string) =>
    apiClient<TestResult>(`/tests/sessions/${sessionId}/result`),
  history: () => apiClient<TestHistoryItem[]>('/tests/history'),
};
