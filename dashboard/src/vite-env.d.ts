/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  // When set, the dashboard calls GoldRush directly from the browser (CORS is
  // open) and needs no backend. The key ships in the bundle — use a scoped /
  // rotatable key for public deploys.
  readonly VITE_GOLDRUSH_API_KEY?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
