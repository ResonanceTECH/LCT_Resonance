import { Navigate, Outlet, useLocation } from 'react-router-dom';
import type { Role } from '@/entities/types';
import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { Loader } from '@/shared/ui';

export function AuthGuard() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <Loader label="Проверяем сессию..." />;
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

export function RoleGuard({ allow }: { allow: Role[] }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <Loader />;
  if (!user) return <Navigate to="/login" replace />;
  if (!allow.includes(user.role)) {
    return <Navigate to="/403" replace />;
  }
  return <Outlet />;
}

export function GuestGuard() {
  const { user, isLoading, isAuthenticated } = useAuth();
  if (isLoading) return <Loader />;
  if (isAuthenticated && user) {
    return <Navigate to={roleHome(user.role)} replace />;
  }
  return <Outlet />;
}

