import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { notificationsApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatDateTime } from '@/shared/lib/formatters';
import { Badge, Button, EmptyState, ErrorState, Loader } from '@/shared/ui';

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['notifications'],
    queryFn: notificationsApi.list,
  });

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const markAll = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  if (query.isLoading) return <Loader label="Загружаем уведомления..." />;
  if (query.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить уведомления"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  const items = query.data?.items ?? [];
  const unread = query.data?.unread ?? 0;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Уведомления</h1>
          <p>Предложения, ответы и события профиля.</p>
        </div>
        <Button
          type="button"
          variant="secondary"
          disabled={unread === 0 || markAll.isPending}
          onClick={() => markAll.mutate()}
        >
          Прочитать все ({unread})
        </Button>
      </div>

      {items.length === 0 ? (
        <EmptyState title="Уведомлений пока нет" description="Когда появится оффер или ответ — увидите здесь." />
      ) : (
        <div className="stack" data-testid="notifications-list">
          {items.map((n) => (
            <article
              key={n.id}
              className="section-card"
              style={{
                borderColor: n.read ? undefined : 'rgba(13, 122, 95, 0.35)',
                background: n.read ? undefined : 'rgba(215, 239, 230, 0.45)',
              }}
            >
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <div>
                  <h3 style={{ margin: 0 }}>{n.title}</h3>
                  <p style={{ margin: '0.35rem 0 0' }}>{n.body}</p>
                  <span className="muted" style={{ fontSize: '0.85rem' }}>
                    {formatDateTime(n.createdAt)}
                  </span>
                </div>
                {!n.read ? <Badge tone="accent">Непрочитано</Badge> : <Badge>Прочитано</Badge>}
              </div>
              <div className="row" style={{ marginTop: '0.85rem' }}>
                {n.href ? (
                  <Link to={n.href}>
                    <Button
                      type="button"
                      onClick={() => {
                        if (!n.read) markRead.mutate(n.id);
                      }}
                    >
                      Открыть
                    </Button>
                  </Link>
                ) : null}
                {!n.read ? (
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={markRead.isPending}
                    onClick={() => markRead.mutate(n.id)}
                  >
                    Отметить прочитанным
                  </Button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
