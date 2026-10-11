import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Ban,
  FileQuestion,
  ServerCrash,
  Wrench,
  type LucideIcon,
} from 'lucide-react';
import { Button } from './Button';
import styles from './StatusPage.module.css';

export type StatusTone = 'primary' | 'danger' | 'warn' | 'info';

export type StatusAction = {
  label: string;
  to?: string;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
};

export type StatusPageProps = {
  code: string;
  title: string;
  description: string;
  tone?: StatusTone;
  icon?: LucideIcon;
  primaryAction?: StatusAction;
  secondaryAction?: StatusAction;
  meta?: string;
  /** Compact card for /ui-kit demos */
  compact?: boolean;
  hideChrome?: boolean;
};

function ActionButton({ action }: { action: StatusAction }) {
  const btn = (
    <Button type="button" variant={action.variant ?? 'primary'} onClick={action.onClick}>
      {action.label}
    </Button>
  );
  if (action.to) {
    return <Link to={action.to}>{btn}</Link>;
  }
  return btn;
}

export function StatusPage({
  code,
  title,
  description,
  tone = 'primary',
  icon: Icon = FileQuestion,
  primaryAction,
  secondaryAction,
  meta,
  compact = false,
  hideChrome = false,
}: StatusPageProps) {
  return (
    <div
      className={[styles.page, compact ? styles.compact : ''].filter(Boolean).join(' ')}
      data-testid="status-page"
      data-status-code={code}
    >
      {!hideChrome ? (
        <header className={styles.topbar}>
          <Link to="/" className={styles.brand}>
            <img className={styles.brandLogo} src="/fsp-logo.svg" alt="" />
            <span className={styles.brandName}>FSP Talent</span>
          </Link>
          {!compact ? (
            <Link to="/login">
              <Button type="button" variant="ghost" size="sm">
                Войти
              </Button>
            </Link>
          ) : null}
        </header>
      ) : null}

      <main className={styles.main}>
        <div className={styles.panel}>
          <div className={styles.iconWrap} data-tone={tone} aria-hidden>
            <Icon size={compact ? 20 : 24} strokeWidth={1.75} />
          </div>
          <p className={styles.code} data-tone={tone}>
            {code}
          </p>
          <h1 className={styles.title}>{title}</h1>
          <p className={styles.description}>{description}</p>
          {primaryAction || secondaryAction ? (
            <div className={styles.actions}>
              {primaryAction ? <ActionButton action={primaryAction} /> : null}
              {secondaryAction ? (
                <ActionButton action={{ variant: 'secondary', ...secondaryAction }} />
              ) : null}
            </div>
          ) : null}
          {meta ? <p className={styles.meta}>{meta}</p> : null}
        </div>
      </main>
    </div>
  );
}

export const STATUS_PRESETS = {
  notFound: {
    code: '404',
    title: 'Страница не найдена',
    description: 'Такого адреса нет — ссылка устарела или страница переехала.',
    tone: 'primary' as const,
    icon: FileQuestion,
    primaryAction: { label: 'На главную', to: '/' },
    secondaryAction: { label: 'Войти', to: '/login', variant: 'secondary' as const },
  },
  forbidden: {
    code: '403',
    title: 'Доступ ограничен',
    description:
      'У вашей роли нет прав на этот раздел. Войдите под нужным аккаунтом или вернитесь в кабинет.',
    tone: 'warn' as const,
    icon: Ban,
    primaryAction: { label: 'В кабинет', to: '/' },
    secondaryAction: { label: 'Сменить аккаунт', to: '/login', variant: 'secondary' as const },
  },
  serverError: {
    code: '500',
    title: 'Что-то сломалось',
    description: 'Сервер не ответил как надо. Попробуйте ещё раз — если не поможет, зайдите позже.',
    tone: 'danger' as const,
    icon: ServerCrash,
    primaryAction: { label: 'На главную', to: '/' },
    secondaryAction: {
      label: 'Обновить',
      onClick: () => window.location.reload(),
      variant: 'secondary' as const,
    },
  },
  maintenance: {
    code: '503',
    title: 'Технические работы',
    description: 'Платформа временно недоступна. Обычно это занимает несколько минут.',
    tone: 'info' as const,
    icon: Wrench,
    primaryAction: { label: 'На главную', to: '/' },
  },
  offline: {
    code: 'Offline',
    title: 'Нет соединения',
    description:
      'Проверьте интернет и обновите страницу. Данные подтянутся, как только сеть вернётся.',
    tone: 'warn' as const,
    icon: AlertTriangle,
    primaryAction: {
      label: 'Обновить',
      onClick: () => window.location.reload(),
    },
    secondaryAction: { label: 'На главную', to: '/', variant: 'secondary' as const },
  },
} as const;

export type StatusPresetKey = keyof typeof STATUS_PRESETS;

export function StatusPageFromPreset({
  preset,
  compact,
  overrides,
}: {
  preset: StatusPresetKey;
  compact?: boolean;
  overrides?: Partial<StatusPageProps>;
}) {
  const base = STATUS_PRESETS[preset];
  return <StatusPage {...base} compact={compact} {...overrides} />;
}
