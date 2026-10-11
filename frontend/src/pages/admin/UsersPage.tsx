import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import type { AdminUserRow } from '@/entities/types';
import { adminApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatDate, formatGrade } from '@/shared/lib/formatters';
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Input,
  Loader,
  Modal,
  Select,
  Textarea,
} from '@/shared/ui';

const PAGE_SIZE = 8;

const ROLE_LABEL: Record<string, string> = {
  candidate: 'Кандидат',
  employer: 'Работодатель',
};

const TEST_LABEL: Record<NonNullable<AdminUserRow['testStatus']>, string> = {
  none: 'Нет теста',
  passed: 'Пройден',
  failed: 'Не подтверждён',
  in_progress: 'В процессе',
};

function UserDrawer({
  user,
  onClose,
  onBlock,
  onUnblock,
  busy,
}: {
  user: AdminUserRow;
  onClose: () => void;
  onBlock: () => void;
  onUnblock: () => void;
  busy: boolean;
}) {
  return (
    <div className="drawer-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="drawer-panel"
        role="dialog"
        aria-modal="true"
        aria-label={user.displayName}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="drawer-header">
          <div>
            <h2>{user.displayName}</h2>
            <p className="muted" style={{ margin: 0 }}>
              {user.email}
            </p>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={onClose} aria-label="Закрыть">
            ✕
          </Button>
        </div>

        <dl className="drawer-meta">
          <div>
            <dt>Роль</dt>
            <dd>{ROLE_LABEL[user.role] ?? user.role}</dd>
          </div>
          <div>
            <dt>Статус</dt>
            <dd>
              <Badge tone={user.status === 'blocked' ? 'danger' : 'success'}>
                {user.status === 'blocked' ? 'Заблокирован' : 'Активен'}
              </Badge>
            </dd>
          </div>
          <div>
            <dt>Регистрация</dt>
            <dd>{formatDate(user.createdAt)}</dd>
          </div>
          {user.role === 'candidate' ? (
            <>
              <div>
                <dt>Специализация</dt>
                <dd>{user.specialization ?? '—'}</dd>
              </div>
              <div>
                <dt>Подтверждённая категория</dt>
                <dd>
                  {user.confirmedGrade
                    ? `${user.specialization ?? '—'} / ${formatGrade(user.confirmedGrade)}`
                    : 'Не подтверждена'}
                </dd>
              </div>
              <div>
                <dt>Статус тестирования</dt>
                <dd>{TEST_LABEL[user.testStatus ?? 'none']}</dd>
              </div>
              <div>
                <dt>FSP ID</dt>
                <dd>{user.hasFspId ? 'Связан (демо)' : 'Нет'}</dd>
              </div>
            </>
          ) : null}
          {user.blockReason ? (
            <div>
              <dt>Причина блокировки</dt>
              <dd>{user.blockReason}</dd>
            </div>
          ) : null}
        </dl>

        <div className="row" style={{ marginTop: 'auto' }}>
          {user.status === 'active' ? (
            <Button type="button" variant="danger" disabled={busy} onClick={onBlock}>
              Заблокировать
            </Button>
          ) : (
            <Button type="button" variant="secondary" disabled={busy} onClick={onUnblock}>
              Разблокировать
            </Button>
          )}
        </div>
      </aside>
    </div>
  );
}

export function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [role, setRole] = useState<'' | 'candidate' | 'employer'>('');
  const [status, setStatus] = useState<'' | 'active' | 'blocked'>('');
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<AdminUserRow | null>(null);
  const [blockTarget, setBlockTarget] = useState<AdminUserRow | null>(null);
  const [blockReason, setBlockReason] = useState('');

  const query = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: adminApi.users,
  });

  const statusMutation = useMutation({
    mutationFn: ({
      userId,
      next,
      reason,
    }: {
      userId: string;
      next: 'active' | 'blocked';
      reason?: string;
    }) => adminApi.setUserStatus(userId, next, reason),
    onSuccess: async (row) => {
      await queryClient.invalidateQueries({ queryKey: ['admin'] });
      setSelected((prev) => (prev && prev.id === row.id ? { ...prev, ...row } : prev));
      setBlockTarget(null);
      setBlockReason('');
    },
  });

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (query.data ?? []).filter((user) => {
      if (role && user.role !== role) return false;
      if (status && user.status !== status) return false;
      if (!q) return true;
      return (
        user.displayName.toLowerCase().includes(q) || user.email.toLowerCase().includes(q)
      );
    });
  }, [query.data, role, search, status]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = filtered.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);

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
          <p>Поиск, фильтры и блокировка. Грейд меняется только через тестирование.</p>
        </div>
      </div>

      <div className="toolbar">
        <div className="toolbar-grow">
          <Input
            label="Поиск"
            placeholder="Имя или email"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
          />
        </div>
        <Select
          label="Роль"
          allowEmpty
          emptyLabel="Все роли"
          value={role}
          onChange={(e) => {
            setRole(e.target.value as '' | 'candidate' | 'employer');
            setPage(0);
          }}
          options={[
            { value: 'candidate', label: 'Кандидат' },
            { value: 'employer', label: 'Работодатель' },
          ]}
        />
        <Select
          label="Статус"
          allowEmpty
          emptyLabel="Все статусы"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as '' | 'active' | 'blocked');
            setPage(0);
          }}
          options={[
            { value: 'active', label: 'Активен' },
            { value: 'blocked', label: 'Заблокирован' },
          ]}
        />
      </div>

      {pageRows.length === 0 ? (
        <EmptyState title="Никого не найдено" description="Сбросьте фильтры или измените запрос." />
      ) : (
        <div className="data-table-wrap" data-testid="admin-users">
          <table className="data-table">
            <thead>
              <tr>
                <th>Имя</th>
                <th>Email</th>
                <th>Роль</th>
                <th>Регистрация</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.map((user) => (
                <tr
                  key={user.id}
                  className={[
                    'is-clickable',
                    selected?.id === user.id ? 'is-selected' : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  onClick={() => setSelected(user)}
                >
                  <td>
                    <strong>{user.displayName}</strong>
                  </td>
                  <td>{user.email}</td>
                  <td>{ROLE_LABEL[user.role] ?? user.role}</td>
                  <td>{formatDate(user.createdAt)}</td>
                  <td>
                    <Badge tone={user.status === 'blocked' ? 'danger' : 'success'}>
                      {user.status === 'blocked' ? 'Заблокирован' : 'Активен'}
                    </Badge>
                  </td>
                  <td onClick={(e) => e.stopPropagation()}>
                    {user.status === 'active' ? (
                      <Button
                        type="button"
                        variant="danger"
                        size="sm"
                        disabled={statusMutation.isPending}
                        onClick={() => {
                          setBlockTarget(user);
                          setBlockReason('');
                        }}
                      >
                        Заблокировать
                      </Button>
                    ) : (
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        disabled={statusMutation.isPending}
                        onClick={() =>
                          statusMutation.mutate({ userId: user.id, next: 'active' })
                        }
                      >
                        Разблокировать
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {filtered.length > PAGE_SIZE ? (
        <div className="pagination">
          <span>
            {safePage * PAGE_SIZE + 1}–{Math.min((safePage + 1) * PAGE_SIZE, filtered.length)} из{' '}
            {filtered.length}
          </span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={safePage === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            Назад
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={safePage >= pageCount - 1}
            onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
          >
            Далее
          </Button>
        </div>
      ) : null}

      {selected ? (
        <UserDrawer
          user={selected}
          busy={statusMutation.isPending}
          onClose={() => setSelected(null)}
          onBlock={() => {
            setBlockTarget(selected);
            setBlockReason('');
          }}
          onUnblock={() => statusMutation.mutate({ userId: selected.id, next: 'active' })}
        />
      ) : null}

      <Modal
        open={Boolean(blockTarget)}
        title="Заблокировать пользователя"
        onClose={() => {
          setBlockTarget(null);
          setBlockReason('');
        }}
      >
        <p className="muted">
          {blockTarget
            ? `${blockTarget.displayName} (${blockTarget.email}) потеряет доступ сразу.`
            : null}
        </p>
        <Textarea
          label="Причина блокировки"
          value={blockReason}
          onChange={(e) => setBlockReason(e.target.value)}
          placeholder="Кратко опишите причину"
          rows={3}
        />
        {statusMutation.isError ? (
          <p style={{ color: 'var(--error-main)', margin: 0 }}>
            {getErrorMessage(statusMutation.error)}
          </p>
        ) : null}
        <div className="row" style={{ justifyContent: 'flex-end', marginTop: 16 }}>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setBlockTarget(null);
              setBlockReason('');
            }}
          >
            Отмена
          </Button>
          <Button
            type="button"
            variant="danger"
            disabled={!blockReason.trim() || statusMutation.isPending}
            onClick={() => {
              if (!blockTarget) return;
              statusMutation.mutate({
                userId: blockTarget.id,
                next: 'blocked',
                reason: blockReason.trim(),
              });
            }}
          >
            Заблокировать
          </Button>
        </div>
      </Modal>
    </div>
  );
}
