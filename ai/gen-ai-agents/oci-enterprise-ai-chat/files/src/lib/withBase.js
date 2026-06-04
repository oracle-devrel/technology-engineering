// Prefixes a path with the placeholder that the container entrypoint
// rewrites at startup using the BASE_PATH env var. Use this only for
// assets that don't go through Next's asset pipeline (e.g. web workers,
// raw fetch calls). For <img>/<Image>/fonts/CSS, Next handles the prefix
// automatically via assetPrefix or the custom image loader.
//
// In dev (`next dev`) the entrypoint doesn't run, so we return the path
// as-is to keep local dev working against localhost.
const isProd = process.env.NODE_ENV === 'production';

export const withBase = (path) => (isProd ? `/__BASE_PATH_PLACEHOLDER__${path}` : path);
