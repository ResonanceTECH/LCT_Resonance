import { uiStyles } from '@/shared/ui';

export function SkillBadge({ skill }: { skill: string }) {
  return <span className={uiStyles.skillChip}>{skill}</span>;
}
