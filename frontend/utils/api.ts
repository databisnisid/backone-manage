export class ApiError extends Error {
  data: unknown;
  constructor(message: string, data: unknown) {
    super(message);
    this.data = data;
  }
}

import { useBackendStore } from "~/stores/backend";
import type { Controller, WebFilter, WebFilterOrg, WebFilterMember, ZabbixConfig, MonitorRule, MonitorItem, HSUser, HSNode, HSPreauthkey, LicenseItem } from "~/types/api";
import type { Route, NetworkDetail } from "~/types/api";

// csrftoken cookie lives on the backend domain — invisible to this cross-origin
// CSRF token: read from X-CSRFToken header on any backend response.
// The backend middleware sets this header on every response, so the SPA
// doesn't need to fetch a separate endpoint cross-origin.
let csrfToken = "";

/** Capture CSRF token from a response's X-CSRFToken header. */
function captureCsrfToken(res: Response) {
  const h = res.headers.get("x-csrftoken");
  if (h) csrfToken = h;
}

/** Ensure we have a CSRF token. If not, make a lightweight GET to grab one. */
async function ensureCsrfToken(base: string): Promise<string> {
  if (csrfToken) return csrfToken;
  const res = await fetch(`${base}/api/app/me/`, { credentials: "include" });
  captureCsrfToken(res);
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
    const token = csrfToken ?? (await ensureCsrfToken(base));
    if (token) headers.set("X-CSRFToken", token);
  }
  const res = await fetch(`${base}${path}`, { credentials: "include", ...init, headers });
  captureCsrfToken(res);
  if (res.status === 401) {
    // session expired — redirect to our login page
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.assign(`/login/?next=${next}`);
    throw new Error("unauthorized");
  }
  if (res.status === 404) throw new Error("not found");
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new ApiError(`API ${res.status} ${path}`, errBody);
  }
  return res.json() as Promise<T>;
}
/** Login: GET login form, extract CSRF token from HTML, then POST credentials. */
export async function loginToBackend(
  username: string,
  password: string,
  remember = false,
): Promise<{ ok: boolean }> {
  const backend = useBackendStore();
  if (!backend.selected) throw new Error("No backend selected");
  const base = backend.apiBase.replace(/\/$/, "");

  // Step 1: Ensure we have a CSRF token for the login POST
  // First make a GET to get the token via X-CSRFToken header
  const csrfRes = await fetch(`${base}/api/app/me/`, { credentials: "include" });
  captureCsrfToken(csrfRes);
  const csrfTokenVal = csrfToken;
  if (!csrfTokenVal) {
    if (csrfRes.ok) return { ok: true }; // already authenticated
    throw new Error("CSRF token not found — reload and retry");
  }

  // Step 3: POST credentials to /login/ (form-urlencoded, CSRF via header)
  const formData = new URLSearchParams();
  formData.append("csrfmiddlewaretoken", csrfTokenVal);
  formData.append("username", username);
  formData.append("password", password);
  if (remember) formData.append("remember", "on");
  const loginRes = await fetch(`${base}/login/`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": csrfTokenVal,
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

// ── Controllers ──
export function fetchControllers(): Promise<Controller[]> {
  return api<Controller[]>("/api/app/controllers/");
}
export function fetchControllerDetail(id: number): Promise<Controller> {
  return api<Controller>(`/api/app/controllers/${id}/`);
}
export function createController(data: { name: string; description?: string; uri: string; token: string }): Promise<Controller> {
  return api<Controller>("/api/app/controllers/", { method: "POST", body: JSON.stringify(data) });
}
export function updateController(id: number, data: { name?: string; description?: string; uri?: string; token?: string }): Promise<Controller> {
  return api<Controller>(`/api/app/controllers/${id}/`, { method: "PUT", body: JSON.stringify(data) });
}
export function deleteController(id: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/controllers/${id}/`, { method: "DELETE" });
}

// ── WebFilters ──
export function fetchWebfilters(): Promise<WebFilter[]> {
  return api<WebFilter[]>("/api/app/webfilters/");
}
export function fetchWebfiltersOrg(): Promise<WebFilterOrg[]> {
  return api<WebFilterOrg[]>("/api/app/webfilters-org/");
}
export function createWebfiltersOrg(data: { webfilter_id: number; network_id: string; organization_uuid?: string }): Promise<WebFilterOrg> {
  return api<WebFilterOrg>("/api/app/webfilters-org/", { method: "POST", body: JSON.stringify(data) });
}
export function fetchWebfilterDetail(id: number): Promise<WebFilter> {
  return api<WebFilter>(`/api/app/webfilters/${id}/`);
}
export function updateWebfilter(id: number, data: Partial<WebFilter>): Promise<WebFilter> {
  return api<WebFilter>(`/api/app/webfilters/${id}/`, { method: "PUT", body: JSON.stringify(data) });
}
export function deleteWebfilter(id: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/webfilters/${id}/`, { method: "DELETE" });
}
export function fetchWebfilterMembers(wfId: number): Promise<WebFilterMember[]> {
  return api<WebFilterMember[]>(`/api/app/webfilters/${wfId}/members/list/`);
}
export function addWebfilterMember(wfId: number, memberId: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/webfilters/${wfId}/members/`, { method: "POST", body: JSON.stringify({ member_id: memberId }) });
}
export function removeWebfilterMember(wfId: number, memberId: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/webfilters/${wfId}/members/${memberId}/`, { method: "DELETE" });
}

// ── Zabbix ──
export function fetchZabbixConfigs(): Promise<ZabbixConfig[]> {
  return api<ZabbixConfig[]>("/api/app/zabbix-configs/");
}
export function createZabbixConfig(data: { name: string; url: string; token: string }): Promise<ZabbixConfig> {
  return api<ZabbixConfig>("/api/app/zabbix-configs/", { method: "POST", body: JSON.stringify(data) });
}
export function updateZabbixConfig(id: number, data: Partial<ZabbixConfig>): Promise<ZabbixConfig> {
  return api<ZabbixConfig>(`/api/app/zabbix-configs/${id}/`, { method: "PUT", body: JSON.stringify(data) });
}
export function deleteZabbixConfig(id: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/zabbix-configs/${id}/`, { method: "DELETE" });
}

// ── Monitor ──
export function fetchMonitorRules(): Promise<MonitorRule[]> {
  return api<MonitorRule[]>("/api/app/monitor-rules/");
}
export function createMonitorRule(data: Partial<MonitorRule>): Promise<MonitorRule> {
  return api<MonitorRule>("/api/app/monitor-rules/", { method: "POST", body: JSON.stringify(data) });
}
export function updateMonitorRule(id: number, data: Partial<MonitorRule>): Promise<MonitorRule> {
  return api<MonitorRule>(`/api/app/monitor-rules/${id}/`, { method: "PUT", body: JSON.stringify(data) });
}
export function deleteMonitorRule(id: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/monitor-rules/${id}/`, { method: "DELETE" });
}
export function fetchMonitorItems(): Promise<MonitorItem[]> {
  return api<MonitorItem[]>("/api/app/monitor-items/");
}

// ── Headscale ──
export function fetchHSUsers(): Promise<HSUser[]> {
  return api<HSUser[]>("/api/app/headscale-users/");
}
export function createHSUser(data: { name: string; description?: string; organization: number }): Promise<HSUser> {
  return api<HSUser>("/api/app/headscale-users/", { method: "POST", body: JSON.stringify(data) });
}
export function updateHSUser(id: number, data: Partial<HSUser>): Promise<HSUser> {
  return api<HSUser>(`/api/app/headscale-users/${id}/`, { method: "PUT", body: JSON.stringify(data) });
}
export function deleteHSUser(id: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/headscale-users/${id}/`, { method: "DELETE" });
}
export function fetchHSNodes(): Promise<HSNode[]> {
  return api<HSNode[]>("/api/app/headscale-nodes/");
}
export function fetchHSPreauthkeys(): Promise<HSPreauthkey[]> {
  return api<HSPreauthkey[]>("/api/app/headscale-preauthkeys/");
}
export function createHSPreauthkey(data: { hs_user_id: number; is_reusable?: boolean; is_ephemeral?: boolean }): Promise<HSPreauthkey> {
  return api<HSPreauthkey>("/api/app/headscale-preauthkeys/", { method: "POST", body: JSON.stringify(data) });
}
export function deleteHSPreauthkey(id: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/headscale-preauthkeys/${id}/`, { method: "DELETE" });
}

// ── Licenses ──
export function fetchLicenses(): Promise<LicenseItem[]> {
  return api<LicenseItem[]>("/api/app/licenses/");
}

// -- OperationalTime --
export function fetchOperationalTimes(): Promise<OperationalTime[]> {
  return api<OperationalTime[]>("/api/app/operational-times/");
}
export function createOperationalTime(data: Partial<OperationalTime>): Promise<OperationalTime> {
  return api<OperationalTime>("/api/app/operational-times/", { method: "POST", body: JSON.stringify(data) });
}
export function updateOperationalTime(id: number, data: Partial<OperationalTime>): Promise<OperationalTime> {
  return api<OperationalTime>(`/api/app/operational-times/${id}/`, { method: "PUT", body: JSON.stringify(data) });
}
export function deleteOperationalTime(id: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/operational-times/${id}/`, { method: "DELETE" });
}

// -- Features (superuser) --
export function fetchFeatures(): Promise<Feature[]> {
  return api<Feature[]>("/api/app/features/");
}
export function createFeature(data: Partial<Feature>): Promise<Feature> {
  return api<Feature>("/api/app/features/", { method: "POST", body: JSON.stringify(data) });
}
export function updateFeature(id: number, data: Partial<Feature>): Promise<Feature> {
  return api<Feature>(`/api/app/features/${id}/`, { method: "PUT", body: JSON.stringify(data) });
}
export function deleteFeature(id: number): Promise<{ ok: boolean }> {
  return api<{ ok: boolean }>(`/api/app/features/${id}/`, { method: "DELETE" });
}

// -- Organizations + Devices (superuser) --
export function fetchOrganizationsDevices(): Promise<OrgWithDevices[]> {
  return api<OrgWithDevices[]>("/api/app/organizations/");
}
