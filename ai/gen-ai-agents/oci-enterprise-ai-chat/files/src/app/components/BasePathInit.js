"use client";

// Global fetch patch for OCI Hosted Deployments (see lib/withBase.js for the why).
//
// All the app's API calls are root-absolute (`fetch('/api/...')`). Under a base
// path those would resolve to https://host/api/... — dropping the prefix the OCI
// gateway needs to route the request. Rather than touch ~28 call sites, we patch
// window.fetch once to prepend BASE to root-absolute, same-origin URLs.
//
// This also fixes Next's own RSC navigation fetches, which is what lets prefixed
// router.push() do a proper soft navigation under the prefix.
//
// Installed at module scope (before any component effect fires) and only when a
// prefix is actually present, so dev and root deployments are completely untouched.
import { BASE } from "@/lib/withBase";

if (BASE && typeof window !== "undefined" && !window.__baseFetchPatched) {
  window.__baseFetchPatched = true;
  const orig = window.fetch.bind(window);
  window.fetch = (input, init) => {
    if (
      typeof input === "string" &&
      input[0] === "/" && // root-absolute
      input[1] !== "/" && // not protocol-relative (//cdn)
      !input.startsWith(BASE + "/") // not already prefixed (assets, RSC)
    ) {
      return orig(BASE + input, init);
    }
    return orig(input, init);
  };
}

export default function BasePathInit() {
  return null;
}
