import type { VacancyWithMatch } from '@/entities/types';
import {
  formatGrade,
  formatSpecialization,
  formatVacancyStatus,
  formatWorkFormat,
} from '@/shared/lib/formatters';
import { Badge, Card } from '@/shared/ui';
import { SalaryRange } from './SalaryRange';

export function VacancyCard({ vacancy, to }: { vacancy: VacancyWithMatch; to?: string }) {
  return (
    <Card to={to}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>{vacancy.title}</h3>
        <div className="row">
          {vacancy.match ? (
            <span data-testid="vacancy-match-badge">
              <Badge tone="success">Соответствие {vacancy.match.score}%</Badge>
            </span>
          ) : null}
          {vacancy.saved ? <Badge tone="accent">В избранном</Badge> : null}
          {vacancy.applied ? <Badge tone="warn">Отклик</Badge> : null}
          <Badge tone={vacancy.status === 'active' ? 'success' : 'default'}>
            {formatVacancyStatus(vacancy.status)}
          </Badge>
        </div>
      </div>
      <p style={{ margin: '0.4rem 0' }}>
        {formatSpecialization(vacancy.specialization)} · {formatGrade(vacancy.requiredGrade)} ·{' '}
        {formatWorkFormat(vacancy.workFormat)}
      </p>
      <strong>
        <SalaryRange
          from={vacancy.salaryFrom}
          to={vacancy.salaryTo}
          currency={vacancy.currency}
        />
      </strong>
    </Card>
  );
}
