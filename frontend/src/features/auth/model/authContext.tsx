import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { queryClient } from '@/shared/api/queryClient';
import { clearTokens, getTokens, saveTokens } from '@/shared/session/tokens';
import { setTenantSlug } from '@/shared/session/tenant';
import * as authApi from '../api/auth.api';
import type { Me, PermissionScope } from './auth.types';

type Status = 'loading' | 'authenticated' | 'anonymous';

interface AuthContextValue {
  status: Status;
  me: Me | null;
  signIn: (email: string, password: string, tenantSlug?: string) => Promise<void>;
  signOut: () => Promise<void>;
  /** Fetch `/auth/me` again — after a change it reflects (units, the shop's name). */
  reloadMe: () => Promise<void>;
  /** Scope the role has for the permission, or null when it lacks it. */
  can: (permission: string) => PermissionScope | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>('loading');
  const [me, setMe] = useState<Me | null>(null);

  // On boot, a stored token is only a hint — /auth/me is what proves it still
  // works. It also covers the token being revoked while the tab was closed.
  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      if (!getTokens()) {
        setStatus('anonymous');
        return;
      }
      try {
        const profile = await authApi.fetchMe();
        if (cancelled) return;
        setMe(profile);
        setStatus('authenticated');
      } catch {
        if (cancelled) return;
        clearTokens();
        setStatus('anonymous');
      }
    }

    void hydrate();
    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback(async (email: string, password: string, tenantSlug?: string) => {
    // The slug has to be stored before the call: the request interceptor reads
    // it to build the X-Tenant-Slug header.
    if (tenantSlug) setTenantSlug(tenantSlug);

    const tokens = await authApi.login(email, password);
    saveTokens(tokens);

    try {
      const profile = await authApi.fetchMe();
      setMe(profile);
      setStatus('authenticated');
    } catch (error) {
      // Signed in but unable to load the profile — do not leave a half session.
      clearTokens();
      setStatus('anonymous');
      throw error;
    }
  }, []);

  const signOut = useCallback(async () => {
    const tokens = getTokens();
    if (tokens) {
      // Best effort: revoking the refresh token server-side is desirable, but a
      // failure here must not trap the user in a session they asked to leave.
      await authApi.logout(tokens.refreshToken).catch(() => undefined);
    }
    clearTokens();
    // Cached lists belong to this session (and shop): the next login starts clean.
    queryClient.clear();
    setMe(null);
    setStatus('anonymous');
  }, []);

  const reloadMe = useCallback(async () => {
    setMe(await authApi.fetchMe());
  }, []);

  const can = useCallback(
    (permission: string) => me?.permissions[permission] ?? null,
    [me],
  );

  const value = useMemo(
    () => ({ status, me, signIn, signOut, reloadMe, can }),
    [status, me, signIn, signOut, reloadMe, can],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth precisa estar dentro de <AuthProvider>');
  return ctx;
}

/** The signed-in profile, for screens that already run behind RequireAuth. */
export function useMe(): Me {
  const { me } = useAuth();
  if (!me) throw new Error('useMe só pode ser usado em rotas autenticadas');
  return me;
}
