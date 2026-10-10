import type { TestQuestion as Question } from '@/entities/types';
import { Button } from '@/shared/ui';

export function TestQuestionView({
  question,
  selected,
  onSelect,
  onNext,
  isLast,
  submitting,
}: {
  question: Question;
  selected?: string;
  onSelect: (optionId: string) => void;
  onNext: () => void;
  isLast: boolean;
  submitting?: boolean;
}) {
  return (
    <div className="section-card stack">
      <h2>{question.text}</h2>
      {question.code ? (
        <pre
          data-testid="question-code"
          style={{
            background: 'var(--surface-2)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.75rem 1rem',
            overflowX: 'auto',
            margin: 0,
          }}
        >
          <code>{question.code}</code>
        </pre>
      ) : null}
      <div className="stack">
        {question.options.map((option) => (
          <label key={option.id} className="section-card" style={{ cursor: 'pointer' }}>
            <input
              type="radio"
              name={question.id}
              checked={selected === option.id}
              onChange={() => onSelect(option.id)}
            />{' '}
            {option.text}
          </label>
        ))}
      </div>
      <div>
        <Button type="button" disabled={!selected || submitting} onClick={onNext}>
          {isLast ? 'Завершить тест' : 'Далее'}
        </Button>
      </div>
    </div>
  );
}
