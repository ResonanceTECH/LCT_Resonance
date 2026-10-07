import { useQuery } from '@tanstack/react-query';
import { OfferCard } from '@/entities/ui/OfferCard';
import { adminApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { EmptyState, ErrorState, Loader } from '@/shared/ui';

export function AdminOffersPage() {
  const query = useQuery({
    queryKey: ['admin', 'offers'],
    queryFn: adminApi.offers,
  });

  if (query.isLoading) return <Loader />;
  if (query.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить офферы"
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
          <h1>Все предложения</h1>
          <p>Обзор офферов платформы.</p>
        </div>
      </div>
      {offers.length === 0 ? (
        <EmptyState title="Офферов нет" />
      ) : (
        <div className="stack" data-testid="admin-offers">
          {offers.map((offer) => (
            <OfferCard key={offer.id} offer={offer} />
          ))}
        </div>
      )}
    </div>
  );
}
