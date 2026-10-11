import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { LandingPage } from '@/pages/LandingPage';
import { renderWithProviders } from '@/test/test-utils';

describe('LandingPage', () => {
  it('renders brand-first hero with CTA and below-fold flow', () => {
    renderWithProviders(<LandingPage />, { route: '/' });

    expect(screen.getByTestId('landing-page')).toBeInTheDocument();
    expect(screen.getAllByText('FSP Talent').length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      /подтверждёнными компетенциями/i,
    );

    const startLinks = screen.getAllByRole('link', { name: 'Начать' });
    expect(startLinks.length).toBeGreaterThan(0);
    expect(startLinks.every((link) => link.getAttribute('href') === '/register')).toBe(true);

    const demoLinks = screen.getAllByRole('link', { name: 'Демовход' });
    expect(demoLinks.length).toBeGreaterThan(0);
    expect(demoLinks.every((link) => link.getAttribute('href') === '/login')).toBe(true);

    expect(screen.getAllByText('Как это работает').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Пул кандидатов').length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { name: 'Четыре шага до сигнала' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Открыть меню' })).toBeInTheDocument();
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    expect(screen.getByText('© 2026 FSP Talent')).toBeInTheDocument();
  });
});
