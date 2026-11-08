/** Units, opening hours and calendar exceptions (`/tenant/units`, `/tenant/unit-exceptions`). */

export interface UnitRecord {
  id: string;
  name: string;
  timezone: string;
  address: string | null;
  /** E.164. */
  phone: string | null;
  /** Offered to the AI and the public booking link. */
  online_booking: boolean;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UnitInput {
  name: string;
  timezone: string;
  address: string | null;
  phone: string | null;
  online_booking: boolean;
  active: boolean;
}

export interface Interval {
  opens_at: string;
  closes_at: string;
}

/** ISO weekday: 1 = Monday … 7 = Sunday. No interval = closed. */
export interface DayHours {
  weekday: number;
  intervals: Interval[];
}

export interface WeeklyHours {
  unit_id: string;
  days: DayHours[];
  /** Set when the whole week is closed. */
  warning: string | null;
}

export type ExceptionKind = 'closed' | 'special_hours';

export interface UnitException {
  id: string;
  unit_id: string;
  starts_on: string;
  ends_on: string;
  kind: ExceptionKind;
  opens_at: string | null;
  closes_at: string | null;
  reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface UnitExceptionInput {
  unit_ids: string[];
  starts_on: string;
  ends_on: string;
  kind: ExceptionKind;
  opens_at: string | null;
  closes_at: string | null;
  reason: string | null;
}

export interface Holiday {
  date: string;
  name: string;
  already_closed_unit_ids: string[];
}
