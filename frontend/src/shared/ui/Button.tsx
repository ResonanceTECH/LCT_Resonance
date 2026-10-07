import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './ui.module.css';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  children: ReactNode;
};

export function Button({ variant = 'primary', className, children, ...props }: Props) {
  return (
    <button
      className={[styles.button, styles[variant], className].filter(Boolean).join(' ')}
      {...props}
    >
      {children}
    </button>
  );
}
