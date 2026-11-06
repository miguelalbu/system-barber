/** Registry endpoints: barbers (identity), services and barber ↔ service links (catalog). */

import { request } from '@/shared/api/http';
import type {
  Barber,
  BarberInput,
  Member,
  Service,
  ServiceInput,
  Unit,
} from '../model/registry.types';

export function listBarbers() {
  return request<Barber[]>('/barbers');
}

export function createBarber(input: BarberInput) {
  return request<Barber>('/barbers', { method: 'POST', body: input });
}

export function updateBarber(id: string, input: Partial<BarberInput>) {
  return request<Barber>(`/barbers/${id}`, { method: 'PATCH', body: input });
}

export function deleteBarber(id: string) {
  return request<void>(`/barbers/${id}`, { method: 'DELETE' });
}

/** Replaces the whole set of services the barber performs. */
export function setBarberServices(barberId: string, serviceIds: string[]) {
  return request<Service[]>(`/barbers/${barberId}/services`, {
    method: 'PUT',
    body: { service_ids: serviceIds },
  });
}

export function listServices() {
  return request<Service[]>('/services');
}

export function createService(input: ServiceInput) {
  return request<Service>('/services', { method: 'POST', body: input });
}

export function updateService(id: string, input: Partial<ServiceInput>) {
  return request<Service>(`/services/${id}`, { method: 'PATCH', body: input });
}

export function deleteService(id: string) {
  return request<void>(`/services/${id}`, { method: 'DELETE' });
}

export function listUnits() {
  return request<Unit[]>('/tenant/units');
}

export function listMembers() {
  return request<Member[]>('/team');
}
