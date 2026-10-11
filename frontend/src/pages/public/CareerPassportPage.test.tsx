import { render, screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { CareerPassportPage, QrCode } from '@/pages/public/CareerPassportPage';
import { renderWithProviders } from '@/test/test-utils';

function renderPassport(route: string) {
  renderWithProviders(
    <Routes>
      <Route path="/p/:slug" element={<CareerPassportPage />} />
    </Routes>,
    { route },
  );
}

describe('CareerPassportPage', () => {
  it('loads public passport without auth and shows QR + radar', async () => {
    renderPassport('/p/passport-cand-1');

    expect(await screen.findByRole('heading', { name: 'Анна Ковалёва' })).toBeInTheDocument();
    expect(screen.getByTestId('passport-qr')).toBeInTheDocument();
    expect(screen.getByTestId('passport-qr').getAttribute('data-url')).toMatch(/\/p\/passport-cand-1$/);
    expect(screen.getByTestId('skill-radar')).toBeInTheDocument();
    expect(screen.getByText(/Публичный карьерный паспорт/)).toBeInTheDocument();
    expect(screen.getByText(/Инженер фронтенда/)).toBeInTheDocument();
  });

  it('opens by the token even when the name part is outdated', async () => {
    renderPassport('/p/old-name-cand-1');

    expect(await screen.findByRole('heading', { name: 'Анна Ковалёва' })).toBeInTheDocument();
  });

  it('shows error for unknown slug', async () => {
    renderPassport('/p/unknown-slug');

    await waitFor(() => {
      expect(screen.getAllByText(/Паспорт не найден/).length).toBeGreaterThan(0);
    });
  });
});

describe('QrCode', () => {
  it('renders a real QR code of the URL as accessible svg', () => {
    render(<QrCode value="http://localhost:5173/p/anna-kovaleva-k7m2q9xw" />);
    const qr = screen.getByTestId('passport-qr');
    expect(qr.tagName.toLowerCase()).toBe('svg');
    expect(qr).toHaveAttribute('data-url', 'http://localhost:5173/p/anna-kovaleva-k7m2q9xw');
    expect(qr.getAttribute('aria-label')).toMatch(/anna-kovaleva-k7m2q9xw/);
    // qrcode.react draws the modules as a path, not the old decorative grid of rects.
    expect(qr.querySelector('path')).not.toBeNull();
  });
});
