# SPEC — backone-frontend

## §G Goal

Dedicated Nuxt 4 (Vue 3) SPA frontend. Dashboard, map, telemetry, network views. Separate Docker container, always. Multi-tenant org-scoped. Wagtail admin untouched. Django serves auth + API.

## §C Constraints

- Nuxt 4.5.2 (Vue 3) SPA, `ssr: false`, separate Docker container; `/app/` path prefix same-domain (separate domain accepted fallback)
- Django serves auth + API via existing FBV `JsonResponse`; no new DRF viewsets, no new serializer layer
- Multi-tenancy enforced server-side (`get_user()`/`org_uuid`); frontend trusts nothing client-side
- Auth via existing Django session + mailauth + 2FA + CSRF; SPA same-origin path prefix; no new auth surface
- CORS env-driven: `CORS_ALLOW_ALL_ORIGINS` default preserves legacy; separate domain sets `CORS_ALLOWED_ORIGINS` + `FRONTEND_ORIGIN`
- MVP: polling only (`MAP_REFRESH_INTERVAL`, default 300s), no WebSocket
- No changes to Wagtail admin or modeladmin surface
- No new dependency unless stdlib/framework can't cover it
- New read-only `/api/app/*` endpoints; legacy `/api/members/*`, `/api/networks/*` untouched

## §I Interact

Frontend surfaces:
- Nuxt 4.5.2 SPA at `/app/` path prefix, served by separate Docker container (nginx static)
- Reverse-proxied via nginx: `/app/` → frontend container; `/api/`, `/accounts/`, `/two/`, `/login/`, `/custom/`, `/documents/` → Django upstream

Consumes existing Django endpoints:
- `api/networks/` — networks, routes, rules (`networks/`)
- `api/webfilters/` — webfilter by network/member (`webfilters/views.py`)
- `api/licenses/` — license download/handler (`licenses/`)

New `/api/app/*` endpoints (org-scoped FBV, `@login_required`):
- `GET /api/app/me/` — user/org/features for SPA guard
- `GET /api/app/members/` — prepare_data-shape list (map + member list)
- `GET /api/app/members/<member_id>/telemetry/` — latest Mqtt snapshot
- `GET /api/app/networks/` — org-scoped networks + member_count
- `GET /api/app/summary/` — counts (members/online/problems/networks)
- `GET /api/app/problems/` — unsolved problems

Auth handshake: Django session cookie, same domain, `credentials` on reads; mutations later carry `X-CSRFToken` from cookie.

## §V Invariants

- V1. Frontend never trusts client-side org/user state for data filtering — every API call scoped by Django `get_user()`/`org_uuid` server-side
- V2. Auth tokens/cookies validated server-side on every API request — no client-side-only auth gates
- V3. API responses carry only data for the authenticated user's org — zero cross-tenant leakage
- V4. Frontend Docker image built from same `requirements.txt`-inspired lockfile principle — pinned `package.json` + `package-lock.json`, reproducible builds
- V5. No direct DB/Redis/MQTT access from frontend container — all data via Django HTTP API only
- V6. No raw Django PKs in client-visible URLs — use `member_id`/`network_id` strings
- V7. Auth only via existing Django backends (Axes, mailauth, 2FA) — no new auth surface

## §T Tasks

| id | status | task | cites |

| T11 | x | Django: new org-scoped `/api/app/*` FBV endpoints (me, members, telemetry, networks, summary, problems) | V1,V3,V6,V7 |
| T12 | x | Django: CORS env-driven lockdown (`CORS_ALLOW_ALL_ORIGINS`/`CORS_ALLOWED_ORIGINS`) | V3 |
| T13 | x | Frontend: Nuxt 4.5.2 scaffold (`ssr:false`, baseURL `/app/`, Tailwind v4, ECharts, Pinia) | V4 |
| T14 | x | Frontend: auth store + router guard (redirect `/login/?next=/app/`, 401 handling) | V2,V7 |
| T15 | x | Frontend: API client + types (fetch wrapper, prepare_data shapes) | V3,V5 |
| T16 | x | Frontend: dashboard summary view (counts, poll) | V1,V3 |
| T17 | x | Frontend: map view (Google Maps markers, online/problem coloring, poll) | V1,V3 |
| T18 | x | Frontend: members list + member detail (ECharts telemetry, quota bars) | V1,V3 |
| T19 | x | Frontend: networks list (org-scoped) | V1,V3 |
| T20 | x | Test: multi-tenancy guard (non-superuser sees own org only, disjoint member_id sets) | V1,V3 |
| T21 | x | Docker: frontend Dockerfile (node build → nginx) + nginx path-prefix proxy | V4,V5 |


## §B Bugs

| id | date | cause | fix |
|----|------|-------|-----|
