import type { Grade, ReadinessStatus, WorkFormat } from '@/entities/types';

export const GRADE_OPTIONS: { value: Grade; label: string }[] = [
  { value: 'intern', label: 'Intern' },
  { value: 'junior', label: 'Junior' },
  { value: 'middle', label: 'Middle' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead' },
];

export const WORK_FORMAT_OPTIONS: { value: WorkFormat; label: string }[] = [
  { value: 'remote', label: 'Удалённо' },
  { value: 'hybrid', label: 'Гибрид' },
  { value: 'office', label: 'Офис' },
];

export const READINESS_OPTIONS: { value: ReadinessStatus; label: string }[] = [
  { value: 'actively_looking', label: 'Активно ищу работу' },
  { value: 'open_to_offers', label: 'Открыт к предложениям' },
  { value: 'not_looking', label: 'Не рассматриваю предложения' },
];

export const SPECIALIZATION_OPTIONS = [
  'Frontend',
  'Backend',
  'Fullstack',
  'Mobile',
  'DevOps',
  'Data Science',
  'QA',
];
