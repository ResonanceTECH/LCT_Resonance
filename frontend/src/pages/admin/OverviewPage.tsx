import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { adminApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatDateTime } from '@/shared/lib/formatters';
import { Badge, ErrorState, Loader } from '@/shared/ui';

export function AdminOverviewPage() {
  const query = useQuery({
    queryKey: ['admin', 'overview'],
    queryFn: adminApi.overview,
  });

  if (query.isLoading) return <Loader label="Загружаем обзор..." />;
  if (query.isError || !query.data) {
    return (
      <ErrorState
        title="Нет доступа к админке"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const data = query.data;
  const assessments = data.assessmentsCompleted ?? 0;
  const invitations = data.offersTotal ?? data.offersOpen + data.offersAccepted;
  const events = data.recentEvents ?? [];
  const apiTone =
    data.apiStatus === 'ok' ? 'success' : data.apiStatus === 'degraded' ? 'warn' : 'danger';

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Панель администратора</h1>
          <p>Компактный контроль платформы — пользователи, тестирование и категории.</p>
        </div>
        {data.apiStatus ? (
          <Badge tone={apiTone}>
            API: {data.apiStatus === 'ok' ? 'в порядке' : data.apiStatus}
          </Badge>
        ) : null}
      </div>

      <div className="kpi-grid" data-testid="admin-overview">
        <div className="kpi-card">
          <span className="kpi-value">{data.candidates}</span>
          <span className="kpi-label">Кандидатов</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-value">{data.employers}</span>
          <span className="kpi-label">Работодателей</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-value">{assessments}</span>
          <span className="kpi-label">Тестирований</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-value">{invitations}</span>
          <span className="kpi-label">Приглашений</span>
        </div>
      </div>

      <div className="bento-grid">
        <section className="section-card bento-span-8">
          <h3>Последние события</h3>
          {events.length === 0 ? (
            <p className="muted" style={{ margin: 0 }}>
              События появятся после активности на платформе.
              {data.confirmedCategories != null
                ? ` Подтверждённых категорий: ${data.confirmedCategories}.`
                : null}
            </p>
          ) : (
            <ul className="event-list">
              {events.map((event) => {
                const body = (
                  <>
                    <span className="event-title">{event.title}</span>
                    {event.description ? (
                      <span className="event-desc">{event.description}</span>
                    ) : null}
                    <span className="event-time">{formatDateTime(event.createdAt)}</span>
                  </>
                );
                return (
                  <li key={event.id}>
                    {event.href ? <Link to={event.href}>{body}</Link> : body}
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section className="section-card bento-span-4">
          <h3>Сводка</h3>
          <dl className="drawer-meta">
            <div>
              <dt>Активные вакансии</dt>
              <dd>{data.vacanciesActive}</dd>
            </div>
            <div>
              <dt>Открытые приглашения</dt>
              <dd>{data.offersOpen}</dd>
            </div>
            <div>
              <dt>Заблокированные</dt>
              <dd>{data.blockedUsers}</dd>
            </div>
            {data.confirmedCategories != null ? (
              <div>
                <dt>Подтверждённые категории</dt>
                <dd>{data.confirmedCategories}</dd>
              </div>
            ) : null}
          </dl>
          <div className="row" style={{ marginTop: 8 }}>
            <Link to="/admin/users">Пользователи →</Link>
            <Link to="/admin/assessments">Тестирование →</Link>
          </div>
        </section>
      </div>
    </div>
  );
}
