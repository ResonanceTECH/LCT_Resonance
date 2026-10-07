import { describe, expect, it } from 'vitest';
import {
  formatGrade,
  formatOfferStatus,
  formatReadiness,
  formatSalary,
  formatWorkFormat,
} from '@/shared/lib/formatters';

describe('formatters', () => {
  it('formats salary ranges for offers', () => {
    const range = formatSalary(280000, 320000, 'RUB');
    expect(range).toMatch(/280/);
    expect(range).toMatch(/320/);
    expect(range).toContain('₽');
    expect(formatSalary(100, undefined, 'USD')).toMatch(/от 100/);
  });

  it('maps domain enums to RU labels used in UI', () => {
    expect(formatGrade('middle')).toBe('Middle');
    expect(formatWorkFormat('remote')).toBe('Удалённо');
    expect(formatReadiness('open_to_offers')).toBe('Открыт к предложениям');
    expect(formatOfferStatus('accepted')).toBe('Принято');
  });
});
