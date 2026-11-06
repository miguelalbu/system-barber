import { describe, expect, it } from 'vitest';
import {
  barberInput,
  barberToForm,
  emptyBarberForm,
  formatCommission,
  linkableMembers,
  servicesOf,
  suggestedInitials,
  validateBarber,
} from '@/features/registry/model/barber.rules';
import type { Barber, Member, Service } from '@/features/registry/model/registry.types';
import { serviceInput, serviceToForm, validateService } from '@/features/registry/model/service.rules';

const service = (id: string, name: string, barberIds: string[]): Service => ({
  id,
  name,
  description: null,
  duration_minutes: 30,
  price_cents: 4500,
  active: true,
  barber_ids: barberIds,
  created_at: '',
  updated_at: '',
});

const barber: Barber = {
  id: 'b1',
  name: 'Diego Martins',
  initials: 'DM',
  unit_id: 'u1',
  default_commission: 42.5,
  active: true,
  user_id: null,
  email: null,
  created_at: '',
  updated_at: '',
};

const member = (id: string, barberId: string | null, active = true): Member => ({
  id,
  name: id,
  email: `${id}@x.com`,
  role: 'owner',
  active,
  barber_id: barberId,
});

describe('barber rules', () => {
  it('lists the services a barber performs', () => {
    const services = [service('s1', 'Corte', ['b1']), service('s2', 'Barba', ['b1', 'b2']), service('s3', 'Pigmentação', [])];
    expect(servicesOf('b1', services)).toBe('Corte, Barba');
    expect(servicesOf('b9', services)).toBe('—');
  });

  it('round-trips a barber through the form', () => {
    const form = barberToForm(barber, [service('s1', 'Corte', ['b1'])]);
    expect(form.commission).toBe('42,5');
    expect(form.serviceIds).toEqual(['s1']);
    expect(barberInput(form)).toEqual({
      name: 'Diego Martins',
      unit_id: 'u1',
      initials: 'DM',
      default_commission: 42.5,
      active: true,
      user_id: null,
    });
  });

  it('leaves initials to the API when blank', () => {
    const form = { ...emptyBarberForm('u1'), name: ' Ana Souza ' };
    expect(suggestedInitials(form.name)).toBe('AS');
    expect(barberInput(form)).not.toHaveProperty('initials');
  });

  it('validates like the API', () => {
    expect(validateBarber({ ...emptyBarberForm('u1'), name: 'Ana' })).toEqual({});
    const errors = validateBarber({ ...emptyBarberForm(''), name: 'A', commission: '101' });
    expect(Object.keys(errors).sort()).toEqual(['commission', 'name', 'unitId']);
  });

  it('offers only free, active logins — plus the one already linked', () => {
    const members = [member('free', null), member('taken', 'b2'), member('off', null, false), member('mine', 'b1')];
    expect(linkableMembers(members, { ...barber, user_id: 'mine' }).map((m) => m.id)).toEqual(['free', 'mine']);
    expect(linkableMembers(members, null).map((m) => m.id)).toEqual(['free']);
  });

  it('formats commission', () => {
    expect(formatCommission(45)).toBe('45%');
    expect(formatCommission(42.5)).toBe('42,5%');
  });
});

describe('service rules', () => {
  it('round-trips a service and converts the price to cents', () => {
    const form = serviceToForm(service('s1', 'Corte', []));
    expect(form.price).toBe('45,00');
    expect(serviceInput({ ...form, price: '50,5', description: '  ' })).toEqual({
      name: 'Corte',
      description: null,
      duration_minutes: 30,
      price_cents: 5050,
      active: true,
    });
  });

  it('validates like the API', () => {
    const errors = validateService({ name: 'C', description: '', duration: 30, price: 'abc', active: true });
    expect(Object.keys(errors).sort()).toEqual(['name', 'price']);
  });
});
