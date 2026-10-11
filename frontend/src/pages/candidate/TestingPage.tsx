import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { candidateApi, testingApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatDateTime, formatGrade, formatSpecialization } from '@/shared/lib/formatters';
import { GRADE_OPTIONS, SPECIALIZATION_OPTIONS } from '@/shared/lib/labels';
import { Badge, Button, Input, Select } from '@/shared/ui';

const schema = z.object({
  specialization: z.string().min(1),
  stack: z.string().min(1, 'Укажите стек'),
  claimedGrade: z.enum(['intern', 'junior', 'middle', 'senior', 'lead']),
});

type FormValues = z.infer<typeof schema>;

export function CandidateTestingPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const isRetestIntent = params.get('retest') === '1';
  const [error, setError] = useState('');

  const profileQuery = useQuery({
    queryKey: ['candidate', 'me'],
    queryFn: candidateApi.me,
  });
  const historyQuery = useQuery({
    queryKey: ['testing', 'history'],
    queryFn: testingApi.history,
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: {
      specialization: profileQuery.data?.specialization ?? 'Frontend',
      stack: (profileQuery.data?.skills ?? ['React', 'TypeScript']).join(', '),
      claimedGrade: profileQuery.data?.claimedGrade ?? 'middle',
    },
  });

  const mutation = useMutation({
    mutationFn: testingApi.start,
    onSuccess: (session) => navigate(`/candidate/testing/${session.id}`),
  });

  const hasPrevious = Boolean(profileQuery.data?.testResult) || (historyQuery.data?.length ?? 0) > 0;

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>{hasPrevious || isRetestIntent ? 'Повторное тестирование' : 'Профессиональное тестирование'}</h1>
          <p>Правильные ответы не приходят на клиент до завершения теста.</p>
        </div>
      </div>

      {profileQuery.data?.testResult ? (
        <section className="section-card" data-testid="last-test-result">
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <div>
              <div className="muted">Последний результат</div>
              <strong>
                {profileQuery.data.testResult.score}/{profileQuery.data.testResult.maxScore}
              </strong>
              <div className="muted" style={{ fontSize: '0.85rem' }}>
                {formatDateTime(profileQuery.data.testResult.completedAt)} · заявленный{' '}
                {formatGrade(profileQuery.data.claimedGrade)}
              </div>
            </div>
            {profileQuery.data.testResult.gradeConfirmed ? (
              <Badge tone="success">Уровень подтвержден</Badge>
            ) : (
              <Badge tone="warn">Не подтвержден</Badge>
            )}
          </div>
        </section>
      ) : null}

      {(historyQuery.data?.length ?? 0) > 0 ? (
        <section className="section-card" data-testid="test-history">
          <h3 style={{ marginTop: 0 }}>История попыток</h3>
          <ul className="reason-list">
            {historyQuery.data!.map((item) => (
              <li key={item.sessionId}>
                {formatDateTime(item.completedAt)} — {item.score}/{item.maxScore} ·{' '}
                {item.specialization}
                {item.isRetest ? ' · retest' : ''}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <form
        className="section-card stack"
        onSubmit={form.handleSubmit((values) => {
          setError('');
          mutation.mutate(
            {
              specialization: values.specialization,
              claimedGrade: values.claimedGrade,
              stack: values.stack
                .split(',')
                .map((s) => s.trim())
                .filter(Boolean),
              retest: hasPrevious || isRetestIntent,
            },
            {
              onError: (e) => setError(getErrorMessage(e)),
            },
          );
        })}
      >
        <Select
          label="Специализация"
          options={SPECIALIZATION_OPTIONS.map((s) => ({
            value: s,
            label: formatSpecialization(s),
          }))}
          {...form.register('specialization')}
        />
        <Input
          label="Технологический стек"
          {...form.register('stack')}
          error={form.formState.errors.stack?.message}
        />
        <Select
          label="Предполагаемый грейд"
          options={GRADE_OPTIONS}
          {...form.register('claimedGrade')}
        />
        {error ? <div style={{ color: 'var(--danger)' }}>{error}</div> : null}
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending
            ? 'Стартуем...'
            : hasPrevious || isRetestIntent
              ? 'Пройти повторно'
              : 'Начать тестирование'}
        </Button>
        {hasPrevious ? (
          <p className="muted" style={{ marginBottom: 0 }}>
            Повторный тест обновит актуальный результат в профиле. История сохраняется на сервере.
          </p>
        ) : null}
      </form>

      <Link to="/candidate/profile" className="muted">
        Вернуться в профиль
      </Link>
    </div>
  );
}
