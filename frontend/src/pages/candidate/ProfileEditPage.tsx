import { useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { candidateApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import {
  GRADE_OPTIONS,
  READINESS_OPTIONS,
  SPECIALIZATION_OPTIONS,
  WORK_FORMAT_OPTIONS,
} from '@/shared/lib/labels';
import { Button, ErrorState, Input, Loader, Select, Textarea } from '@/shared/ui';

const schema = z.object({
  fullName: z.string().min(2),
  about: z.string().optional(),
  specialization: z.string().min(1),
  claimedGrade: z.enum(['intern', 'junior', 'middle', 'senior', 'lead']),
  experienceYears: z.coerce.number().min(0).optional(),
  experienceDescription: z.string().optional(),
  skills: z.string().min(1, 'Укажите навыки через запятую'),
  desiredPosition: z.string().optional(),
  salaryFrom: z.coerce.number().min(0).optional(),
  salaryTo: z.coerce.number().min(0).optional(),
  currency: z.enum(['RUB', 'USD']),
  city: z.string().optional(),
  workFormat: z.enum(['remote', 'hybrid', 'office']),
  readiness: z.enum(['actively_looking', 'open_to_offers', 'not_looking']),
});

type FormValues = z.infer<typeof schema>;

export function CandidateProfileEditPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const profileQuery = useQuery({
    queryKey: ['candidate', 'me'],
    queryFn: candidateApi.me,
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (!profileQuery.data) return;
    const p = profileQuery.data;
    form.reset({
      fullName: p.fullName,
      about: p.about ?? '',
      specialization: p.specialization,
      claimedGrade: p.claimedGrade,
      experienceYears: p.experienceYears,
      experienceDescription: p.experienceDescription ?? '',
      skills: p.skills.join(', '),
      desiredPosition: p.desiredPosition ?? '',
      salaryFrom: p.salaryFrom,
      salaryTo: p.salaryTo,
      currency: p.currency,
      city: p.city ?? '',
      workFormat: p.workFormat ?? 'remote',
      readiness: p.readiness,
    });
  }, [profileQuery.data, form]);

  const mutation = useMutation({
    mutationFn: candidateApi.updateMe,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['candidate', 'me'] });
      navigate('/candidate/profile');
    },
  });

  if (profileQuery.isLoading) return <Loader />;
  if (profileQuery.isError) {
    return (
      <ErrorState
        title="Не удалось загрузить профиль"
        description={getErrorMessage(profileQuery.error)}
        onRetry={() => void profileQuery.refetch()}
      />
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Редактирование профиля</h1>
          <p>Заполните навыки, грейд и карьерные предпочтения.</p>
        </div>
      </div>
      <form
        className="section-card stack"
        onSubmit={form.handleSubmit((values) => {
          mutation.mutate({
            ...values,
            skills: values.skills
              .split(',')
              .map((s) => s.trim())
              .filter(Boolean),
          });
        })}
      >
        <Input label="Имя" {...form.register('fullName')} error={form.formState.errors.fullName?.message} />
        <Textarea label="О себе" {...form.register('about')} />
        <div className="grid-2">
          <Select
            label="Специализация"
            options={SPECIALIZATION_OPTIONS.map((s) => ({ value: s, label: s }))}
            {...form.register('specialization')}
          />
          <Select label="Заявленный грейд" options={GRADE_OPTIONS} {...form.register('claimedGrade')} />
        </div>
        <div className="grid-2">
          <Input label="Опыт (лет)" type="number" {...form.register('experienceYears')} />
          <Input label="Желаемая должность" {...form.register('desiredPosition')} />
        </div>
        <Textarea label="Описание опыта" {...form.register('experienceDescription')} />
        <Input
          label="Навыки (через запятую)"
          {...form.register('skills')}
          error={form.formState.errors.skills?.message}
        />
        <div className="grid-3">
          <Input label="Зарплата от" type="number" {...form.register('salaryFrom')} />
          <Input label="Зарплата до" type="number" {...form.register('salaryTo')} />
          <Select
            label="Валюта"
            options={[
              { value: 'RUB', label: 'RUB' },
            ]}
            {...form.register('currency')}
          />
        </div>
        <div className="grid-3">
          <Input label="Город" {...form.register('city')} />
          <Select label="Формат работы" options={WORK_FORMAT_OPTIONS} {...form.register('workFormat')} />
          <Select label="Готовность" options={READINESS_OPTIONS} {...form.register('readiness')} />
        </div>
        {mutation.isError ? (
          <div style={{ color: 'var(--danger)' }}>{getErrorMessage(mutation.error)}</div>
        ) : null}
        <div className="row">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Сохраняем...' : 'Сохранить'}
          </Button>
          <Button type="button" variant="secondary" onClick={() => navigate('/candidate/profile')}>
            Отмена
          </Button>
        </div>
      </form>
    </div>
  );
}
