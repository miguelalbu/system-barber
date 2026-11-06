import { describe, expect, it } from 'vitest';
import { initialsOf } from '@/shared/text/initials';

describe('initialsOf', () => {
  it('uses the first and last names', () => {
    expect(initialsOf('Miguel de Albuquerque')).toBe('MA');
  });

  it('uses two letters of a single name', () => {
    expect(initialsOf('diego')).toBe('DI');
  });

  it('survives an empty name', () => {
    expect(initialsOf('   ')).toBe('??');
  });
});
