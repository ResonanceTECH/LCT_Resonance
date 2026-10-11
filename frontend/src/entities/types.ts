export type Role = 'candidate' | 'employer' | 'admin';

export type AuthUser = {
  id: string;
  email: string;
  role: Role;
  displayName: string;
  /** Backend: until verified, employers cannot send offers and candidates are hidden. */
  emailVerified?: boolean;
};

export type LoginPayload = { email: string; password: string };

export type RegisterPayload = {
  email: string;
  password: string;
  role: 'candidate' | 'employer';
  displayName: string;
};

export type AuthResponse = {
  accessToken: string;
  user: AuthUser;
};

export type WorkFormat = 'remote' | 'hybrid' | 'office';

export type ReadinessStatus =
  | 'actively_looking'
  | 'open_to_offers'
  | 'not_looking';

export type Grade = 'intern' | 'junior' | 'middle' | 'senior' | 'lead';

export type TestResultSummary = {
  score: number;
  maxScore: number;
  gradeConfirmed: boolean;
  completedAt: string;
};

export type CandidateProfile = {
  id: string;
  userId: string;
  fullName: string;
  about?: string;
  specialization: string;
  claimedGrade: Grade;
  confirmedGrade?: Grade | null;
  experienceYears?: number;
  experienceDescription?: string;
  skills: string[];
  desiredPosition?: string;
  salaryFrom?: number;
  salaryTo?: number;
  currency: 'RUB' | 'USD';
  city?: string;
  workFormat?: WorkFormat;
  readiness: ReadinessStatus;
  testResult?: TestResultSummary | null;
  fspSyncedAt?: string | null;
  hasFspAchievements?: boolean;
  profileCompleteness?: number;
};

export type FspAchievement = {
  id: string;
  title: string;
  discipline?: string;
  date?: string;
  placeOrResult?: string;
  participantRole?: string;
  sportRank?: string;
  extra?: Record<string, string>;
  verified: true;
};

export type FspAchievementsResponse = {
  achievements: FspAchievement[];
  syncedAt: string | null;
};

export type VacancyStatus = 'draft' | 'active' | 'closed' | 'archived';

export type Vacancy = {
  id: string;
  employerId: string;
  companyName?: string;
  title: string;
  description: string;
  specialization: string;
  requiredGrade: Grade;
  requiredSkills: string[];
  niceToHaveSkills: string[];
  salaryFrom: number;
  salaryTo: number;
  currency: 'RUB' | 'USD';
  city?: string;
  workFormat: WorkFormat;
  extraInfo?: string;
  status: VacancyStatus;
  createdAt: string;
  updatedAt: string;
};

export type MatchReason = {
  code: string;
  label: string;
  positive: boolean;
};

export type CandidateMatch = {
  candidateId: string;
  vacancyId: string;
  score: number;
  matchedSkills: string[];
  missingInProfileSkills: string[];
  reasons: MatchReason[];
  relevantFsp?: FspAchievement[];
};

export type TalentPoolItem = CandidateProfile & {
  match?: CandidateMatch;
};

export type TalentPoolResponse = {
  items: TalentPoolItem[];
  total: number;
};

export type OfferStatus = 'new' | 'viewed' | 'accepted' | 'declined';

export type Offer = {
  id: string;
  vacancyId: string;
  candidateId: string;
  employerId: string;
  companyName: string;
  positionTitle: string;
  salaryFrom: number;
  salaryTo: number;
  currency: 'RUB' | 'USD';
  workFormat: WorkFormat;
  message: string;
  status: OfferStatus;
  createdAt: string;
  respondedAt?: string | null;
};

export type CreateOfferPayload = {
  vacancyId: string;
  candidateId: string;
  companyName: string;
  positionTitle: string;
  salaryFrom: number;
  salaryTo: number;
  currency: 'RUB' | 'USD';
  workFormat: WorkFormat;
  message: string;
};

export type CandidateContacts = {
  email?: string;
  phone?: string;
  telegram?: string;
};

export type TestSession = {
  id: string;
  specialization: string;
  stack: string[];
  claimedGrade: Grade;
  currentIndex: number;
  totalQuestions: number;
  status: 'in_progress' | 'completed';
};

export type TestQuestion = {
  id: string;
  text: string;
  /** Code snippet the question is about (generated questions). */
  code?: string | null;
  options: { id: string; text: string }[];
  /** Position in the session and its length, from the Backend. */
  index?: number;
  total?: number;
};

export type TestResult = TestResultSummary & {
  sessionId: string;
  claimedGrade: Grade;
  isRetest?: boolean;
};

export type TestHistoryItem = TestResult & {
  specialization: string;
};

export type ProfileCompletenessItem = {
  key: string;
  label: string;
  done: boolean;
  weight: number;
  href?: string;
};

export type ProfileCompleteness = {
  percent: number;
  items: ProfileCompletenessItem[];
};

export type ConsentType = 'personal_data' | 'profile_publication' | 'fsp_sync';

export type Consent = {
  type: ConsentType;
  accepted: boolean;
  version?: string | null;
  currentVersion: string;
  acceptedAt?: string | null;
  withdrawnAt?: string | null;
};

/** Why strangers cannot open the passport yet; null when it is published. */
export type PassportUnpublishedReason = 'EMAIL_NOT_VERIFIED' | 'CONSENT_REQUIRED';

/** The candidate's own Career Passport link: /p/<name>-<token>. */
export type CandidatePassport = {
  slug: string;
  url: string;
  published: boolean;
  reason?: PassportUnpublishedReason | null;
};

export type PublicPassport = {
  profile: CandidateProfile;
  achievements: FspAchievement[];
  radar: SkillRadar;
  publicUrl: string;
};

export type NotificationType =
  | 'offer_new'
  | 'offer_accepted'
  | 'offer_declined'
  | 'fsp_synced'
  | 'application'
  | 'system';

export type AppNotification = {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  createdAt: string;
  read: boolean;
  href?: string;
};

export type VacancyWithMatch = Vacancy & {
  match?: CandidateMatch;
  saved?: boolean;
  applied?: boolean;
};

export type CandidateDashboard = {
  profileViews: number;
  offersReceived: number;
  offersAccepted: number;
  profileStatus: string;
  fspSyncStatus: string;
  completeness?: ProfileCompleteness;
  unreadNotifications?: number;
  savedVacanciesCount?: number;
  applicationsCount?: number;
};

export type EmployerDashboard = {
  candidatesFound: number;
  shortlistSize: number;
  offersSent: number;
  offersAccepted: number;
  unreadNotifications?: number;
};

/** Advanced analytics — calculated on Backend, frontend only renders. */
export type EmployerAnalytics = {
  funnel: {
    viewedCandidates: number;
    shortlisted: number;
    offersSent: number;
    offersAccepted: number;
    offersDeclined: number;
  };
  conversion: {
    shortlistRate: number; // 0..1
    offerAcceptRate: number; // 0..1
  };
  bySpecialization: { specialization: string; count: number }[];
  avgMatchScore: number | null;
  readinessBreakdown: { readiness: ReadinessStatus; count: number }[];
  topSkills: { skill: string; count: number }[];
};

export type TalentPoolFilters = {
  specialization?: string;
  grade?: Grade | '';
  skills?: string;
  workFormat?: WorkFormat | '';
  salaryFrom?: number | '';
  salaryTo?: number | '';
  fspDiscipline?: string;
  hasFspAchievements?: boolean | '';
  readiness?: ReadinessStatus | '';
  vacancyId?: string;
  q?: string;
  page?: number;
  limit?: number;
  sort?: 'match' | 'grade' | 'salary' | 'name' | '';
};

/** Backend/ML skill radar — frontend only visualizes. */
export type SkillRadarAxis = {
  skill: string;
  score: number; // 0..100
};

export type SkillRadar = {
  candidateId: string;
  axes: SkillRadarAxis[];
};

export type CandidateCompareResponse = {
  candidates: CandidateProfile[];
  skillMatrix: {
    skill: string;
    values: Record<string, number | null>;
  }[];
  radars: SkillRadar[];
};

export type AdminOverview = {
  usersTotal: number;
  candidates: number;
  employers: number;
  vacanciesActive: number;
  offersOpen: number;
  offersAccepted: number;
  blockedUsers: number;
};

export type AdminUserRow = AuthUser & {
  status: 'active' | 'blocked';
};

/** Backend AI draft for vacancy form — frontend only fills UI. */
export type VacancyParseResult = {
  title?: string;
  description?: string;
  specialization?: string;
  requiredGrade?: Grade;
  requiredSkills?: string[];
  niceToHaveSkills?: string[];
  salaryFrom?: number;
  salaryTo?: number;
  workFormat?: WorkFormat;
  city?: string;
};
