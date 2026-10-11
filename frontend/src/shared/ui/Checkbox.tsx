import type { InputHTMLAttributes, ReactNode } from 'react';
import styles from './ui.module.css';

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label: ReactNode;
};

export function Checkbox({ label, id, className, ...props }: Props) {
  const checkId = id ?? props.name;
  return (
    <label
      className={[styles.checkbox, styles.checkboxTop, className].filter(Boolean).join(' ')}
      htmlFor={checkId}
    >
      <input id={checkId} type="checkbox" {...props} />
      <span>{label}</span>
    </label>
  );
}
