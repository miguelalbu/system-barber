import type { UserRole } from './auth.types';

/** Labels for the roles the API returns, for display in the panel. */
export const ROLE_LABELS: Record<UserRole, string> = {
  owner: 'Dono',
  manager: 'Gerente',
  receptionist: 'Recepção',
  barber: 'Barbeiro',
};
