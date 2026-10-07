import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { CandidateProfileView } from '@/entities/ui/CandidateProfile';
import { SkillRadar } from '@/entities/ui/SkillRadar';
import { candidateApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Button, ErrorState, Loader } from '@/shared/ui';

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
          <Link to={`/p/${profileQuery.data?.id ?? ''}`} target="_blank" rel="noreferrer">
            <Button type="button" variant="secondary">
              Public Career Passport
            </Button>
          </Link>
          <Link to="/candidate/profile/edit">
            <Button type="button">Редактировать</Button>
          </Link>
        </div>
      </div>
      <CandidateProfileView
        mode="self"
        profile={profileQuery.data!}
        achievements={fspQuery.data?.achievements ?? []}
      />
      {radarQuery.data ? <SkillRadar radar={radarQuery.data} /> : null}
    </div>
  );
}
