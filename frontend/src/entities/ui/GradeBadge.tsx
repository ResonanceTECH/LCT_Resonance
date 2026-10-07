import type { Grade } from '@/entities/types';
import { formatGrade } from '@/shared/lib/formatters';
import { Badge } from '@/shared/ui';

export function GradeBadge({ grade }: { grade: Grade }) {
  return <Badge>{formatGrade(grade)}</Badge>;
}
