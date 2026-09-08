// Base-path support for OCI Hosted Deployments.
//
// The app may be served under a runtime-unknown prefix like
//   /20251112/hostedApplications/<OCID>/actions/invoke
// OCI strips that prefix before forwarding to the container (the app serves at
// root internally), so we DON'T use Next's build-time `basePath`. Instead the
// browser must keep the prefix on every absolute URL it emits.
//
// The placeholder below is baked into the production bundle and rewritten at
// container startup by entrypoint.sh (sed) with the real prefix (from the
// reserved APPLICATION_BASE_URL env var). It MUST stay inside a template literal
// (`${...}`) and never be passed through a foldable expression like
// String.includes, or the minifier could evaluate it away at build time and the
// sed would have nothing to replace.
//
// In dev (`next dev`) the entrypoint doesn't run and in a root deployment the
// prefix is empty, so BASE is "" and every helper here is a no-op.
//
// Coverage map — what prefixes paths in each case:
//   <Image>/fonts/CSS ....... Next assetPrefix + custom image loader (automatic)
//   fetch('/api/...') ....... global patch in components/BasePathInit.js
//   router.push/replace ..... useBaseRouter (lib/useBaseRouter.js)
//   workers / window.location / raw <a>/<img> hrefs ..... withBase() below
const isProd = process.env.NODE_ENV === "production";

export const BASE = isProd ? "/__BASE_PATH_PLACEHOLDER__" : "";

/** Prepend the deployment base path to a root-absolute app path. */
export const withBase = (path) => `${BASE}${path}`;
