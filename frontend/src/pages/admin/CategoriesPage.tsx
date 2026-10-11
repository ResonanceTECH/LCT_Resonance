import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { adminApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatGrade, formatSpecialization } from '@/shared/lib/formatters';
import { Badge, ErrorState, Loader, Tabs } from '@/shared/ui';

type Tab = 'categories' | 'specializations' | 'grades' | 'skills' | 'industries';

export function AdminCategoriesPage() {
  const [tab, setTab] = useState<Tab>('categories');
  const query = useQuery({
    queryKey: ['admin', 'categories'],
    queryFn: adminApi.categories,
  });

  if (query.isLoading) return <Loader label="Загружаем справочники..." />;
  if (query.isError || !query.data) {
    return (
      <ErrorState
        title="Не удалось загрузить категории"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const data = query.data;
  const confirmedTotal = data.categories.reduce((n, c) => n + c.confirmedCandidates, 0);

  return (
    <div data-testid="admin-categories">
      <div className="page-header">
        <div>
          <h1>Категории и справочники</h1>
          <p>
            Профессиональные категории и таксономия. В MVP — просмотр; правка появится позже.
          </p>
        </div>
        <Badge tone="accent">Подтверждено профилей: {confirmedTotal}</Badge>
      </div>

      <Tabs
        value={tab}
        onChange={(v) => setTab(v as Tab)}
        tabs={[
          { id: 'categories', label: 'Категории' },
          { id: 'specializations', label: 'Специализации' },
          { id: 'grades', label: 'Грейды' },
          { id: 'skills', label: 'Навыки' },
          { id: 'industries', label: 'Отрасли' },
        ]}
      />

      {tab === 'categories' ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Категория</th>
                <th>Грейд</th>
                <th>Подтверждённых кандидатов</th>
              </tr>
            </thead>
            <tbody>
              {data.categories.map((cat) => (
                <tr key={cat.id}>
                  <td>
                    <strong>
                      {formatSpecialization(cat.specialization)} / {formatGrade(cat.grade)}
                    </strong>
                  </td>
                  <td>{formatGrade(cat.grade)}</td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {cat.confirmedCandidates}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === 'specializations' ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Направление</th>
                <th>ID</th>
              </tr>
            </thead>
            <tbody>
              {data.specializations.map((s) => (
                <tr key={s.id}>
                  <td>
                    <strong>{s.name}</strong>
                  </td>
                  <td className="muted">{s.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === 'grades' ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Грейд</th>
                <th>Код</th>
              </tr>
            </thead>
            <tbody>
              {data.grades.map((g) => (
                <tr key={g.id}>
                  <td>
                    <strong>{g.name}</strong>
                  </td>
                  <td className="muted">{g.code}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === 'skills' ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Навык</th>
                <th>Алиасы</th>
              </tr>
            </thead>
            <tbody>
              {data.skills.map((skill) => (
                <tr key={skill.id}>
                  <td>
                    <strong>{skill.name}</strong>
                  </td>
                  <td className="muted">
                    {skill.aliases?.length ? skill.aliases.join(', ') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === 'industries' ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Отрасль</th>
              </tr>
            </thead>
            <tbody>
              {data.industries.map((ind) => (
                <tr key={ind.id}>
                  <td>
                    <strong>{ind.name}</strong>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
