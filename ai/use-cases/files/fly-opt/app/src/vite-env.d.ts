/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CUOPT_ENDPOINT: string;
  readonly VITE_OCI_GENAI_ENDPOINT: string;
  readonly VITE_OCI_GENAI_MODEL_ID: string;
  readonly VITE_OCI_COMPARTMENT_ID: string;
  readonly VITE_APP_TITLE: string;
  readonly VITE_PARALLEL_MAX_JOBS: string;
  readonly VITE_DEFAULT_SOLVE_TIMEOUT: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
