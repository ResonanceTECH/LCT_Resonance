import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { TestQuestionView } from '@/entities/ui/TestQuestion';
import { testingApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { ErrorState, Loader, ProgressBar } from '@/shared/ui';

export function CandidateTestingSessionPage() {
  const { sessionId = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string>();
  const [index, setIndex] = useState(0);
  const total = 3;

  const questionQuery = useQuery({
    queryKey: ['testing', sessionId, 'question', index],
    queryFn: () => testingApi.question(sessionId),
    enabled: Boolean(sessionId),
  });

  const answerMutation = useMutation({
    mutationFn: (payload: { questionId: string; optionId: string }) =>
      testingApi.answer(sessionId, payload),
  });

  const finishMutation = useMutation({
    mutationFn: () => testingApi.finish(sessionId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['candidate', 'me'] });
      navigate(`/candidate/testing/result?sessionId=${sessionId}`);
    },
  });

  if (questionQuery.isLoading) return <Loader label="Загружаем вопрос..." />;
  if (questionQuery.isError || !questionQuery.data) {
    return (
      <ErrorState
        title="Не удалось загрузить вопрос"
        description={getErrorMessage(questionQuery.error)}
        onRetry={() => void questionQuery.refetch()}
      />
    );
  }

  const question = questionQuery.data;
  const isLast = index >= total - 1;

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Тестирование</h1>
          <p>
            Вопрос {index + 1} из {total}
          </p>
        </div>
      </div>
      <ProgressBar value={index + 1} max={total} />
      <TestQuestionView
        question={question}
        selected={selected}
        onSelect={setSelected}
        submitting={answerMutation.isPending || finishMutation.isPending}
        isLast={isLast}
        onNext={() => {
          if (!selected) return;
          answerMutation.mutate(
            { questionId: question.id, optionId: selected },
            {
              onSuccess: () => {
                if (isLast) {
                  finishMutation.mutate();
                } else {
                  setSelected(undefined);
                  setIndex((v) => v + 1);
                }
              },
            },
          );
        }}
      />
      {(answerMutation.isError || finishMutation.isError) && (
        <div style={{ color: 'var(--danger)' }}>
          {getErrorMessage(answerMutation.error || finishMutation.error)}
        </div>
      )}
    </div>
  );
}
