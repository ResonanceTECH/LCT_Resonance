import { render, screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { CareerPassportPage, QrCode } from '@/pages/public/CareerPassportPage';
import { renderWithProviders } from '@/test/test-utils';

describe('CareerPassportPage', () => {
  it('loads public passport without auth and shows QR + radar', async () => {
    renderWithProviders(
      <Routes>
        <Route path="/p/:slug" element={<CareerPassportPage />} />
      </Routes>,
      { route: '/p/cand-1' },
    );

    expect((await screen.findAllByText('Анна Ковалёва')).length).toBeGreaterThan(0);
    expect(screen.getByTestId('passport-qr')).toBeInTheDocument();
    expect(screen.getByTestId('passport-qr').getAttribute('data-url')).toMatch(/\/p\/cand-1/);
    expect(screen.getByTestId('skill-radar')).toBeInTheDocument();
    expect(screen.getByText(/Публичный паспорт кандидата/)).toBeInTheDocument();
  });

  it('shows error for unknown slug', async () => {
    renderWithProviders(
      <Routes>
        <Route path="/p/:slug" element={<CareerPassportPage />} />
      </Routes>,
      { route: '/p/unknown-slug' },
    );

    await waitFor(() => {
      expect(screen.getAllByText(/Паспорт не найден/).length).toBeGreaterThan(0);
    });
  });
});

describe('QrCode', () => {
  it('encodes URL into accessible svg', () => {
    render(<QrCode value="http://localhost:5173/p/cand-1" />);
    const qr = screen.getByTestId('passport-qr');
    expect(qr).toHaveAttribute('data-url', 'http://localhost:5173/p/cand-1');
    expect(qr.getAttribute('aria-label')).toMatch(/cand-1/);
  });
});
