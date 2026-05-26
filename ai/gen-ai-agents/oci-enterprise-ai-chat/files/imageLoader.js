// Custom image loader for next/image. In Next 16, neither assetPrefix nor
// `unoptimized: true` consistently prepend the base path to image URLs.
// This loader prepends the BASE_PATH placeholder, which the container's
// entrypoint rewrites at startup using the BASE_PATH env var.
export default function imageLoader({ src }) {
  return `/__BASE_PATH_PLACEHOLDER__${src}`;
}
