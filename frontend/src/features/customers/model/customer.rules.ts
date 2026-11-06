import { formatPhone, isValidPhone } from '@/shared/text/phone';
import type { Client, ClientInput } from './customers.types';

export const PAGE_SIZE = 50;

export interface ClientForm {
  name: string;
  phone: string;
  email: string;
  birthDate: string;
  notes: string;
  active: boolean;
}

export type ClientErrors = Partial<Record<'name' | 'phone' | 'email' | 'birthDate' | 'notes', string>>;

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function emptyClientForm(): ClientForm {
  return { name: '', phone: '', email: '', birthDate: '', notes: '', active: true };
}

export function clientToForm(client: Client): ClientForm {
  return {
    name: client.name,
    phone: formatPhone(client.phone),
    email: client.email ?? '',
    birthDate: client.birth_date ?? '',
    notes: client.notes ?? '',
    active: client.active,
  };
}

/** Same limits as the API (`ClientIn`); `today` is "YYYY-MM-DD", injectable for tests. */
export function validateClient(form: ClientForm, today = new Date().toISOString().slice(0, 10)): ClientErrors {
  const errors: ClientErrors = {};
  const name = form.name.trim();
  if (name.length < 2) errors.name = 'Informe o nome (mínimo 2 letras)';
  else if (name.length > 120) errors.name = 'Nome muito longo (máximo 120)';
  if (!form.phone.trim()) errors.phone = 'Informe o telefone';
  else if (!isValidPhone(form.phone)) errors.phone = 'Telefone inválido: use DDD + número';
  if (form.email.trim() && !EMAIL.test(form.email.trim())) errors.email = 'E-mail inválido';
  if (form.birthDate && form.birthDate > today) errors.birthDate = 'Data no futuro';
  if (form.notes.trim().length > 1000) errors.notes = 'Máximo de 1000 caracteres';
  return errors;
}

export function clientInput(form: ClientForm): ClientInput {
  return {
    name: form.name.trim(),
    phone: form.phone.trim(),
    email: form.email.trim() || null,
    birth_date: form.birthDate || null,
    notes: form.notes.trim() || null,
    active: form.active,
  };
}

/** "1990-05-17" → "17/05". */
export function formatBirthday(date: string | null): string {
  if (!date) return '—';
  const [, month, day] = date.split('-');
  return `${day}/${month}`;
}

/** Page from the URL (`?pagina=`), 1-based and never below 1. */
export function pageFrom(param: string | null): number {
  const n = Number(param);
  return Number.isInteger(n) && n > 1 ? n : 1;
}

export function pageCount(total: number): number {
  return Math.max(1, Math.ceil(total / PAGE_SIZE));
}
