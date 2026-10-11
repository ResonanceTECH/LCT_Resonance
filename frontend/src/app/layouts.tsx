import { useMutation } from '@tanstack/react-query';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '@/features/auth/AuthContext';
import { NotificationBell } from '@/features/notifications/NotificationBell';
import { authApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Button } from '@/shared/ui';

const ROLE_LABEL: Record<string, string> = {
  candidate: 'Кандидат',
  employer: 'Работодатель',
  admin: 'Администратор',
};

/** Backend rule: an unverified employer cannot send offers, a candidate is not in search. */
function VerifyEmailBanner() {
  const { user } = useAuth();
  const resend = useMutation({ mutationFn: authApi.resendVerification });
  if (!user || user.emailVerified !== false) return null;
  const effect =
    user.role === 'employer'
      ? 'отправлять предложения можно после подтверждения'
      : 'до подтверждения профиль не виден работодателям';
  return (
    <div className="section-card row" data-testid="verify-email-banner" style={{ marginBottom: '1.5rem' }}>
      <span>
        Подтвердите email {user.email}: ссылка отправлена при регистрации, {effect}.
      </span>
      <Button
        type="button"
        variant="secondary"
        onClick={() => resend.mutate()}
        disabled={resend.isPending || resend.isSuccess}
      >
        {resend.isSuccess ? 'Письмо отправлено' : 'Отправить ещё раз'}
      </Button>
      {resend.isError ? <span className="muted">{getErrorMessage(resend.error)}</span> : null}
    </div>
  );
}

function initials(name?: string) {
  if (!name) return 'U';
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('');
}

function Shell({ links }: { links: { to: string; label: string }[] }) {
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-sidebar-brand">
          FSP <span>Talent</span>
        </div>
        <nav className="nav" aria-label="Основная навигация">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
              end={
                link.to === '/admin/overview'
                  ? false
                  : link.to.split('/').length <= 2
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="app-main">
        <header className="topbar">
          <div className="row" style={{ marginRight: 'auto' }} />
          <NotificationBell />
          <div className="topbar-user">
            <div className="topbar-avatar" aria-hidden>
              {initials(user?.displayName)}
            </div>
            <div className="topbar-meta">
              <strong>{user?.displayName}</strong>
              <span>{user ? ROLE_LABEL[user.role] ?? user.role : ''}</span>
            </div>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={() => void logout()}>
            Выйти
          </Button>
        </header>
        <main className="page">
          <VerifyEmailBanner />
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function CandidateLayout() {
  return (
    <Shell
      links={[
        { to: '/candidate', label: 'Обзор' },
        { to: '/candidate/profile', label: 'Профиль' },
        { to: '/candidate/fsp', label: 'ФСП' },
        { to: '/candidate/offers', label: 'Предложения' },
        { to: '/candidate/testing', label: 'Тест' },
        { to: '/candidate/vacancies', label: 'Вакансии' },
      ]}
    />
  );
}

export function EmployerLayout() {
  return (
    <Shell
      links={[
        { to: '/employer', label: 'Обзор' },
        { to: '/employer/talent-pool', label: 'Пул кандидатов' },
        { to: '/employer/vacancies', label: 'Вакансии' },
        { to: '/employer/shortlist', label: 'Избранное' },
        { to: '/employer/compare', label: 'Сравнение' },
        { to: '/employer/offers', label: 'Предложения' },
      ]}
    />
  );
}

export function AdminLayout() {
  return (
    <Shell
      links={[
        { to: '/admin/overview', label: 'Обзор' },
        { to: '/admin/users', label: 'Пользователи' },
        { to: '/admin/assessments', label: 'Тестирование' },
        { to: '/admin/categories', label: 'Категории' },
        { to: '/admin/offers', label: 'Приглашения' },
        { to: '/admin/vacancies', label: 'Вакансии' },
      ]}
    />
  );
}
