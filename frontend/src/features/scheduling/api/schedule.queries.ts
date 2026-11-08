/** Server state of the schedule screens (TanStack Query). */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { TimeOffInput, WorkDay, WorkInterval } from '../model/schedule.types';
import * as api from './schedule.api';

export const scheduleKeys = {
  schedules: (unitId: string | null) => ['schedules', unitId] as const,
  allSchedules: ['schedules'] as const,
  overrides: (barberId: string) => ['shift-overrides', barberId] as const,
  timeOff: (unitId: string | null, from: string, to: string) => ['time-off', unitId, from, to] as const,
  allTimeOff: ['time-off'] as const,
  barbers: ['scheduling', 'barbers'] as const,
};

export function useSchedules(unitId: string | null) {
  return useQuery({ queryKey: scheduleKeys.schedules(unitId), queryFn: () => api.listSchedules(unitId) });
}

export function useBarberRefs(enabled: boolean) {
  return useQuery({ queryKey: scheduleKeys.barbers, queryFn: api.listBarberRefs, enabled, staleTime: 60_000 });
}

export function useShiftOverrides(barberId: string) {
  return useQuery({ queryKey: scheduleKeys.overrides(barberId), queryFn: () => api.listShiftOverrides(barberId) });
}

export function useTimeOff(unitId: string | null, from: string, to: string) {
  return useQuery({
    queryKey: scheduleKeys.timeOff(unitId, from, to),
    queryFn: () => api.listTimeOff({ from, to, unitId }),
  });
}

export function useSaveSchedule() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ barberId, week }: { barberId: string; week: { days: WorkDay[] } }) => api.setSchedule(barberId, week),
    onSettled: () => client.invalidateQueries({ queryKey: scheduleKeys.allSchedules }),
  });
}

export function useSaveShiftOverride(barberId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ date, intervals, reason }: { date: string; intervals: WorkInterval[]; reason: string | null }) =>
      api.setShiftOverride(barberId, date, intervals, reason),
    onSettled: () => client.invalidateQueries({ queryKey: scheduleKeys.overrides(barberId) }),
  });
}

export function useDeleteShiftOverride(barberId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (date: string) => api.deleteShiftOverride(barberId, date),
    onSettled: () => client.invalidateQueries({ queryKey: scheduleKeys.overrides(barberId) }),
  });
}

export function useSaveTimeOff() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string | null; input: TimeOffInput }) =>
      id
        ? api.updateTimeOff(id, { starts_on: input.starts_on, ends_on: input.ends_on, reason: input.reason })
        : api.createTimeOff(input),
    onSettled: () => client.invalidateQueries({ queryKey: scheduleKeys.allTimeOff }),
  });
}

export function useDeleteTimeOff() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.deleteTimeOff,
    onSettled: () => client.invalidateQueries({ queryKey: scheduleKeys.allTimeOff }),
  });
}
