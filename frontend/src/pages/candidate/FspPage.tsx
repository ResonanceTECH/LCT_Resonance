import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FSPAchievementCard } from '@/entities/ui/FSPAchievementCard';
import { candidateApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatDateTime } from '@/shared/lib/formatters';
import { Button, EmptyState, ErrorState, Loader, Skeleton } from '@/shared/ui';

export function CandidateFspPage() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['candidate', 'fsp'],
    queryFn: candidateApi.fspAchievements,
  });

  const syncMutation = useMutation({
    mutationFn: candidateApi.fspSync,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['candidate', 'fsp'] });
      await queryClient.invalidateQueries({ queryKey: ['candidate', 'me'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard', 'candidate'] });
    },
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Достижения ФСП</h1>
          <p>Данные приходят только через Backend. На фронте — отображение и синхронизация.</p>
        </div>
        <Button
          type="button"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
        >
          {syncMutation.isPending ? 'Синхронизация...' : 'Синхронизировать ФСП'}
        </Button>
      </div>

      {syncMutation.isPending ? (
        <div className="section-card stack">
          <p>Получаем данные ФСП...</p>
          <Skeleton height={72} />
          <Skeleton height={72} />
        </div>
      ) : null}

      {syncMutation.isError ? (
        <ErrorState
          title="Не удалось получить данные ФСП"
          description="Попробуйте выполнить синхронизацию позже."
          onRetry={() => syncMutation.mutate()}
        />
      ) : null}

      {syncMutation.isSuccess ? (
        <div className="section-card" style={{ marginBottom: '1rem' }}>
          Найдено {syncMutation.data.achievements.length} подтвержденных достижения.
        </div>
      ) : null}

      {query.isLoading ? <Loader label="Загружаем достижения..." /> : null}
      {query.isError ? (
        <ErrorState
          title="Ошибка загрузки"
          description={getErrorMessage(query.error)}
          onRetry={() => void query.refetch()}
        />
      ) : null}

      {query.data ? (
        <>
          <p className="muted">
            Последняя синхронизация: {formatDateTime(query.data.syncedAt)}
          </p>
          {query.data.achievements.length === 0 ? (
            <EmptyState
              title="Достижения ФСП пока не найдены"
              description="Запустите синхронизацию или проверьте данные позже."
            />
          ) : (
            <div className="stack">
              {query.data.achievements.map((a) => (
                <FSPAchievementCard key={a.id} achievement={a} />
              ))}
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
