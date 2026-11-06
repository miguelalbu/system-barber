import { describe, expect, it } from 'vitest';
import {
  clientInput,
  clientToForm,
  emptyClientForm,
  formatBirthday,
  pageCount,
  pageFrom,
  validateClient,
} from '@/features/customers/model/customer.rules';

const TODAY = '2026-11-06';

describe('customer rules', () => {
  it('validates like the API', () => {
    const ok = { ...emptyClientForm(), name: 'João', phone: '(11) 98765-4321' };
    expect(validateClient(ok, TODAY)).toEqual({});

    const errors = validateClient(
      { ...ok, name: 'J', phone: '1234', email: 'nope', birthDate: '2030-01-01' },
      TODAY,
    );
    expect(Object.keys(errors).sort()).toEqual(['birthDate', 'email', 'name', 'phone']);
    expect(validateClient({ ...ok, phone: '' }, TODAY).phone).toBe('Informe o telefone');
  });

  it('sends blanks as null and shows E.164 formatted', () => {
    const form = clientToForm({
      id: 'c1',
      name: 'João',
      phone: '+5511987654321',
      email: null,
      birth_date: '1990-05-17',
      notes: null,
      active: true,
      created_at: '',
      updated_at: '',
    });
    expect(form.phone).toBe('(11) 98765-4321');
    expect(clientInput({ ...form, notes: '  ' })).toEqual({
      name: 'João',
      phone: '(11) 98765-4321',
      email: null,
      birth_date: '1990-05-17',
      notes: null,
      active: true,
    });
  });

  it('formats the birthday as day/month', () => {
    expect(formatBirthday('1990-05-17')).toBe('17/05');
    expect(formatBirthday(null)).toBe('—');
  });

  it('reads the page from the URL safely', () => {
    expect(pageFrom(null)).toBe(1);
    expect(pageFrom('3')).toBe(3);
    expect(pageFrom('-2')).toBe(1);
    expect(pageFrom('abc')).toBe(1);
    expect(pageCount(0)).toBe(1);
    expect(pageCount(51)).toBe(2);
  });
});
