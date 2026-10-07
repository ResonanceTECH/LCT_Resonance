import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import type { CreateOfferPayload, Vacancy, WorkFormat } from '@/entities/types';
import { WORK_FORMAT_OPTIONS } from '@/shared/lib/labels';
import { Button, Input, Select, Textarea } from '@/shared/ui';
import { SalaryRange } from './SalaryRange';

const schema = z.object({
  vacancyId: z.string().min(1, 'Выберите вакансию'),
  companyName: z.string().min(2),
  positionTitle: z.string().min(2),
  salaryFrom: z.coerce.number().min(0),
  salaryTo: z.coerce.number().min(0),
  currency: z.enum(['RUB', 'USD']),
  workFormat: z.enum(['remote', 'hybrid', 'office']),
  message: z.string().min(10, 'Сообщение слишком короткое'),
});

type FormValues = z.infer<typeof schema>;

export function OfferForm({
  vacancies,
  candidateId,
  defaultVacancyId,
  onSubmit,
  submitting,
}: {
  vacancies: Vacancy[];
  candidateId: string;
  defaultVacancyId?: string;
  onSubmit: (payload: CreateOfferPayload) => Promise<void> | void;
  submitting?: boolean;
}) {
  const selectedDefault = vacancies.find((v) => v.id === defaultVacancyId) ?? vacancies[0];

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      vacancyId: selectedDefault?.id ?? '',
      companyName: selectedDefault?.companyName ?? 'Resonance Labs',
      positionTitle: selectedDefault?.title ?? '',
      salaryFrom: selectedDefault?.salaryFrom ?? 0,
      salaryTo: selectedDefault?.salaryTo ?? 0,
      currency: selectedDefault?.currency ?? 'RUB',
      workFormat: (selectedDefault?.workFormat ?? 'remote') as WorkFormat,
      message: 'Здравствуйте! Хотим предложить вам позицию в нашей команде.',
    },
  });

  const values = form.watch();

  return (
    <form
      className="stack"
      onSubmit={form.handleSubmit(async (data) => {
        await onSubmit({ ...data, candidateId });
      })}
    >
      <Select
        label="Вакансия"
        options={vacancies.map((v) => ({ value: v.id, label: v.title }))}
        {...form.register('vacancyId', {
          onChange: (e) => {
            const vac = vacancies.find((v) => v.id === e.target.value);
            if (!vac) return;
            form.setValue('positionTitle', vac.title);
            form.setValue('salaryFrom', vac.salaryFrom);
            form.setValue('salaryTo', vac.salaryTo);
            form.setValue('currency', vac.currency);
            form.setValue('workFormat', vac.workFormat);
            form.setValue('companyName', vac.companyName ?? form.getValues('companyName'));
          },
        })}
        error={form.formState.errors.vacancyId?.message}
      />
      <Input label="Компания" {...form.register('companyName')} error={form.formState.errors.companyName?.message} />
      <Input label="Позиция" {...form.register('positionTitle')} error={form.formState.errors.positionTitle?.message} />
      <div className="grid-2">
        <Input label="Зарплата от" type="number" {...form.register('salaryFrom')} error={form.formState.errors.salaryFrom?.message} />
        <Input label="Зарплата до" type="number" {...form.register('salaryTo')} error={form.formState.errors.salaryTo?.message} />
      </div>
      <Select
        label="Формат работы"
        options={WORK_FORMAT_OPTIONS}
        {...form.register('workFormat')}
      />
      <div className="section-card">
        <div className="muted">Зарплатная вилка в предложении</div>
        <strong>
          <SalaryRange from={values.salaryFrom} to={values.salaryTo} currency={values.currency} />
        </strong>
      </div>
      <Textarea label="Сообщение кандидату" {...form.register('message')} error={form.formState.errors.message?.message} />
      <Button type="submit" disabled={submitting || vacancies.length === 0}>
        {submitting ? 'Отправка...' : 'Отправить предложение'}
      </Button>
    </form>
  );
}
