/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL for the PROXIMUS API. Defaults to the `/api` nginx proxy. */
  readonly VITE_API_BASE_URL?: string;
  /** API key sent as `X-API-Key` when the backend is key-protected. */
  readonly VITE_API_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
