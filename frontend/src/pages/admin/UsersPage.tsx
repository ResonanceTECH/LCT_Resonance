import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { Badge, Button, ErrorState, Loader } from '@/shared/ui';

export function AdminUsersPage() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: adminApi.users,
  });

  const statusMutation = useMutation({
    mutationFn: ({ userId, status }: { userId: string; status: 'active' | 'blocked' }) =>
      adminApi.setUserStatus(userId, status),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin'] });
    },
  });

  if (query.isLoading) return <Loader />;
  if (query.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить пользователей"
        description={getErrorMessage(query.error)}
        onRetry={() => void query.refetch()}
      />
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Пользователи</h1>
          <p>Блокировка запрещает повторный вход.</p>
        </div>
      </div>
      <div className="stack" data-testid="admin-users">
        {query.data!.map((user) => (
          <div key={user.id} className="section-card row" style={{ justifyContent: 'space-between' }}>
            <div>
              <strong>{user.displayName}</strong>
              <div className="muted">
                {user.email} · {user.role}
              </div>
            </div>
            <div className="row">
              <Badge tone={user.status === 'blocked' ? 'danger' : 'success'}>
                {user.status === 'blocked' ? 'Заблокирован' : 'Активен'}
              </Badge>
              {user.status === 'active' ? (
                <Button
                  type="button"
                  variant="danger"
                  disabled={statusMutation.isPending}
                  onClick={() => statusMutation.mutate({ userId: user.id, status: 'blocked' })}
                >
                  Заблокировать
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="secondary"
                  disabled={statusMutation.isPending}
                  onClick={() => statusMutation.mutate({ userId: user.id, status: 'active' })}
                >
                  Разблокировать
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
