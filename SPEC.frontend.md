# SPEC — backone-frontend

## §G Goal

Dedicated Nuxt 4 (Vue 3) SPA frontend. Dashboard, map, telemetry, network views. **CRUD for**: Networks (Routes + Rules), Members (list + detail + Peers + Mqtt telemetry), Controllers, and all Settings tables (Features, Licenses, WebFilters, ZabbixConfigs, MonitorItems/Rules, OperationalTime, HS_Users/Nodes/Preauthkeys, Devices). Separate Docker container, always. Multi-tenant org-scoped. Wagtail admin untouched. Django serves auth + API. Multi-backend white-label: user picks backend from dropdown on login, frontend routes all API calls to that selected backend.

## §C Constraints

- Nuxt 4.5.2 (Vue 3) SPA, `ssr: false`, separate Docker container; served at root `/` on own domain (e.g. `fe.nexus.manage.backone.cloud`), cross-origin to backend domain
- **No `/app/` path prefix** — frontend domain serves at `/`, backend stays on its own domain. All API calls cross-origin.
- Django serves auth + API via existing FBV `JsonResponse`; no new DRF viewsets, no new serializer layer
- Multi-tenancy enforced server-side (`get_user()`/`org_uuid`); frontend trusts nothing client-side
- Auth via existing Django session + mailauth + 2FA + CSRF; no new auth surface
- CORS env-driven: `CORS_ALLOW_ALL_ORIGINS` default preserves legacy; separate domain sets `CORS_ALLOWED_ORIGINS` + `FRONTEND_ORIGIN`
- MVP: polling only (`MAP_REFRESH_INTERVAL`, default 300s), no WebSocket
- No changes to Wagtail admin or modeladmin surface
- No new dependency unless stdlib/framework can't cover it
- New `/api/app/*` endpoints (reads + all CRUD); legacy `/api/members/*`, `/api/networks/*` untouched
- Route CRUD endpoints trigger ZeroTier sync via `NetworkRoutes.save()`/`.delete()` model overrides — no additional sync code needed
- `NetworkRoutes` fields: `ip_network` (target CIDR), `gateway` (via IP), FK to `Networks`. No `metric` field exists.
- Network CRUD: create (name, description, IP Allocation comma-separated CIDRs) + update (name, description, IP Allocation). No delete endpoint — destroy stays in Wagtail admin.
- `network_id` is ZT-generated on create, not user-editable. Controller is auto-assigned from org default (`Organizations.controller` FK).
- IP Allocation: comma-separated CIDR string(s) stored in `Networks.ip_address_networks`. `save()` + `post_save` signal handle ZT route sync — no additional backend parsing
- `Controllers` model has no `organization` FK. Each org has ONE controller via `Organizations.controller`. No controller list endpoint — controller is auto-assigned. **NEW**: User wants Controllers CRUD — must scope by `is_superuser` (admin-only), no org filter.
- **CRITICAL — side-effect model `save()` overrides**: `Controllers.save()` calls `Zerotier(uri, token).status()` (real ZT API); `Members.save()` calls `zt.set_member()` + `zt.get_member_peers()`; `NetworkRules.save()` runs Node.js subprocess + `zt.set_network()`; `MemberPeers.save()` calls `zt.get_member_peers()`. `Members.delete()` calls `zt.delete_member()`. Form submissions for these models trigger real external calls — errors surface as `ValidationError`, must return 400 JSON with field-specific messages.
- **NEW**: `Mqtt` model has org-scoped via `Members` — Mqtt list/filter scoped to org's members only
- **NEW**: `MemberPeers` has no org FK — only accessible via `Members.peers` FK. Mqtt telemetry read-only from SPA (Mqtt rows auto-created by daemon)
,- **NEW**: `Licenses` model: `save()` only sets `node_id` from hex. RSA decryption happens in `check_license()` method, called externally (cron, not from save). SPA CRUD must send raw `license_key`/`license_string` strings — do NOT attempt decrypt/encrypt roundtrip. `license_features` is `editable=False` (auto-populated by `check_license()`). `clean()` requires organization FK. Org-scoped via OneToOneField to Organizations.
,- **NEW**: `ZabbixConfigs` (name, url, token) — **global model**, NO org FK. `ZabbixNetworks` (name, networks M2M to Networks, config OneToOne to ZabbixConfigs) — also **global model**, no org FK. Token stored plaintext — list endpoint must mask token, detail endpoint full value. Superuser-only access (no org scoping possible). `ZabbixNetworks.config` is OneToOne — each config has one network group.
- **NEW**: `OperationalTime` has org FK + `clean()` validates start < end per day. Full day-by-day schedule form
,- **NEW**: `WebFilters` (name, description, uuid, domains_black, domains_white, is_default_block, organization FK, network OneToOne) — org-scoped. `WebFiltersOrg` (organization OneToOne, network FK) — org-scoped. `WebFiltersMembers` (member OneToOne to Members, webfilter FK to WebFilters) — **M2M through table**, no org FK. Need POST/DELETE endpoints to add/remove member from webfilter (org-scoped via webfilter FK). Domains stored as newline-separated text.
,- **NEW**: `MonitorRules` + `OperationalTime` — org-scoped via `crum.get_current_user()` in `save()`/`clean()`. Need org filter on list endpoints. `MonitorItems` is a **global lookup table** (name, item_id only, no org FK) — GET-only from SPA, no create/edit/delete (managed in Wagtail admin).
,- `HS_Users`/`HS_Nodes`/`HS_Preauthkeys` — Headscale models all have `organization` FK. `HS_Users.save()` does NOT auto-set org (commented out at line 72); endpoint must require `organization` in request body. `HS_Nodes.save()` auto-sets org from `self.hs_user.organization` (line 198). `HS_Preauthkeys.save()` auto-sets org from `self.hs_user.organization` (line 132). `HS_Users.clean()` calls Headscale API (`add_user`/`rename_user`) on name change — must catch `ValidationError`. `HS_Preauthkeys.clean()` calls `add_preauth_key` — must catch `ValidationError`. Org-scoped, not superuser-only.
- **NEW**: `Devices` is a `ClusterableModel` with `ParentalKey(Organizations)` — inline child of Organizations. NOT a standalone CRUD entity. Accessed via Organizations detail endpoint if needed. No separate `/api/app/devices/` endpoint.
- **Cross-domain auth**: Frontend domain ≠ backend domain. Session cookie stays on backend domain. `credentials: "include"` on all API calls. Each backend must set `CORS_ALLOWED_ORIGINS` to include the frontend domain.
- **Standalone login page**: Login page lives on frontend domain, not Django's `/login/`. User selects backend → frontend POSTs credentials to that backend → gets session cookie for that backend domain.
- **CSRF cross-domain**: Django `CSRF_TRUSTED_ORIGINS` must include the frontend domain. CSRF token extracted from the **login form HTML** (`name="csrfmiddlewaretoken"`), not `document.cookie` — cross-origin csrftoken cookie is invisible to JS. API mutations reuse the cached token via `X-CSRFToken`.
- **Session cookie flags**: Backend must set `SESSION_COOKIE_SAMESITE = "None"` + `SESSION_COOKIE_SECURE = True` and `CSRF_COOKIE_SAMESITE = "None"` + `CSRF_COOKIE_SECURE = True` so the session survives cross-origin.
- **Backend memory**: Frontend remembers last-selected backend in `localStorage` so returning users skip the dropdown.
- **Backend down**: If selected backend is unreachable, show error on login. No retry, no auto-fallback to another backend.

## §I Interact

Frontend surfaces:
- Nuxt 4.5.2 SPA at root `/` on own domain (`fe.nexus.manage.backone.cloud`), served by separate Docker container (nginx static)
- Standalone login page on frontend domain with backend selector dropdown
- Dashboard layout (`UDashboardPanel` + `UDashboardNavbar` + `UDashboardSidebar`) with nav for: Dashboard, Members, Networks, Controllers, Settings (sub-pages for Features, Licenses, WebFilters, Zabbix, Monitor, Headscale, Devices)
- All API calls routed to selected backend via absolute URL

Backend config:
- `BACKEND_SERVERS` env var: JSON array of `{ label, url }` objects
- Frontend reads this config at runtime to populate the login dropdown

Existing API endpoints (already built):
- `POST /login/` — Django session login (CSRF cookie set here, token also in login form HTML)
- `GET /api/app/me/` — user/org/features/controller info for SPA guard
- `GET /api/app/members/` — prepare_data-shape list (map + member list)
- `GET /api/app/members/<member_id>/telemetry/` — latest Mqtt snapshot
- `GET /api/app/networks/` — org-scoped networks + member_count
- `GET /api/app/networks/<network_id>/` — single network detail
- `POST /api/app/networks/` — create network (name, description, ip_allocation)
- `PUT /api/app/networks/<network_id>/` — update network name/description/ip_allocation (triggers ZT sync via model save)
- `GET /api/app/summary/` — counts (members/online/problems/networks)
- `GET /api/app/problems/` — unsolved problems
- `GET /api/app/networks/<network_id>/routes/` — org-scoped routes for a network; response includes `gateway_member_name` (member name if gateway IP matches a member in the same network, else raw IP string, null if gateway is null)
- `POST /api/app/networks/<network_id>/routes/` — create route (triggers ZT sync via model save)
- `PUT /api/app/networks/<network_id>/routes/<ip_network>/` — update route by CIDR (triggers ZT sync via model save)
- `DELETE /api/app/networks/<network_id>/routes/<ip_network>/` — delete route by CIDR (triggers ZT sync via model delete)
- `GET /api/app/ip-loc/?ip=` — geolocate IP from Redis cache

**New API endpoints needed:**
- `GET/POST /api/app/controllers/` — list + create (superuser-only; no org FK on model)
- `GET/PUT/DELETE /api/app/controllers/<id>/` — detail/update/delete (superuser-only)
- `GET /api/app/networks/<id>/rules/` — get NetworkRules for a network
- `PUT /api/app/networks/<id>/rules/` — update NetworkRules (triggers ZT API via `save()`)
- `GET /api/app/member-peers/<member_id>/` — get peers for a member (via Members.peers FK)
,- `GET /api/app/monitor-items/` — global lookup list (no org filter, no create/edit/delete)
- `GET/POST /api/app/monitor-rules/` — list + create MonitorRules (org-scoped)
- `GET/PUT/DELETE /api/app/monitor-rules/<id>/` — detail/update/delete (org-scoped)
- `GET/POST /api/app/operational-times/` — list + create (org-scoped)
- `GET/PUT/DELETE /api/app/operational-times/<id>/` — detail/update/delete (org-scoped)
- `GET /api/app/webfilters/` — list (org-scoped)
- `GET/POST /api/app/webfilters-org/` — list + create (org-scoped)
- `GET/PUT/DELETE /api/app/webfilters-org/<id>/` — detail/update/delete (org-scoped)
- `GET /api/app/zabbix-configs/` — list (superuser-only; masks token)
- `GET/POST /api/app/zabbix-configs/` — create (superuser-only)
- `GET/PUT/DELETE /api/app/zabbix-configs/<id>/` — detail/update/delete (superuser-only)
- `GET /api/app/licenses/` — list (superuser-only; masks license_string)
,- `POST /api/app/webfilters/<id>/members/` — add member to webfilter (org-scoped)
,- `DELETE /api/app/webfilters/<id>/members/<member_id>/` — remove member from webfilter
,- `GET /api/app/monitor-items/` — global lookup list (no org filter, no create/edit/delete)
,- `GET /api/app/headscale-nodes/` — list (org-scoped via organization FK, auto-set in save())
,- `GET /api/app/headscale-users/` — list + create (org-scoped via organization FK)

Auth handshake: Cross-domain session cookie via `credentials: "include"`. CSRF token extracted from login form HTML (`name="csrfmiddlewaretoken"`), cached at module level, mutations carry `X-CSRFToken`. Session + CSRF cookies both `SameSite=None; Secure`.

## §V Invariants

- V1. Frontend never trusts client-side org/user state for data filtering — every API call scoped by Django `get_user()`/`org_uuid` server-side
- V2. Auth tokens/cookies validated server-side on every API request — no client-side-only auth gates
- V3. API responses carry only data for the authenticated user's org — zero cross-tenant leakage
- V4. Frontend Docker image built from same `requirements.txt`-inspired lockfile principle — pinned `package.json` + `package-lock.json`, reproducible builds
- V5. No direct DB/Redis/MQTT access from frontend container — all data via Django HTTP API only
- V6. No raw Django PKs in client-visible URLs — use `member_id`/`network_id`/`ip_network`/`node_id` strings
- V7. Auth only via existing Django backends (Axes, mailauth, 2FA) — no new auth surface
- V8. Route CRUD endpoints call `full_clean()` before `save()`; validation errors (duplicate CIDR, max 128, bad IP format) return 400 JSON with field-specific messages
- V9. Route map polylines use `get_ip_loc(ip)` from `connectors/redis_ipinfo.py` to extract lat/lng from the IPInfo Redis cache; no geo data → hide line silently, no error state
- V10. Network create/update endpoints call `full_clean()` before `save()`; ZT API failures surface as 400 JSON, not 500
- V11. Controller is auto-assigned from `request.user.organization.controller` on create — no controller selection exposed to frontend
- V12. IP Allocation: comma-separated CIDR string(s) passed directly to `Networks.ip_address_networks`; `save()` + `post_save` signal handle ZT route sync — no additional backend parsing
- V13. Network CRUD endpoints run within Django request cycle so `crum.get_current_user()` returns the authenticated user — never call `Networks.save()` from cron/management commands in this path
- V14. Backend URL list sourced from `BACKEND_SERVERS` env var (JSON). Frontend reads at startup to populate login dropdown. Config change = new backend, not code deploy.
- V26. Members CRUD endpoints must NOT accept `user` or `organization` fields in request body — `Members.save()` auto-populates both from `self.network.user` and `self.network.organization`. Client passes `network_id` only; server resolves org from network FK. Endpoint must catch ZT API `ValidationError` (invalid member_id on controller, duplicate IP) and return 400.
- V27. `HS_Users.save()` does NOT auto-set organization (commented out at line 72 of `headscale/models.py`). Create/update endpoints must require `organization` in request body. `HS_Nodes.save()` auto-sets `self.organization = self.hs_user.organization`. `HS_Preauthkeys.save()` auto-sets `self.organization = self.hs_user.organization`. `HS_Users.clean()` calls Headscale API on name change — catch `ValidationError`, return 400.
- V28. `WebFiltersMembers` is a M2M through table (member OneToOne + webfilter FK, no org FK). POST endpoint creates `WebFiltersMembers(member=member, webfilter=webfilter)` — org derived from webfilter's organization. DELETE endpoint removes by member_id. Both org-scoped via webfilter FK join.
- V29. `MonitorItems` is a global reference table (CPU, Memory, Quota, LTE Signal) with no org FK. GET endpoint returns all items unfiltered. No create/update/delete endpoints — managed in Wagtail admin only.
,- V30. `WebFiltersMembers` list endpoint (`GET /api/app/webfilters/<id>/members/list/`) returns members assigned to the webfilter, org-scoped via webfilter FK join. Response shape: `[{id, webfilter_id, member_id, member_name, member_member_id}]`.
- V15. All API calls use absolute URL from selected backend (`apiBase` runtime config). Session cookie and CSRF cookie scoped to backend domain via `credentials: "include"`. Frontend DOMAIN serves at root `/` (no path prefix).
- V16. Selected backend persisted in `localStorage` key `selectedBackend`. Returning users skip dropdown. Clear on logout.
- V17. Login page lives on frontend domain at `/`. POST credentials to selected backend's `/login/` endpoint. CSRF token extracted from login form HTML (`name="csrfmiddlewaretoken"`), cached module-level, mutations carry `X-CSRFToken`. Backend must have `CORS_ALLOWED_ORIGINS` including frontend domain and `CSRF_TRUSTED_ORIGINS` including frontend domain, plus `SESSION_COOKIE_SAMESITE=None` + `CSRF_COOKIE_SAMESITE=None` (both Secure).
,- V21. RBAC: **Superuser-only** (global models, no org FK): Controllers, Licenses, ZabbixConfigs, ZabbixNetworks, Devices. **Org-scoped** (organization FK): MonitorRules, OperationalTime, WebFilters, WebFiltersOrg, WebFiltersMembers, HS_Users, HS_Nodes, HS_Preauthkeys. **Global reference** (GET-only, no CRUD): MonitorItems. Non-superuser accessing superuser-only → 403.
- V19. Side-effect model CRUD (Controllers, Members, NetworkRules, MemberPeers) must catch `ValidationError` from `save()` that wraps ZeroTier API failures (bad token, network unreachable, member ID validation) and surface as 400 with field-specific messages — never let ZeroTier errors bubble as 500
- V20. `Members.delete()` calls ZeroTier `zt.delete_member()` — delete endpoint must catch `ValidationError` and return 400, not 500
- V22. `ZabbixConfigs.token` and `Licenses.license_string` must be masked (e.g. `"****"`) in list/detail responses; only superuser GET on detail endpoint returns full value
- V23. `NetworkRules.save()` runs Node.js subprocess (`settings.NODEJS` + `settings.CLIJS`) — update endpoint must catch `FileNotFoundError` (Node.js not installed) and `subprocess.CalledProcessError` and return 400 JSON
- V24. `Mqtt` telemetry is read-only from SPA — Mqtt rows auto-created by `mqtt_presence` daemon. No create/update/delete endpoints. Mqtt data accessed via `Members` FK or member telemetry endpoint
- V25. `MemberPeers` has no org FK — list endpoint must filter via `Members` org-scoping (join on `Members.peers` FK) to prevent cross-tenant data leakage
- V31. Network routes inherit RBAC from Django `network_qs()` backend — no additional frontend guard needed. Non-superusers see org-scoped networks; superusers see all. Routes visible for any network user can access.

- V32. Routes GET response includes `gateway_member_name`: backend resolves `Members.objects.filter(network=net, ip_address=gateway).first()`. Match → member.name. No match → raw gateway IP string as-is. Null gateway → null. Resolution scoped to same network only (no cross-network lookup).
## §T Tasks

| id | status | task | cites |
|----|--------|------|-------|
| T11 | x | Django: new org-scoped `/api/app/*` FBV endpoints (me, members, telemetry, networks, summary, problems) | V1,V3,V6,V7 |
| T12 | x | Django: CORS env-driven lockdown (`CORS_ALLOW_ALL_ORIGINS`/`CORS_ALLOWED_ORIGINS`) | V3 |
| T13 | x | Frontend: Nuxt 4.5.2 scaffold (`ssr:false`, baseURL `/`, Tailwind v4, ECharts, Pinia) | V4 |
| T14 | x | Frontend: auth store + router guard (redirect `/login/?next=/`, 401 handling) | V2,V7 |
| T15 | x | Frontend: API client + types (fetch wrapper, prepare_data shapes) | V3,V5 |
| T16 | x | Frontend: dashboard summary view (counts, poll) | V1,V3 |
| T17 | x | Frontend: map view (Google Maps markers, online/problem coloring, poll) | V1,V3 |
| T18 | x | Frontend: members list + member detail (ECharts telemetry, quota bars) | V1,V3 |
| T19 | x | Frontend: networks list (org-scoped) | V1,V3 |
| T20 | x | Test: multi-tenancy guard (non-superuser sees own org only, disjoint member_id sets) | V1,V3 |
| T21 | x | Docker: frontend Dockerfile (node build → nginx) + nginx serve at root `/` | V4,V5 |
| T22 | x | Django: add `get_ip_loc(ip) -> (lat, lng) | None` to `connectors/redis_ipinfo.py` | |
| T23 | x | Django: `/api/app/networks/<id>/routes/` GET (list) + POST (create) FBV, full_clean before save | V1,V3,V8 |
| T24 | x | Django: `/api/app/networks/<id>/routes/<ip_network>/` PUT + DELETE FBV, full_clean before save | V1,V3,V8 |
| T25 | x | Frontend: network detail page (`/networks/[network_id].vue`) — routes table (ip_network, gateway, delete action) + create modal (CIDR required, gateway optional), refresh on create/delete. RBAC inherits from backend `network_qs()`, no frontend guard. | V1,V3,V6,V8 |
| T26 | x | Frontend: map polylines — get_ip_loc on route target+gateway, draw lines | V1,V3,V9 |
| T27 | x | Frontend: types + API client for route CRUD (CSRF token from login form HTML) | V3,V5,V8 |
| T28 | x | Django: `GET /api/app/networks/<id>/` — single network detail FBV | V1,V3,V6 |
| T29 | x | Django: `POST /api/app/networks/` — create network FBV (name, description, ip_allocation) | V1,V3,V6,V10,V11,V12 |
| T30 | x | Django: `PUT /api/app/networks/<id>/` — update network FBV (name, description, ip_allocation) | V1,V3,V6,V10,V11,V12 |
| T31 | x | Frontend: network create/edit form — name, description, CIDR input (controller auto-assigned) | V1,V3,V6,V10,V11,V12 |
| T32 | x | Frontend: types + API client network CRUD | V3,V5,V10 |
| T33 | x | Backend: `CORS_ALLOWED_ORIGINS` + `CSRF_TRUSTED_ORIGINS` env vars, `SESSION_COOKIE_SAMESITE=None`/Secure + `CSRF_COOKIE_SAMESITE=None`/Secure for cross-origin frontend | V15,V17 |
| T37 | x | Django: Controllers CRUD FBV (`/api/app/controllers/` GET+POST, `/<id>/` GET+PUT+DELETE) — superuser-only, token masked in responses, validates ZT connection before save | V18,V19,V21 |
| T38 | x | Django: NetworkRules CRUD FBV (`/api/app/networks/<id>/rules/` GET+PUT) — org-scoped via network, catches ZT API + Node.js subprocess errors | V18,V19,V23 |
| T39 | x | Django: MemberPeers list FBV (`/api/app/member-peers/<member_id>/` GET) — org-scoped via Members join | V18,V25 |
| T40 | x | Django: MonitorRules CRUD FBV (`/api/app/monitor-rules/` GET+POST, `/<id>/` GET+PUT+DELETE) — org-scoped. MonitorItems GET-only list FBV (global, no CRUD) | V18,V21 |
| T42 | x | Django: WebFilters CRUD FBV (`/api/app/webfilters/` GET, `/api/app/webfilters-org/` GET+POST, `/<id>/` GET+PUT+DELETE) — org-scoped | V18,V21 |
| T43 | x | Django: ZabbixConfigs CRUD FBV (`/api/app/zabbix-configs/` GET+POST, `/<id>/` GET+PUT+DELETE) — superuser-only, token masked | V18,V21,V22 |
| T44 | x | Django: Licenses list FBV (`/api/app/licenses/` GET) — superuser-only, license_string masked | V18,V21,V22 |
| T49 | x | Django: HS_Users CRUD FBV (`/api/app/headscale-users/` GET+POST, `/<id>/` GET+PUT+DELETE) — org-scoped, requires `organization` in create body, catches Headscale API ValidationError | V18,V27 |
| T50 | x | Django: HS_Nodes list FBV (`/api/app/headscale-nodes/` GET) — org-scoped, org auto-set in save() | V18,V27 |
| T51 | x | Django: HS_Preauthkeys CRUD FBV (`/api/app/headscale-preauthkeys/` GET+POST, `/<id>/` GET+DELETE) — org-scoped, org auto-set in save() | V18,V27 |
| T52 | x | Django: WebFiltersMembers add/remove FBV (`/api/app/webfilters/<id>/members/` POST, `/members/<member_id>/` DELETE) — org-scoped via webfilter FK | V18,V28 |
| T53 | x | Django: MonitorItems list FBV (`/api/app/monitor-items/` GET) — global, no org filter, no create/edit/delete | V18,V29 |
| T54 | x | Frontend: Headscale users/nodes/preauthkeys list pages (`/settings/headscale/`) — org-scoped table views with create/delete | V1,V3,V27 |
| T34 | x | Frontend: backend selector store — `BACKEND_SERVERS` env → login dropdown, `localStorage` memory | V14,V16 |
| T35 | x | Frontend: standalone login page at `/` on frontend domain with backend selector + credential POST | V7,V14,V15,V17 |
| T36 | x | Frontend: API client rewrite — `apiBase` from selected backend, `credentials: "include"`, CSRF from HTML | V15 |
| T37 | x | Django: Controllers CRUD FBV (`/api/app/controllers/` GET+POST, `/<id>/` GET+PUT+DELETE) — superuser-only, no org filter | V18,V19,V21 |
| T38 | x | Django: NetworkRules CRUD FBV (`/api/app/networks/<id>/rules/` GET+PUT) — org-scoped via network, catches ZT API + Node.js subprocess errors | V18,V19,V23 |
| T39 | x | Django: MemberPeers list FBV (`/api/app/member-peers/<member_id>/` GET) — org-scoped via Members join | V18,V25 |
| T40 | x | Django: MonitorRules CRUD FBV (`/api/app/monitor-rules/` GET+POST, `/<id>/` GET+PUT+DELETE) — org-scoped. MonitorItems GET-only list FBV (global, no CRUD) | V18,V21 |
| T42 | x | Django: WebFilters CRUD FBV (`/api/app/webfilters/` GET, `/api/app/webfilters-org/` GET+POST, `/<id>/` GET+PUT+DELETE) — org-scoped | V18,V21 |
| T43 | x | Django: ZabbixConfigs CRUD FBV (`/api/app/zabbix-configs/` GET+POST, `/<id>/` GET+PUT+DELETE) — superuser-only, token masked | V18,V21,V22 |
| T44 | x | Django: Licenses list FBV (`/api/app/licenses/` GET) — superuser-only, license_string masked | V18,V21,V22 |
| T47 | x | Frontend: Controllers list page (`/controllers/`) — superuser-only table view | V1,V3,V21 |
| T48 | x | Frontend: Settings navigation + pages — sub-navigation for Features/Licenses/WebFilters/Zabbix/Monitor/Headscale/Devices/OperationalTime | V1,V3,V21 |
| T56 | x | Django: WebFiltersMembers list FBV (`/api/app/webfilters/<id>/members/list/` GET) — org-scoped via webfilter FK | V18,V30 |
| T55 | x | Frontend: WebFilters detail page — domains list + member assignment (add/remove via POST/DELETE) | V1,V3,V28 |
| T57 | x | Frontend: Controllers "Create Controller" button + create modal (Name, Description, URI, Token) — superuser-only, ZT validation errors shown inline | V1,V19,V21 |
| T58 | x | Frontend: Controllers edit modal — pre-fills from GET detail (full token), all fields editable including Token, PUT on save | V1,V19,V21 |
| T59 | x | Frontend: Controllers delete — row action button, confirm dialog, DELETE call, remove row | V1,V21 |
| T60 | x | Frontend: API client — add `createController`, `fetchControllerDetail`, `updateController`, `deleteController` to `utils/api.ts` | V3 |
| T61 | x | Frontend: networks list — add "Routes" button per row navigating to `/networks/${network_id}` + route count column | V6 |
| T64 | x | Frontend: route delete — row action button, `confirm()` dialog, `DELETE /routes/<ip_network>/`, remove row | V1,V3,V6 |
| T65 | x | Backend + Frontend: show `gateway_member_name` in routes GET response — backend resolves gateway IP → member name in same network (match → name, no match → raw IP, null → null); frontend displays in Gateway column | V32 |

## §B Bugs

| id | date | cause | fix |
|----|------|-------|-----|
| B1 | 2026-09-29 | T48 marked done but `settings.vue` `navItems` had no Headscale entries — T54 pages `/settings/headscale/{users,nodes,preauthkeys}` unreachable from UI | added Headscale Users/Nodes/Keys nav entries in `settings.vue` |

