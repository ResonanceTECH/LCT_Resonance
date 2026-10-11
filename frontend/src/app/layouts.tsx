import { useEffect, useId, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
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
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);
  const navId = useId();

  useEffect(() => {
    setNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!navOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setNavOpen(false);
    };
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [navOpen]);

  return (
    <div className={`app-shell${navOpen ? ' nav-open' : ''}`}>
      {navOpen ? (
        <button
          type="button"
          className="app-nav-backdrop"
          aria-label="Закрыть меню"
          onClick={() => setNavOpen(false)}
        />
      ) : null}
      <aside className="app-sidebar" id={navId}>
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
              onClick={() => setNavOpen(false)}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="app-main">
        <header className="topbar">
          <button
            type="button"
            className="app-nav-toggle"
            aria-expanded={navOpen}
            aria-controls={navId}
            aria-label={navOpen ? 'Закрыть меню' : 'Открыть меню'}
            onClick={() => setNavOpen((v) => !v)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
              {navOpen ? (
                <path
                  d="M6 6l12 12M18 6L6 18"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              ) : (
                <path
                  d="M4 7h16M4 12h16M4 17h16"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              )}
            </svg>
          </button>
          <div className="topbar-brand" aria-hidden>
            FSP <span>Talent</span>
          </div>
          <div className="topbar-actions">
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
          </div>
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
