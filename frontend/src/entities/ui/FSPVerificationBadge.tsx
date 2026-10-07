import { Badge } from '@/shared/ui';

export function FSPVerificationBadge({ label = 'Подтверждено ФСП' }: { label?: string }) {
  return <Badge tone="fsp">{label}</Badge>;
}
