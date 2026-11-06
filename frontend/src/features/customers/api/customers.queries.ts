/** Server state of the clients screen (TanStack Query, DEC-005). */

import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { PAGE_SIZE } from '../model/customer.rules';
import type { ClientInput, ClientQuery } from '../model/customers.types';
import * as api from './customers.api';

export const customerKeys = {
  all: ['customers'] as const,
  page: (query: ClientQuery) => ['customers', query] as const,
};

export function useClients(query: ClientQuery) {
  return useQuery({
    queryKey: customerKeys.page(query),
    queryFn: () =>
      api.listClients({
        q: query.q || undefined,
        limit: PAGE_SIZE,
        offset: (query.page - 1) * PAGE_SIZE,
      }),
    // Typing in the search keeps the last page on screen instead of flashing empty.
    placeholderData: keepPreviousData,
  });
}

function useInvalidateClients() {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: customerKeys.all });
}

export function useSaveClient() {
  const invalidate = useInvalidateClients();
  return useMutation({
    mutationFn: ({ id, input }: { id: string | null; input: ClientInput }) =>
      id ? api.updateClient(id, input) : api.createClient(input),
    onSettled: invalidate,
  });
}

export function useSetClientActive() {
  const invalidate = useInvalidateClients();
  return useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => api.updateClient(id, { active }),
    onSettled: invalidate,
  });
}

export function useDeleteClient() {
  const invalidate = useInvalidateClients();
  return useMutation({ mutationFn: api.deleteClient, onSettled: invalidate });
}
