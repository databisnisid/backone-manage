# SPEC — backone-manage

## §G Goal

SD-WAN / ZeroTier network management platform. Django+Wagtail. Manage orgs, ZeroTier controllers, networks, members(nodes). Ingest MQTT telemetry, threshold-monitor members, create/resolve problems. Webfilter, RSA licenses, Zabbix, Headscale alt-controller. Admin UI pure Wagtail modeladmin.

White-label SPA login: frontend `fe.nexus` posts cross-origin to backend `nexus` `/login/`. Add "Remember me" checkbox — checked → session persists 30 days; unchecked → session cookie expires at browser close.

SPA dashboard map: members with near-identical coords (no-geo fallback `GEO_WIDGET_DEFAULT_LOCATION`) cluster into a count bubble like the Wagtail dashboard map — every site stays reachable by zooming, and no pin stack hides members.

SPA dashboard map search: live search box overlays the map; typing filters markers to members whose name/member_id/ipaddress contain the query and fits the view to them; clearing restores all pins.

SPA access history: `/settings/access` lists axes login history in two tabs — **Log** (successful logins) and **Failure** (failed attempts) — served by one org-scoped `GET /api/app/access-logs/`.

## §C Constraints

- Python 3.12, Django 5.2.17, Wagtail 7.4.3. pip pinned `requirements.txt`. venv.
- External packages: `wagtail-modeladmin` (replaces removed wagtail core modeladmin), `modelsearch` (Wagtail 7.2+ search backend).
- DB single default — SQLite dev, MySQL/MariaDB prod (`DB_ENGINE`). `mysqlclient`.
- Redis cache/broker — db0 MQTT telemetry, db1 peer cache.
- ZeroTier = primary controller (`controllers/backend.py` Zerotier). Headscale = alt.
- MQTT via paho — 21-field semicolon payload on `backone/presence`.
- Admin UI only Wagtail modeladmin — no Django admin (admin.py stubs dead).
- Workers = cron functions (Docker `dockerize/cronjobs`), not Celery/APScheduler.
- Multi-tenancy by `accounts.User.organization` FK, `org_uuid`, `DEFAULT_ORGANIZATION_UUID`.
- Node.js required for rule compiler (`controllers/rule-compiler`).
- Auth: axes + mailauth passwordless + 2FA (`two_factor_custom`, gated `IS_2FA_ENABLE`).
- "Remember me" login: Wagtail `LoginForm.remember` BooleanField (`wagtail/admin/forms/auth.py:20`) + `LoginView.form_valid` reads it (`wagtail/admin/views/account.py:398`). SPA POSTs `remember`. CustomLoginView overrides `form_valid` to honor 30d (grill decision) instead of Wagtail default `SESSION_COOKIE_AGE` (1d).
- No pytest — Django unittest only. 14 empty tests.py placeholders.
- `save()` overrides push to external APIs in real time.
- Clustering lives in `frontend/components/MapPanel.vue` (`MarkerClusterer`, dep `@googlemaps/markerclusterer` ^2.6.2). Marker coords are exact; the library resolves overlap. Same UX as the Wagtail dashboard map (`dashboard/static/dashboard/js/map_dashboard.js:303`).
- No-geo members need a distinct coord or the cluster can never split: `app/views.py:_jitter()` offsets them by a stable hash of `member_id`, ±0.0025° (~278 m), only when `member.location` is empty. Hash not `random()` — identical across refreshes and clients.
- Viewport is fitted to members once (Web-Mercator fit computed up front, 60 px padding) and clamped to `NUXT_PUBLIC_MAP_ZOOM` (default 13) **before** the camera moves, then applied as a single `setCenter`+`setZoom`; later refreshes keep the user's viewport. `fitBounds` is deliberately not used: it animates to the uncapped zoom and a corrective `idle` listener pins it back, which renders as zoom-in→zoom-out flicker on every keystroke.
- `is_new` flyer circle centers on the member's own coord, so the pulse stays attached to its pin.
- Route polylines (`drawPolylines`) untouched — network endpoints, not member markers.
- Legacy jitter (`members/views.py:80`, `zabbix/utils.py:29`, `random.uniform(-0.0025,0.0025)`) untouched — Wagtail dashboard path only, SPA does not use it.
- Marker guard is `lat == null || lng == null` (not falsy) — a member at lat/lng 0 is real and must plot.
- Search lives in `frontend/components/MapPanel.vue` only, hidden when `props.single` (member detail = one pin). Client-side filter over the already-fetched `GET /api/app/members/` payload — no new endpoint, no query param, no request per keystroke.
- Match = case-insensitive substring, OR across `name`, `member_id`, `ipaddress`. Org/network matching explicitly out.
- Live trigger, ~200 ms debounce; `Enter` applies immediately; `Escape` clears.
- Filter survives the 300 s auto-refresh: `refreshMarkers()` re-applies the current query to fresh data; the query is never silently dropped.
- Zero matches → pins cleared + "No members match" overlay inside the map. Never a silent blank map.
- `MarkerClusterer` is rebuilt from the filtered set (`clearMarkers`/`addMarkers`), not merely emptied — otherwise stale count bubbles survive a filter.
- Input overlays the map and is styled with the existing Tailwind tokens, not Wagtail's inline JS style block (`dashboard/static/dashboard/js/map_dashboard.js:658`).
- ? Wagtail dashboard map search box (unstyled, no width) left untouched — separate ticket.
- Access history reads axes tables only — no new model, no logging middleware, no duplicate audit trail. `AccessLog` = successful logins (239 rows live), `AccessFailureLog` = failed attempts, `AccessAttempt` = derived lockout snapshot (`AXES_RESET_ON_SUCCESS=True` clears it on next success) and therefore **not a history** — not shown.
- `AXES_ENABLE_ACCESS_FAILURE_LOG` is env-gated in `config/settings.py` `# AXES` block, default `True`. Verified gap: setting unset → axes defaults `False` → `AccessFailureLog.objects.count() == 0` live.
- Failure log is self-capped by axes (`remove_out_of_limit_failure_logs`); `AccessLog` has no automatic retention (unbounded — server paging is the upgrade path, not day-one).
- Scope: superuser → all rows. `is_no_org` user → rows matching own username only. Org user → rows whose `username` matches a `User` in that org (`User.objects.filter(organization=…).values_list("username", flat=True)`). NULL-org user → own username only. Unattributable rows (username absent from `User`) are superuser-only — showing them to an org admin leaks foreign usernames/IPs (V3). Mirrors the `member_qs` branch shape (`app/views.py:41-47`); never filter by `organization=None` (matches every NULL-org user).
- Cap: scope **first**, then latest 200 per tab. Never slice-then-scope — live data proves the newest 200 rows split 136/60/4 across three different owners, so a global slice hands one tenant another's window and can starve it to zero. Order explicitly `order_by("-attempt_time", "-id")`. Client-side filter on `username`/`ip_address`, mirroring map search (V21). `ponytail:` comment marks ceiling.
- Payload fields: `id`, `username`, `ip_address`, `user_agent`, `attempt_time`, plus `logout_time` (logs) / `locked_out` (failures). `path_info`, `session_hash`, `http_accept` are **excluded** — `path_info` stores passwordless login tokens (`/accounts/login/<signature>`, 2 live rows) and a login token is a credential.
- Single endpoint, single fetch: `GET /api/app/access-logs/` → `{"logs": [...], "failures": [...]}`; tabs switch client-side, no per-tab lazy request.

## §I Interact

Public HTTP routes (`config/urls.py`):
- `custom/` Django admin (dev only)
- `networks/` + `api/networks/` → networks.urls
- `api/members/` → members.urls (`get_all/`, `get_member/<id>/`, `get_member_by_net/<id>/<net>/`, `get_by_user/<user>/`, `get_by_org/<org>/`, `get_by_net/<net>/`, `get_by_net_mqtt/<net>/`)
- `api/webfilters/` → webfilters.urls (network/<id>/, member/<id>/)
- `api/licenses/` → licenses.urls (download/<id>/, handler/)
- `accounts/` → mailauth.urls
- `login/` → CustomLoginView (`config/customviews.py:13`). POST body `[csrfmiddlewaretoken, username, password, remember]`. `remember` boolean — checked → 30d session, unchecked → browser-close. Cross-origin: `credentials:"include"`, `X-CSRFToken` header from HTML token.
- `/` Wagtail admin + docs; prometheus at root
- handler400/403/404/500 → config.customviews

CLI/management commands:
- `mqtt_presence`, `mqtt_presence_redis`, `mqtt_presence_redis_to_db`
- `sync_member_peers`, `ipinfo_list_peers`

Entrypoints (dockerize): `entrypoint.ds`(dev), `entrypoint_gunicorn.ds`(prod), `entrypoint_mqtt*.ds`, `entrypoint_crond.ds`, `entrypoint_sync_member_peers.ds`. Cron: `dockerize/cronjobs`.

External surfaces: ZeroTier API, Headscale API, Zabbix API (`zabbix-utils`), MQTT broker, Redis, ipinfo.io (`connectors/drivers/ipinfo_lite.py`), MQTT rcall topic (`connectors/drivers/mqtt.py`).

SPA map: `frontend/components/MapPanel.vue` `refreshMarkers()` -> `GET /api/app/members/` (`lat`/`lng` per member; `props.members` has no callers so it is always fetched, `MapPanel.vue:122`). Rendered at `fe.nexus.manage.backone.cloud/`. Refresh `config.public.mapRefreshInterval` (`MapPanel.vue:228`, default 300 s). Marker pin 36 px wide, click navigates to the member page. `props.single` (member detail, `pages/members/[memberId].vue`) bypasses `refreshMarkers` and mounts one unclustered pin.
SPA map search: internal to `MapPanel.vue`. No URL param, no persisted state, no backend surface — the input mutates a local filtered marker array.
SPA access history: `GET /api/app/access-logs/` (`app/urls.py`, `@login_required` + `@never_cache`) → `{"logs": [{id, username, ip_address, user_agent, attempt_time, logout_time}], "failures": [{id, username, ip_address, user_agent, attempt_time, locked_out}]}` — no `path_info`/`session_hash`/`http_accept` (V30); scoped then capped 200 per kind (V29, V31). Page `frontend/pages/settings/access/index.vue`, nav entry in `frontend/pages/settings.vue` base `navItems` array (visible to all users, not the superuser block). Data source `axes.models.AccessLog`/`AccessFailureLog`.

## §R Research

No research skill run — section omitted (right-size).

## §V Invariants

- V1. `Members.save()` surfaces ZeroTier API failure to the user — do not silently swallow; the DB write must not proceed with a stale/absent controller write. ? (policy set: surface to user)
- V2. Admin surface always via external `wagtail_modeladmin` package (`wagtail_hooks.py`) — never Django admin, never `wagtail.contrib.modeladmin`.
- V3. Multi-tenancy: member/network/problem queries scoped by org (`get_user()`, `org_uuid`); no cross-tenant leakage.
- V4. MQTT telemetry: 21-field semicolon payload parse must be tolerant to malformed/missing fields — no daemon crash.
- V5. Redis key namespace: telemetry lives in `MQTT_REDIS_DB`, peer cache in `MQTT_REDIS_DB + 1` (`members/models.py:r_peers`), both under prefix `MQTT_REDIS_PREFIX` which is per-deployment (`backone` vs `nexus`). Index off the setting, never hardcode a db number. No cross-collision.
- V6. License `check_license` + `is_license_valid` return bool on any input — never raise.
- V7. `Mqtt.save()` must guard index access on `packet_loss_string`/`round_trip_string` (`[2]`, `[1]`) — never IndexError on malformed telemetry. (guards V4 gap)
- V8. `Licenses.check_license()` (model method) returns `(bool, datetime, msg)`; module-level `licenses.utils.check_license(lic_json)` returns `{status, msg}` — these are separate symbols, never assume either is "never-raise" without input guards. (fixes V6)
- V9. ZeroTier API calls in `Members.save`/`MemberPeers.save`/`Members.delete` must validate controller success — `Zerotier.query()` swallows `RequestException` and returns `{'status': 0}` (`controllers/backend.py:37-38`); a failure result must surface a user-facing error and abort the save, so local DB row never diverges from controller state. JSON-decode failure on non-JSON response (`request.json()` at `backend.py:35`, not a RequestException) must also be caught. (policy: surface error to user, per user decision 2026-09-02)
- V10. `§C` version strings must match `requirements.txt` pinned versions; version bump PRs must update both.
- V11. `§C` must document that `wagtail-modeladmin` is an external package (not wagtail core) and `modelsearch` is a required search backend dependency.
- V12. Module-level `wagtail.contrib.modeladmin` imports are prohibited — use `wagtail_modeladmin` (external package). Verified: all 10 apps comply.
- V13. "Remember me" session: checked → `session.set_expiry(30*24*3600)` (30d); unchecked → `set_expiry(0)` (browser-close). Must override Wagtail `form_valid` (`account.py:398`) which uses `SESSION_COOKIE_AGE` (1d) — grill decided 30d.
- V14. SPA map markers plot **exact** member coords — no jitter, no offset. Overlaps are resolved by `@googlemaps/markerclusterer` (`MarkerClusterer`), the same UX as the Wagtail dashboard map (`dashboard/static/dashboard/js/map_dashboard.js:303`). Clusters collapse as the user zooms in, so spread scales with zoom naturally.
- V20. A member with non-null coords is never dropped by a falsy check (`lat`/`lng` of `0` are real). `MapPanel.vue:refreshMarkers`.
- V21. SPA map search filters client-side over the fetched member array only — no request per keystroke, `GET /api/app/members/` payload unchanged (`name`/`member_id`/`ipaddress` already present, `app/views.py:127`).
- V22. The active search query is re-applied on every auto-refresh and is never silently dropped; zero matches renders the explicit "No members match" overlay, never an unexplained blank map.
- V23. `Members.save()` must assign the `MemberPeers` row it just wrote back to `self.peers`. A saved member with a NULL peers FK cannot report online: `is_online()` has no local fallback.
- V24. `is_online()` reads Redis first, DB row second, and returns `False` — never raises — when neither exists; a freshly created member legitimately has neither.
- V25. `sync_member_peers` re-queries the member list every loop (a start-time snapshot never sees new members) and isolates per-member failures so one dead controller cannot stall the whole daemon.
- V26. `GET /api/app/access-logs/` never returns rows a caller cannot attribute: superuser sees all, non-superuser sees only rows whose `username` exists on a `User` in their own org. Unattributable rows are superuser-only. (extends V3 to a table with no org FK)
- V27. Access-history reads never mutate axes state — no `reset_logs`, no writes, no lockout changes. A read-only page must never unlock or lock an account.
- V28. The Failure tab must show real data, not an empty table: `AXES_ENABLE_ACCESS_FAILURE_LOG` must be `True` in settings. Shipping the page while the flag is off is a defect, not a config choice.
- V29. Access-log queries state their order explicitly: `order_by("-attempt_time", "-id")`. axes `AccessLog`/`AccessFailureLog` declare no `Meta.ordering` (`axes/models.py:61-66`, live `_meta.ordering == []`, SQL has no `ORDER BY`) — the abstract base's ordering does not reach them, so no default gives "latest".
- V30. Access-history payload never contains `path_info`, `session_hash`, or `http_accept`. `path_info` stores live passwordless login tokens (`/accounts/login/<signature>`, `axes/handlers/database.py:279`) and a login token is a credential.
- V31. Access-log scoping never raises and never over-shares: superuser → all; `is_no_org` → own username; org user → that org's usernames; NULL org → own username only; unattributable rows → superuser only. Scope before cap. Mirrors `member_qs` (`app/views.py:41-47`).

## §T Tasks

| id | status | task | cites |
|----|--------|------|-------|
| T1 | x | Distill spec from existing code | |
| T2 | x | Write tests for license utils (`is_license_valid`, both `check_license` symbols) | V6, V8 |
| T3 | x | Write tests for monitor threshold logic (`monitor/utils.py`) | V4 |
| T4 | x | Write tests for MQTT 21-field payload parser tolerant to malformed input | V4, V7 |
| T5 | x | Make `Members.save`/`MemberPeers.save`/`Members.delete` ZeroTier-sync surface errors to user (mock): catch API failure, show user-facing error, abort save; then test | V1, V9 |
| T6 | x | Remove dead broken `encrypt_node_id()` in `licenses/utils.py` (marked "Not Used", refs undefined) | |
| T7 | x | Guard index access in `Mqtt.save()` on `packet_loss_string`/`round_trip_string` | V7 |
| T8 | x | Add input guards to module `licenses.utils.check_license(lic_json)` for missing `node_id`/`uuid`/`token` keys + `b64decode` | V8 |
| T9 | x | Override `CustomLoginView.form_valid` (`config/customviews.py`) — read `form.cleaned_data["remember"]`, `set_expiry(30d)` when true else `set_expiry(0)`; keep `super().form_valid(form)`; verify SPA POST of `remember` sets expiry | V13, I.login |
| T10 | x | SPA `login.vue` add "Remember me" checkbox (v-model `rememberMe`), `loginToBackend(username,password,rememberMe)` appends `remember` to POST body; verify click E2E persists session 30d vs browser-close | V13, I.login |
| T11 | x | Cluster markers in `MapPanel.vue`: `MarkerClusterer` on exact coords, null-check marker guard, `fitBounds` clamped to configured zoom; `app/views.py:_jitter()` spreads no-geo members so clusters can split | V14, V20 |
| T12 | x | Verified live: 40 coincident members render one count bubble at zoom 13, splitting into 4 then 7+individual pins while zooming in; clicking a pin navigates to `/members/<id>`; member page renders its telemetry chart | V14 |
| T13 | x | Live map search in `MapPanel.vue`: overlay input, 200 ms debounce, OR-substring match on `name`/`member_id`/`ipaddress`, filter markers + zoom clamped to configured value, rebuild `MarkerClusterer`, empty-state overlay, Escape/Enter handling, re-apply on refresh, single-shot camera move (no fit/refit flicker) | V21, V22, I.spa_map_search |
| T14 | x | Fix member OFFLINE despite live controller path: link peers FK in `Members.save()`, re-query members per loop in `sync_member_peers`, per-member failure isolation, make `is_online()` return `False` instead of raising; backfilled stranded row live; 5 tests pass | V23, V24, V25, B6 |
| T15 | x | Add `AXES_ENABLE_ACCESS_FAILURE_LOG` env-gated default `True` to `config/settings.py` `# AXES` block | V28 |
| T16 | x | `GET /api/app/access-logs/` in `app/views.py` + `app/urls.py`: superuser all rows; `is_no_org`/NULL-org own username; org user org usernames; unattributable superuser-only; scope **then** `order_by("-attempt_time","-id")[:200]` per kind; payload drops `path_info`/`session_hash`/`http_accept`; `{logs, failures}`; 8 tests in `app/tests.py:AccessLogApiTests` | V26, V27, V29, V30, V31, I.access_history |
| T17 | x | SPA `frontend/pages/settings/access/index.vue` (Log/Failure tabs, client-side filter) + `Access History` entry in the **base** `navItems` array of `frontend/pages/settings.vue` + `fetchAccessLogs` in `frontend/utils/api.ts` + types in `frontend/types/api.ts` | V26, I.access_history |
| T18 | x | Live verify on :8008 + `nuxt dev`: failure tab renders real `AccessFailureLog` rows (a 403 bad-token login produced one), org user sees only own-org usernames, unattributable rows (`username IS NULL`, `ghostuser`) appear for superuser only, `path_info`/`session_hash`/`http_accept` absent, filter matches username and IP | V26, V28, V30 |

## §B Bugs

| id | date | cause | fix |
|----|------|-------|-----|
| B2 | 2026-09-02 | §V6 conflates two `check_license` symbols; module fn returns dict + unguarded `lic_json[...]`/`b64decode` at `licenses/utils.py:81-86` raises | V8: split symbols, add input guards |
| B3 | 2026-09-02 | `Mqtt.save()` unguarded `packet_loss_split[2]`/`round_trip_string[1]` at `mqtt/models.py:96,105` IndexError on malformed telemetry — violates V4 | V7: guard index access |
| B1 | 2026-09-02 | `Members.save()`/`MemberPeers.save()`/`Members.delete()` call ZeroTier API unguarded (`members/models.py:297,309,270`); raw API exception propagates | V9: wrap, surface error to user, abort save |
| B4 | 2026-11-10 | SPA map plots `member.lat/lng` verbatim (`MapPanel.vue` `refreshMarkers`); no-geo members fall back to `GEO_WIDGET_DEFAULT_LOCATION` (`app/views.py:118` → `config/settings.py:313`), so N sites collapse into one pin | V14: `MarkerClusterer` count bubble, exact coords |
| B5 | 2026-11-10 | `MapPanel.vue:130` `if (!m.lat \|\| !m.lng) continue` treats coord `0` as missing — a member on the equator or prime meridian is silently unplotted | V20: null check |
| B6 | 2026-11-11 | `Members.save()` wrote the `MemberPeers` row but never set `self.peers`, so every member created through the admin kept `peers_id = NULL`; `sync_member_peers` also snapshotted `Members.objects.filter(is_authorized=True)` before its `while True`, so members created after daemon start never got a Redis peer key. Both paths empty → `is_online()` read OFFLINE for a node with a live ZeroTier path | V23, V25: link FK in `save()`, re-query per loop, guard per-member, make `is_online()` total; backfilled the one stranded row via `queryset.update()` (bypasses `Members.save()`) |
