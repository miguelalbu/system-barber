/** Units, weekly hours, calendar exceptions and suggested holidays (identity, spec S01). */

import { request } from '@/shared/api/http';
import type {
  DayHours,
  Holiday,
  UnitException,
  UnitExceptionInput,
  UnitInput,
  UnitRecord,
  WeeklyHours,
} from '../model/unit.types';

export function listUnitRecords() {
  return request<UnitRecord[]>('/tenant/units');
}

export function createUnit(input: UnitInput) {
  return request<UnitRecord>('/tenant/units', { method: 'POST', body: input });
}

export function updateUnit(id: string, input: Partial<UnitInput>) {
  return request<UnitRecord>(`/tenant/units/${id}`, { method: 'PATCH', body: input });
}

export function deleteUnit(id: string) {
  return request<void>(`/tenant/units/${id}`, { method: 'DELETE' });
}

export function getUnitHours(id: string) {
  return request<WeeklyHours>(`/tenant/units/${id}/hours`);
}

/** Replaces the whole week: a day without intervals is closed. */
export function setUnitHours(id: string, week: { days: DayHours[] }) {
  return request<WeeklyHours>(`/tenant/units/${id}/hours`, { method: 'PUT', body: week });
}

export function listUnitExceptions(unitId: string) {
  return request<UnitException[]>('/tenant/unit-exceptions', { query: { unit_id: unitId } });
}

/** One exception per unit in `unit_ids`, all or nothing. */
export function createUnitExceptions(input: UnitExceptionInput) {
  return request<UnitException[]>('/tenant/unit-exceptions', { method: 'POST', body: input });
}

export function updateUnitException(id: string, input: Partial<Omit<UnitExceptionInput, 'unit_ids'>>) {
  return request<UnitException>(`/tenant/unit-exceptions/${id}`, { method: 'PATCH', body: input });
}

export function deleteUnitException(id: string) {
  return request<void>(`/tenant/unit-exceptions/${id}`, { method: 'DELETE' });
}

export function listHolidays(year: number) {
  return request<Holiday[]>('/tenant/holidays', { query: { year } });
}
