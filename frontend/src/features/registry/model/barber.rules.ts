import { initialsOf } from '@/shared/text/initials';
import type { Barber, BarberInput, Member, Service } from './registry.types';

export interface BarberForm {
  name: string;
  initials: string;
  unitId: string;
  commission: string;
  active: boolean;
  userId: string;
  serviceIds: string[];
}

export type BarberErrors = Partial<Record<'name' | 'initials' | 'unitId' | 'commission', string>>;

export function emptyBarberForm(unitId: string): BarberForm {
  return { name: '', initials: '', unitId, commission: '40', active: true, userId: '', serviceIds: [] };
}

export function barberToForm(barber: Barber, services: Service[]): BarberForm {
  return {
    name: barber.name,
    initials: barber.initials,
    unitId: barber.unit_id,
    commission: String(barber.default_commission).replace('.', ','),
    active: barber.active,
    userId: barber.user_id ?? '',
    serviceIds: services.filter((s) => s.barber_ids.includes(barber.id)).map((s) => s.id),
  };
}

/** The initials shown while typing the name, until the user sets their own. */
export function suggestedInitials(name: string): string {
  return name.trim() ? initialsOf(name.trim()) : '';
}

function parseCommission(text: string): number | null {
  const value = Number(text.trim().replace('%', '').replace(',', '.'));
  if (!text.trim() || Number.isNaN(value) || value < 0 || value > 100) return null;
  return Math.round(value * 100) / 100;
}

/** Same limits as the API (`BarberIn`), so the form warns before sending. */
export function validateBarber(form: BarberForm): BarberErrors {
  const errors: BarberErrors = {};
  const name = form.name.trim();
  if (name.length < 2) errors.name = 'Informe o nome (mínimo 2 letras)';
  else if (name.length > 120) errors.name = 'Nome muito longo (máximo 120)';
  if (form.initials.trim().length > 4) errors.initials = 'No máximo 4 letras';
  if (!form.unitId) errors.unitId = 'Escolha a unidade';
  if (parseCommission(form.commission) === null) errors.commission = 'Entre 0 e 100';
  return errors;
}

export function barberInput(form: BarberForm): BarberInput {
  const initials = form.initials.trim();
  return {
    name: form.name.trim(),
    unit_id: form.unitId,
    ...(initials ? { initials } : {}),
    default_commission: parseCommission(form.commission) ?? 0,
    active: form.active,
    user_id: form.userId || null,
  };
}

/** "Corte, Barba" — the services a barber performs, from each service's `barber_ids`. */
export function servicesOf(barberId: string, services: Service[]): string {
  const names = services.filter((s) => s.barber_ids.includes(barberId)).map((s) => s.name);
  return names.length ? names.join(', ') : '—';
}

/**
 * Logins that may be linked to this barber: active, and not linked to another
 * barber (the API refuses those) — plus the one already linked to it.
 */
export function linkableMembers(members: Member[], barber: Barber | null): Member[] {
  return members.filter(
    (m) => m.id === barber?.user_id || (m.active && m.barber_id === null),
  );
}

/** "45%" / "42,5%". */
export function formatCommission(value: number): string {
  return `${String(value).replace('.', ',')}%`;
}
