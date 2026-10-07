import type { CandidateMatch, CandidateProfile as Profile, FspAchievement } from '@/entities/types';
import {
  formatGrade,
  formatReadiness,
  formatWorkFormat,
} from '@/shared/lib/formatters';
import { Badge, uiStyles } from '@/shared/ui';
import { FSPAchievementCard } from './FSPAchievementCard';
import { GradeBadge } from './GradeBadge';
import { MatchScore } from './MatchScore';
import { SalaryRange } from './SalaryRange';
import { SkillBadge } from './SkillBadge';

export function CandidateProfileView({
  profile,
  achievements = [],
  match,
  mode,
}: {
  profile: Profile;
  achievements?: FspAchievement[];
  match?: CandidateMatch;
  mode: 'self' | 'employer';
}) {
  return (
    <div className="stack">
      <section className="section-card">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ marginBottom: 0 }}>{profile.fullName}</h2>
            <p style={{ margin: '0.35rem 0 0' }}>
              {profile.desiredPosition ?? profile.specialization}
              {profile.city ? ` · ${profile.city}` : ''}
            </p>
          </div>
          <Badge tone="accent">{formatReadiness(profile.readiness)}</Badge>
        </div>
        {profile.about ? <p style={{ marginTop: '1rem' }}>{profile.about}</p> : null}
      </section>

      <div className="grid-2">
        <section className="section-card">
          <h3>Специализация и уровень</h3>
          <div className="row">
            <Badge>{profile.specialization}</Badge>
            <div>
              <div className="muted" style={{ fontSize: '0.85rem' }}>
                Заявленный уровень
              </div>
              <GradeBadge grade={profile.claimedGrade} />
            </div>
          </div>
          {profile.testResult ? (
            <div style={{ marginTop: '1rem' }}>
              <div className="muted" style={{ fontSize: '0.85rem' }}>
                Результат тестирования
              </div>
              <strong>
                {profile.testResult.score}/{profile.testResult.maxScore}
              </strong>
              {profile.testResult.gradeConfirmed ? (
                <div>
                  <Badge tone="success">Уровень подтвержден</Badge>
                </div>
              ) : null}
            </div>
          ) : null}
          {profile.experienceYears != null ? (
            <p style={{ marginTop: '1rem', marginBottom: 0 }}>
              Опыт: {profile.experienceYears} лет
              {profile.experienceDescription ? ` — ${profile.experienceDescription}` : ''}
            </p>
          ) : null}
        </section>

        <section className="section-card">
          <h3>Карьерные предпочтения</h3>
          <p>
            Зарплата:{' '}
            <SalaryRange
              from={profile.salaryFrom}
              to={profile.salaryTo}
              currency={profile.currency}
            />
          </p>
          <p>
            Формат:{' '}
            {profile.workFormat ? formatWorkFormat(profile.workFormat) : 'Не указан'}
          </p>
          <p style={{ marginBottom: 0 }}>Статус: {formatReadiness(profile.readiness)}</p>
        </section>
      </div>

      <section className="section-card">
        <h3>Навыки и технологии</h3>
        <div className={uiStyles.skills}>
          {profile.skills.map((skill) => (
            <SkillBadge key={skill} skill={skill} />
          ))}
        </div>
        <p className="muted" style={{ marginTop: '0.75rem', marginBottom: 0, fontSize: '0.85rem' }}>
          Самостоятельно указанные навыки не помечаются как подтверждённые ФСП.
        </p>
      </section>

      {mode === 'employer' && match ? <MatchScore match={match} /> : null}

      <section className="section-card fsp-block">
        <h3>Подтверждённые достижения ФСП</h3>
        {achievements.length === 0 ? (
          <p style={{ marginBottom: 0 }}>Достижения ФСП пока не найдены.</p>
        ) : (
          <div className="stack">
            {achievements.map((a) => (
              <FSPAchievementCard key={a.id} achievement={a} />
            ))}
          </div>
        )}
      </section>

      {mode === 'employer' ? (
        <p className="muted" style={{ fontSize: '0.85rem' }}>
          Заявленный уровень: {formatGrade(profile.claimedGrade)}
          {profile.confirmedGrade
            ? ` · подтверждённый: ${formatGrade(profile.confirmedGrade)}`
            : ''}
        </p>
      ) : null}
    </div>
  );
}
