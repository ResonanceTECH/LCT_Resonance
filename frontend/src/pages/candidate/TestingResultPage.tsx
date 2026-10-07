import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { TestResultView } from '@/entities/ui/TestResult';
import { testingApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Button, ErrorState, Loader } from '@/shared/ui';

export function CandidateTestingResultPage() {
  const [params] = useSearchParams();
  const sessionId = params.get('sessionId') ?? '';

  const query = useQuery({
    queryKey: ['testing', sessionId, 'result'],
    queryFn: () => testingApi.result(sessionId),
    enabled: Boolean(sessionId),
  });

  if (!sessionId) {
    return <ErrorState title="Сессия не указана" action={<Link to="/candidate/testing"><Button type="button">К тесту</Button></Link>} />;
  }
  if (query.isLoading) return <Loader />;
  if (query.isError || !query.data) {
    return (
      <ErrorState
        title="Результат недоступен"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  return (
    <div className="stack">
      <TestResultView result={query.data} />
      {query.data.isRetest ? (
        <BadgeLike>Повторное прохождение</BadgeLike>
      ) : null}
      <div className="row">
        <Link to="/candidate/testing?retest=1">
          <Button type="button">Пройти повторно</Button>
        </Link>
        <Link to="/candidate/profile">
          <Button type="button" variant="secondary">
            В профиль
          </Button>
        </Link>
      </div>
    </div>
  );
}

function BadgeLike({ children }: { children: string }) {
  return (
    <div className="section-card" data-testid="retest-badge">
      {children}
    </div>
  );
}
