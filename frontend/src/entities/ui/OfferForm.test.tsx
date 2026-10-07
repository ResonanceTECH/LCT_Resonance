import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { OfferForm } from '@/entities/ui/OfferForm';
import type { Vacancy } from '@/entities/types';

const vacancies: Vacancy[] = [
  {
    id: 'vac-1',
    employerId: 'user-emp-1',
    companyName: 'Resonance Labs',
    title: 'Frontend Engineer (React)',
    description: 'desc',
    specialization: 'Frontend',
    requiredGrade: 'middle',
    requiredSkills: ['React'],
    niceToHaveSkills: ['Jest'],
    salaryFrom: 260000,
    salaryTo: 340000,
    currency: 'RUB',
    workFormat: 'remote',
    status: 'active',
    createdAt: '2026-09-01T10:00:00.000Z',
    updatedAt: '2026-09-15T10:00:00.000Z',
  },
];

describe('OfferForm', () => {
  it('always shows explicit salary range before submit', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <OfferForm
        vacancies={vacancies}
        candidateId="cand-1"
        defaultVacancyId="vac-1"
        onSubmit={onSubmit}
      />,
    );

    expect(screen.getByText(/Зарплатная вилка в предложении/)).toBeInTheDocument();
    expect(screen.getByText(/260/)).toBeInTheDocument();
    expect(screen.getByText(/340/)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Отправить предложение/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      candidateId: 'cand-1',
      vacancyId: 'vac-1',
      salaryFrom: 260000,
      salaryTo: 340000,
    });
  });
});
