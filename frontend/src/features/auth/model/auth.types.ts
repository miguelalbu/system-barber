/** Session domain types, mirroring `GET /auth/me` (backend `MeOut`). */

/** Operational lifecycle of a shop (backend DEC-013). Only `active` is ever served. */
export type TenantStatus = 'provisioning' | 'active' | 'failed' | 'suspended' | 'archived';

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
  status: TenantStatus;
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

/** A valid invite, as `POST /team/invites/lookup` describes it (backend `InviteLookupOut`). */
export interface InviteLookup {
  name: string;
  email: string;
  role: UserRole;
  expires_at: string;
}
