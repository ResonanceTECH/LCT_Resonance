import type { InputHTMLAttributes } from 'react';
import styles from './ui.module.css';

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label: string;
};

export function Radio({ label, id, className, ...props }: Props) {
  const radioId =
    id ??
    (typeof props.name === 'string' && props.value != null
      ? `${props.name}-${String(props.value)}`
      : undefined) ??
    `radio-${label.replace(/\s+/g, '-').toLowerCase()}`;

  return (
    <label className={[styles.radio, className].filter(Boolean).join(' ')} htmlFor={radioId}>
      <input id={radioId} type="radio" className={styles.radioInput} {...props} />
      <span>{label}</span>
    </label>
  );
}
