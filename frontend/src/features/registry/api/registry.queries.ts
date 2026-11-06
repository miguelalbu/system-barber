/** Server state of the registry (TanStack Query, DEC-005). */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { BarberInput, ServiceInput } from '../model/registry.types';
import * as api from './registry.api';

export const registryKeys = {
  barbers: ['registry', 'barbers'] as const,
  services: ['registry', 'services'] as const,
  units: ['registry', 'units'] as const,
  members: ['registry', 'members'] as const,
};

export function useBarbers(enabled = true) {
  return useQuery({ queryKey: registryKeys.barbers, queryFn: api.listBarbers, enabled });
}

export function useServices(enabled = true) {
  return useQuery({ queryKey: registryKeys.services, queryFn: api.listServices, enabled });
}

export function useUnits() {
  return useQuery({ queryKey: registryKeys.units, queryFn: api.listUnits, staleTime: 300_000 });
}

export function useMembers(enabled: boolean) {
  return useQuery({ queryKey: registryKeys.members, queryFn: api.listMembers, enabled });
}

/** Barbers and services change together (the "enabled services" link): refresh both. */
function useInvalidateRegistry() {
  const client = useQueryClient();
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: registryKeys.barbers }),
      client.invalidateQueries({ queryKey: registryKeys.services }),
      client.invalidateQueries({ queryKey: registryKeys.members }),
    ]);
}

interface SaveBarber {
  id: string | null;
  input: BarberInput;
  serviceIds: string[];
}

/** Create or update the barber, then set its services (two calls, one action). */
export function useSaveBarber() {
  const invalidate = useInvalidateRegistry();
  return useMutation({
    mutationFn: async ({ id, input, serviceIds }: SaveBarber) => {
      const barber = id ? await api.updateBarber(id, input) : await api.createBarber(input);
      await api.setBarberServices(barber.id, serviceIds);
      return barber;
    },
    onSettled: invalidate,
  });
}

export function useSetBarberActive() {
  const invalidate = useInvalidateRegistry();
  return useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api.updateBarber(id, { active }),
    onSettled: invalidate,
  });
}

export function useDeleteBarber() {
  const invalidate = useInvalidateRegistry();
  return useMutation({ mutationFn: api.deleteBarber, onSettled: invalidate });
}

export function useSaveService() {
  const invalidate = useInvalidateRegistry();
  return useMutation({
    mutationFn: ({ id, input }: { id: string | null; input: ServiceInput }) =>
      id ? api.updateService(id, input) : api.createService(input),
    onSettled: invalidate,
  });
}

export function useSetServiceActive() {
  const invalidate = useInvalidateRegistry();
  return useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api.updateService(id, { active }),
    onSettled: invalidate,
  });
}

export function useDeleteService() {
  const invalidate = useInvalidateRegistry();
  return useMutation({ mutationFn: api.deleteService, onSettled: invalidate });
}
