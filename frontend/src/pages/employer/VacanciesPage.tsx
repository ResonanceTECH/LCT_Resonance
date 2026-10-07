import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { VacancyCard } from '@/entities/ui/VacancyCard';
import { vacancyApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Button, EmptyState, ErrorState, Loader } from '@/shared/ui';

export function EmployerVacanciesPage() {
  const query = useQuery({
    queryKey: ['vacancies', 'employer'],
    queryFn: vacancyApi.employerList,
  });

  if (query.isLoading) return <Loader />;
  if (query.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить вакансии"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const items = query.data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Вакансии</h1>
          <p>Создание, просмотр и статусы.</p>
        </div>
        <Link to="/employer/vacancies/new">
          <Button type="button">Создать вакансию</Button>
        </Link>
      </div>
      {items.length === 0 ? (
        <EmptyState
          title="Вакансий пока нет"
          action={
            <Link to="/employer/vacancies/new">
              <Button type="button">Создать первую</Button>
            </Link>
          }
        />
      ) : (
        <div className="stack">
          {items.map((v) => (
            <VacancyCard key={v.id} vacancy={v} to={`/employer/vacancies/${v.id}`} />
          ))}
        </div>
      )}
    </div>
  );
}
