import type { TalentPoolItem } from '@/entities/types';
import {
  formatGrade,
  formatSpecialization,
  formatReadiness,
} from '@/shared/lib/formatters';
import { Badge, Card, uiStyles } from '@/shared/ui';
import { FSPVerificationBadge } from './FSPVerificationBadge';
import { SkillBadge } from './SkillBadge';

export function CandidateCard({
  candidate,
  to,
}: {
  candidate: TalentPoolItem;
  to: string;
}) {
  return (
    <Card to={to}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ margin: 0 }}>{candidate.fullName}</h3>
          <p style={{ margin: '0.25rem 0 0' }}>
            {formatSpecialization(candidate.specialization)} · {formatGrade(candidate.claimedGrade)}
          </p>
        </div>
        {candidate.match ? (
          <Badge tone="success">Соответствие {candidate.match.score}%</Badge>
        ) : null}
      </div>
      <div className={uiStyles.skills} style={{ marginTop: '0.75rem' }}>
        {candidate.skills.slice(0, 5).map((skill) => (
          <SkillBadge key={skill} skill={skill} />
        ))}
      </div>
      <div className="row" style={{ marginTop: '0.85rem' }}>
        <Badge tone="accent">{formatReadiness(candidate.readiness)}</Badge>
        {candidate.hasFspAchievements ? <FSPVerificationBadge label="Подтверждено ФСП" /> : null}
      </div>
      {candidate.match?.reasons?.length ? (
        <p style={{ marginTop: '0.75rem', marginBottom: 0, fontSize: '0.9rem' }}>
          {candidate.match.reasons
            .filter((r) => r.positive)
            .slice(0, 2)
            .map((r) => r.label)
            .join(' · ')}
        </p>
      ) : null}
    </Card>
  );
}
