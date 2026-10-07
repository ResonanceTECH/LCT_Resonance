import { Badge } from '@/shared/ui';

export function SkillBadge({ skill }: { skill: string }) {
  return <Badge tone="accent">{skill}</Badge>;
}
