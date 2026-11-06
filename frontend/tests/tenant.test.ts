import { describe, expect, it } from 'vitest';
import { slugFromHostname } from '@/shared/session/tenant';

// VITE_BASE_DOMAIN is unset in tests, so the default `navalha.local` applies.
describe('slugFromHostname', () => {
  it('reads the shop from its subdomain', () => {
    expect(slugFromHostname('central.navalha.local')).toBe('central');
  });

  it('has no shop on localhost or an IP', () => {
    expect(slugFromHostname('localhost')).toBeNull();
    expect(slugFromHostname('127.0.0.1')).toBeNull();
  });

  it('rejects nested subdomains', () => {
    expect(slugFromHostname('a.b.navalha.local')).toBeNull();
  });

  it('does not accept the bare base domain or a look-alike', () => {
    expect(slugFromHostname('navalha.local')).toBeNull();
    expect(slugFromHostname('central.navalha.local.evil.com')).toBeNull();
  });
});
