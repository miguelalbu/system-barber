/** Authentication endpoints. These are live — no mocks behind them. */

import { request } from './http';

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

interface TokensResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export async function login(email: string, password: string) {
  const tokens = await request<TokensResponse>('/auth/login', {
    method: 'POST',
    body: { email, password },
    anonymous: true,
  });
  return { accessToken: tokens.access_token, refreshToken: tokens.refresh_token };
}

export function fetchMe() {
  return request<Me>('/auth/me');
}

export function logout(refreshToken: string) {
  return request<void>('/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
    anonymous: true,
  });
}

/** Labels for the roles the API returns, for display in the panel. */
export const ROLE_LABELS: Record<UserRole, string> = {
  owner: 'Dono',
  manager: 'Gerente',
  receptionist: 'Recepção',
  barber: 'Barbeiro',
};
