import { describe, expect, it } from 'vitest';
import {
  configurableUnitIds,
  copyToAllDays,
  dayError,
  exceptionInput,
  emptyExceptionForm,
  fullWeek,
  holidayClosures,
  validateException,
  validateUnit,
  emptyUnitForm,
  unitInput,
  weekErrors,
  weekInput,
} from '@/features/registry/model/unit.rules';
import type { DayHours, Holiday } from '@/features/registry/model/unit.types';
import { FIVE_MINUTE_TIMES, fromMinutes, toMinutes } from '@/shared/text/time';

const i = (opens_at: string, closes_at: string) => ({ opens_at, closes_at });

describe('HH:MM ↔ minutes', () => {
  it('converts both ways and rejects garbage', () => {
    expect(toMinutes('09:30')).toBe(570);
    expect(toMinutes('9:05')).toBe(545);
    expect(fromMinutes(570)).toBe('09:30');
    expect(Number.isNaN(toMinutes('24:00'))).toBe(true);
    expect(Number.isNaN(toMinutes('nove'))).toBe(true);
    expect(FIVE_MINUTE_TIMES).toHaveLength(288);
    expect(FIVE_MINUTE_TIMES[FIVE_MINUTE_TIMES.length - 1]).toBe('23:55');
  });
});

describe('weekly hours editor', () => {
  it('accepts a split day and a closed day', () => {
    expect(dayError([i('13:00', '19:00'), i('09:00', '12:00')])).toBeNull();
    expect(dayError([])).toBeNull();
  });

  it('mirrors the API rules', () => {
    expect(dayError([i('09:00', '12:00'), i('12:00', '13:00')])).toBe('Junte os intervalos que se encostam');
    expect(dayError([i('09:00', '12:00'), i('11:00', '13:00')])).toBe('Os intervalos não podem se sobrepor');
    expect(dayError([i('12:00', '09:00')])).toBe('O início deve ser antes do fim');
    expect(dayError([i('09:03', '12:00')])).toBe('Use horários de 5 em 5 minutos');
    expect(dayError([i('08:00', '09:00'), i('10:00', '11:00'), i('12:00', '13:00'), i('14:00', '15:00')])).toMatch(
      /No máximo 3/,
    );
  });

  it('copies one day to all and fills missing days as closed', () => {
    const week = fullWeek([{ weekday: 2, intervals: [i('10:00', '18:00')] }]);
    expect(week).toHaveLength(7);
    expect(week[0].intervals).toEqual([]);
    const copied = copyToAllDays(week, 2);
    expect(copied.every((d) => d.intervals[0].opens_at === '10:00')).toBe(true);
    copied[0].intervals[0].opens_at = '11:00'; // copies, not shared references
    expect(copied[1].intervals[0].opens_at).toBe('10:00');
  });

  it('reports errors by weekday and sorts intervals for the API', () => {
    const days: DayHours[] = fullWeek([{ weekday: 1, intervals: [i('13:00', '19:00'), i('09:00', '12:00')] }]);
    expect(weekErrors(days)).toEqual({});
    expect(weekInput(days).days[0].intervals.map((x) => x.opens_at)).toEqual(['09:00', '13:00']);
    expect(weekErrors(fullWeek([{ weekday: 3, intervals: [i('10:00', '09:00')] }]))).toHaveProperty('3');
  });
});

describe('unit form', () => {
  it('validates and builds the body', () => {
    expect(validateUnit({ ...emptyUnitForm(), name: 'X' })).toHaveProperty('name');
    expect(validateUnit({ ...emptyUnitForm(), name: 'Centro', phone: '12' })).toHaveProperty('phone');
    expect(unitInput({ ...emptyUnitForm(), name: ' Centro ', address: ' ', phone: '' })).toMatchObject({
      name: 'Centro',
      address: null,
      phone: null,
      timezone: 'America/Sao_Paulo',
    });
  });
});

describe('special dates', () => {
  const today = '2026-11-06';

  it('validates the period and the special hours', () => {
    const form = emptyExceptionForm(today);
    expect(validateException(form, today)).toEqual({});
    expect(validateException({ ...form, endsOn: '2026-11-05' }, today)).toHaveProperty('period');
    expect(validateException({ ...form, startsOn: '2026-11-01', endsOn: '2026-11-02' }, today).period).toBe(
      'Data no passado',
    );
    expect(validateException({ ...form, kind: 'special_hours', opensAt: '14:00', closesAt: '09:00' }, today)).toHaveProperty(
      'hours',
    );
  });

  it('applies to the other units picked, without repeats', () => {
    const form = { ...emptyExceptionForm(today, ['b', 'a']), reason: ' Reforma ' };
    const body = exceptionInput(form, 'a');
    expect(body.unit_ids).toEqual(['a', 'b']);
    expect(body.reason).toBe('Reforma');
    expect(body.opens_at).toBeNull(); // closed day: no hours
  });

  it('offers only the units the user configures', () => {
    const units = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];
    expect(configurableUnitIds(units, 'all', { all_units: false, units: [] })).toEqual(['a', 'b', 'c']);
    expect(configurableUnitIds(units, 'unit', { all_units: false, units: [{ id: 'b' }] })).toEqual(['b']);
    expect(configurableUnitIds(units, 'unit', { all_units: true, units: [] })).toEqual(['a', 'b', 'c']);
    expect(configurableUnitIds(units, null, { all_units: true, units: [] })).toEqual([]);
  });

  it('turns the ticked holidays into closures, skipping the ones already closed', () => {
    const holidays: Holiday[] = [
      { date: '2027-12-25', name: 'Natal', already_closed_unit_ids: [] },
      { date: '2027-11-02', name: 'Finados', already_closed_unit_ids: ['u1'] },
      { date: '2027-09-07', name: 'Independência do Brasil', already_closed_unit_ids: [] },
    ];
    const closures = holidayClosures(holidays, ['2027-12-25', '2027-11-02'], 'u1');
    expect(closures).toHaveLength(1);
    expect(closures[0]).toMatchObject({ unit_ids: ['u1'], starts_on: '2027-12-25', kind: 'closed', reason: 'Natal' });
  });
});
