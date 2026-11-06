/** Scheduling domain types. Mirror what the backend scheduling module will expose. */

export type AppointmentStatus = 'confirmado' | 'pendente' | 'concluido' | 'cancelado';

export interface Barber {
  id: string;
  name: string;
  initials: string;
  /** Working window for the day, e.g. "09:00–19:00". */
  shift: string;
}

export interface Appointment {
  id: string;
  barberId: string;
  /** "HH:MM" */
  start: string;
  /** "HH:MM" */
  end: string;
  client: string;
  service: string;
  status: AppointmentStatus;
  /** Created by the automated WhatsApp assistant. */
  fromAi?: boolean;
}

/** Who started the booking: the WhatsApp assistant or the front desk. */
export type AppointmentOrigin = 'ia' | 'manual';

/** Calendar demo states, until the backend is wired in. */
export type AgendaDemoState = 'normal' | 'vazio' | 'conflito';
