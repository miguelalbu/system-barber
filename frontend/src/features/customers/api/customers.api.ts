/** Client endpoints (backend module `clients`). */

import { request } from '@/shared/api/http';
import type { Client, ClientInput, ClientPage } from '../model/customers.types';

export function listClients(params: { q?: string; limit: number; offset: number }) {
  return request<ClientPage>('/clients', { query: params });
}

export function createClient(input: ClientInput) {
  return request<Client>('/clients', { method: 'POST', body: input });
}

export function updateClient(id: string, input: Partial<ClientInput>) {
  return request<Client>(`/clients/${id}`, { method: 'PATCH', body: input });
}

export function deleteClient(id: string) {
  return request<void>(`/clients/${id}`, { method: 'DELETE' });
}
