import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { VacancyCard } from '@/entities/ui/VacancyCard';
import { vacancyApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatSpecialization } from '@/shared/lib/formatters';
import { SPECIALIZATION_OPTIONS } from '@/shared/lib/labels';
import { Checkbox, EmptyState, ErrorState, Loader, Select } from '@/shared/ui';

export function CandidateVacanciesPage() {
  const [specialization, setSpecialization] = useState('');
  const [matchToMe, setMatchToMe] = useState(true);
  const [savedOnly, setSavedOnly] = useState(false);

  const query = useQuery({
    queryKey: ['vacancies', 'public', specialization, matchToMe, savedOnly],
    queryFn: () =>
      vacancyApi.publicList({
        specialization: specialization || undefined,
        matchToMe,
        savedOnly,
      }),
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
          <h1>Каталог вакансий</h1>
          <p>Оценку соответствия считает сервер. Отклик — доп. сценарий к обратному рекрутингу.</p>
        </div>
      </div>
      <div className="filters section-card">
        <Select
          label="Специализация"
          allowEmpty
          options={SPECIALIZATION_OPTIONS.map((s) => ({
            value: s,
            label: formatSpecialization(s),
          }))}
          value={specialization}
          onChange={(e) => setSpecialization(e.target.value)}
        />
        <Checkbox
          id="match-to-me"
          label="Показать оценку соответствия"
          checked={matchToMe}
          onChange={(e) => setMatchToMe(e.target.checked)}
        />
        <Checkbox
          id="saved-only"
          label="Только избранное"
          checked={savedOnly}
          onChange={(e) => setSavedOnly(e.target.checked)}
        />
      </div>
      {items.length === 0 ? (
        <EmptyState
          title="Вакансии не найдены"
          description={savedOnly ? 'Добавьте вакансии в избранное из карточки.' : undefined}
        />
      ) : (
        <div className="stack" data-testid="candidate-vacancies-list">
          {items.map((v) => (
            <VacancyCard key={v.id} vacancy={v} to={`/candidate/vacancies/${v.id}`} />
          ))}
        </div>
      )}
    </div>
  );
}
