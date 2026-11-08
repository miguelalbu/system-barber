/** Pure rules of the settings screen: contact form, policies form, what changed. */

import { formatPhone, isValidPhone } from '@/shared/text/phone';
import type { SettingsSection, ShopSettings, ShopSettingsUpdate } from './settings.types';

export const SECTIONS: { key: SettingsSection; label: string }[] = [
  { key: 'barbearia', label: 'Barbearia' },
  { key: 'agendamento', label: 'Agendamento' },
];

export function sectionOf(raw: string | null): SettingsSection {
  return SECTIONS.some((s) => s.key === raw) ? (raw as SettingsSection) : 'barbearia';
}

/**
 * What the owner pastes into "Instagram" → just the username:
 * "@barbearia", "instagram.com/barbearia/", "https://www.instagram.com/barbearia?igsh=x".
 */
export function normalizeInstagram(raw: string): string {
  let text = raw.trim();
  const url = /^(?:https?:\/\/)?(?:www\.)?instagram\.com\/([^/?#\s]+)/i.exec(text);
  if (url) text = url[1];
  return text.replace(/^@+/, '').trim();
}

export function isValidInstagram(username: string): boolean {
  return username === '' || /^[A-Za-z0-9._]{1,60}$/.test(username);
}

// --- "Barbearia" -------------------------------------------------------------

export interface ShopForm {
  name: string;
  contactPhone: string;
  instagram: string;
  about: string;
  barberSeesClientContact: boolean;
}

export type ShopErrors = Partial<Record<'name' | 'contactPhone' | 'instagram' | 'about', string>>;

export const ABOUT_MAX = 1000;

export function shopToForm(name: string, s: ShopSettings): ShopForm {
  return {
    name,
    contactPhone: s.contact_phone ? formatPhone(s.contact_phone) : '',
    instagram: s.instagram ?? '',
    about: s.about ?? '',
    barberSeesClientContact: s.barber_sees_client_contact,
  };
}

export function validateShop(form: ShopForm): ShopErrors {
  const errors: ShopErrors = {};
  const name = form.name.trim();
  if (name.length < 2 || name.length > 120) errors.name = 'Informe o nome da barbearia (2 a 120 letras)';
  if (form.contactPhone.trim() && !isValidPhone(form.contactPhone)) errors.contactPhone = 'Telefone inválido';
  if (!isValidInstagram(normalizeInstagram(form.instagram)))
    errors.instagram = 'Use só o usuário do Instagram (letras, números, ponto e _)';
  if (form.about.length > ABOUT_MAX) errors.about = `No máximo ${ABOUT_MAX} caracteres`;
  return errors;
}

export function shopSettingsInput(form: ShopForm): ShopSettingsUpdate {
  return {
    contact_phone: form.contactPhone.trim() || null,
    instagram: normalizeInstagram(form.instagram) || null,
    about: form.about.trim() || null,
    barber_sees_client_contact: form.barberSeesClientContact,
  };
}

// --- "Agendamento" -----------------------------------------------------------

export type PolicyForm = Pick<
  ShopSettings,
  | 'min_advance_minutes'
  | 'max_advance_days'
  | 'confirmation_deadline_hours'
  | 'client_change_min_hours'
  | 'late_tolerance_minutes'
  | 'max_future_appointments_per_client'
>;

export const POLICY_KEYS: (keyof PolicyForm)[] = [
  'min_advance_minutes',
  'max_advance_days',
  'confirmation_deadline_hours',
  'client_change_min_hours',
  'late_tolerance_minutes',
  'max_future_appointments_per_client',
];

export const MIN_ADVANCE_OPTIONS: { value: number; label: string }[] = [
  { value: 0, label: 'Sem mínimo' },
  { value: 15, label: '15 minutos' },
  { value: 30, label: '30 minutos' },
  { value: 60, label: '1 hora' },
  { value: 120, label: '2 horas' },
  { value: 240, label: '4 horas' },
  { value: 720, label: '12 horas' },
  { value: 1440, label: '24 horas' },
  { value: 2880, label: '48 horas' },
];

/** Allowed range of each numeric policy (same as the API). */
export const POLICY_RANGES: Record<Exclude<keyof PolicyForm, 'min_advance_minutes'>, [number, number]> = {
  max_advance_days: [1, 180],
  confirmation_deadline_hours: [1, 48],
  client_change_min_hours: [0, 72],
  late_tolerance_minutes: [0, 60],
  max_future_appointments_per_client: [1, 20],
};

export function policiesOf(s: ShopSettings): PolicyForm {
  return Object.fromEntries(POLICY_KEYS.map((k) => [k, s[k]])) as PolicyForm;
}

export function validatePolicies(form: PolicyForm): Partial<Record<keyof PolicyForm, string>> {
  const errors: Partial<Record<keyof PolicyForm, string>> = {};
  for (const [key, [min, max]] of Object.entries(POLICY_RANGES) as [keyof typeof POLICY_RANGES, [number, number]][]) {
    const value = form[key];
    if (!Number.isInteger(value) || value < min || value > max) errors[key] = `Entre ${min} e ${max}`;
  }
  return errors;
}

/** Only what changed, so a save never overwrites a field someone else just changed. */
export function changedFields<T extends object>(before: T, after: T): Partial<T> {
  return Object.fromEntries(
    (Object.keys(after) as (keyof T)[])
      .filter((k) => after[k] !== before[k])
      .map((k) => [k, after[k]]),
  ) as Partial<T>;
}
