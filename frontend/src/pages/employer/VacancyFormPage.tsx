import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { vacancyApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatSpecialization } from '@/shared/lib/formatters';
import {
  GRADE_OPTIONS,
  SPECIALIZATION_OPTIONS,
  WORK_FORMAT_OPTIONS,
} from '@/shared/lib/labels';
import { Button, ErrorState, Input, Loader, Select, Textarea } from '@/shared/ui';

const schema = z.object({
  title: z.string().min(3, 'Укажите название'),
  description: z.string().min(10, 'Описание слишком короткое'),
  specialization: z.string().min(1),
  requiredGrade: z.enum(['intern', 'junior', 'middle', 'senior', 'lead']),
  requiredSkills: z.string().min(1, 'Укажите обязательные навыки'),
  niceToHaveSkills: z.string().optional(),
  salaryFrom: z.coerce.number().min(0),
  salaryTo: z.coerce.number().min(0),
  currency: z.enum(['RUB', 'USD']),
  city: z.string().optional(),
  workFormat: z.enum(['remote', 'hybrid', 'office']),
  extraInfo: z.string().optional(),
  status: z.enum(['draft', 'active', 'closed', 'archived']),
  companyName: z.string().min(2),
});

type FormValues = z.infer<typeof schema>;

export function EmployerVacancyFormPage({ mode }: { mode: 'create' | 'edit' }) {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [aiText, setAiText] = useState('');

  const vacancyQuery = useQuery({
    queryKey: ['vacancies', id],
    queryFn: () => vacancyApi.byId(id),
    enabled: mode === 'edit' && Boolean(id),
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: '',
      description: '',
      specialization: 'Frontend',
      requiredGrade: 'middle',
      requiredSkills: 'React, TypeScript',
      niceToHaveSkills: 'Jest',
      salaryFrom: 250000,
      salaryTo: 320000,
      currency: 'RUB',
      city: 'Москва',
      workFormat: 'remote',
      extraInfo: '',
      status: 'active',
      companyName: 'Resonance Labs',
    },
  });

  useEffect(() => {
    if (!vacancyQuery.data) return;
    const v = vacancyQuery.data;
    form.reset({
      title: v.title,
      description: v.description,
      specialization: v.specialization,
      requiredGrade: v.requiredGrade,
      requiredSkills: v.requiredSkills.join(', '),
      niceToHaveSkills: v.niceToHaveSkills.join(', '),
      salaryFrom: v.salaryFrom,
      salaryTo: v.salaryTo,
      currency: v.currency,
      city: v.city ?? '',
      workFormat: v.workFormat,
      extraInfo: v.extraInfo ?? '',
      status: v.status,
      companyName: v.companyName ?? 'Resonance Labs',
    });
  }, [vacancyQuery.data, form]);

  const parseMutation = useMutation({
    mutationFn: () => vacancyApi.parseAi(aiText),
    onSuccess: (draft) => {
      form.reset({
        ...form.getValues(),
        title: draft.title ?? form.getValues('title'),
        description: draft.description ?? form.getValues('description'),
        specialization: draft.specialization ?? form.getValues('specialization'),
        requiredGrade: draft.requiredGrade ?? form.getValues('requiredGrade'),
        requiredSkills: draft.requiredSkills?.join(', ') ?? form.getValues('requiredSkills'),
        niceToHaveSkills:
          draft.niceToHaveSkills?.join(', ') ?? form.getValues('niceToHaveSkills'),
        salaryFrom: draft.salaryFrom ?? form.getValues('salaryFrom'),
        salaryTo: draft.salaryTo ?? form.getValues('salaryTo'),
        workFormat: draft.workFormat ?? form.getValues('workFormat'),
        city: draft.city ?? form.getValues('city'),
      });
    },
  });

  const createMutation = useMutation({
    mutationFn: vacancyApi.create,
    onSuccess: async (vacancy) => {
      await queryClient.invalidateQueries({ queryKey: ['vacancies'] });
      navigate(`/employer/vacancies/${vacancy.id}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: FormValues) =>
      vacancyApi.update(id, {
        ...payload,
        requiredSkills: payload.requiredSkills.split(',').map((s) => s.trim()).filter(Boolean),
        niceToHaveSkills: (payload.niceToHaveSkills ?? '')
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['vacancies'] });
      navigate(`/employer/vacancies/${id}`);
    },
  });

  if (mode === 'edit' && vacancyQuery.isLoading) return <Loader />;
  if (mode === 'edit' && vacancyQuery.isError) {
    return (
      <ErrorState
        title="Вакансия не найдена"
        description={getErrorMessage(vacancyQuery.error)}
        onRetry={() => void vacancyQuery.refetch()}
      />
    );
  }

  const pending = createMutation.isPending || updateMutation.isPending;
  const error = createMutation.error || updateMutation.error;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{mode === 'create' ? 'Новая вакансия' : 'Редактирование вакансии'}</h1>
          <p>Обязательные поля валидируются на клиенте до отправки.</p>
        </div>
      </div>

      {mode === 'create' ? (
        <section className="section-card stack" style={{ marginBottom: '1rem' }} data-testid="ai-parse">
          <h3 style={{ margin: 0 }}>AI-разбор текста вакансии</h3>
          <p className="muted" style={{ margin: 0 }}>
            Парсинг выполняется на сервере. Интерфейс только подставляет черновик в форму.
          </p>
          <Textarea
            label="Текст вакансии"
            value={aiText}
            onChange={(e) => setAiText(e.target.value)}
            placeholder="Вставьте описание вакансии..."
          />
          <Button
            type="button"
            variant="secondary"
            disabled={parseMutation.isPending || aiText.trim().length < 20}
            onClick={() => parseMutation.mutate()}
          >
            {parseMutation.isPending ? 'Разбираем...' : 'Заполнить форму из текста'}
          </Button>
          {parseMutation.isError ? (
            <div style={{ color: 'var(--danger)' }}>{getErrorMessage(parseMutation.error)}</div>
          ) : null}
          {parseMutation.isSuccess ? (
            <div className="muted">Черновик подставлен. Проверьте и сохраните.</div>
          ) : null}
        </section>
      ) : null}

      <form
        className="section-card stack"
        onSubmit={form.handleSubmit((values) => {
          const payload = {
            ...values,
            requiredSkills: values.requiredSkills.split(',').map((s) => s.trim()).filter(Boolean),
            niceToHaveSkills: (values.niceToHaveSkills ?? '')
              .split(',')
              .map((s) => s.trim())
              .filter(Boolean),
          };
          if (mode === 'create') createMutation.mutate(payload);
          else updateMutation.mutate(values);
        })}
      >
        <Input label="Название" {...form.register('title')} error={form.formState.errors.title?.message} />
        <Input label="Компания" {...form.register('companyName')} error={form.formState.errors.companyName?.message} />
        <Textarea label="Описание" {...form.register('description')} error={form.formState.errors.description?.message} />
        <div className="grid-2">
          <Select
            label="Специализация"
            options={SPECIALIZATION_OPTIONS.map((s) => ({
              value: s,
              label: formatSpecialization(s),
            }))}
            {...form.register('specialization')}
          />
          <Select label="Грейд" options={GRADE_OPTIONS} {...form.register('requiredGrade')} />
        </div>
        <Input
          label="Обязательные навыки"
          {...form.register('requiredSkills')}
          error={form.formState.errors.requiredSkills?.message}
        />
        <Input label="Дополнительные навыки" {...form.register('niceToHaveSkills')} />
        <div className="grid-3">
          <Input label="Зарплата от" type="number" {...form.register('salaryFrom')} error={form.formState.errors.salaryFrom?.message} />
          <Input label="Зарплата до" type="number" {...form.register('salaryTo')} error={form.formState.errors.salaryTo?.message} />
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
          <Select label="Формат" options={WORK_FORMAT_OPTIONS} {...form.register('workFormat')} />
          <Select
            label="Статус"
            options={[
              { value: 'draft', label: 'Черновик' },
              { value: 'active', label: 'Активна' },
              { value: 'closed', label: 'Закрыта' },
              { value: 'archived', label: 'В архиве' },
            ]}
            {...form.register('status')}
          />
        </div>
        <Textarea label="Дополнительно" {...form.register('extraInfo')} />
        {error ? <div style={{ color: 'var(--danger)' }}>{getErrorMessage(error)}</div> : null}
        <Button type="submit" disabled={pending}>
          {pending ? 'Сохраняем...' : 'Сохранить'}
        </Button>
      </form>
    </div>
  );
}
