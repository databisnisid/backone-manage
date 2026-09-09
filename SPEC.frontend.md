# SPEC — backone-frontend

## §G Goal

Dedicated Nuxt 4 (Vue 3) SPA frontend. Dashboard, map, telemetry, network views, route + network CRUD. Separate Docker container, always. Multi-tenant org-scoped. Wagtail admin untouched. Django serves auth + API. Multi-backend white-label: user picks backend from dropdown on login, frontend routes all API calls to that selected backend.

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
- New `/api/app/*` endpoints (reads + route/network CRUD); legacy `/api/members/*`, `/api/networks/*` untouched
- Route CRUD endpoints trigger ZeroTier sync via `NetworkRoutes.save()`/`.delete()` model overrides — no additional sync code needed
- `NetworkRoutes` fields: `ip_network` (target CIDR), `gateway` (via IP), FK to `Networks`. No `metric` field exists.
- Network CRUD: create (name, description, IP Allocation comma-separated CIDRs) + update (name, description, IP Allocation). No delete endpoint — destroy stays in Wagtail admin.
- `network_id` is ZT-generated on create, not user-editable. Controller is auto-assigned from org default (`Organizations.controller` FK).
- IP Allocation: comma-separated CIDR string(s) stored in `Networks.ip_address_networks`. `save()` already parses into ZT routes. No backend re-parsing needed.
- `Controllers` model has no `organization` FK. Each org has ONE controller via `Organizations.controller`. No controller list endpoint — controller is auto-assigned.
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
- All API calls routed to selected backend via absolute URL (`https://manage.backone.cloud/api/app/...`)

Backend config:
- `BACKEND_SERVERS` env var: JSON array of `{ label, url }` objects (e.g. `[{"label":"Global","url":"https://manage.backone.cloud"},{"label":"Vietnam","url":"https://manage.vn.backone.cloud"}]`)
- Frontend reads this config at build/runtime to populate the login dropdown

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
- `GET /api/app/networks/<network_id>/routes/` — org-scoped routes for a network
- `POST /api/app/networks/<network_id>/routes/` — create route (triggers ZT sync via model save)
- `PUT /api/app/networks/<network_id>/routes/<ip_network>/` — update route by CIDR (triggers ZT sync via model save)
- `DELETE /api/app/networks/<network_id>/routes/<ip_network>/` — delete route by CIDR (triggers ZT sync via model delete)
- `GET /api/app/ip-loc/?ip=` — geolocate IP from Redis cache

Auth handshake: Cross-domain session cookie via `credentials: "include"`. CSRF token extracted from login form HTML (`name="csrfmiddlewaretoken"`), cached at module level, mutations carry `X-CSRFToken`. Session + CSRF cookies both `SameSite=None; Secure`.

## §V Invariants

- V1. Frontend never trusts client-side org/user state for data filtering — every API call scoped by Django `get_user()`/`org_uuid` server-side
- V2. Auth tokens/cookies validated server-side on every API request — no client-side-only auth gates
- V3. API responses carry only data for the authenticated user's org — zero cross-tenant leakage
- V4. Frontend Docker image built from same `requirements.txt`-inspired lockfile principle — pinned `package.json` + `package-lock.json`, reproducible builds
- V5. No direct DB/Redis/MQTT access from frontend container — all data via Django HTTP API only
- V6. No raw Django PKs in client-visible URLs — use `member_id`/`network_id`/`ip_network` strings
- V7. Auth only via existing Django backends (Axes, mailauth, 2FA) — no new auth surface
- V8. Route CRUD endpoints call `full_clean()` before `save()`; validation errors (duplicate CIDR, max 128, bad IP format) return 400 JSON with field-specific messages
- V9. Route map polylines use `get_ip_loc(ip)` from `connectors/redis_ipinfo.py` to extract lat/lng from the IPInfo Redis cache; no geo data → hide line silently, no error state
- V10. Network create/update endpoints call `full_clean()` before `save()`; ZT API failures surface as 400 JSON, not 500
- V11. Controller is auto-assigned from `request.user.organization.controller` on create — no controller selection exposed to frontend
- V12. IP Allocation: comma-separated CIDR string(s) passed directly to `Networks.ip_address_networks`; `save()` + `post_save` signal handle ZT route sync — no additional backend parsing
- V13. Network CRUD endpoints run within Django request cycle so `crum.get_current_user()` returns the authenticated user — never call `Networks.save()` from cron/management commands in this path
- V14. Backend URL list sourced from `BACKEND_SERVERS` env var (JSON). Frontend reads at startup to populate login dropdown. Config change = new backend, not code deploy.
- V15. All API calls use absolute URL from selected backend (`apiBase` runtime config). Session cookie and CSRF cookie scoped to backend domain via `credentials: "include"`. Frontend DOMAIN serves at root `/` (no path prefix).
- V16. Selected backend persisted in `localStorage` key `selectedBackend`. Returning users skip dropdown. Clear on logout.
- V17. Login page lives on frontend domain at `/`. POST credentials to selected backend's `/login/` endpoint. CSRF token extracted from login form HTML (`name="csrfmiddlewaretoken"`), cached module-level, mutations carry `X-CSRFToken`. Backend must have `CORS_ALLOWED_ORIGINS` including frontend domain and `CSRF_TRUSTED_ORIGINS` including frontend domain, plus `SESSION_COOKIE_SAMESITE=None` + `CSRF_COOKIE_SAMESITE=None` (both Secure).

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
| T25 | x | Frontend: network detail page — routes table (ip_network, gateway) + create/edit/delete | V1,V3,V6,V8 |
| T26 | x | Frontend: map polylines — get_ip_loc on route target+gateway, draw lines | V1,V3,V9 |
| T27 | x | Frontend: types + API client for route CRUD (CSRF token from login form HTML) | V3,V5,V8 |
| T28 | . | Django: `GET /api/app/networks/<id>/` — single network detail FBV | V1,V3,V6 |
| T29 | . | Django: `POST /api/app/networks/` — create network FBV (name, description, ip_allocation) | V1,V3,V6,V10,V11,V12 |
| T30 | . | Django: `PUT /api/app/networks/<id>/` — update network FBV (name, description, ip_allocation) | V1,V3,V6,V10,V11,V12 |
| T31 | . | Frontend: network create/edit form — name, description, CIDR input (controller auto-assigned) | V1,V3,V6,V10,V11,V12 |
| T32 | . | Frontend: types + API client for network CRUD | V3,V5,V10 |
| T33 | x | Backend: `CORS_ALLOWED_ORIGINS` + `CSRF_TRUSTED_ORIGINS` env vars, `SESSION_COOKIE_SAMESITE=None`/Secure + `CSRF_COOKIE_SAMESITE=None`/Secure for cross-origin frontend | V15,V17 |
| T34 | x | Frontend: backend selector store — `BACKEND_SERVERS` env → login dropdown, `localStorage` memory | V14,V16 |
| T35 | x | Frontend: standalone login page at `/` on frontend domain with backend selector + credential POST | V7,V14,V15,V17 |
| T36 | x | Frontend: API client rewrite — `apiBase` from selected backend, `credentials: "include"`, CSRF from HTML | V15 |

## §B Bugs

| id | date | cause | fix |
|----|------|-------|-----|
