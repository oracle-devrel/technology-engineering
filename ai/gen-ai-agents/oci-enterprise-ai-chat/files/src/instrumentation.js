// Next.js server-start hook. Corporate networks route some egress (e.g. the
// DBTools MCP host) through an HTTP proxy, but Node's fetch ignores the
// HTTP(S)_PROXY env vars — every server-side call to those hosts dies with
// "fetch failed". EnvHttpProxyAgent honors HTTP_PROXY/HTTPS_PROXY/NO_PROXY.
// Applied only when the vars are present, so environments with direct egress
// (home, Container Instances) are untouched. NO_PROXY keeps localhost direct.
export async function register() {
  if (process.env.NEXT_RUNTIME !== 'nodejs') return;
  const proxy = process.env.HTTPS_PROXY || process.env.HTTP_PROXY;
  if (!proxy) return;
  const { setGlobalDispatcher, EnvHttpProxyAgent } = await import('undici');
  setGlobalDispatcher(new EnvHttpProxyAgent());
  console.log(`[instrumentation] proxy-aware fetch enabled via ${proxy}`);
}
