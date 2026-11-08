import { describe, expect, it } from 'vitest';
import {
  addDays,
  copyMondayToWeekdays,
  dayFormError,
  dayToForm,
  daySummary,
  formToIntervals,
  formatWeeklyHours,
  formsToWeek,
  periodLabel,
  validateTimeOff,
  weekFormErrors,
  weekToForms,
} from '@/features/scheduling/model/schedule.rules';

const i = (starts_at: string, ends_at: string) => ({ starts_at, ends_at });

describe('"expediente + pausas" ↔ intervals', () => {
  it('round-trips a day with lunch', () => {
    const intervals = [i('13:00', '19:00'), i('09:00', '12:00')];
    const form = dayToForm(1, intervals);
    expect(form).toEqual({ weekday: 1, works: true, start: '09:00', end: '19:00', pauses: [{ start: '12:00', end: '13:00' }] });
    expect(formToIntervals(form)).toEqual([i('09:00', '12:00'), i('13:00', '19:00')]);
  });

  it('treats no intervals as a day off, and back', () => {
    const off = dayToForm(7, []);
    expect(off.works).toBe(false);
    expect(formToIntervals(off)).toEqual([]);
  });

  it('two pauses make three intervals', () => {
    const form = { weekday: 2, works: true, start: '08:00', end: '20:00', pauses: [{ start: '15:00', end: '15:30' }, { start: '12:00', end: '13:00' }] };
    expect(formToIntervals(form)).toEqual([i('08:00', '12:00'), i('13:00', '15:00'), i('15:30', '20:00')]);
  });
});

describe('editor validation', () => {
  const day = { weekday: 1, works: true, start: '09:00', end: '19:00', pauses: [] as { start: string; end: string }[] };

  it('mirrors the API', () => {
    expect(dayFormError(day)).toBeNull();
    expect(dayFormError({ ...day, end: '08:00' })).toBe('O início deve ser antes do fim');
    expect(dayFormError({ ...day, start: '09:02' })).toBe('Use horários de 5 em 5 minutos');
    expect(dayFormError({ ...day, pauses: [{ start: '09:00', end: '10:00' }] })).toMatch(/dentro do expediente/);
    expect(dayFormError({ ...day, pauses: [{ start: '12:00', end: '13:00' }, { start: '12:30', end: '14:00' }] })).toMatch(
      /dentro do expediente/,
    );
  });

  it('refuses a week with no working day', () => {
    const allOff = weekToForms([]);
    expect(weekFormErrors(allOff)[0]).toMatch(/registre uma ausência/);
  });

  it('copies Monday to the weekdays only', () => {
    const forms = weekToForms([{ weekday: 1, intervals: [i('10:00', '12:00'), i('13:00', '18:00')] }]);
    const copied = copyMondayToWeekdays(forms);
    expect(formsToWeek(copied).days.filter((d) => d.intervals.length).map((d) => d.weekday)).toEqual([1, 2, 3, 4, 5]);
    copied[1].pauses[0].start = '12:30';
    expect(copied[2].pauses[0].start).toBe('12:00'); // copies, not shared
  });
});

describe('grid and absence labels', () => {
  it('summarizes a day', () => {
    expect(daySummary([i('09:00', '12:00'), i('13:00', '19:00')])).toBe('09:00–19:00 · pausa 12:00–13:00');
    expect(daySummary([])).toBe('Folga');
  });

  it('formats weekly hours', () => {
    expect(formatWeeklyHours(2640)).toBe('44 h');
    expect(formatWeeklyHours(2610)).toBe('43 h 30');
  });

  it('labels a period with its length', () => {
    expect(periodLabel('2026-11-12', '2026-11-26')).toBe('12/11 a 26/11 · 15 dias');
    expect(periodLabel('2026-11-12', '2026-11-12')).toBe('12/11 · 1 dia');
    expect(addDays('2026-12-31', 1)).toBe('2027-01-01');
  });

  it('validates the absence form', () => {
    const form = { barberId: 'b', kind: 'vacation' as const, startsOn: '2026-11-10', endsOn: '2026-11-20', reason: '' };
    expect(validateTimeOff(form, '2026-11-07')).toEqual({});
    expect(validateTimeOff({ ...form, endsOn: '2026-11-09' }, '2026-11-07')).toHaveProperty('period');
    expect(validateTimeOff({ ...form, endsOn: '2027-06-01' }, '2026-11-07').period).toBe('No máximo 180 dias');
    expect(validateTimeOff({ ...form, barberId: '' }, '2026-11-07')).toHaveProperty('barberId');
  });
});
