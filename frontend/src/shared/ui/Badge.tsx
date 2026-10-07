import type { ReactNode } from 'react';
import styles from './ui.module.css';

type Tone = 'default' | 'accent' | 'fsp' | 'warn' | 'success' | 'danger';

const toneMap: Record<Tone, string | undefined> = {
  default: undefined,
  accent: styles.badgeAccent,
  fsp: styles.badgeFsp,
  warn: styles.badgeWarn,
  success: styles.badgeSuccess,
  danger: styles.badgeDanger,
};

export function Badge({ children, tone = 'default' }: { children: ReactNode; tone?: Tone }) {
  return <span className={[styles.badge, toneMap[tone]].filter(Boolean).join(' ')}>{children}</span>;
}
