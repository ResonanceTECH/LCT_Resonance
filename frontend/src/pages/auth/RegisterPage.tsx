import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { getErrorMessage } from '@/shared/api/errors';
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
      <div className="auth-card">
        <h1>Регистрация</h1>
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
          <Input label="Имя" {...form.register('displayName')} error={form.formState.errors.displayName?.message} />
          <Input label="Email" type="email" {...form.register('email')} error={form.formState.errors.email?.message} />
          <Input label="Пароль" type="password" {...form.register('password')} error={form.formState.errors.password?.message} />
          <Select
            label="Роль"
            options={[
              { value: 'candidate', label: 'Кандидат' },
              { value: 'employer', label: 'Работодатель' },
            ]}
            {...form.register('role')}
          />
          {error ? <div style={{ color: 'var(--danger)' }}>{error}</div> : null}
          <Button type="submit" disabled={form.formState.isSubmitting}>
            Создать аккаунт
          </Button>
        </form>
        <p style={{ marginTop: '1rem' }}>
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </div>
    </div>
  );
}
