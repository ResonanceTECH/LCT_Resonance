import type { SelectHTMLAttributes } from 'react';
import styles from './ui.module.css';

type Option = { value: string; label: string };

type Props = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  options: Option[];
  error?: string;
  allowEmpty?: boolean;
  emptyLabel?: string;
};

export function Select({
  label,
  options,
  error,
  id,
  allowEmpty,
  emptyLabel = 'Все',
  ...props
}: Props) {
  const selectId =
    id ??
    (typeof props.name === 'string' ? props.name : undefined) ??
    `select-${label.replace(/\s+/g, '-').toLowerCase()}`;
  return (
    <div className={styles.field}>
      <label htmlFor={selectId}>{label}</label>
      <select id={selectId} className={styles.control} {...props}>
        {allowEmpty ? <option value="">{emptyLabel}</option> : null}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error ? <span className={styles.errorText}>{error}</span> : null}
    </div>
  );
}
