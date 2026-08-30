/**
 * Bridge to the backend.
 *
 * While `VITE_API_URL` is unset, the functions below return the demo data from
 * `src/data/app.ts`. Once the backend is up, swap each body for a `request()`
 * call — the screens do not change, because they already consume these types.
 */
import type {
  Appointment,
  Barber,
  BarberOccupancy,
  BarberRecord,
  Kpi,
  Message,
  Thread,
  UpcomingAppointment,
} from '@/types';
import * as mock from '@/data/app';

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  });

  if (!res.ok) {
    throw new ApiError(`${init?.method ?? 'GET'} ${path} falhou`, res.status);
  }

  return (await res.json()) as T;
}

const useMocks = BASE_URL === '';

export const api = {
  async listBarbers(): Promise<Barber[]> {
    return useMocks ? mock.barbers : request<Barber[]>('/api/barbers');
  },

  async listAppointments(_day: string): Promise<Appointment[]> {
    return useMocks ? mock.appointments : request<Appointment[]>(`/api/appointments?day=${_day}`);
  },

  async dashboardKpis(): Promise<Kpi[]> {
    return useMocks ? mock.dashboardKpis : request<Kpi[]>('/api/dashboard/kpis');
  },

  async upcoming(): Promise<UpcomingAppointment[]> {
    return useMocks ? mock.upcoming : request<UpcomingAppointment[]>('/api/dashboard/upcoming');
  },

  async occupancy(): Promise<BarberOccupancy[]> {
    return useMocks ? mock.occupancy : request<BarberOccupancy[]>('/api/dashboard/occupancy');
  },

  async listThreads(): Promise<Thread[]> {
    return useMocks ? mock.threads : request<Thread[]>('/api/threads');
  },

  async listMessages(threadId: string): Promise<Message[]> {
    return useMocks ? mock.messages : request<Message[]>(`/api/threads/${threadId}/messages`);
  },

  async listBarberRecords(): Promise<BarberRecord[]> {
    return useMocks ? mock.barberRecords : request<BarberRecord[]>('/api/staff');
  },
};
