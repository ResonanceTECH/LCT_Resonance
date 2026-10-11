import { useState } from 'react';
import { KeyRound, User } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { getErrorMessage } from '@/shared/api/errors';
import { AuthVisual } from '@/pages/auth/AuthVisual';
import { Button, Checkbox, Input } from '@/shared/ui';

const schema = z.object({
  email: z.string().email('Некорректный email'),
  password: z.string().min(6, 'Минимум 6 символов'),
  remember: z.boolean().optional(),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: 'candidate@demo.ru', password: 'demo1234', remember: true },
  });

  return (
    <div className="auth-page">
      <AuthVisual
        title="Найм, где навык уже доказан"
        description="Резюме можно написать красиво. ФСП и тесты — нет. Оффер с вилкой до созвона, контакты — только если сам ок."
      />
      <div className="auth-panel">
        <div className="auth-card">
          <h1>Вход в систему</h1>
          <p>Войдите в кабинет кандидата, работодателя или администратора.</p>
          <form
            className="stack"
            onSubmit={form.handleSubmit(async (values) => {
              setError('');
              try {
                const user = await login({ email: values.email, password: values.password });
                navigate(roleHome(user.role));
              } catch (e) {
                setError(getErrorMessage(e, 'Не удалось войти'));
              }
            })}
          >
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              icon={User}
              {...form.register('email')}
              error={form.formState.errors.email?.message}
            />
            <Input
              label="Пароль"
              type="password"
              autoComplete="current-password"
              icon={KeyRound}
              {...form.register('password')}
              error={form.formState.errors.password?.message}
            />
            <div className="auth-form-row">
              <Checkbox label="Запомнить меня" {...form.register('remember')} />
              <span className="muted" style={{ fontSize: 13 }}>
                Пароль забыли? Напишите в поддержку
              </span>
            </div>
            {error ? <div className="errorText" style={{ color: 'var(--error-main)' }}>{error}</div> : null}
            <Button type="submit" fullWidth disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? 'Входим...' : 'Войти'}
            </Button>
          </form>
          <p className="auth-footer">
            Нет аккаунта? <Link to="/register">Регистрация</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
