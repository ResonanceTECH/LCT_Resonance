import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { CandidateCard } from '@/entities/ui/CandidateCard';
import type { TalentPoolFilters } from '@/entities/types';
import { candidateApi, vacancyApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { formatSpecialization } from '@/shared/lib/formatters';
import {
  GRADE_OPTIONS,
  READINESS_OPTIONS,
  SPECIALIZATION_OPTIONS,
  WORK_FORMAT_OPTIONS,
} from '@/shared/lib/labels';
import { Button, Checkbox, EmptyState, ErrorState, Input, Loader, Select } from '@/shared/ui';

function useDebounced<T>(value: T, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export function EmployerTalentPoolPage() {
  const [params, setParams] = useSearchParams();
  const [selected, setSelected] = useState<string[]>([]);
  const [filters, setFilters] = useState<TalentPoolFilters>({
    specialization: params.get('specialization') ?? '',
    grade: (params.get('grade') as TalentPoolFilters['grade']) ?? '',
    skills: params.get('skills') ?? '',
    workFormat: (params.get('workFormat') as TalentPoolFilters['workFormat']) ?? '',
    salaryFrom: params.get('salaryFrom') ? Number(params.get('salaryFrom')) : '',
    salaryTo: params.get('salaryTo') ? Number(params.get('salaryTo')) : '',
    fspDiscipline: params.get('fspDiscipline') ?? '',
    hasFspAchievements:
      params.get('hasFspAchievements') === 'true'
        ? true
        : params.get('hasFspAchievements') === 'false'
          ? false
          : '',
    readiness: (params.get('readiness') as TalentPoolFilters['readiness']) ?? '',
    vacancyId: params.get('vacancyId') ?? '',
    q: params.get('q') ?? '',
    sort: (params.get('sort') as TalentPoolFilters['sort']) ?? '',
  });

  const debounced = useDebounced(filters);

  useEffect(() => {
    const next = new URLSearchParams();
    Object.entries(debounced).forEach(([key, value]) => {
      if (value === '' || value === undefined || value === null) return;
      next.set(key, String(value));
    });
    setParams(next, { replace: true });
  }, [debounced, setParams]);

  const vacanciesQuery = useQuery({
    queryKey: ['vacancies', 'employer'],
    queryFn: vacancyApi.employerList,
  });

  const query = useQuery({
    queryKey: ['talent-pool', debounced],
    queryFn: () => candidateApi.list(debounced),
  });

  const vacancyOptions = useMemo(
    () =>
      (vacanciesQuery.data ?? []).map((v) => ({
        value: v.id,
        label: v.title,
      })),
    [vacanciesQuery.data],
  );

  const toggleSelected = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length >= 4 ? prev : [...prev, id],
    );
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Пул кандидатов</h1>
          <p>Фильтры применяются на сервере. Оценка соответствия — только при выбранной вакансии.</p>
        </div>
        <Link
          to={
            selected.length >= 2
              ? `/employer/compare?ids=${selected.join(',')}`
              : '/employer/talent-pool'
          }
          aria-disabled={selected.length < 2}
          onClick={(e) => {
            if (selected.length < 2) e.preventDefault();
          }}
        >
          <Button type="button" disabled={selected.length < 2}>
            Сравнить ({selected.length})
          </Button>
        </Link>
      </div>

      <div className="filters section-card">
        <Input
          label="Поиск"
          value={filters.q ?? ''}
          onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
        />
        <Select
          label="Вакансия для оценки"
          allowEmpty
          emptyLabel="Без оценки соответствия"
          options={vacancyOptions}
          value={filters.vacancyId ?? ''}
          onChange={(e) => setFilters((f) => ({ ...f, vacancyId: e.target.value }))}
        />
        <Select
          label="Сортировка"
          allowEmpty
          emptyLabel="По умолчанию"
          options={[
            { value: 'match', label: 'Оценка соответствия' },
            { value: 'name', label: 'Имя' },
            { value: 'grade', label: 'Грейд' },
            { value: 'salary', label: 'Зарплата' },
          ]}
          value={filters.sort ?? ''}
          onChange={(e) =>
            setFilters((f) => ({ ...f, sort: e.target.value as TalentPoolFilters['sort'] }))
          }
        />
        <Select
          label="Специализация"
          allowEmpty
          options={SPECIALIZATION_OPTIONS.map((s) => ({
            value: s,
            label: formatSpecialization(s),
          }))}
          value={filters.specialization ?? ''}
          onChange={(e) => setFilters((f) => ({ ...f, specialization: e.target.value }))}
        />
        <Select
          label="Грейд"
          allowEmpty
          options={GRADE_OPTIONS}
          value={filters.grade ?? ''}
          onChange={(e) =>
            setFilters((f) => ({ ...f, grade: e.target.value as TalentPoolFilters['grade'] }))
          }
        />
        <Input
          label="Стек"
          value={filters.skills ?? ''}
          onChange={(e) => setFilters((f) => ({ ...f, skills: e.target.value }))}
        />
        <Select
          label="Формат"
          allowEmpty
          options={WORK_FORMAT_OPTIONS}
          value={filters.workFormat ?? ''}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              workFormat: e.target.value as TalentPoolFilters['workFormat'],
            }))
          }
        />
        <Input
          label="Зарплата от"
          type="number"
          value={filters.salaryFrom ?? ''}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              salaryFrom: e.target.value ? Number(e.target.value) : '',
            }))
          }
        />
        <Input
          label="Зарплата до"
          type="number"
          value={filters.salaryTo ?? ''}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              salaryTo: e.target.value ? Number(e.target.value) : '',
            }))
          }
        />
        <Input
          label="Дисциплина ФСП"
          value={filters.fspDiscipline ?? ''}
          onChange={(e) => setFilters((f) => ({ ...f, fspDiscipline: e.target.value }))}
        />
        <Select
          label="Есть ФСП"
          allowEmpty
          options={[
            { value: 'true', label: 'Да' },
            { value: 'false', label: 'Нет' },
          ]}
          value={
            filters.hasFspAchievements === true
              ? 'true'
              : filters.hasFspAchievements === false
                ? 'false'
                : ''
          }
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              hasFspAchievements: e.target.value === '' ? '' : e.target.value === 'true',
            }))
          }
        />
        <Select
          label="Готовность"
          allowEmpty
          options={READINESS_OPTIONS}
          value={filters.readiness ?? ''}
          onChange={(e) =>
            setFilters((f) => ({
              ...f,
              readiness: e.target.value as TalentPoolFilters['readiness'],
            }))
          }
        />
      </div>

      {query.isLoading ? <Loader label="Ищем кандидатов..." /> : null}
      {query.isError ? (
        <ErrorState
          title="Ошибка поиска"
          description={getErrorMessage(query.error)}
          onRetry={() => void query.refetch()}
        />
      ) : null}
      {query.data && query.data.items.length === 0 ? (
        <EmptyState title="Подходящие кандидаты не найдены" description="Измените фильтры." />
      ) : null}
      {query.data && query.data.items.length > 0 ? (
        <div className="stack">
          {query.data.items.map((candidate) => (
            <div key={candidate.id} className="stack">
              <Checkbox
                label={`Выбрать ${candidate.fullName} для сравнения`}
                checked={selected.includes(candidate.id)}
                onChange={() => toggleSelected(candidate.id)}
              />
              <CandidateCard
                candidate={candidate}
                to={`/employer/candidates/${candidate.id}${
                  filters.vacancyId ? `?vacancyId=${filters.vacancyId}` : ''
                }`}
              />
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
