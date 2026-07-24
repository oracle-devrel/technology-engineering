"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { withBase } from "./withBase";

// Drop-in replacement for next/navigation's useRouter that prefixes push/replace
// targets with the deployment base path, so the URL bar keeps the prefix under an
// OCI Hosted Deployment. Import it aliased so existing call sites need no change:
//   import { useBaseRouter as useRouter } from "@/lib/useBaseRouter";
// In dev / root deployments withBase is a no-op, so behavior is unchanged.
export function useBaseRouter() {
  const router = useRouter();
  return useMemo(
    () => ({
      ...router,
      push: (href, opts) => router.push(withBase(href), opts),
      replace: (href, opts) => router.replace(withBase(href), opts),
    }),
    [router]
  );
}
