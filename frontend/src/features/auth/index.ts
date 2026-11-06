/** Public API of the auth feature — the only entry point other code may import. */
export { default as LoginScreen } from './pages/LoginScreen';
export { default as AcceptInviteScreen } from './pages/AcceptInviteScreen';
export { default as RequireAuth } from './ui/RequireAuth';
export { AuthProvider, useAuth, useMe } from './model/authContext';
export { UnitSelectionProvider, useUnitSelection } from './model/unitSelection';
export { ROLE_LABELS } from './model/auth.constants';
export type { Me, PermissionScope, TenantStatus, UserRole } from './model/auth.types';
