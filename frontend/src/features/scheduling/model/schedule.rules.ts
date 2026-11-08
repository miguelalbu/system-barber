/**
 * Pure rules of the schedule screens (spec S02). The API keeps a day as
 * intervals (lunch = the gap); the editor shows "start, end and pauses".
 */

import { fromMinutes, toMinutes } from '@/shared/text/time';
import type { TimeOffKind, WorkDay, WorkInterval } from './schedule.types';

export const WEEKDAYS: { weekday: number; short: string; label: string }[] = [
  { weekday: 1, short: 'Seg', label: 'Segunda' },
  { weekday: 2, short: 'Ter', label: 'Terça' },
  { weekday: 3, short: 'Qua', label: 'Quarta' },
  { weekday: 4, short: 'Qui', label: 'Quinta' },
  { weekday: 5, short: 'Sex', label: 'Sexta' },
  { weekday: 6, short: 'Sáb', label: 'Sábado' },
  { weekday: 7, short: 'Dom', label: 'Domingo' },
];

export const MAX_PAUSES = 2;

export interface Pause {
  start: string;
  end: string;
}

export interface DayForm {
  weekday: number;
  works: boolean;
  start: string;
  end: string;
  pauses: Pause[];
}

/** Intervals → "works from start to end, with these pauses". */
export function dayToForm(weekday: number, intervals: WorkInterval[]): DayForm {
  if (!intervals.length) return { weekday, works: false, start: '09:00', end: '19:00', pauses: [] };
  const sorted = [...intervals].sort((a, b) => toMinutes(a.starts_at) - toMinutes(b.starts_at));
  const pauses: Pause[] = [];
  for (let i = 1; i < sorted.length; i += 1) {
    pauses.push({ start: sorted[i - 1].ends_at, end: sorted[i].starts_at });
  }
  return { weekday, works: true, start: sorted[0].starts_at, end: sorted[sorted.length - 1].ends_at, pauses };
}

/** The form back to intervals (empty when off). Assumes `dayFormError` is null. */
export function formToIntervals(day: DayForm): WorkInterval[] {
  if (!day.works) return [];
  const cuts = [...day.pauses].sort((a, b) => toMinutes(a.start) - toMinutes(b.start));
  const out: WorkInterval[] = [];
  let cursor = day.start;
  for (const pause of cuts) {
    out.push({ starts_at: cursor, ends_at: pause.start });
    cursor = pause.end;
  }
  out.push({ starts_at: cursor, ends_at: day.end });
  return out;
}

/** What is wrong with a day of the editor, or null (mirrors the API). */
export function dayFormError(day: DayForm): string | null {
  if (!day.works) return null;
  const start = toMinutes(day.start);
  const end = toMinutes(day.end);
  const times = [start, end, ...day.pauses.flatMap((p) => [toMinutes(p.start), toMinutes(p.end)])];
  if (times.some(Number.isNaN)) return 'Horário inválido';
  if (times.some((t) => t % 5)) return 'Use horários de 5 em 5 minutos';
  if (start >= end) return 'O início deve ser antes do fim';
  if (day.pauses.length > MAX_PAUSES) return `No máximo ${MAX_PAUSES} pausas`;
  const pauses = [...day.pauses].map((p) => [toMinutes(p.start), toMinutes(p.end)] as const).sort((a, b) => a[0] - b[0]);
  let previousEnd = start;
  for (const [ps, pe] of pauses) {
    if (ps >= pe) return 'A pausa deve começar antes de terminar';
    if (ps <= previousEnd || pe >= end) return 'A pausa precisa ficar dentro do expediente, sem encostar no início ou fim';
    previousEnd = pe;
  }
  return null;
}

export function weekToForms(days: WorkDay[]): DayForm[] {
  return WEEKDAYS.map(({ weekday }) => dayToForm(weekday, days.find((d) => d.weekday === weekday)?.intervals ?? []));
}

export function formsToWeek(forms: DayForm[]): { days: WorkDay[] } {
  return { days: forms.map((f) => ({ weekday: f.weekday, intervals: formToIntervals(f) })) };
}

export function weekFormErrors(forms: DayForm[]): Record<number, string> {
  const errors: Record<number, string> = {};
  for (const f of forms) {
    const e = dayFormError(f);
    if (e) errors[f.weekday] = e;
  }
  if (!forms.some((f) => f.works)) {
    errors[0] = 'Para afastar o barbeiro, registre uma ausência ou inative o cadastro';
  }
  return errors;
}

/** "Copiar segunda para dias úteis": Tuesday to Friday get Monday's day. */
export function copyMondayToWeekdays(forms: DayForm[]): DayForm[] {
  const monday = forms.find((f) => f.weekday === 1);
  if (!monday) return forms;
  return forms.map((f) =>
    f.weekday >= 2 && f.weekday <= 5 ? { ...monday, weekday: f.weekday, pauses: monday.pauses.map((p) => ({ ...p })) } : f,
  );
}

/** Grid cell: "09:00–19:00 · pausa 12:00–13:00", or "Folga". */
export function daySummary(intervals: WorkInterval[]): string {
  if (!intervals.length) return 'Folga';
  const form = dayToForm(1, intervals);
  const head = `${form.start}–${form.end}`;
  if (!form.pauses.length) return head;
  const pauses = form.pauses.map((p) => `${p.start}–${p.end}`).join(', ');
  return `${head} · ${form.pauses.length > 1 ? 'pausas' : 'pausa'} ${pauses}`;
}

/** 2640 → "44 h"; 2610 → "43 h 30". */
export function formatWeeklyHours(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h} h ${String(m).padStart(2, '0')}` : `${h} h`;
}

export const TIME_OFF_LABELS: Record<TimeOffKind, string> = {
  day_off: 'Folga',
  vacation: 'Férias',
  sick_leave: 'Atestado',
  block: 'Bloqueio',
};

const DAY_MS = 86_400_000;

/** Inclusive number of days between two ISO dates. */
export function daysBetween(startsOn: string, endsOn: string): number {
  return Math.round((Date.parse(endsOn) - Date.parse(startsOn)) / DAY_MS) + 1;
}

/** "12/11 a 26/11 · 15 dias", or "12/11 · 1 dia". */
export function periodLabel(startsOn: string, endsOn: string): string {
  const fmt = (iso: string) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;
  const n = daysBetween(startsOn, endsOn);
  const range = startsOn === endsOn ? fmt(startsOn) : `${fmt(startsOn)} a ${fmt(endsOn)}`;
  return `${range} · ${n} ${n === 1 ? 'dia' : 'dias'}`;
}

export interface TimeOffForm {
  barberId: string;
  kind: Exclude<TimeOffKind, 'block'>;
  startsOn: string;
  endsOn: string;
  reason: string;
}

export function validateTimeOff(form: TimeOffForm, today: string): Partial<Record<'barberId' | 'period' | 'reason', string>> {
  const errors: Partial<Record<'barberId' | 'period' | 'reason', string>> = {};
  if (!form.barberId) errors.barberId = 'Escolha o barbeiro';
  if (!form.startsOn || !form.endsOn) errors.period = 'Informe o período';
  else if (form.endsOn < form.startsOn) errors.period = 'O último dia deve ser igual ou depois do primeiro';
  else if (form.endsOn < today) errors.period = 'Período no passado';
  else if (daysBetween(form.startsOn, form.endsOn) > 180) errors.period = 'No máximo 180 dias';
  if (form.reason.trim().length > 200) errors.reason = 'Motivo muito longo (máximo 200)';
  return errors;
}

/** Shift override form: one interval with an optional pause. */
export function overrideIntervals(start: string, end: string, pause: Pause | null): WorkInterval[] {
  return formToIntervals({ weekday: 1, works: true, start, end, pauses: pause ? [pause] : [] });
}

/** ISO date `days` after `iso` (local, no timezone drift). */
export function addDays(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number);
  const date = new Date(Date.UTC(y, m - 1, d + days));
  return date.toISOString().slice(0, 10);
}

export { fromMinutes };
