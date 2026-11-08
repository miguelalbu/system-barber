/** Barber schedules, special shifts and time off (`/schedules`, `/time-off`, spec S02). */

export interface WorkInterval {
  starts_at: string;
  ends_at: string;
}

export interface WorkDay {
  /** ISO: 1 = Monday … 7 = Sunday. */
  weekday: number;
  intervals: WorkInterval[];
}

export interface BarberSchedule {
  barber_id: string;
  unit_id: string;
  /** False: nothing saved, the unit's hours apply. */
  configured: boolean;
  days: WorkDay[];
  weekly_minutes: number;
  warnings: string[];
}

export interface ShiftOverride {
  barber_id: string;
  date: string;
  intervals: WorkInterval[];
  reason: string | null;
  warnings: string[];
}

export type TimeOffKind = 'day_off' | 'vacation' | 'sick_leave' | 'block';

export interface TimeOff {
  id: string;
  barber_id: string;
  kind: TimeOffKind;
  all_day: boolean;
  starts_at: string;
  ends_at: string;
  starts_on: string;
  ends_on: string;
  reason: string | null;
  created_by_user_id: string | null;
  created_at: string;
}

export interface TimeOffInput {
  barber_id: string;
  kind: TimeOffKind;
  starts_on?: string;
  ends_on?: string;
  starts_at?: string;
  ends_at?: string;
  reason?: string | null;
}

export interface AffectedAppointment {
  id: string;
  starts_at: string;
  client_name: string;
}

export interface TimeOffResult {
  time_off: TimeOff;
  affected_appointments: AffectedAppointment[];
}

/** Minimal barber row for names (`GET /barbers`). */
export interface BarberRef {
  id: string;
  name: string;
  unit_id: string;
  active: boolean;
}
