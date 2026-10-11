import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { SkillRadar } from '@/entities/ui/SkillRadar';
import { GradeBadge } from '@/entities/ui/GradeBadge';
import { candidateApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatReadiness, formatSalary, formatWorkFormat } from '@/shared/lib/formatters';
import { Button, EmptyState, ErrorState, Loader } from '@/shared/ui';

export function EmployerComparePage() {
  const [params] = useSearchParams();
  const ids = useMemo(
    () =>
      (params.get('ids') ?? '')
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    [params],
  );

  const query = useQuery({
    queryKey: ['compare', ids],
    queryFn: () => candidateApi.compare(ids),
    enabled: ids.length >= 2,
  });

  if (ids.length < 2) {
    return (
      <EmptyState
        title="Выберите минимум 2 кандидатов"
        description="Отметьте кандидатов в пуле и нажмите «Сравнить»."
        action={
          <Link to="/employer/talent-pool">
            <Button type="button">В пул кандидатов</Button>
          </Link>
        }
      />
    );
  }

  if (query.isLoading) return <Loader label="Сравниваем кандидатов..." />;
  if (query.isError || !query.data) {
    return (
      <ErrorState
        title="Не удалось сравнить"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const { candidates, skillMatrix, radars } = query.data;

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Сравнение кандидатов</h1>
          <p>Матрица навыков и радар — данные с сервера.</p>
        </div>
        <Link to="/employer/talent-pool">
          <Button type="button" variant="secondary">
            Назад
          </Button>
        </Link>
      </div>

      <div className="grid-2">
        {candidates.map((c) => (
          <section key={c.id} className="section-card">
            <h3 style={{ marginTop: 0 }}>{c.fullName}</h3>
            <div className="row">
              <span>{c.specialization}</span>
              <GradeBadge grade={c.claimedGrade} />
            </div>
            <p style={{ marginBottom: 0 }}>
              {formatReadiness(c.readiness)}
              {c.workFormat ? ` · ${formatWorkFormat(c.workFormat)}` : ''}
              <br />
              {formatSalary(c.salaryFrom, c.salaryTo, c.currency)}
            </p>
            <Link to={`/employer/candidates/${c.id}`}>Открыть профиль</Link>
          </section>
        ))}
      </div>

      <section className="section-card" data-testid="compare-matrix">
        <h3>Матрица навыков</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: '0.5rem' }}>Навык</th>
                {candidates.map((c) => (
                  <th key={c.id} style={{ textAlign: 'left', padding: '0.5rem' }}>
                    {c.fullName.split(' ')[0]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {skillMatrix.map((row) => (
                <tr key={row.skill}>
                  <td style={{ padding: '0.5rem', borderTop: '1px solid var(--line)' }}>
                    {row.skill}
                  </td>
                  {candidates.map((c) => (
                    <td
                      key={c.id}
                      style={{ padding: '0.5rem', borderTop: '1px solid var(--line)' }}
                    >
                      {row.values[c.id] == null ? (
                        <span className="muted">не указан в профиле</span>
                      ) : (
                        row.values[c.id]
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid-2">
        {radars.map((radar) => (
          <SkillRadar key={radar.candidateId} radar={radar} />
        ))}
      </div>
    </div>
  );
}
