import type { CandidateMatch } from '@/entities/types';
import { MatchReasonList } from './MatchReason';

export function MatchScore({ match }: { match: CandidateMatch }) {
  return (
    <div className="match-box">
      <div className="match-score">Соответствие {match.score}%</div>
      <h3 style={{ marginTop: '0.5rem' }}>Почему подходит:</h3>
      <MatchReasonList reasons={match.reasons} />
      {match.missingInProfileSkills.length > 0 ? (
        <div style={{ marginTop: '0.85rem' }}>
          <strong>Не указано в профиле:</strong>
          <p style={{ margin: '0.35rem 0 0' }}>
            {match.missingInProfileSkills.join(', ')}
            <span className="muted"> — навык не указан в профиле</span>
          </p>
        </div>
      ) : null}
    </div>
  );
}
