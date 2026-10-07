import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { LandingPage } from '@/pages/LandingPage';
import { renderWithProviders } from '@/test/test-utils';

describe('LandingPage', () => {
  it('renders brand-first hero with CTA and below-fold flow', () => {
    renderWithProviders(<LandingPage />, { route: '/' });

    expect(screen.getByTestId('landing-page')).toBeInTheDocument();
    expect(screen.getAllByText('LCT Resonance').length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Resonance/i);

    const startLinks = screen.getAllByRole('link', { name: 'Начать' });
    expect(startLinks.length).toBeGreaterThan(0);
    expect(startLinks.every((link) => link.getAttribute('href') === '/register')).toBe(true);

    expect(screen.getByRole('link', { name: 'Demo-вход' })).toHaveAttribute('href', '/login');
    expect(screen.getByText('Как это работает')).toBeInTheDocument();
    expect(screen.getAllByText('Talent Pool').length).toBeGreaterThan(0);
    expect(screen.getByRole('navigation', { name: 'Разделы лендинга' })).toBeInTheDocument();
  });
});
