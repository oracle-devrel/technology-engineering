const basePath = process.env.NEXT_PUBLIC_FORGE_BASE_PATH || ""

export function publicAssetPath(path: string) {
  return `${basePath}${path.startsWith("/") ? path : `/${path}`}`
}
