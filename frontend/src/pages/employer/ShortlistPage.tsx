import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CandidateCard } from '@/entities/ui/CandidateCard';
import { shortlistApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Button, EmptyState, ErrorState, Loader } from '@/shared/ui';

export function EmployerShortlistPage() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['shortlist'],
    queryFn: shortlistApi.list,
  });

  const removeMutation = useMutation({
    mutationFn: shortlistApi.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['shortlist'] }),
  });

  if (query.isLoading) return <Loader />;
  if (query.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить shortlist"
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
          <h1>Shortlist</h1>
          <p>Сохранённые кандидаты.</p>
        </div>
      </div>
      {items.length === 0 ? (
        <EmptyState title="Shortlist пуст" />
      ) : (
        <div className="stack">
          {items.map((candidate) => (
            <div key={candidate.id} className="stack">
              <CandidateCard
                candidate={candidate}
                to={`/employer/candidates/${candidate.id}`}
              />
              <div>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => removeMutation.mutate(candidate.id)}
                >
                  Удалить
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
