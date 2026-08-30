/**
 * Session token storage.
 *
 * The API returns both tokens in the response body, so the browser has to hold
 * them somewhere. localStorage is what survives a reload, and it is readable by
 * any script on the page — so this is only as safe as the app is free of XSS.
 *
 * The stronger shape is a refresh token in an httpOnly cookie with the access
 * token kept in memory, and that is where this should end up; it needs the API
 * to set the cookie, so it is a backend change too. See README, "Pendências".
 */

const ACCESS_KEY = 'navalha.access_token';
const REFRESH_KEY = 'navalha.refresh_token';

export interface SessionTokens {
  accessToken: string;
  refreshToken: string;
}

function read(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function getTokens(): SessionTokens | null {
  const accessToken = read(ACCESS_KEY);
  const refreshToken = read(REFRESH_KEY);
  if (!accessToken || !refreshToken) return null;
  return { accessToken, refreshToken };
}

export function getAccessToken(): string | null {
  return read(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return read(REFRESH_KEY);
}

export function saveTokens(tokens: SessionTokens): void {
  try {
    window.localStorage.setItem(ACCESS_KEY, tokens.accessToken);
    window.localStorage.setItem(REFRESH_KEY, tokens.refreshToken);
  } catch {
    /* storage blocked: the session simply will not survive a reload */
  }
}

export function clearTokens(): void {
  try {
    window.localStorage.removeItem(ACCESS_KEY);
    window.localStorage.removeItem(REFRESH_KEY);
  } catch {
    /* ignore */
  }
}
