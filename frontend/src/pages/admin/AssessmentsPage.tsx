import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { adminApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatDateTime, formatGrade } from '@/shared/lib/formatters';
import { Badge, ErrorState, Loader, Tabs } from '@/shared/ui';

type Tab = 'catalog' | 'templates' | 'attempts' | 'analytics';

export function AdminAssessmentsPage() {
  const [tab, setTab] = useState<Tab>('catalog');
  const query = useQuery({
    queryKey: ['admin', 'assessments'],
    queryFn: adminApi.assessments,
  });

  if (query.isLoading) return <Loader label="Загружаем тестирование..." />;
  if (query.isError || !query.data) {
    return (
      <ErrorState
        title="Не удалось загрузить тестирование"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const { catalog, templates, attempts, stats } = query.data;
  const maxBucket = Math.max(1, ...stats.scoreDistribution.map((b) => b.count));

  return (
    <div data-testid="admin-assessments">
      <div className="page-header">
        <div>
          <h1>Тестирование</h1>
          <p>
            Каталог тестов, банк заданий и результаты. Редактор шаблонов — через seed на Backend.
          </p>
        </div>
      </div>

      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
        <div className="kpi-card">
          <span className="kpi-value">{catalog.filter((t) => t.status === 'active').length}</span>
          <span className="kpi-label">Активных тестов</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-value">{stats.totalAttempts}</span>
          <span className="kpi-label">Попыток</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-value">{Math.round(stats.successRate * 100)}%</span>
          <span className="kpi-label">Успешных прохождений</span>
        </div>
      </div>

      <Tabs
        value={tab}
        onChange={(v) => setTab(v as Tab)}
        tabs={[
          { id: 'catalog', label: 'Каталог тестов' },
          { id: 'templates', label: 'Банк заданий' },
          { id: 'attempts', label: 'История' },
          { id: 'analytics', label: 'Аналитика' },
        ]}
      />

      {tab === 'catalog' ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Специализация</th>
                <th>Грейд</th>
                <th>Заданий</th>
                <th>Blueprint</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {catalog.map((test) => (
                <tr key={test.id}>
                  <td>
                    <strong>{test.specialization}</strong>
                  </td>
                  <td>{formatGrade(test.grade)}</td>
                  <td>{test.questionCount}</td>
                  <td>
                    <span className="muted">
                      {test.topics
                        .map((t) => `${t.name} (${t.count}, ${t.difficulty})`)
                        .join(' · ')}
                    </span>
                  </td>
                  <td>
                    <Badge
                      tone={
                        test.status === 'active'
                          ? 'success'
                          : test.status === 'draft'
                            ? 'warn'
                            : 'default'
                      }
                    >
                      {test.status === 'active'
                        ? 'Активен'
                        : test.status === 'draft'
                          ? 'Черновик'
                          : 'Архив'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === 'templates' ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Тема</th>
                <th>Специализация</th>
                <th>Сложность</th>
                <th>Шаблон</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {templates.map((tpl) => (
                <tr key={tpl.id}>
                  <td>
                    <strong>{tpl.topic}</strong>
                  </td>
                  <td>{tpl.specialization}</td>
                  <td>{tpl.difficulty}</td>
                  <td>
                    <span className="muted">
                      {tpl.parameterized ? 'Параметризованный · ' : ''}
                      {tpl.promptPreview}
                    </span>
                  </td>
                  <td>
                    <Badge tone={tpl.active ? 'success' : 'default'}>
                      {tpl.active ? 'Активен' : 'Выключен'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === 'attempts' ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Кандидат</th>
                <th>Категория</th>
                <th>Дата</th>
                <th>Результат</th>
                <th>Статус</th>
                <th>Пересдача</th>
              </tr>
            </thead>
            <tbody>
              {attempts.map((att) => (
                <tr key={att.id}>
                  <td>
                    <strong>{att.displayName}</strong>
                  </td>
                  <td>
                    {att.specialization} / {formatGrade(att.grade)}
                  </td>
                  <td>{formatDateTime(att.completedAt)}</td>
                  <td>
                    {att.score}/{att.maxScore}
                  </td>
                  <td>
                    <Badge tone={att.passed ? 'success' : 'danger'}>
                      {att.passed ? 'Успешно' : 'Не сдан'}
                    </Badge>
                  </td>
                  <td className="muted">{formatDateTime(att.nextRetestAt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === 'analytics' ? (
        <div className="bento-grid">
          <section className="section-card bento-span-6">
            <h3>Успешность</h3>
            <p className="muted">
              {Math.round(stats.successRate * 100)}% прохождений подтверждают заявленный грейд
              ({stats.totalAttempts} попыток).
            </p>
          </section>
          <section className="section-card bento-span-6">
            <h3>Распределение результатов</h3>
            {stats.scoreDistribution.map((bucket) => (
              <div key={bucket.bucket} className="dist-bar">
                <span style={{ width: 64, fontSize: 12, color: 'var(--text-secondary)' }}>
                  {bucket.bucket}
                </span>
                <div className="dist-bar-track">
                  <div
                    className="dist-bar-fill"
                    style={{ width: `${(bucket.count / maxBucket) * 100}%` }}
                  />
                </div>
                <span
                  style={{
                    width: 24,
                    textAlign: 'right',
                    fontVariantNumeric: 'tabular-nums',
                    fontSize: 13,
                  }}
                >
                  {bucket.count}
                </span>
              </div>
            ))}
          </section>
        </div>
      ) : null}
    </div>
  );
}
