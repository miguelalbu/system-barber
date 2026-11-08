/** Barber schedules, special shifts and time off (scheduling, spec S02). */

import { request } from '@/shared/api/http';
import type {
  BarberRef,
  BarberSchedule,
  ShiftOverride,
  TimeOff,
  TimeOffInput,
  TimeOffResult,
  WorkDay,
  WorkInterval,
} from '../model/schedule.types';

export function listSchedules(unitId: string | null) {
  return request<BarberSchedule[]>('/schedules', { query: { unit_id: unitId } });
}

export function setSchedule(barberId: string, week: { days: WorkDay[] }) {
  return request<BarberSchedule>(`/barbers/${barberId}/schedule`, { method: 'PUT', body: week });
}

export function listShiftOverrides(barberId: string) {
  return request<ShiftOverride[]>(`/barbers/${barberId}/shift-overrides`);
}

export function setShiftOverride(barberId: string, date: string, intervals: WorkInterval[], reason: string | null) {
  return request<ShiftOverride>(`/barbers/${barberId}/shift-overrides/${date}`, {
    method: 'PUT',
    body: { intervals, reason },
  });
}

export function deleteShiftOverride(barberId: string, date: string) {
  return request<void>(`/barbers/${barberId}/shift-overrides/${date}`, { method: 'DELETE' });
}

export function listTimeOff(params: { from: string; to: string; unitId: string | null }) {
  return request<TimeOff[]>('/time-off', {
    query: { from: params.from, to: params.to, unit_id: params.unitId },
  });
}

export function createTimeOff(input: TimeOffInput) {
  return request<TimeOffResult>('/time-off', { method: 'POST', body: input });
}

export function updateTimeOff(id: string, input: Partial<Omit<TimeOffInput, 'barber_id' | 'kind'>>) {
  return request<TimeOffResult>(`/time-off/${id}`, { method: 'PATCH', body: input });
}

export function deleteTimeOff(id: string) {
  return request<void>(`/time-off/${id}`, { method: 'DELETE' });
}

/** Names of the barbers (needs `team:read`). */
export function listBarberRefs() {
  return request<BarberRef[]>('/barbers');
}
