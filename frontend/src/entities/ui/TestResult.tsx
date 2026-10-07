import type { TestResult as Result } from '@/entities/types';
import { formatGrade } from '@/shared/lib/formatters';
import { Badge } from '@/shared/ui';

export function TestResultView({ result }: { result: Result }) {
  return (
    <div className="section-card stack">
      <h2>Результат тестирования</h2>
      <div>
        <div className="muted">Заявленный уровень</div>
        <strong>{formatGrade(result.claimedGrade)}</strong>
      </div>
      <div>
        <div className="muted">Результат тестирования</div>
        <strong>
          {result.score}/{result.maxScore}
        </strong>
      </div>
      {result.gradeConfirmed ? (
        <Badge tone="success">Уровень подтвержден</Badge>
      ) : (
        <Badge tone="warn">Уровень не подтвержден</Badge>
      )}
      {result.isRetest ? <Badge tone="accent">Retest</Badge> : null}
    </div>
  );
}
