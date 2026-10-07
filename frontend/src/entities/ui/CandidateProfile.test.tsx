import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { CandidateProfileView } from '@/entities/ui/CandidateProfile';
import type { CandidateProfile, FspAchievement } from '@/entities/types';

const profile: CandidateProfile = {
  id: 'cand-1',
  userId: 'user-cand-1',
  fullName: 'Анна Ковалёва',
  specialization: 'Frontend',
  claimedGrade: 'middle',
  skills: ['React', 'TypeScript'],
  currency: 'RUB',
  readiness: 'open_to_offers',
  workFormat: 'remote',
  salaryFrom: 250000,
  salaryTo: 320000,
  testResult: {
    score: 82,
    maxScore: 100,
    gradeConfirmed: true,
    completedAt: '2026-09-12T10:00:00.000Z',
  },
};

const achievements: FspAchievement[] = [
  {
    id: 'fsp-1',
    title: 'Кубок ФСП',
    discipline: 'Frontend',
    verified: true,
  },
];

describe('CandidateProfileView', () => {
  it('shows claimed grade and test result separately', () => {
    render(
      <MemoryRouter>
        <CandidateProfileView mode="self" profile={profile} />
      </MemoryRouter>,
    );
    expect(screen.getByText('Заявленный уровень')).toBeInTheDocument();
    expect(screen.getByText('Результат тестирования')).toBeInTheDocument();
    expect(screen.getByText('82/100')).toBeInTheDocument();
    expect(screen.getByText('Уровень подтвержден')).toBeInTheDocument();
  });

  it('marks FSP achievements as verified, not self-reported skills', () => {
    render(
      <MemoryRouter>
        <CandidateProfileView mode="employer" profile={profile} achievements={achievements} />
      </MemoryRouter>,
    );
    expect(screen.getByText('Кубок ФСП')).toBeInTheDocument();
    expect(screen.getAllByText(/Подтверждено ФСП|FSP Verified/).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Самостоятельно указанные навыки не помечаются как подтверждённые ФСП/),
    ).toBeInTheDocument();
  });
});
