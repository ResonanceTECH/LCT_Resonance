import { useState } from 'react';
import { KeyRound, User } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { getErrorMessage } from '@/shared/api/errors';
import { AuthVisual } from '@/pages/auth/AuthVisual';
import { Button, Checkbox, Input, Select } from '@/shared/ui';

const schema = z.object({
  displayName: z.string().min(2, 'Укажите имя'),
  email: z.string().email(),
  password: z.string().min(8, 'Минимум 8 символов'),
  role: z.enum(['candidate', 'employer']),
  termsAccepted: z.literal(true, {
    errorMap: () => ({ message: 'Примите Условия использования' }),
  }),
  personalDataConsent: z.literal(true, {
    errorMap: () => ({ message: 'Нужно согласие на обработку персональных данных' }),
  }),
  publicPassportConsent: z.boolean(),
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
      termsAccepted: undefined as unknown as true,
      personalDataConsent: undefined as unknown as true,
      publicPassportConsent: false,
    },
  });
  const role = useWatch({ control: form.control, name: 'role' });

  return (
    <div className="auth-page">
      <AuthVisual
        title="Найм без холодных звонков и лишней суеты"
        description="Кандидаты с подтверждёнными навыками сами получают предложения. Работодатели — сразу релевантный пул, без бесконечного скрининга резюме."
      />
      <div className="auth-panel">
        <div className="auth-card auth-cardWide">
          <h1>Регистрация в FSP Talent</h1>
          <p>Выберите роль и создайте аккаунт. Согласия принимаются отдельно.</p>
          <form
            className="stack"
            onSubmit={form.handleSubmit(async (values) => {
              setError('');
              try {
                const user = await registerUser({
                  displayName: values.displayName,
                  email: values.email,
                  password: values.password,
                  role: values.role,
                  termsAccepted: values.termsAccepted,
                  personalDataConsent: values.personalDataConsent,
                  publicPassportConsent:
                    values.role === 'candidate' ? values.publicPassportConsent : false,
                });
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

            <fieldset className="auth-consents">
              <legend className="auth-consentsLegend">Согласия</legend>
              <Checkbox
                label={
                  <>
                    Я ознакомился(-ась) и принимаю{' '}
                    <Link to="/terms" target="_blank" rel="noopener noreferrer">
                      Условия использования
                    </Link>
                    .
                  </>
                }
                {...form.register('termsAccepted')}
              />
              {form.formState.errors.termsAccepted?.message ? (
                <p className="auth-consentError">{form.formState.errors.termsAccepted.message}</p>
              ) : null}

              <Checkbox
                label={
                  <>
                    Я даю отдельное согласие на обработку персональных данных в указанных целях (
                    <Link to="/privacy" target="_blank" rel="noopener noreferrer">
                      Политика конфиденциальности
                    </Link>
                    ).
                  </>
                }
                {...form.register('personalDataConsent')}
              />
              {form.formState.errors.personalDataConsent?.message ? (
                <p className="auth-consentError">
                  {form.formState.errors.personalDataConsent.message}
                </p>
              ) : null}

              {role === 'candidate' ? (
                <Checkbox
                  label="Хочу сделать выбранные сведения моего карьерного паспорта публичными."
                  {...form.register('publicPassportConsent')}
                />
              ) : null}
            </fieldset>

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
