import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SkillRadar } from '@/entities/ui/SkillRadar';

describe('SkillRadar', () => {
  it('renders backend axes without inventing scores', () => {
    render(
      <SkillRadar
        radar={{
          candidateId: 'cand-1',
          axes: [
            { skill: 'React', score: 88 },
            { skill: 'TypeScript', score: 91 },
            { skill: 'CSS', score: 70 },
          ],
        }}
      />,
    );

    expect(screen.getByTestId('skill-radar')).toBeInTheDocument();
    expect(screen.getByText(/React \(88\)/)).toBeInTheDocument();
    expect(screen.getByText(/TypeScript \(91\)/)).toBeInTheDocument();
    expect(
      screen.getByText(/Оценки рассчитаны на Backend\/ML/),
    ).toBeInTheDocument();
  });

  it('shows empty state when axes are missing', () => {
    render(<SkillRadar radar={{ candidateId: 'cand-1', axes: [] }} />);
    expect(screen.getByText(/Нет данных для Skill Radar/)).toBeInTheDocument();
  });
});
