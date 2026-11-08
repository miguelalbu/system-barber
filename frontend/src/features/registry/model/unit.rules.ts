/**
 * Pure rules of the Units page: the unit form, the weekly hours editor and the
 * calendar-exception form. They mirror the API's rules (spec S01) so the form
 * warns first; the API stays the judge.
 */

import { formatPhone, isValidPhone } from '@/shared/text/phone';
import { fromMinutes, toMinutes } from '@/shared/text/time';
import type {
  DayHours,
  ExceptionKind,
  Holiday,
  Interval,
  UnitException,
  UnitExceptionInput,
  UnitInput,
  UnitRecord,
} from './unit.types';

export const DEFAULT_TIMEZONE = 'America/Sao_Paulo';

/** The Brazilian IANA zones, by how the owner knows them. */
export const BR_TIMEZONES: { value: string; label: string }[] = [
  { value: 'America/Sao_Paulo', label: 'Brasília (SP, RJ, MG, Sul, GO, DF, BA…)' },
  { value: 'America/Manaus', label: 'Amazonas, Roraima, Rondônia, MT, MS (−1 h)' },
  { value: 'America/Cuiaba', label: 'Mato Grosso — Cuiabá (−1 h)' },
  { value: 'America/Campo_Grande', label: 'Mato Grosso do Sul — Campo Grande (−1 h)' },
  { value: 'America/Rio_Branco', label: 'Acre (−2 h)' },
  { value: 'America/Noronha', label: 'Fernando de Noronha (+1 h)' },
  { value: 'America/Belem', label: 'Pará, Amapá (Brasília, sem horário de verão)' },
  { value: 'America/Fortaleza', label: 'Nordeste — CE, RN, PB, PI, MA' },
  { value: 'America/Recife', label: 'Pernambuco' },
  { value: 'America/Bahia', label: 'Bahia' },
];

export const WEEKDAY_LABELS: Record<number, string> = {
  1: 'Segunda',
  2: 'Terça',
  3: 'Quarta',
  4: 'Quinta',
  5: 'Sexta',
  6: 'Sábado',
  7: 'Domingo',
};

export const MAX_INTERVALS = 3;

// --- Unit form ---------------------------------------------------------------

export interface UnitForm {
  name: string;
  timezone: string;
  address: string;
  phone: string;
  onlineBooking: boolean;
  active: boolean;
}

export type UnitErrors = Partial<Record<'name' | 'timezone' | 'address' | 'phone', string>>;

export function emptyUnitForm(): UnitForm {
  return { name: '', timezone: DEFAULT_TIMEZONE, address: '', phone: '', onlineBooking: true, active: true };
}

export function unitToForm(unit: UnitRecord): UnitForm {
  return {
    name: unit.name,
    timezone: unit.timezone,
    address: unit.address ?? '',
    phone: unit.phone ? formatPhone(unit.phone) : '',
    onlineBooking: unit.online_booking,
    active: unit.active,
  };
}

export function validateUnit(form: UnitForm): UnitErrors {
  const errors: UnitErrors = {};
  const name = form.name.trim();
  if (name.length < 2) errors.name = 'Informe o nome da unidade (mínimo 2 letras)';
  else if (name.length > 120) errors.name = 'Nome muito longo (máximo 120)';
  if (!form.timezone.trim()) errors.timezone = 'Escolha o fuso horário';
  if (form.address.trim().length > 300) errors.address = 'Endereço muito longo (máximo 300)';
  if (form.phone.trim() && !isValidPhone(form.phone)) errors.phone = 'Telefone inválido';
  return errors;
}

export function unitInput(form: UnitForm): UnitInput {
  return {
    name: form.name.trim(),
    timezone: form.timezone.trim(),
    address: form.address.trim() || null,
    phone: form.phone.trim() || null,
    online_booking: form.onlineBooking,
    active: form.active,
  };
}

/** Columns worth showing: the timezone only matters when some unit is not in Brasília time. */
export function showTimezoneColumn(units: UnitRecord[]): boolean {
  return units.some((u) => u.timezone !== DEFAULT_TIMEZONE);
}

// --- Weekly hours -------------------------------------------------------------

/** The 7 days in order, filling the ones the API did not send as closed. */
export function fullWeek(days: DayHours[]): DayHours[] {
  return [1, 2, 3, 4, 5, 6, 7].map((weekday) => ({
    weekday,
    intervals: (days.find((d) => d.weekday === weekday)?.intervals ?? []).map((i) => ({ ...i })),
  }));
}

/** What is wrong with one day's intervals, or null. Same rules as the API. */
export function dayError(intervals: Interval[]): string | null {
  if (intervals.length > MAX_INTERVALS) return `No máximo ${MAX_INTERVALS} intervalos por dia`;
  const ranges = intervals.map((i) => [toMinutes(i.opens_at), toMinutes(i.closes_at)] as const);
  if (ranges.some(([o, c]) => Number.isNaN(o) || Number.isNaN(c))) return 'Horário inválido';
  if (ranges.some(([o, c]) => o % 5 || c % 5)) return 'Use horários de 5 em 5 minutos';
  if (ranges.some(([o, c]) => o >= c)) return 'O início deve ser antes do fim';
  const sorted = [...ranges].sort((a, b) => a[0] - b[0]);
  for (let i = 1; i < sorted.length; i += 1) {
    if (sorted[i][0] === sorted[i - 1][1]) return 'Junte os intervalos que se encostam';
    if (sorted[i][0] < sorted[i - 1][1]) return 'Os intervalos não podem se sobrepor';
  }
  return null;
}

/** Errors by weekday; empty when the week can be saved. */
export function weekErrors(days: DayHours[]): Record<number, string> {
  const errors: Record<number, string> = {};
  for (const day of days) {
    const error = dayError(day.intervals);
    if (error) errors[day.weekday] = error;
  }
  return errors;
}

/** "Copiar para todos os dias": every day gets the intervals of `weekday`. */
export function copyToAllDays(days: DayHours[], weekday: number): DayHours[] {
  const source = days.find((d) => d.weekday === weekday)?.intervals ?? [];
  return days.map((d) => ({ weekday: d.weekday, intervals: source.map((i) => ({ ...i })) }));
}

/** The week as the API wants it: intervals sorted, every day present. */
export function weekInput(days: DayHours[]): { days: DayHours[] } {
  return {
    days: fullWeek(days).map((d) => ({
      weekday: d.weekday,
      intervals: [...d.intervals].sort((a, b) => toMinutes(a.opens_at) - toMinutes(b.opens_at)),
    })),
  };
}

/** A sensible next interval after the last one (or the default day). */
export function nextInterval(intervals: Interval[]): Interval {
  const last = intervals[intervals.length - 1];
  if (!last) return { opens_at: '09:00', closes_at: '19:00' };
  const start = Math.min(toMinutes(last.closes_at) + 60, 22 * 60);
  return { opens_at: fromMinutes(start), closes_at: fromMinutes(Math.min(start + 120, 23 * 60 + 55)) };
}

// --- Calendar exceptions ------------------------------------------------------

export interface ExceptionForm {
  startsOn: string;
  endsOn: string;
  kind: ExceptionKind;
  opensAt: string;
  closesAt: string;
  reason: string;
  /** Other units to apply the same exception to (only ones the user configures). */
  alsoUnitIds: string[];
}

export type ExceptionErrors = Partial<Record<'period' | 'hours' | 'reason', string>>;

export function emptyExceptionForm(today: string, alsoUnitIds: string[] = []): ExceptionForm {
  return {
    startsOn: today,
    endsOn: today,
    kind: 'closed',
    opensAt: '09:00',
    closesAt: '14:00',
    reason: '',
    alsoUnitIds,
  };
}

export function exceptionToForm(exception: UnitException): ExceptionForm {
  return {
    startsOn: exception.starts_on,
    endsOn: exception.ends_on,
    kind: exception.kind,
    opensAt: exception.opens_at ?? '09:00',
    closesAt: exception.closes_at ?? '14:00',
    reason: exception.reason ?? '',
    alsoUnitIds: [],
  };
}

const DAY_MS = 86_400_000;

export function validateException(form: ExceptionForm, today: string): ExceptionErrors {
  const errors: ExceptionErrors = {};
  if (!form.startsOn || !form.endsOn) errors.period = 'Informe o período';
  else if (form.endsOn < form.startsOn) errors.period = 'A data final deve ser igual ou depois da inicial';
  else if (form.endsOn < today) errors.period = 'Data no passado';
  else if ((Date.parse(form.endsOn) - Date.parse(form.startsOn)) / DAY_MS + 1 > 366)
    errors.period = 'No máximo 366 dias';
  if (form.kind === 'special_hours') {
    const error = dayError([{ opens_at: form.opensAt, closes_at: form.closesAt }]);
    if (error) errors.hours = error;
  }
  if (form.reason.trim().length > 120) errors.reason = 'Motivo muito longo (máximo 120)';
  return errors;
}

/** The POST body: this unit plus the "Aplicar também em" ones, without repeats. */
export function exceptionInput(form: ExceptionForm, unitId: string): UnitExceptionInput {
  const special = form.kind === 'special_hours';
  return {
    unit_ids: [...new Set([unitId, ...form.alsoUnitIds])],
    starts_on: form.startsOn,
    ends_on: form.endsOn,
    kind: form.kind,
    opens_at: special ? form.opensAt : null,
    closes_at: special ? form.closesAt : null,
    reason: form.reason.trim() || null,
  };
}

/** The PATCH body of an existing exception (its unit does not change). */
export function exceptionUpdate(form: ExceptionForm): Omit<UnitExceptionInput, 'unit_ids'> {
  const input: Partial<UnitExceptionInput> = exceptionInput(form, '');
  delete input.unit_ids;
  return input as Omit<UnitExceptionInput, 'unit_ids'>;
}

/** "24/12" or "24/12 a 26/12" (with the year when it is not the current one). */
export function formatPeriod(startsOn: string, endsOn: string, currentYear: number): string {
  const fmt = (iso: string) => {
    const [y, m, d] = iso.split('-');
    return Number(y) === currentYear ? `${d}/${m}` : `${d}/${m}/${y}`;
  };
  return startsOn === endsOn ? fmt(startsOn) : `${fmt(startsOn)} a ${fmt(endsOn)}`;
}

/**
 * Units the user may configure (`unit:configure`): every unit for scope `all`,
 * or for a manager linked to every unit; otherwise the linked ones.
 */
export function configurableUnitIds(
  units: { id: string }[],
  scope: string | null,
  me: { all_units: boolean; units: { id: string }[] },
): string[] {
  if (scope === null) return [];
  if (scope === 'all' || me.all_units) return units.map((u) => u.id);
  const linked = new Set(me.units.map((u) => u.id));
  return units.filter((u) => linked.has(u.id)).map((u) => u.id);
}

/** Suggested holidays: which are already closed in this unit (shown checked and locked). */
export function holidayAlreadyClosed(holiday: Holiday, unitId: string): boolean {
  return holiday.already_closed_unit_ids.includes(unitId);
}

/** The closures to create from the holidays the user ticked (one POST each). */
export function holidayClosures(
  holidays: Holiday[],
  picked: string[],
  unitId: string,
): UnitExceptionInput[] {
  return holidays
    .filter((h) => picked.includes(h.date) && !holidayAlreadyClosed(h, unitId))
    .map((h) => ({
      unit_ids: [unitId],
      starts_on: h.date,
      ends_on: h.date,
      kind: 'closed' as const,
      opens_at: null,
      closes_at: null,
      reason: h.name,
    }));
}
