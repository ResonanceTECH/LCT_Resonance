import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { StatusPage, STATUS_PRESETS } from '@/shared/ui/StatusPage';

export function NotFoundPage() {
  const { isAuthenticated, user } = useAuth();
  const home = isAuthenticated && user ? roleHome(user.role) : '/';

  return (
    <StatusPage
      {...STATUS_PRESETS.notFound}
      primaryAction={{ label: isAuthenticated ? 'В кабинет' : 'На главную', to: home }}
      secondaryAction={
        isAuthenticated
          ? { label: 'На главную', to: '/', variant: 'secondary' }
          : STATUS_PRESETS.notFound.secondaryAction
      }
    />
  );
}

export function ForbiddenPage() {
  const { isAuthenticated, user } = useAuth();
  const home = isAuthenticated && user ? roleHome(user.role) : '/login';

  return (
    <StatusPage
      {...STATUS_PRESETS.forbidden}
      primaryAction={{
        label: isAuthenticated ? 'В кабинет' : 'Войти',
        to: home,
      }}
      secondaryAction={
        isAuthenticated
          ? { label: 'Сменить аккаунт', to: '/login', variant: 'secondary' }
          : { label: 'На главную', to: '/', variant: 'secondary' }
      }
    />
  );
}

export function ServerErrorPage() {
  return <StatusPage {...STATUS_PRESETS.serverError} />;
}

export function MaintenancePage() {
  return <StatusPage {...STATUS_PRESETS.maintenance} />;
}

export function OfflinePage() {
  return <StatusPage {...STATUS_PRESETS.offline} />;
}
