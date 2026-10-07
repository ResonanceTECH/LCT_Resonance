import type { Offer } from '@/entities/types';
import {
  formatDateTime,
  formatOfferStatus,
  formatWorkFormat,
} from '@/shared/lib/formatters';
import { Badge, Card } from '@/shared/ui';
import { SalaryRange } from './SalaryRange';

const toneByStatus = {
  new: 'accent',
  viewed: 'warn',
  accepted: 'success',
  declined: 'danger',
} as const;

export function OfferCard({ offer, to }: { offer: Offer; to?: string }) {
  return (
    <Card to={to}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ margin: 0 }}>{offer.positionTitle}</h3>
          <p style={{ margin: '0.25rem 0 0' }}>{offer.companyName}</p>
        </div>
        <Badge tone={toneByStatus[offer.status]}>{formatOfferStatus(offer.status)}</Badge>
      </div>
      <p style={{ marginTop: '0.75rem' }}>
        <strong>
          <SalaryRange
            from={offer.salaryFrom}
            to={offer.salaryTo}
            currency={offer.currency}
          />
        </strong>
        {' · '}
        {formatWorkFormat(offer.workFormat)}
      </p>
      <p style={{ marginBottom: 0 }}>{offer.message}</p>
      <p className="muted" style={{ marginTop: '0.75rem', marginBottom: 0, fontSize: '0.85rem' }}>
        {formatDateTime(offer.createdAt)}
      </p>
    </Card>
  );
}
