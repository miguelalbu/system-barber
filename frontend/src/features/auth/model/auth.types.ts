/** Session domain types, mirroring `GET /auth/me` (backend `MeOut`). */

export type UserRole = 'owner' | 'manager' | 'receptionist' | 'barber';

/** Reach of a permission, mirroring the backend's Scope enum. */
export type PermissionScope = 'all' | 'unit' | 'own';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  active: boolean;
  last_login_at: string | null;
}

export interface AuthTenant {
  id: string;
  slug: string;
  name: string;
  custom_domain: string | null;
  plan: string;
  status: 'trial' | 'active' | 'suspended' | 'canceled';
  created_at: string;
}

export interface AuthUnit {
  id: string;
  name: string;
  timezone: string;
  active: boolean;
}

export interface Me {
  user: AuthUser;
  tenant: AuthTenant;
  barber_id: string | null;
  units: AuthUnit[];
  all_units: boolean;
  permissions: Record<string, PermissionScope>;
}
