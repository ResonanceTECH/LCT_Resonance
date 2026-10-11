import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ProfileCompletenessCard } from '@/entities/ui/ProfileCompleteness';
import { candidateApi, dashboardApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Button, ErrorState, Loader } from '@/shared/ui';

export function CandidateDashboardPage() {
  const query = useQuery({
    queryKey: ['dashboard', 'candidate'],
    queryFn: dashboardApi.candidate,
  });

  const completenessQuery = useQuery({
    queryKey: ['candidate', 'completeness'],
    queryFn: candidateApi.completeness,
  });

  if (query.isLoading) return <Loader label="Загружаем dashboard..." />;
  if (query.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить обзор"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const data = query.data!;
  const completeness = completenessQuery.data ?? data.completeness;

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Кабинет кандидата</h1>
          <p>Сводка по профилю, предложениям и заполненности.</p>
        </div>
        <Link to="/candidate/profile/edit">
          <Button type="button">Редактировать профиль</Button>
        </Link>
      </div>

      <div className="stats">
        <div className="stat">
          <span className="muted">Просмотры профиля</span>
          <strong>{data.profileViews}</strong>
        </div>
        <div className="stat">
          <span className="muted">Получено предложений</span>
          <strong>{data.offersReceived}</strong>
        </div>
        <div className="stat">
          <span className="muted">Принято</span>
          <strong>{data.offersAccepted}</strong>
        </div>
        <div className="stat">
          <span className="muted">Избранные вакансии</span>
          <strong>{data.savedVacanciesCount ?? 0}</strong>
        </div>
        <div className="stat">
          <span className="muted">Отклики</span>
          <strong>{data.applicationsCount ?? 0}</strong>
        </div>
        <div className="stat">
          <span className="muted">Статус профиля</span>
          <strong style={{ fontSize: '1.2rem' }}>{data.profileStatus}</strong>
        </div>
        <div className="stat">
          <span className="muted">ФСП</span>
          <strong style={{ fontSize: '1.1rem' }}>{data.fspSyncStatus}</strong>
        </div>
      </div>

      {completenessQuery.isLoading && !completeness ? <Loader label="Считаем заполненность..." /> : null}
      {completeness ? <ProfileCompletenessCard data={completeness} /> : null}
      {completenessQuery.isError ? (
        <ErrorState
          title="Не удалось загрузить заполненность"
          description={getErrorMessage(completenessQuery.error)}
          onRetry={() => void completenessQuery.refetch()}
        />
      ) : null}
    </div>
  );
}
