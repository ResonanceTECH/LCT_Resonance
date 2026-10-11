import { useState } from 'react';
import { KeyRound, User } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { getErrorMessage } from '@/shared/api/errors';
import { AuthVisual } from '@/pages/auth/AuthVisual';
import { Button, Input, Select } from '@/shared/ui';

const schema = z.object({
  displayName: z.string().min(2, 'Укажите имя'),
  email: z.string().email(),
  password: z.string().min(8, 'Минимум 8 символов'),
  role: z.enum(['candidate', 'employer']),
});

type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      displayName: '',
      email: '',
      password: '',
      role: 'candidate',
    },
  });

  return (
    <div className="auth-page">
      <AuthVisual
        title="Найм без холодных звонков и лишней суеты"
        description="Кандидаты с подтверждёнными навыками сами получают предложения. Работодатели — сразу релевантный Talent Pool, без бесконечного скрининга резюме."
      />
      <div className="auth-panel">
        <div className="auth-card">
          <h1>Регистрация</h1>
          <p>Выберите роль и создайте аккаунт FSP Talent.</p>
          <form
            className="stack"
            onSubmit={form.handleSubmit(async (values) => {
              setError('');
              try {
                const user = await registerUser(values);
                navigate(roleHome(user.role));
              } catch (e) {
                setError(getErrorMessage(e, 'Не удалось зарегистрироваться'));
              }
            })}
          >
            <Input
              label="Имя"
              icon={User}
              {...form.register('displayName')}
              error={form.formState.errors.displayName?.message}
            />
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
              autoComplete="new-password"
              icon={KeyRound}
              {...form.register('password')}
              error={form.formState.errors.password?.message}
            />
            <Select
              label="Роль"
              options={[
                { value: 'candidate', label: 'Кандидат' },
                { value: 'employer', label: 'Работодатель' },
              ]}
              {...form.register('role')}
            />
            {error ? <div style={{ color: 'var(--error-main)' }}>{error}</div> : null}
            <Button type="submit" fullWidth disabled={form.formState.isSubmitting}>
              Создать аккаунт
            </Button>
          </form>
          <p className="auth-footer">
            Уже есть аккаунт? <Link to="/login">Войти</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
