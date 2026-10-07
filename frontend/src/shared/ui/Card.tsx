import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import styles from './ui.module.css';

export function Card({
  children,
  to,
  className,
}: {
  children: ReactNode;
  to?: string;
  className?: string;
}) {
  const cls = [styles.card, to ? styles.cardClickable : '', className].filter(Boolean).join(' ');
  if (to) return <Link to={to} className={cls}>{children}</Link>;
  return <div className={cls}>{children}</div>;
}
