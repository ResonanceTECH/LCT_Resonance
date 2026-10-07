import type { ReactNode } from 'react';
import styles from './ui.module.css';
import { Button } from './Button';

export function ErrorState({
  title = 'Ошибка',
  description,
  onRetry,
  action,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
  action?: ReactNode;
}) {
  return (
    <div className={styles.stateBox}>
      <h3>{title}</h3>
      {description ? <p>{description}</p> : null}
      {onRetry ? (
        <Button type="button" variant="secondary" onClick={onRetry}>
          Повторить
        </Button>
      ) : null}
      {action}
    </div>
  );
}
