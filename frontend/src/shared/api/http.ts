/**
 * HTTP client for the Core API.
 *
 * Handles the three things every call needs: the tenant header in development,
 * the bearer token, and renewing that token when it expires mid-session.
 */

import { getTenantSlug } from '@/shared/session/tenant';
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from '@/shared/session/tokens';

// Default goes through the Vite proxy, which strips the prefix and keeps the
// call same-origin. Point VITE_API_URL at the API to bypass the proxy.
const BASE_URL = import.meta.env.VITE_API_URL ?? '/api';

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/** Thrown when the network is unreachable — the API never answered. */
export class NetworkError extends Error {
  constructor() {
    super('Não foi possível falar com o servidor');
    this.name = 'NetworkError';
  }
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  /** Skip the Authorization header (login, refresh). */
  anonymous?: boolean;
  /** Internal: prevents a refresh loop when the refresh call itself fails. */
  retrying?: boolean;
}

function buildHeaders(options: RequestOptions): Headers {
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');

  // On a real subdomain the API reads the tenant from the Host header and
  // ignores this one; on localhost it is the only way to say which shop.
  const slug = getTenantSlug();
  if (slug) headers.set('X-Tenant-Slug', slug);

  if (!options.anonymous) {
    const token = getAccessToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }

  return headers;
}

async function errorFrom(response: Response): Promise<ApiError> {
  let detail = `Erro ${response.status}`;
  try {
    const body = await response.json();
    // FastAPI answers with {detail}; a validation error makes it a list.
    if (typeof body?.detail === 'string') {
      detail = body.detail;
    } else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
      detail = body.detail[0].msg;
    }
  } catch {
    /* no JSON body — keep the generic message */
  }
  return new ApiError(detail, response.status);
}

// A single in-flight refresh, shared by every call that got a 401 at once.
// Without this, five parallel requests would burn five refresh tokens, and
// rotation would invalidate four of them.
let refreshInFlight: Promise<boolean> | null = null;

async function runRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const tokens = await request<{ access_token: string; refresh_token: string }>(
      '/auth/refresh',
      { method: 'POST', body: { refresh_token: refreshToken }, anonymous: true, retrying: true },
    );
    saveTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

function refreshSession(): Promise<boolean> {
  refreshInFlight ??= runRefresh().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, anonymous, retrying, ...init } = options;

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: buildHeaders({ ...options, anonymous }),
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new NetworkError();
  }

  // The access token lives 15 minutes, so an expired one is routine rather than
  // an error: renew it once and replay the call.
  if (response.status === 401 && !anonymous && !retrying) {
    const renewed = await refreshSession();
    if (renewed) {
      return request<T>(path, { ...options, retrying: true });
    }
  }

  if (!response.ok) {
    throw await errorFrom(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
