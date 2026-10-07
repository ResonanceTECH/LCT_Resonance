import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { getErrorMessage } from '@/shared/api/errors';
import { Button, Input } from '@/shared/ui';

const schema = z.object({
  email: z.string().email('Некорректный email'),
  password: z.string().min(6, 'Минимум 6 символов'),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: 'candidate@demo.ru', password: 'demo1234' },
  });

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Вход</h1>
        <p>Войдите в кабинет кандидата или работодателя.</p>
        <form
          className="stack"
          onSubmit={form.handleSubmit(async (values) => {
            setError('');
            try {
              const user = await login(values);
              navigate(roleHome(user.role));
            } catch (e) {
              setError(getErrorMessage(e, 'Не удалось войти'));
            }
          })}
        >
          <Input label="Email" type="email" {...form.register('email')} error={form.formState.errors.email?.message} />
          <Input label="Пароль" type="password" {...form.register('password')} error={form.formState.errors.password?.message} />
          {error ? <div className="errorText" style={{ color: 'var(--danger)' }}>{error}</div> : null}
          <Button type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? 'Входим...' : 'Войти'}
          </Button>
        </form>
        <p style={{ marginTop: '1rem' }}>
          Нет аккаунта? <Link to="/register">Регистрация</Link>
        </p>
        <div className="demo-hint">
          Demo: candidate@demo.ru · employer@demo.ru · admin@demo.ru · пароль demo1234
        </div>
      </div>
    </div>
  );
}
