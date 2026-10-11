import type { InputHTMLAttributes } from 'react';
import styles from './ui.module.css';

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> & {
  label: string;
};

export function Switch({ label, id, className, ...props }: Props) {
  const switchId =
    id ??
    (typeof props.name === 'string' ? props.name : undefined) ??
    `switch-${label.replace(/\s+/g, '-').toLowerCase()}`;

  return (
    <label className={[styles.switch, className].filter(Boolean).join(' ')} htmlFor={switchId}>
      <input id={switchId} type="checkbox" role="switch" className={styles.switchInput} {...props} />
      <span className={styles.switchTrack} aria-hidden>
        <span className={styles.switchThumb} />
      </span>
      <span>{label}</span>
    </label>
  );
}
