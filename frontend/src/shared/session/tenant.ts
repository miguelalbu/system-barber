/**
 * Which barbershop the browser is talking to.
 *
 * In production the answer comes from the address bar: each shop is served at
 * `<slug>.navalha.app`, and the backend reads it from the Host header — the
 * frontend does not have to send anything.
 *
 * In development everything runs on `localhost`, where there is no subdomain to
 * read, so the slug is kept here and sent as `X-Tenant-Slug` (a header the API
 * only honours outside production).
 */

const BASE_DOMAIN = import.meta.env.VITE_BASE_DOMAIN ?? 'navalha.local';
const STORAGE_KEY = 'navalha.tenant';

/** The slug in the hostname, or null when there is none (localhost, an IP…). */
export function slugFromHostname(hostname = window.location.hostname): string | null {
  const suffix = `.${BASE_DOMAIN}`;
  if (!hostname.endsWith(suffix)) return null;

  const slug = hostname.slice(0, -suffix.length);
  // Reject nested subdomains: only `central.navalha.app` counts, not `a.b.…`.
  return slug && !slug.includes('.') ? slug : null;
}

/**
 * True when the shop is decided by the address, so the login screen must not
 * ask for it.
 */
export function tenantComesFromHostname(): boolean {
  return slugFromHostname() !== null;
}

export function getTenantSlug(): string | null {
  const fromHost = slugFromHostname();
  if (fromHost) return fromHost;

  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    // Private browsing, or storage blocked by the browser.
    return null;
  }
}

export function setTenantSlug(slug: string): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, slug.trim().toLowerCase());
  } catch {
    /* not fatal: the slug just will not survive a reload */
  }
}

export function clearTenantSlug(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}
