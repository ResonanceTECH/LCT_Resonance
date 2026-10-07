import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MatchScore } from '@/entities/ui/MatchScore';
import type { CandidateMatch } from '@/entities/types';

const match: CandidateMatch = {
  candidateId: 'cand-1',
  vacancyId: 'vac-1',
  score: 91,
  matchedSkills: ['React', 'TypeScript'],
  missingInProfileSkills: ['Jest'],
  reasons: [
    { code: 'spec', label: 'совпадает специализация Frontend', positive: true },
    { code: 'skill-React', label: 'React указан в профиле', positive: true },
  ],
};

describe('MatchScore', () => {
  it('renders backend score and positive reasons', () => {
    render(<MatchScore match={match} />);
    expect(screen.getByText('Match 91%')).toBeInTheDocument();
    expect(screen.getByText(/совпадает специализация Frontend/)).toBeInTheDocument();
  });

  it('uses «не указан в профиле» wording, never claims candidate lacks the skill', () => {
    render(<MatchScore match={match} />);
    expect(screen.getByText(/Не указано в профиле/)).toBeInTheDocument();
    expect(screen.getByText(/навык не указан в профиле/)).toBeInTheDocument();
    expect(screen.getByText(/Jest/)).toBeInTheDocument();
    expect(screen.queryByText(/не умеет/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/не знает/i)).not.toBeInTheDocument();
  });
});
