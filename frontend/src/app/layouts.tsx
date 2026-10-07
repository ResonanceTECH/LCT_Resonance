import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '@/features/auth/AuthContext';
import { NotificationBell } from '@/features/notifications/NotificationBell';
import { Button } from '@/shared/ui';

function Shell({ links }: { links: { to: string; label: string }[] }) {
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">LCT Resonance</div>
        <nav className="nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
              end={link.to.split('/').length <= 2}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="row">
          <NotificationBell />
          <span className="muted">{user?.displayName}</span>
          <Button type="button" variant="secondary" onClick={() => void logout()}>
            Выйти
          </Button>
        </div>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </div>
  );
}

export function CandidateLayout() {
  return (
    <Shell
      links={[
        { to: '/candidate', label: 'Dashboard' },
        { to: '/candidate/profile', label: 'Профиль' },
        { to: '/candidate/fsp', label: 'ФСП' },
        { to: '/candidate/offers', label: 'Предложения' },
        { to: '/candidate/testing', label: 'Тест' },
        { to: '/candidate/vacancies', label: 'Вакансии' },
        { to: '/candidate/notifications', label: 'Увед.' },
      ]}
    />
  );
}

export function EmployerLayout() {
  return (
    <Shell
      links={[
        { to: '/employer', label: 'Dashboard' },
        { to: '/employer/talent-pool', label: 'Talent Pool' },
        { to: '/employer/vacancies', label: 'Вакансии' },
        { to: '/employer/shortlist', label: 'Shortlist' },
        { to: '/employer/compare', label: 'Сравнение' },
        { to: '/employer/offers', label: 'Офферы' },
        { to: '/employer/notifications', label: 'Увед.' },
      ]}
    />
  );
}

export function AdminLayout() {
  return (
    <Shell
      links={[
        { to: '/admin', label: 'Overview' },
        { to: '/admin/users', label: 'Пользователи' },
        { to: '/admin/vacancies', label: 'Вакансии' },
        { to: '/admin/offers', label: 'Офферы' },
      ]}
    />
  );
}
