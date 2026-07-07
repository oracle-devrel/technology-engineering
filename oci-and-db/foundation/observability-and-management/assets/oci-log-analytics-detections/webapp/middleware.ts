import { NextRequest, NextResponse } from "next/server"

const allowedExactPaths = new Set(["/forge", "/api/health", "/favicon.ico", "/robots.txt", "/octo-logo.png", "/octo-icon.png"])
const allowedPrefixes = ["/api/forge/", "/_next/"]

function isAllowedPath(pathname: string) {
  return allowedExactPaths.has(pathname) || allowedPrefixes.some((prefix) => pathname.startsWith(prefix))
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (isAllowedPath(pathname)) {
    return NextResponse.next()
  }

  const acceptsHtml = request.headers.get("accept")?.includes("text/html") ?? false
  if (pathname === "/" || acceptsHtml) {
    return NextResponse.redirect(new URL("/forge", request.url))
  }

  return new NextResponse("Not found", { status: 404 })
}

export const config = {
  matcher: ["/((?!api/health$|api/forge/|_next/|favicon.ico|robots.txt|octo-logo.png|octo-icon.png).*)"],
}
