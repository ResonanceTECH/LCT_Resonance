import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { CandidateProfileView } from '@/entities/ui/CandidateProfile';
import { OfferForm } from '@/entities/ui/OfferForm';
import { SkillRadar } from '@/entities/ui/SkillRadar';
import { candidateApi, offerApi, shortlistApi, vacancyApi } from '@/shared/api/endpoints';
import { ApiError, getErrorMessage } from '@/shared/api/errors';
import { Button, ErrorState, Loader, Modal } from '@/shared/ui';

export function EmployerCandidateDetailPage() {
  const { id = '' } = useParams();
  const [params] = useSearchParams();
  const vacancyId = params.get('vacancyId') ?? undefined;
  const queryClient = useQueryClient();
  const [offerOpen, setOfferOpen] = useState(false);
  const [offerSuccess, setOfferSuccess] = useState(false);

  const profileQuery = useQuery({
    queryKey: ['candidates', id],
    queryFn: () => candidateApi.byId(id),
    enabled: Boolean(id),
  });

  const vacanciesQuery = useQuery({
    queryKey: ['vacancies', 'employer'],
    queryFn: vacancyApi.employerList,
  });

  const shortlistQuery = useQuery({
    queryKey: ['shortlist'],
    queryFn: shortlistApi.list,
  });

  const contactsQuery = useQuery({
    queryKey: ['candidates', id, 'contacts'],
    queryFn: () => candidateApi.contacts(id),
    enabled: Boolean(id),
    retry: false,
  });

  const fspQuery = useQuery({
    queryKey: ['candidates', id, 'fsp'],
    queryFn: () => candidateApi.fspByCandidateId(id),
    enabled: Boolean(id),
  });

  const matchQuery = useQuery({
    queryKey: ['candidates', id, 'match', vacancyId],
    queryFn: () => candidateApi.list({ vacancyId }),
    enabled: Boolean(id && vacancyId),
  });

  const radarQuery = useQuery({
    queryKey: ['candidates', id, 'radar'],
    queryFn: () => candidateApi.skillRadar(id),
    enabled: Boolean(id),
  });

  const addShortlist = useMutation({
    mutationFn: () => shortlistApi.add(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['shortlist'] }),
  });
  const removeShortlist = useMutation({
    mutationFn: () => shortlistApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['shortlist'] }),
  });

  const createOffer = useMutation({
    mutationFn: offerApi.create,
    onSuccess: async () => {
      setOfferSuccess(true);
      setOfferOpen(false);
      await queryClient.invalidateQueries({ queryKey: ['offers'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard', 'employer'] });
    },
  });

  if (profileQuery.isLoading) return <Loader />;
  if (profileQuery.isError || !profileQuery.data) {
    return (
      <ErrorState
        title="Кандидат не найден"
        description={getErrorMessage(profileQuery.error)}
        onRetry={() => void profileQuery.refetch()}
      />
    );
  }

  const profile = profileQuery.data;
  const match = matchQuery.data?.items.find((i) => i.id === id)?.match;
  const inShortlist = (shortlistQuery.data ?? []).some((c) => c.id === id);
  const contactsHidden =
    contactsQuery.isError &&
    contactsQuery.error instanceof ApiError &&
    contactsQuery.error.status === 403;

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>{profile.fullName}</h1>
          <p>Просмотр работодателем. Контакты открываются только после согласия кандидата.</p>
        </div>
        <div className="row">
          <Link to="/employer/talent-pool">
            <Button type="button" variant="secondary">
              Назад
            </Button>
          </Link>
          {inShortlist ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() => removeShortlist.mutate()}
              disabled={removeShortlist.isPending}
            >
              Убрать из избранного
            </Button>
          ) : (
            <Button
              type="button"
              variant="secondary"
              onClick={() => addShortlist.mutate()}
              disabled={addShortlist.isPending}
            >
              В избранное
            </Button>
          )}
          <Button type="button" onClick={() => setOfferOpen(true)}>
            Отправить предложение
          </Button>
        </div>
      </div>

      {offerSuccess ? (
        <div className="section-card">Предложение успешно отправлено.</div>
      ) : null}

      <section className="section-card">
        <h3>Контакты</h3>
        {contactsQuery.isLoading ? <Loader label="Проверяем доступ..." /> : null}
        {contactsHidden ? (
          <div className="hidden-contacts">
            <strong>Контактные данные скрыты</strong>
            <p style={{ marginBottom: 0 }}>
              Контакты будут доступны после того, как кандидат примет предложение.
            </p>
          </div>
        ) : null}
        {contactsQuery.data ? (
          <div>
            {contactsQuery.data.email ? <div>Email: {contactsQuery.data.email}</div> : null}
            {contactsQuery.data.phone ? <div>Телефон: {contactsQuery.data.phone}</div> : null}
            {contactsQuery.data.telegram ? (
              <div>Telegram: {contactsQuery.data.telegram}</div>
            ) : null}
          </div>
        ) : null}
      </section>

      <CandidateProfileView
        mode="employer"
        profile={profile}
        match={match}
        achievements={fspQuery.data?.achievements ?? []}
      />

      {radarQuery.data ? <SkillRadar radar={radarQuery.data} /> : null}

      <Modal open={offerOpen} title="Новое предложение" onClose={() => setOfferOpen(false)}>
        <OfferForm
          vacancies={vacanciesQuery.data ?? []}
          candidateId={id}
          defaultVacancyId={vacancyId}
          submitting={createOffer.isPending}
          onSubmit={async (payload) => {
            await createOffer.mutateAsync(payload);
          }}
        />
        {createOffer.isError ? (
          <div style={{ color: 'var(--danger)', marginTop: '0.75rem' }}>
            {getErrorMessage(createOffer.error)}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
