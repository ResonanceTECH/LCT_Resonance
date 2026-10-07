import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { OfferCard } from '@/entities/ui/OfferCard';
import { offerApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Button, ErrorState, Loader } from '@/shared/ui';

export function CandidateOfferDetailPage() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['offers', id],
    queryFn: () => offerApi.byId(id),
    enabled: Boolean(id),
  });

  const acceptMutation = useMutation({
    mutationFn: () => offerApi.accept(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['offers'] });
      await query.refetch();
    },
  });

  const declineMutation = useMutation({
    mutationFn: () => offerApi.decline(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['offers'] });
      await query.refetch();
    },
  });

  if (query.isLoading) return <Loader />;
  if (query.isError || !query.data) {
    return (
      <ErrorState
        title="Предложение не найдено"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const offer = query.data;
  const canRespond = offer.status === 'new' || offer.status === 'viewed';

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Предложение</h1>
          <p>Зарплатная вилка отображается явно.</p>
        </div>
        <Button type="button" variant="secondary" onClick={() => navigate('/candidate/offers')}>
          Назад
        </Button>
      </div>
      <OfferCard offer={offer} />
      {canRespond ? (
        <div className="row">
          <Button
            type="button"
            onClick={() => acceptMutation.mutate()}
            disabled={acceptMutation.isPending || declineMutation.isPending}
          >
            Принять
          </Button>
          <Button
            type="button"
            variant="danger"
            onClick={() => declineMutation.mutate()}
            disabled={acceptMutation.isPending || declineMutation.isPending}
          >
            Отклонить
          </Button>
        </div>
      ) : (
        <div className="section-card">Действие уже выполнено. Текущий статус обновлён.</div>
      )}
      {(acceptMutation.isError || declineMutation.isError) && (
        <div style={{ color: 'var(--danger)' }}>
          {getErrorMessage(acceptMutation.error || declineMutation.error)}
        </div>
      )}
    </div>
  );
}
