import { useQuery } from '@tanstack/react-query';
import { OfferCard } from '@/entities/ui/OfferCard';
import { offerApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { EmptyState, ErrorState, Loader } from '@/shared/ui';

export function CandidateOffersPage() {
  const query = useQuery({
    queryKey: ['offers', 'candidate'],
    queryFn: offerApi.candidateList,
  });

  if (query.isLoading) return <Loader label="Загружаем предложения..." />;
  if (query.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить предложения"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const offers = query.data ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Входящие предложения</h1>
          <p>Примите или отклоните оффер — статус обновится сразу.</p>
        </div>
      </div>
      {offers.length === 0 ? (
        <EmptyState title="Пока нет предложений" description="Когда работодатель отправит оффер, он появится здесь." />
      ) : (
        <div className="stack">
          {offers.map((offer) => (
            <OfferCard key={offer.id} offer={offer} to={`/candidate/offers/${offer.id}`} />
          ))}
        </div>
      )}
    </div>
  );
}
