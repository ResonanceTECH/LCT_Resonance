import { Eye, EyeOff, type LucideIcon } from 'lucide-react';
import { useState, type InputHTMLAttributes, type ReactNode } from 'react';
import styles from './ui.module.css';

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
  icon?: LucideIcon;
  hint?: ReactNode;
};

export function Input({ label, error, id, icon: Icon, hint, type = 'text', className, ...props }: Props) {
  const [showPassword, setShowPassword] = useState(false);
  const inputId =
    id ??
    (typeof props.name === 'string' ? props.name : undefined) ??
    `input-${label.replace(/\s+/g, '-').toLowerCase()}`;
  const isPassword = type === 'password';
  const resolvedType = isPassword && showPassword ? 'text' : type;

  return (
    <div className={styles.field}>
      <label htmlFor={inputId}>{label}</label>
      <div className={styles.controlWrap}>
        {Icon ? (
          <span className={styles.controlIcon} aria-hidden>
            <Icon size={18} strokeWidth={1.75} />
          </span>
        ) : null}
        <input
          id={inputId}
          type={resolvedType}
          className={[
            styles.control,
            Icon ? styles.controlWithIcon : '',
            isPassword ? styles.controlWithToggle : '',
            error ? styles.controlError : '',
            className,
          ]
            .filter(Boolean)
            .join(' ')}
          {...props}
        />
        {isPassword ? (
          <button
            type="button"
            className={styles.controlIconRight}
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff size={18} strokeWidth={1.75} /> : <Eye size={18} strokeWidth={1.75} />}
          </button>
        ) : null}
      </div>
      {error ? <span className={styles.errorText}>{error}</span> : null}
      {!error && hint ? hint : null}
    </div>
  );
}
