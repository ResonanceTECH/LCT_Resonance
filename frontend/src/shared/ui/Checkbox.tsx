import type { InputHTMLAttributes } from 'react';
import styles from './ui.module.css';

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label: string;
};

export function Checkbox({ label, id, ...props }: Props) {
  const checkId = id ?? props.name;
  return (
    <label className={styles.checkbox} htmlFor={checkId}>
      <input id={checkId} type="checkbox" {...props} />
      <span>{label}</span>
    </label>
  );
}
