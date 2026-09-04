/**
 * fetch wrapper — session cookie auth, same-origin under /app/ prefix.
 * `apiBase` from runtime config; empty = same origin.
 */
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const config = useRuntimeConfig();
  // Nuxt baseURL (/app/) applies to relative URLs; API lives at origin
  // root, so always hit an absolute-from-root path.
  const base = (config.public.apiBase || "/").replace(/\/$/, "");
  const res = await fetch(`${base}${path}`, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
    ...init,
  });
  if (res.status === 401) {
    // session expired — Django login will redirect with next
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.assign(`/login/?next=${next}`);
    throw new Error("unauthorized");
  }
  if (res.status === 404) throw new Error("not found");
  if (!res.ok) throw new Error(`API ${res.status} ${path}`);
  return res.json() as Promise<T>;
}