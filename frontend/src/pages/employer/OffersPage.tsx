import { useQuery } from '@tanstack/react-query';
import { OfferCard } from '@/entities/ui/OfferCard';
import { offerApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { EmptyState, ErrorState, Loader } from '@/shared/ui';

export function EmployerOffersPage() {
  const query = useQuery({
    queryKey: ['offers', 'employer'],
    queryFn: offerApi.employerList,
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
          <h1>Отправленные предложения</h1>
          <p>Статусы: новое → просмотрено → принято/отклонено.</p>
        </div>
      </div>
      {offers.length === 0 ? (
        <EmptyState title="Офферов пока нет" description="Отправьте предложение из карточки кандидата." />
      ) : (
        <div className="stack">
          {offers.map((offer) => (
            <OfferCard key={offer.id} offer={offer} />
          ))}
        </div>
      )}
    </div>
  );
}
