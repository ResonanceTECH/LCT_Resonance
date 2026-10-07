import { Link } from 'react-router-dom';
import type { ProfileCompleteness as CompletenessData } from '@/entities/types';
import { ProgressBar } from '@/shared/ui';

export function ProfileCompletenessCard({ data }: { data: CompletenessData }) {
  const missing = data.items.filter((i) => !i.done);

  return (
    <section className="section-card stack" data-testid="profile-completeness">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ margin: 0 }}>Заполненность профиля</h2>
          <p style={{ margin: '0.25rem 0 0' }}>Чем полнее профиль — тем выше Match Score.</p>
        </div>
        <strong style={{ fontSize: '1.6rem' }}>{data.percent}%</strong>
      </div>
      <ProgressBar value={data.percent} />
      <ul style={{ listStyle: 'none', margin: 0, padding: 0 }} className="stack">
        {data.items.map((item) => (
          <li
            key={item.key}
            className="row"
            style={{ justifyContent: 'space-between' }}
            data-testid={`completeness-${item.key}`}
          >
            <span>
              <span aria-hidden style={{ marginRight: '0.4rem' }}>
                {item.done ? '✓' : '○'}
              </span>
              {item.label}
            </span>
            {!item.done && item.href ? (
              <Link to={item.href} style={{ color: 'var(--accent-ink)', fontWeight: 600 }}>
                Заполнить
              </Link>
            ) : (
              <span className="muted">{item.done ? 'Готово' : ''}</span>
            )}
          </li>
        ))}
      </ul>
      {missing.length > 0 ? (
        <p className="muted" style={{ marginBottom: 0, fontSize: '0.9rem' }}>
          Осталось: {missing.map((m) => m.label).join(', ')}
        </p>
      ) : (
        <p style={{ marginBottom: 0, color: 'var(--success)' }}>Профиль заполнен максимально.</p>
      )}
    </section>
  );
}
