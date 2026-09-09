import { useBackendStore } from "~/stores/backend";
import type { Route, NetworkDetail } from "~/types/api";

// csrftoken cookie lives on the backend domain — invisible to this cross-origin
// page via document.cookie. Populated by loginToBackend(); used for API mutations.
let csrfToken = "";

/** GET the backend login form and extract the CSRF token (Django sets it on /login/). */
async function loadCsrfToken(base: string): Promise<string> {
  if (csrfToken) return csrfToken;
  const res = await fetch(`${base}/login/`, { credentials: "include" });
  const html = await res.text();
  const match = html.match(/name="csrfmiddlewaretoken"\s+value="([^"]+)"/);
  csrfToken = match?.[1] ?? "";
  return csrfToken;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const backend = useBackendStore();
  if (!backend.selected) throw new Error("No backend selected");

  const base = backend.apiBase.replace(/\/$/, "");
  const headers = new Headers(init.headers);
  const isForm = init.body instanceof FormData || init.body instanceof URLSearchParams;
  if (init.body && !isForm && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (init.method && init.method !== "GET" && init.method !== "HEAD") {
    const token = csrfToken ?? (await loadCsrfToken(base));
    if (token) headers.set("X-CSRFToken", token);
  }
  const res = await fetch(`${base}${path}`, { credentials: "include", ...init, headers });
  if (res.status === 401) {
    // session expired — redirect to our login page
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.assign(`/login/?next=${next}`);
    throw new Error("unauthorized");
  }
  if (res.status === 404) throw new Error("not found");
  if (!res.ok) throw new Error(`API ${res.status} ${path}`);
  return res.json() as Promise<T>;
}
/** Login: GET login form, extract CSRF token from HTML, then POST credentials. */
export async function loginToBackend(
  username: string,
  password: string,
): Promise<{ ok: boolean }> {
  const backend = useBackendStore();
  if (!backend.selected) throw new Error("No backend selected");
  const base = backend.apiBase.replace(/\/$/, "");

  // Step 1: GET login form, extract CSRF token (cross-origin: cookie invisible via document.cookie)
  const csrfToken = await loadCsrfToken(base);
  if (!csrfToken) throw new Error("CSRF token not found on login page — reload and retry");

  // Step 3: POST credentials to /login/ (form-urlencoded, CSRF via header)
  const formData = new URLSearchParams();
  formData.append("csrfmiddlewaretoken", csrfToken);
  formData.append("username", username);
  formData.append("password", password);
  const loginRes = await fetch(`${base}/login/`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": csrfToken,
    },
    body: formData.toString(),
  });
  if (loginRes.status === 403) return { ok: false };
  // Step 4: verify auth by calling a protected endpoint (sessionid is HttpOnly)
  const meRes = await fetch(`${base}/api/app/me/`, { credentials: "include" });
  if (!meRes.ok) return { ok: false };

  return { ok: true };
}

export function fetchRoutes(networkId: string): Promise<Route[]> {
  return api<Route[]>(`/api/app/networks/${networkId}/routes/`);
}

export function createRoute(networkId: string, ipNetwork: string, gateway: string | null): Promise<Route> {
  return api<Route>(`/api/app/networks/${networkId}/routes/`, {
    method: "POST",
    body: JSON.stringify({ ip_network: ipNetwork, gateway }),
  });
}

export function updateRoute(networkId: string, ipNetwork: string, data: { ip_network?: string; gateway?: string | null }): Promise<Route> {
  return api<Route>(`/api/app/networks/${networkId}/routes/${encodeURIComponent(ipNetwork)}/`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteRoute(networkId: string, ipNetwork: string): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/networks/${networkId}/routes/${encodeURIComponent(ipNetwork)}/`, {
    method: "DELETE",
  });
}

export function fetchNetworkDetail(networkId: string): Promise<NetworkDetail> {
  return api<NetworkDetail>(`/api/app/networks/${networkId}/`);
}

export function createNetwork(data: { name: string; description?: string; ip_allocation?: string }): Promise<NetworkDetail> {
  return api<NetworkDetail>("/api/app/networks/create/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateNetwork(networkId: string, data: { name?: string; description?: string; ip_allocation?: string }): Promise<NetworkDetail> {
  return api<NetworkDetail>(`/api/app/networks/${networkId}/update/`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}
