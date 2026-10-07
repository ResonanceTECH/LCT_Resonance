import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { notificationsApi } from '@/shared/api/endpoints';
import { formatDateTime } from '@/shared/lib/formatters';
import { Badge, Button } from '@/shared/ui';
import { useAuth } from '@/features/auth/AuthContext';

export function NotificationBell() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const basePath = user?.role === 'employer' ? '/employer' : '/candidate';

  const query = useQuery({
    queryKey: ['notifications'],
    queryFn: notificationsApi.list,
    refetchInterval: 30_000,
    enabled: Boolean(user),
  });

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const markAll = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  const unread = query.data?.unread ?? 0;
  const preview = (query.data?.items ?? []).slice(0, 5);

  return (
    <div ref={rootRef} style={{ position: 'relative' }}>
      <Button
        type="button"
        variant="secondary"
        aria-label={`Уведомления${unread ? `, непрочитанных: ${unread}` : ''}`}
        aria-expanded={open}
        data-testid="notification-bell"
        onClick={() => setOpen((v) => !v)}
      >
        Увед.
        {unread > 0 ? (
          <Badge tone="danger">
            <span data-testid="notification-unread">{unread}</span>
          </Badge>
        ) : null}
      </Button>
      {open ? (
        <div
          className="section-card"
          data-testid="notification-dropdown"
          style={{
            position: 'absolute',
            right: 0,
            top: 'calc(100% + 0.5rem)',
            width: 'min(360px, 90vw)',
            zIndex: 40,
            boxShadow: 'var(--shadow)',
            background: 'rgba(255,255,255,0.95)',
          }}
        >
          <div className="row" style={{ justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <strong>Уведомления</strong>
            <Button
              type="button"
              variant="ghost"
              disabled={unread === 0 || markAll.isPending}
              onClick={() => markAll.mutate()}
            >
              Прочитать все
            </Button>
          </div>
          {preview.length === 0 ? (
            <p className="muted" style={{ margin: 0 }}>
              Пока пусто
            </p>
          ) : (
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }} className="stack">
              {preview.map((n) => (
                <li key={n.id}>
                  <Link
                    to={n.href ?? `${basePath}/notifications`}
                    onClick={() => {
                      if (!n.read) markRead.mutate(n.id);
                      setOpen(false);
                    }}
                    style={{
                      display: 'block',
                      padding: '0.55rem 0.35rem',
                      borderRadius: 'var(--radius-sm)',
                      background: n.read ? 'transparent' : 'var(--accent-soft)',
                    }}
                  >
                    <div className="row" style={{ justifyContent: 'space-between' }}>
                      <strong style={{ fontSize: '0.95rem' }}>{n.title}</strong>
                      {!n.read ? <Badge tone="accent">new</Badge> : null}
                    </div>
                    <p style={{ margin: '0.2rem 0 0', fontSize: '0.85rem' }}>{n.body}</p>
                    <span className="muted" style={{ fontSize: '0.75rem' }}>
                      {formatDateTime(n.createdAt)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <div style={{ marginTop: '0.85rem' }}>
            <Link to={`${basePath}/notifications`} onClick={() => setOpen(false)}>
              <Button type="button" variant="secondary">
                Все уведомления
              </Button>
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
