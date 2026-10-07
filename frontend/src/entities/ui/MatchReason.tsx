import type { MatchReason as MatchReasonType } from '@/entities/types';

export function MatchReasonList({ reasons }: { reasons: MatchReasonType[] }) {
  return (
    <ul className="reason-list">
      {reasons.map((reason) => (
        <li key={reason.code} className={reason.positive ? 'pos' : 'neg'}>
          {reason.label}
        </li>
      ))}
    </ul>
  );
}
