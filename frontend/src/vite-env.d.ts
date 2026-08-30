/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** API base URL. Unset uses the Vite proxy at /api. */
  readonly VITE_API_URL?: string;
  /** Domain the shop slug is read from: <slug>.<VITE_BASE_DOMAIN>. */
  readonly VITE_BASE_DOMAIN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
