import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import styles from './ui.module.css';

type Variant = 'default' | 'compact' | 'hero';

const variantMap: Record<Variant, string | undefined> = {
  default: undefined,
  compact: styles.cardCompact,
  hero: styles.cardHero,
};

export function Card({
  children,
  to,
  className,
  variant = 'default',
}: {
  children: ReactNode;
  to?: string;
  className?: string;
  variant?: Variant;
}) {
  const cls = [styles.card, variantMap[variant], to ? styles.cardClickable : '', className]
    .filter(Boolean)
    .join(' ');
  if (to) return <Link to={to} className={cls}>{children}</Link>;
  return <div className={cls}>{children}</div>;
}
