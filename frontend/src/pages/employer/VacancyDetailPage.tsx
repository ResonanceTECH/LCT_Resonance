import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { SalaryRange } from '@/entities/ui/SalaryRange';
import { SkillBadge } from '@/entities/ui/SkillBadge';
import { vacancyApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import {
  formatGrade,
  formatSpecialization,
  formatVacancyStatus,
  formatWorkFormat,
} from '@/shared/lib/formatters';
import { Badge, Button, ErrorState, Loader, uiStyles } from '@/shared/ui';

export function EmployerVacancyDetailPage() {
  const { id = '' } = useParams();
  const query = useQuery({
    queryKey: ['vacancies', id],
    queryFn: () => vacancyApi.byId(id),
    enabled: Boolean(id),
  });

  if (query.isLoading) return <Loader />;
  if (query.isError || !query.data) {
    return (
      <ErrorState
        title="Вакансия не найдена"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const vacancy = query.data;

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>{vacancy.title}</h1>
          <p>
            {formatSpecialization(vacancy.specialization)} · {formatGrade(vacancy.requiredGrade)} ·{' '}
            {formatWorkFormat(vacancy.workFormat)}
          </p>
        </div>
        <div className="row">
          <Badge>{formatVacancyStatus(vacancy.status)}</Badge>
          <Link to={`/employer/vacancies/${id}/edit`}>
            <Button type="button" variant="secondary">
              Редактировать
            </Button>
          </Link>
          <Link to={`/employer/talent-pool?vacancyId=${id}`}>
            <Button type="button">Подобрать кандидатов</Button>
          </Link>
        </div>
      </div>
      <section className="section-card">
        <p>{vacancy.description}</p>
        <p>
          Зарплата:{' '}
          <strong>
            <SalaryRange
              from={vacancy.salaryFrom}
              to={vacancy.salaryTo}
              currency={vacancy.currency}
            />
          </strong>
        </p>
        <h3>Обязательные навыки</h3>
        <div className={uiStyles.skills}>
          {vacancy.requiredSkills.map((s) => (
            <SkillBadge key={s} skill={s} />
          ))}
        </div>
        {vacancy.niceToHaveSkills.length > 0 ? (
          <>
            <h3 style={{ marginTop: '1rem' }}>Дополнительные</h3>
            <div className={uiStyles.skills}>
              {vacancy.niceToHaveSkills.map((s) => (
                <SkillBadge key={s} skill={s} />
              ))}
            </div>
          </>
        ) : null}
      </section>
    </div>
  );
}
