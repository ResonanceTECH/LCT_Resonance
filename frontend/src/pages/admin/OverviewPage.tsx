import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { adminApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Button, ErrorState, Loader } from '@/shared/ui';

export function AdminOverviewPage() {
  const query = useQuery({
    queryKey: ['admin', 'overview'],
    queryFn: adminApi.overview,
  });

  if (query.isLoading) return <Loader label="Загружаем overview..." />;
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

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Admin</h1>
          <p>Модерация платформы. Данные только через Backend API.</p>
        </div>
        <Link to="/admin/users">
          <Button type="button">К пользователям</Button>
        </Link>
      </div>
      <div className="stats" data-testid="admin-overview">
        <div className="stat">
          <span className="muted">Пользователи</span>
          <strong>{data.usersTotal}</strong>
        </div>
        <div className="stat">
          <span className="muted">Кандидаты</span>
          <strong>{data.candidates}</strong>
        </div>
        <div className="stat">
          <span className="muted">Работодатели</span>
          <strong>{data.employers}</strong>
        </div>
        <div className="stat">
          <span className="muted">Активные вакансии</span>
          <strong>{data.vacanciesActive}</strong>
        </div>
        <div className="stat">
          <span className="muted">Открытые офферы</span>
          <strong>{data.offersOpen}</strong>
        </div>
        <div className="stat">
          <span className="muted">Принятые офферы</span>
          <strong>{data.offersAccepted}</strong>
        </div>
        <div className="stat">
          <span className="muted">Заблокированы</span>
          <strong>{data.blockedUsers}</strong>
        </div>
      </div>
    </div>
  );
}
