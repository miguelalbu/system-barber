/** Server state of the Units page (TanStack Query). */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/features/auth';
import type { DayHours, UnitExceptionInput, UnitInput } from '../model/unit.types';
import { registryKeys } from './registry.queries';
import * as api from './units.api';

export const unitKeys = {
  records: ['registry', 'units', 'records'] as const,
  hours: (unitId: string) => ['registry', 'units', unitId, 'hours'] as const,
  exceptions: (unitId: string) => ['registry', 'unit-exceptions', unitId] as const,
  allExceptions: ['registry', 'unit-exceptions'] as const,
  holidays: (year: number) => ['registry', 'holidays', year] as const,
};

export function useUnitRecords() {
  return useQuery({ queryKey: unitKeys.records, queryFn: api.listUnitRecords });
}

export function useUnitHours(unitId: string) {
  return useQuery({ queryKey: unitKeys.hours(unitId), queryFn: () => api.getUnitHours(unitId) });
}

export function useUnitExceptions(unitId: string) {
  return useQuery({
    queryKey: unitKeys.exceptions(unitId),
    queryFn: () => api.listUnitExceptions(unitId),
  });
}

export function useHolidays(year: number, enabled: boolean) {
  return useQuery({
    queryKey: unitKeys.holidays(year),
    queryFn: () => api.listHolidays(year),
    enabled,
  });
}

/**
 * Units feed other screens too: the barbers' unit select (`registryKeys.units`)
 * and the sidebar unit switcher (`/auth/me`). Refresh all of them.
 */
function useInvalidateUnits() {
  const client = useQueryClient();
  const { reloadMe } = useAuth();
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: unitKeys.records }),
      client.invalidateQueries({ queryKey: registryKeys.units }),
      reloadMe().catch(() => undefined),
    ]);
}

export function useSaveUnit() {
  const invalidate = useInvalidateUnits();
  return useMutation({
    mutationFn: ({ id, input }: { id: string | null; input: Partial<UnitInput> }) =>
      id ? api.updateUnit(id, input) : api.createUnit(input as UnitInput),
    onSettled: invalidate,
  });
}

export function useDeleteUnit() {
  const invalidate = useInvalidateUnits();
  return useMutation({ mutationFn: api.deleteUnit, onSettled: invalidate });
}

export function useSaveUnitHours(unitId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (week: { days: DayHours[] }) => api.setUnitHours(unitId, week),
    onSuccess: (saved) => client.setQueryData(unitKeys.hours(unitId), saved),
  });
}

/** Exceptions can be created for several units at once: refresh every unit's list. */
function useInvalidateExceptions() {
  const client = useQueryClient();
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: unitKeys.allExceptions }),
      client.invalidateQueries({ queryKey: ['registry', 'holidays'] }),
    ]);
}

export function useCreateUnitExceptions() {
  const invalidate = useInvalidateExceptions();
  return useMutation({
    mutationFn: (input: UnitExceptionInput) => api.createUnitExceptions(input),
    onSettled: invalidate,
  });
}

/** Several holidays at once: one POST per date, then one refresh. */
export function useCreateHolidayClosures() {
  const invalidate = useInvalidateExceptions();
  return useMutation({
    mutationFn: async (inputs: UnitExceptionInput[]) => {
      for (const input of inputs) await api.createUnitExceptions(input);
    },
    onSettled: invalidate,
  });
}

export function useUpdateUnitException() {
  const invalidate = useInvalidateExceptions();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<Omit<UnitExceptionInput, 'unit_ids'>> }) =>
      api.updateUnitException(id, input),
    onSettled: invalidate,
  });
}

export function useDeleteUnitException() {
  const invalidate = useInvalidateExceptions();
  return useMutation({ mutationFn: api.deleteUnitException, onSettled: invalidate });
}
