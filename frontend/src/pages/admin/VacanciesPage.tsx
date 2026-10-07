import { useQuery } from '@tanstack/react-query';
import { VacancyCard } from '@/entities/ui/VacancyCard';
import { adminApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { EmptyState, ErrorState, Loader } from '@/shared/ui';

export function AdminVacanciesPage() {
  const query = useQuery({
    queryKey: ['admin', 'vacancies'],
    queryFn: adminApi.vacancies,
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
          <h1>Все вакансии</h1>
          <p>Обзор вакансий работодателей.</p>
        </div>
      </div>
      {items.length === 0 ? (
        <EmptyState title="Вакансий нет" />
      ) : (
        <div className="stack" data-testid="admin-vacancies">
          {items.map((v) => (
            <VacancyCard key={v.id} vacancy={v} />
          ))}
        </div>
      )}
    </div>
  );
}
