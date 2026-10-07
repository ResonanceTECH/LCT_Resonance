import type {
  Grade,
  OfferStatus,
  ReadinessStatus,
  VacancyStatus,
  WorkFormat,
} from '@/entities/types';

export function formatSalary(
  from?: number,
  to?: number,
  currency: 'RUB' | 'USD' = 'RUB',
): string {
  const symbol = currency === 'RUB' ? '₽' : '$';
  const fmt = (n: number) => n.toLocaleString('ru-RU');
  if (from != null && to != null) return `${fmt(from)}–${fmt(to)} ${symbol}`;
  if (from != null) return `от ${fmt(from)} ${symbol}`;
  if (to != null) return `до ${fmt(to)} ${symbol}`;
  return 'Не указано';
}

export function formatGrade(grade: Grade): string {
  const map: Record<Grade, string> = {
    intern: 'Intern',
    junior: 'Junior',
    middle: 'Middle',
    senior: 'Senior',
    lead: 'Lead',
  };
  return map[grade];
}

export function formatWorkFormat(format: WorkFormat): string {
  const map: Record<WorkFormat, string> = {
    remote: 'Удалённо',
    hybrid: 'Гибрид',
    office: 'Офис',
  };
  return map[format];
}

export function formatReadiness(status: ReadinessStatus): string {
  const map: Record<ReadinessStatus, string> = {
    actively_looking: 'Активно ищу работу',
    open_to_offers: 'Открыт к предложениям',
    not_looking: 'Не рассматриваю предложения',
  };
  return map[status];
}

export function formatOfferStatus(status: OfferStatus): string {
  const map: Record<OfferStatus, string> = {
    new: 'Новое',
    viewed: 'Просмотрено',
    accepted: 'Принято',
    declined: 'Отклонено',
  };
  return map[status];
}

export function formatVacancyStatus(status: VacancyStatus): string {
  const map: Record<VacancyStatus, string> = {
    draft: 'Черновик',
    active: 'Активна',
    closed: 'Закрыта',
    archived: 'В архиве',
  };
  return map[status];
}

export function formatDate(iso?: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export function formatDateTime(iso?: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
