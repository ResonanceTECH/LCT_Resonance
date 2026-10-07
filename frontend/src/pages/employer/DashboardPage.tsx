import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { dashboardApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatReadiness } from '@/shared/lib/formatters';
import { Button, ErrorState, Loader } from '@/shared/ui';

function pct(rate: number) {
  return `${Math.round(rate * 100)}%`;
}

export function EmployerDashboardPage() {
  const summaryQuery = useQuery({
    queryKey: ['dashboard', 'employer'],
    queryFn: dashboardApi.employer,
  });
  const analyticsQuery = useQuery({
    queryKey: ['dashboard', 'employer', 'analytics'],
    queryFn: dashboardApi.employerAnalytics,
  });

  if (summaryQuery.isLoading || analyticsQuery.isLoading) return <Loader />;
  if (summaryQuery.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить dashboard"
        description={getErrorMessage(summaryQuery.error)}
        onRetry={() => void summaryQuery.refetch()}
      />
    );
  }

  const data = summaryQuery.data!;
  const analytics = analyticsQuery.data;

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Кабинет работодателя</h1>
          <p>Сводка и расширенная аналитика с Backend.</p>
        </div>
        <Link to="/employer/talent-pool">
          <Button type="button">Открыть Talent Pool</Button>
        </Link>
      </div>

      <div className="stats">
        <div className="stat">
          <span className="muted">Найдено кандидатов</span>
          <strong>{data.candidatesFound}</strong>
        </div>
        <div className="stat">
          <span className="muted">Shortlist</span>
          <strong>{data.shortlistSize}</strong>
        </div>
        <div className="stat">
          <span className="muted">Отправлено офферов</span>
          <strong>{data.offersSent}</strong>
        </div>
        <div className="stat">
          <span className="muted">Принято</span>
          <strong>{data.offersAccepted}</strong>
        </div>
      </div>

      {analyticsQuery.isError ? (
        <ErrorState
          title="Аналитика недоступна"
          description={getErrorMessage(analyticsQuery.error)}
          onRetry={() => void analyticsQuery.refetch()}
        />
      ) : null}

      {analytics ? (
        <section className="section-card stack" data-testid="employer-analytics">
          <h2 style={{ margin: 0 }}>Расширенная аналитика</h2>
          <p className="muted" style={{ margin: 0 }}>
            Метрики считаются на Backend. Frontend только отображает.
          </p>

          <div>
            <h3>Воронка</h3>
            <div className="stats">
              <div className="stat">
                <span className="muted">Просмотрено</span>
                <strong>{analytics.funnel.viewedCandidates}</strong>
              </div>
              <div className="stat">
                <span className="muted">Shortlist</span>
                <strong>{analytics.funnel.shortlisted}</strong>
              </div>
              <div className="stat">
                <span className="muted">Офферы</span>
                <strong>{analytics.funnel.offersSent}</strong>
              </div>
              <div className="stat">
                <span className="muted">Accept / Decline</span>
                <strong>
                  {analytics.funnel.offersAccepted}/{analytics.funnel.offersDeclined}
                </strong>
              </div>
            </div>
          </div>

          <div className="grid-2">
            <div className="stat">
              <span className="muted">Конверсия в shortlist</span>
              <strong>{pct(analytics.conversion.shortlistRate)}</strong>
            </div>
            <div className="stat">
              <span className="muted">Accept rate офферов</span>
              <strong>{pct(analytics.conversion.offerAcceptRate)}</strong>
            </div>
          </div>

          <div className="stat">
            <span className="muted">Средний Match Score (активная вакансия)</span>
            <strong data-testid="avg-match">
              {analytics.avgMatchScore == null ? '—' : `${analytics.avgMatchScore}%`}
            </strong>
          </div>

          <div className="grid-2">
            <div>
              <h3>По специализациям</h3>
              <ul className="reason-list">
                {analytics.bySpecialization.map((row) => (
                  <li key={row.specialization}>
                    {row.specialization}: {row.count}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Готовность</h3>
              <ul className="reason-list">
                {analytics.readinessBreakdown.map((row) => (
                  <li key={row.readiness}>
                    {formatReadiness(row.readiness)}: {row.count}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div>
            <h3>Топ навыков в пуле</h3>
            <div className="row">
              {analytics.topSkills.map((s) => (
                <span key={s.skill} className="muted">
                  {s.skill} ({s.count})
                </span>
              ))}
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}
