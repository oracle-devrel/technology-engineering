import { dirname } from "node:path"
import { fileURLToPath } from "node:url"

const appDir = dirname(fileURLToPath(import.meta.url))
const staticExport = process.env.NEXT_PUBLIC_FORGE_STATIC_EXPORT === "1" || process.env.FORGE_STATIC_EXPORT === "1"
const basePath = process.env.NEXT_PUBLIC_FORGE_BASE_PATH || ""

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: staticExport ? "export" : "standalone",
  outputFileTracingRoot: appDir,
  ...(basePath ? { basePath, assetPrefix: basePath } : {}),
  ...(staticExport ? { trailingSlash: true } : {}),
  images: {
    unoptimized: true,
  },
  ...(!staticExport
    ? {
        async headers() {
          const csp = [
            "default-src 'self'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
            "object-src 'none'",
            "img-src 'self' data:",
            "font-src 'self' data:",
            "style-src 'self' 'unsafe-inline'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "connect-src 'self'",
            "form-action 'self'",
          ].join("; ")

          return [
            {
              source: "/:path*",
              headers: [
                { key: "Content-Security-Policy", value: csp },
                { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
                { key: "X-Content-Type-Options", value: "nosniff" },
                { key: "X-Frame-Options", value: "DENY" },
                { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
              ],
            },
          ]
        },
      }
    : {}),
}

export default nextConfig
