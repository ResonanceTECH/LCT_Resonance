import type { FspAchievement } from '@/entities/types';
import { formatDate } from '@/shared/lib/formatters';
import { Card } from '@/shared/ui';
import { FSPVerificationBadge } from './FSPVerificationBadge';

export function FSPAchievementCard({ achievement }: { achievement: FspAchievement }) {
  return (
    <Card className="fsp-block">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>{achievement.title}</h3>
        <FSPVerificationBadge />
      </div>
      <p style={{ marginTop: '0.5rem' }}>
        {[achievement.discipline, formatDate(achievement.date), achievement.placeOrResult]
          .filter(Boolean)
          .join(' · ')}
      </p>
      <div className="muted" style={{ fontSize: '0.9rem' }}>
        {achievement.participantRole ? <div>Роль: {achievement.participantRole}</div> : null}
        {achievement.sportRank ? <div>Разряд: {achievement.sportRank}</div> : null}
      </div>
    </Card>
  );
}
