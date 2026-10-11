import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { PassportUnpublishedReason } from '@/entities/types';
import { CandidateProfileView } from '@/entities/ui/CandidateProfile';
import { SkillRadar } from '@/entities/ui/SkillRadar';
import { candidateApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Button, ErrorState, Loader } from '@/shared/ui';

const UNPUBLISHED_HINT: Record<PassportUnpublishedReason, string> = {
  EMAIL_NOT_VERIFIED: 'Паспорт откроется по ссылке после подтверждения email.',
  CONSENT_REQUIRED:
    'Паспорт скрыт: нужно согласие на публикацию профиля. После публикации профиль увидят ' +
    'работодатели, а паспорт откроется по ссылке. Контакты останутся скрытыми. Согласие можно отозвать.',
};

/** Публичный карьерный паспорт: ссылка или причина, почему ещё скрыт. */
function PassportCard() {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const passportQuery = useQuery({
    queryKey: ['candidate', 'passport'],
    queryFn: candidateApi.passport,
  });
  const publishMutation = useMutation({
    mutationFn: () =>
      candidateApi.updateConsents([{ type: 'profile_publication', accepted: true }]),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['candidate', 'passport'] });
      await queryClient.invalidateQueries({ queryKey: ['candidate', 'me'] });
    },
  });

  if (!passportQuery.data) return null;
  const { slug, url, published, reason } = passportQuery.data;

  const copy = () => {
    void navigator.clipboard
      ?.writeText(url)
      .then(() => setCopied(true))
      .catch(() => setCopied(false));
  };

  return (
    <div className="section-card stack" data-testid="passport-card" style={{ marginBottom: '1rem' }}>
      <strong>Карьерный паспорт</strong>
      {published ? (
        <>
          <p className="muted">
            Публичная страница без контактов: ссылкой можно поделиться в резюме или соцсетях.
          </p>
          <code data-testid="passport-url" style={{ wordBreak: 'break-all' }}>
            {url}
          </code>
          <div className="row">
            <Link to={`/p/${slug}`} target="_blank" rel="noreferrer">
              <Button type="button" variant="secondary">
                Открыть паспорт
              </Button>
            </Link>
            <Button type="button" variant="secondary" onClick={copy}>
              {copied ? 'Ссылка скопирована' : 'Скопировать ссылку'}
            </Button>
          </div>
        </>
      ) : (
        <>
          <p className="muted">{reason ? UNPUBLISHED_HINT[reason] : 'Паспорт пока скрыт.'}</p>
          {reason === 'CONSENT_REQUIRED' ? (
            <div>
              <Button
                type="button"
                onClick={() => publishMutation.mutate()}
                disabled={publishMutation.isPending}
              >
                Опубликовать паспорт
              </Button>
            </div>
          ) : null}
          {publishMutation.isError ? (
            <span className="muted">{getErrorMessage(publishMutation.error)}</span>
          ) : null}
        </>
      )}
    </div>
  );
}

export function CandidateProfilePage() {
  const profileQuery = useQuery({
    queryKey: ['candidate', 'me'],
    queryFn: candidateApi.me,
  });
  const fspQuery = useQuery({
    queryKey: ['candidate', 'fsp'],
    queryFn: candidateApi.fspAchievements,
  });
  const radarQuery = useQuery({
    queryKey: ['candidate', profileQuery.data?.id, 'radar'],
    queryFn: () => candidateApi.skillRadar(profileQuery.data!.id),
    enabled: Boolean(profileQuery.data?.id),
  });

  if (profileQuery.isLoading) return <Loader label="Загружаем профиль..." />;
  if (profileQuery.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить профиль"
        description={getErrorMessage(profileQuery.error)}
        onRetry={() => void profileQuery.refetch()}
      />
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Мой профиль</h1>
          <p>Так вас видят работодатели (без контактов до принятия оффера).</p>
        </div>
        <div className="row">
          <Link to="/candidate/profile/edit">
            <Button type="button">Редактировать</Button>
          </Link>
        </div>
      </div>
      <PassportCard />
      <CandidateProfileView
        mode="self"
        profile={profileQuery.data!}
        achievements={fspQuery.data?.achievements ?? []}
      />
      {radarQuery.data ? <SkillRadar radar={radarQuery.data} /> : null}
    </div>
  );
}
