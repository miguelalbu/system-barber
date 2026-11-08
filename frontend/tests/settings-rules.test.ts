import { describe, expect, it } from 'vitest';
import {
  changedFields,
  normalizeInstagram,
  sectionOf,
  shopSettingsInput,
  validatePolicies,
  validateShop,
} from '@/features/settings/model/settings.rules';

describe('instagram', () => {
  it('keeps only the username from what the owner pastes', () => {
    expect(normalizeInstagram('@barbearia.central')).toBe('barbearia.central');
    expect(normalizeInstagram('https://www.instagram.com/barbearia_central/?igsh=abc')).toBe('barbearia_central');
    expect(normalizeInstagram('instagram.com/corte.fino')).toBe('corte.fino');
    expect(normalizeInstagram('  ')).toBe('');
  });

  it('refuses spaces', () => {
    const form = { name: 'Central', contactPhone: '', instagram: 'minha barbearia', about: '', barberSeesClientContact: false };
    expect(validateShop(form)).toHaveProperty('instagram');
  });
});

describe('settings forms', () => {
  it('sends blanks as null and the username alone', () => {
    const body = shopSettingsInput({
      name: 'Central',
      contactPhone: ' ',
      instagram: '@central',
      about: '  ',
      barberSeesClientContact: true,
    });
    expect(body).toEqual({ contact_phone: null, instagram: 'central', about: null, barber_sees_client_contact: true });
  });

  it('checks the policy ranges', () => {
    const ok = {
      min_advance_minutes: 60,
      max_advance_days: 30,
      confirmation_deadline_hours: 3,
      client_change_min_hours: 2,
      late_tolerance_minutes: 10,
      max_future_appointments_per_client: 3,
    };
    expect(validatePolicies(ok)).toEqual({});
    expect(validatePolicies({ ...ok, max_advance_days: 0, confirmation_deadline_hours: 49 })).toEqual({
      max_advance_days: 'Entre 1 e 180',
      confirmation_deadline_hours: 'Entre 1 e 48',
    });
    expect(validatePolicies({ ...ok, late_tolerance_minutes: Number.NaN })).toHaveProperty('late_tolerance_minutes');
  });

  it('sends only what changed and reads the section from the URL', () => {
    expect(changedFields({ a: 1, b: 2 }, { a: 1, b: 3 })).toEqual({ b: 3 });
    expect(sectionOf('agendamento')).toBe('agendamento');
    expect(sectionOf('xyz')).toBe('barbearia');
  });
});
