import { describe, expect, it } from 'vitest';
import { DURATION_OPTIONS, formatDuration } from '@/shared/text/duration';
import { centsToInput, formatBRL, parseBRL } from '@/shared/text/money';
import { formatPhone, isValidPhone, maskPhone } from '@/shared/text/phone';
import { queryString } from '@/shared/api/http';

describe('money', () => {
  it('formats cents as reais', () => {
    expect(formatBRL(4550).replace(/\s/g, ' ')).toBe('R$ 45,50');
    expect(centsToInput(4500)).toBe('45,00');
  });

  it('parses what people type', () => {
    expect(parseBRL('45')).toBe(4500);
    expect(parseBRL('45,5')).toBe(4550);
    expect(parseBRL('R$ 1.234,56')).toBe(123456);
    expect(parseBRL('45.50')).toBe(4550);
    expect(parseBRL('0')).toBe(0);
  });

  it('rejects what is not an amount', () => {
    for (const bad of ['', 'abc', '-5', '45,555', '1,2,3']) expect(parseBRL(bad)).toBeNull();
  });
});

describe('duration', () => {
  it('reads like a person would say it', () => {
    expect(formatDuration(45)).toBe('45 min');
    expect(formatDuration(60)).toBe('1 h');
    expect(formatDuration(90)).toBe('1 h 30 min');
  });

  it('offers 5 min to 8 h in steps of 5, as the API accepts', () => {
    expect(DURATION_OPTIONS[0]).toBe(5);
    expect(DURATION_OPTIONS[DURATION_OPTIONS.length - 1]).toBe(480);
    expect(DURATION_OPTIONS.every((m) => m % 5 === 0)).toBe(true);
  });
});

describe('phone', () => {
  it('formats E.164 Brazilian numbers', () => {
    expect(formatPhone('+5511987654321')).toBe('(11) 98765-4321');
    expect(formatPhone('+551133334444')).toBe('(11) 3333-4444');
    expect(formatPhone('+14155552671')).toBe('+14155552671');
  });

  it('accepts what the API accepts', () => {
    for (const ok of ['(11) 98765-4321', '11 3333-4444', '+55 11 98765-4321', '5511987654321', '+1 415 555 2671']) {
      expect(isValidPhone(ok)).toBe(true);
    }
    for (const bad of ['', '1234', '98765-4321', '+12']) expect(isValidPhone(bad)).toBe(false);
  });

  it('masks while typing', () => {
    expect(maskPhone('11')).toBe('(11');
    // Landline layout until the 11th digit arrives, then the mobile one.
    expect(maskPhone('1198765')).toBe('(11) 9876-5');
    expect(maskPhone('1133334444')).toBe('(11) 3333-4444');
    expect(maskPhone('11987654321')).toBe('(11) 98765-4321');
    expect(maskPhone('+1 415')).toBe('+1 415');
  });
});

describe('queryString', () => {
  it('leaves out empty values', () => {
    expect(queryString({ q: 'ana', limit: 50, offset: 0, active: undefined, x: '' })).toBe(
      '?q=ana&limit=50&offset=0',
    );
    expect(queryString(undefined)).toBe('');
  });
});
