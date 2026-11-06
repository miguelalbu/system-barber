import { describe, expect, it } from 'vitest';
import { passwordProblem, tokenFromPath } from '@/features/auth/model/invite.rules';

describe('passwordProblem', () => {
  it('accepts a good password typed twice', () => {
    expect(passwordProblem('navalha123', 'navalha123')).toBeNull();
  });

  it('refuses short passwords', () => {
    expect(passwordProblem('curta', 'curta')).toMatch(/pelo menos 8/);
  });

  it('refuses a password with a trailing space', () => {
    expect(passwordProblem('navalha123 ', 'navalha123 ')).toMatch(/espaço/);
  });

  it('refuses mismatched confirmation', () => {
    expect(passwordProblem('navalha123', 'navalha124')).toMatch(/não conferem/);
  });
});

describe('tokenFromPath', () => {
  it('reads the token and rejects an empty one', () => {
    expect(tokenFromPath('abc')).toBe('abc');
    expect(tokenFromPath('  ')).toBeNull();
    expect(tokenFromPath(undefined)).toBeNull();
  });
});
