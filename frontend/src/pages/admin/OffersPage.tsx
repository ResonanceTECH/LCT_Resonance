import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import type { OfferStatus } from '@/entities/types';
import { adminApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatDateTime, formatSalary } from '@/shared/lib/formatters';
import {
  Badge,
  EmptyState,
  ErrorState,
  Input,
  Loader,
  Select,
} from '@/shared/ui';

/** Admin monitoring labels — map internal statuses to product terms. */
const STATUS_FILTER: { value: OfferStatus | ''; label: string }[] = [
  { value: '', label: 'Все статусы' },
  { value: 'new', label: 'SENT' },
  { value: 'viewed', label: 'VIEWED' },
  { value: 'accepted', label: 'ACCEPTED' },
  { value: 'declined', label: 'DECLINED' },
];

const STATUS_BADGE: Record<OfferStatus, { label: string; tone: 'accent' | 'success' | 'danger' | 'default' }> = {
  new: { label: 'SENT', tone: 'accent' },
  viewed: { label: 'VIEWED', tone: 'default' },
  accepted: { label: 'ACCEPTED', tone: 'success' },
  declined: { label: 'DECLINED', tone: 'danger' },
};

export function AdminOffersPage() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<OfferStatus | ''>('');

  const query = useQuery({
    queryKey: ['admin', 'offers'],
    queryFn: adminApi.offers,
  });

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (query.data ?? []).filter((offer) => {
      if (status && offer.status !== status) return false;
      if (!q) return true;
      return (
        offer.id.toLowerCase().includes(q) ||
        offer.companyName.toLowerCase().includes(q) ||
        offer.positionTitle.toLowerCase().includes(q)
      );
    });
  }, [query.data, search, status]);

  if (query.isLoading) return <Loader />;
  if (query.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить приглашения"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Приглашения</h1>
          <p>Мониторинг статусов. Решения кандидатов и контакты здесь недоступны.</p>
        </div>
      </div>

      <div className="toolbar">
        <div className="toolbar-grow">
          <Input
            label="Поиск"
            placeholder="ID, компания или позиция"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select
          label="Статус"
          value={status}
          onChange={(e) => setStatus(e.target.value as OfferStatus | '')}
          options={STATUS_FILTER.filter((o) => o.value).map((o) => ({
            value: o.value,
            label: o.label,
          }))}
          allowEmpty
          emptyLabel="Все статусы"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="Приглашений нет" description="Измените фильтры или дождитесь отправок." />
      ) : (
        <div className="data-table-wrap" data-testid="admin-offers">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Компания</th>
                <th>Позиция</th>
                <th>Зарплата</th>
                <th>Отправлено</th>
                <th>Статус</th>
                <th>Изменение</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((offer) => {
                const badge = STATUS_BADGE[offer.status];
                return (
                  <tr key={offer.id}>
                    <td className="muted">{offer.id}</td>
                    <td>
                      <strong>{offer.companyName}</strong>
                    </td>
                    <td>{offer.positionTitle}</td>
                    <td>{formatSalary(offer.salaryFrom, offer.salaryTo, offer.currency)}</td>
                    <td>{formatDateTime(offer.createdAt)}</td>
                    <td>
                      <Badge tone={badge.tone}>{badge.label}</Badge>
                    </td>
                    <td className="muted">{formatDateTime(offer.respondedAt ?? offer.createdAt)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
