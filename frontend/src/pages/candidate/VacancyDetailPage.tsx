import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { MatchScore } from '@/entities/ui/MatchScore';
import { SalaryRange } from '@/entities/ui/SalaryRange';
import { SkillBadge } from '@/entities/ui/SkillBadge';
import { vacancyApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatGrade, formatSpecialization, formatWorkFormat } from '@/shared/lib/formatters';
import { Badge, Button, ErrorState, Loader, uiStyles } from '@/shared/ui';

export function CandidateVacancyDetailPage() {
  const { id = '' } = useParams();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['vacancies', id],
    queryFn: () => vacancyApi.byId(id),
    enabled: Boolean(id),
  });

  const matchQuery = useQuery({
    queryKey: ['vacancies', id, 'match-to-me'],
    queryFn: () => vacancyApi.matchToMe(id),
    enabled: Boolean(id),
  });

  const savedQuery = useQuery({
    queryKey: ['vacancies', 'saved'],
    queryFn: vacancyApi.savedList,
  });

  const applyMutation = useMutation({
    mutationFn: () => vacancyApi.apply(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['vacancies'] });
      void queryClient.invalidateQueries({ queryKey: ['dashboard', 'candidate'] });
    },
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      const saved = (savedQuery.data ?? []).some((v) => v.id === id);
      return saved ? vacancyApi.unsave(id) : vacancyApi.save(id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['vacancies', 'saved'] });
      void queryClient.invalidateQueries({ queryKey: ['vacancies'] });
      void queryClient.invalidateQueries({ queryKey: ['dashboard', 'candidate'] });
    },
  });

  if (query.isLoading) return <Loader />;
  if (query.isError || !query.data) {
    return (
      <ErrorState
        title="Вакансия не найдена"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const vacancy = query.data;
  const isSaved = (savedQuery.data ?? []).some((v) => v.id === id);

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>{vacancy.title}</h1>
          <p>
            {formatSpecialization(vacancy.specialization)} · {formatGrade(vacancy.requiredGrade)} ·{' '}
            {formatWorkFormat(vacancy.workFormat)}
          </p>
        </div>
        <Badge tone="success">
          <SalaryRange from={vacancy.salaryFrom} to={vacancy.salaryTo} currency={vacancy.currency} />
        </Badge>
      </div>

      {matchQuery.isLoading ? <Loader label="Считаем соответствие..." /> : null}
      {matchQuery.data ? (
        <div data-testid="match-to-me">
          <MatchScore match={matchQuery.data} />
        </div>
      ) : null}
      {matchQuery.isError ? (
        <ErrorState
          title="Не удалось получить оценку соответствия"
          description={getErrorMessage(matchQuery.error)}
          onRetry={() => void matchQuery.refetch()}
        />
      ) : null}

      <section className="section-card">
        <p>{vacancy.description}</p>
        <h3>Обязательные навыки</h3>
        <div className={uiStyles.skills}>
          {vacancy.requiredSkills.map((s) => (
            <SkillBadge key={s} skill={s} />
          ))}
        </div>
      </section>

      <div className="row">
        <Button
          type="button"
          onClick={() => applyMutation.mutate()}
          disabled={applyMutation.isPending || applyMutation.isSuccess}
        >
          {applyMutation.isSuccess ? 'Отклик отправлен' : 'Откликнуться'}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          data-testid="save-vacancy"
        >
          {isSaved ? 'Убрать из избранного' : 'В избранное'}
        </Button>
      </div>
      {applyMutation.isError ? (
        <div style={{ color: 'var(--danger)' }}>{getErrorMessage(applyMutation.error)}</div>
      ) : null}
      {saveMutation.isError ? (
        <div style={{ color: 'var(--danger)' }}>{getErrorMessage(saveMutation.error)}</div>
      ) : null}
    </div>
  );
}
