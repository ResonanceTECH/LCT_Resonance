import type { TextareaHTMLAttributes } from 'react';
import styles from './ui.module.css';

type Props = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  error?: string;
};

export function Textarea({ label, error, id, ...props }: Props) {
  const areaId =
    id ??
    (typeof props.name === 'string' ? props.name : undefined) ??
    `textarea-${label.replace(/\s+/g, '-').toLowerCase()}`;
  return (
    <div className={styles.field}>
      <label htmlFor={areaId}>{label}</label>
      <textarea id={areaId} className={`${styles.control} ${styles.textarea}`} {...props} />
      {error ? <span className={styles.errorText}>{error}</span> : null}
    </div>
  );
}
