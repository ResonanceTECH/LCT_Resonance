import { formatSalary } from '@/shared/lib/formatters';

export function SalaryRange({
  from,
  to,
  currency = 'RUB',
}: {
  from?: number;
  to?: number;
  currency?: 'RUB' | 'USD';
}) {
  return <span>{formatSalary(from, to, currency)}</span>;
}
