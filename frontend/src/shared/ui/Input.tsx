import type { InputHTMLAttributes } from 'react';
import styles from './ui.module.css';

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
};

export function Input({ label, error, id, ...props }: Props) {
  const inputId =
    id ??
    (typeof props.name === 'string' ? props.name : undefined) ??
    `input-${label.replace(/\s+/g, '-').toLowerCase()}`;
  return (
    <div className={styles.field}>
      <label htmlFor={inputId}>{label}</label>
      <input id={inputId} className={styles.control} {...props} />
      {error ? <span className={styles.errorText}>{error}</span> : null}
    </div>
  );
}
