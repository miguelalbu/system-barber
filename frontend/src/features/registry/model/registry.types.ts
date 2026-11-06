/** Registry domain types, mirroring the backend contract (barbers, catalog). */

/** A professional who serves — not a login (backend `BarberOut`). */
export interface Barber {
  id: string;
  name: string;
  initials: string;
  unit_id: string;
  default_commission: number;
  active: boolean;
  /** The linked panel login, if any. */
  user_id: string | null;
  email: string | null;
  created_at: string;
  updated_at: string;
}

export interface BarberInput {
  name: string;
  unit_id: string;
  initials?: string;
  default_commission: number;
  active: boolean;
  user_id: string | null;
}

/** Something the shop sells (backend `ServiceOut`). Money in integer cents. */
export interface Service {
  id: string;
  name: string;
  description: string | null;
  duration_minutes: number;
  price_cents: number;
  active: boolean;
  /** Barbers who perform it. */
  barber_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface ServiceInput {
  name: string;
  description: string | null;
  duration_minutes: number;
  price_cents: number;
  active: boolean;
}

/** A unit the user can see (`GET /tenant/units`). */
export interface Unit {
  id: string;
  name: string;
  active: boolean;
}

/** A panel login (`GET /team`), offered when linking a barber to an existing user. */
export interface Member {
  id: string;
  name: string;
  email: string;
  role: string;
  active: boolean;
  barber_id: string | null;
}
