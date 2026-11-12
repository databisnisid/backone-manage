# SPEC — backone-manage

## §G Goal

SD-WAN / ZeroTier network management platform. Django+Wagtail. Manage orgs, ZeroTier controllers, networks, members(nodes). Ingest MQTT telemetry, threshold-monitor members, create/resolve problems. Webfilter, RSA licenses, Zabbix, Headscale alt-controller. Admin UI pure Wagtail modeladmin.

White-label SPA login: frontend `fe.nexus` posts cross-origin to backend `nexus` `/login/`. Add "Remember me" checkbox — checked → session persists 30 days; unchecked → session cookie expires at browser close.

SPA dashboard map: members with near-identical coords (no-geo fallback `GEO_WIDGET_DEFAULT_LOCATION`) cluster into a count bubble like the Wagtail dashboard map — every site stays reachable by zooming, and no pin stack hides members.

SPA dashboard map search: live search box overlays the map; typing filters markers to members whose name/member_id/ipaddress contain the query and fits the view to them; clearing restores all pins.

SPA access history: `/settings/access` lists axes login history in two tabs — **Log** (successful logins) and **Failure** (failed attempts) — served by one org-scoped `GET /api/app/access-logs/`.
SPA member CRUD: `/members` gains add/edit/delete — add adopts a member the ZeroTier controller already knows, every write goes through `Members.save()`/`delete()`, and access is gated by the same rules as the Wagtail admin.

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
- Add = **adopt an existing controller member**, never a DB-only row. The admin picks from `Zerotier.list_members(network_id)` (`controllers/backend.py:52`) minus members that already have a DB row. ZeroTier has no create-member API: an ID exists only after a node joins.
- Out of scope: bulk add/edit/delete, controller-side member discovery/reconciliation beyond the read-only picker, Headscale-backed networks, any change to the Wagtail modeladmin member UI.
- Write path is `Members.save()` / `Members.delete()` for every mutation. No `queryset.update()`, no `skip_controller` flag on `save()` — a second write path is how DB and controller drift. The one carve-out is `?force=true` (V42): a row whose controller member is already gone can only be dropped locally.
- `Members.save()` never calls `full_clean()`, so views must: `Members.clean()` already enforces member_id length 10, no duplicate member_id within a network, IP format, and IP inside `network.ip_address_networks` (`members/models.py:350-460`). Skipping it would let the API create rows the admin rejects. `Members.network` is `limit_choices_to=limit_choices_to_current_user` (`members/models.py:176`), which dereferences `crum.get_current_user()` — `full_clean()` therefore needs a request context; views have one via `@login_required` + `CurrentRequestUserMiddleware` (settings.py:109), tests must set one (V46).
- `network` and `member_id` are immutable after create. Re-assigning a member to another network is delete-on-old + re-adopt-on-new, not a dropdown. Editable: `name`, `member_code`, `description`, `ipaddress`, `tags`, `is_authorized`, `is_bridge`, `is_no_auto_ip`.
- Create body: `{network_id, member_id, name, ipaddress?, tags?, is_bridge?, is_no_auto_ip?, is_authorized?}`. The row is **seeded from the controller**, not from model defaults: `is_authorized`, `is_bridge`, `is_no_auto_ip`, `ipaddress` come from `get_member_info()` and are applied before `save()` (V41). ZeroTier has no create-member API for real nodes, so an adoptable ID is a node that already joined; its pending/authorized state is the controller's decision, not a side effect of adopting it.
- `Members.delete()` deletes on the controller first and raises on refusal, so a controller that no longer has the member strands the row. `DELETE ...?force=true` drops the row without the controller call, logs the controller refusal verbatim with actor + `member_id`, and is only reachable after the plain `DELETE` returned 409 naming that refusal (V42).
- Controller reads never collapse into one error: `Zerotier.query()` (`controllers/backend.py:27-40`) swallows both `RequestException` and JSON-decode failure into `{'status': 0}` and never looks at `status_code`, so the views need a thin wrapper that reports "controller answered, member absent" separately from "controller unreachable" (V43). 400 means the controller answered and does not know the ID; 502 means we could not ask.
- The picker validates the `list_members()` result before iterating: success is `dict[member_id -> int]` (live: 43 keys), failure is `{'status': 0}` whose only key is `status` (`controllers/backend.py:37-38`). Naive iteration offers a member named `status` (V44).
- `(network, member_id)` uniqueness is a DB constraint, not only the `clean()` check: `clean()` guards duplicates only when `self.id is None` and `Members.Meta` (`members/models.py:277-280`) declares no `unique_together`/`constraints`, so two concurrent adopts both pass `full_clean()` (V45).
- RBAC is a **full mirror** of `MembersPermissionHelper` (`members/wagtail_hooks.py:212-290`): `members.add_members` + org member quota (`organization.features.number_of_member`) + not a `GroupOrganizations` main org + `is_license_valid(user)` for create; `change_members` + not superuser + same group/license gates for edit; `delete_members` + same group/license gates for delete (`user_can_delete_obj` has no superuser denial). List stays as today (`view_members` only).
- Verified live (2026-11-12): `backone` is superuser with all three perms but admin add/edit deny it; `user@nexus.id` has all three and is allowed; `support@nexus.id` has none. `Nexus Client` quota 1000 vs 41 members, not a group child, license valid — only the superuser rule bites in practice.
- A superuser sees no Add/Edit control, matching the admin. The 403 body carries a machine-readable reason (`{"error": "...", "rule": "superuser_no_member_write"}`) so the SPA can state why rather than render a silently missing button.
- The rules live in one place, `members/permissions.py`: `can_add_member(user)`, `can_change_member(user, obj)`, `can_delete_member(user, obj)`, `member_write_denial(user, obj, action) -> str | None`. `wagtail_hooks.py` calls them; `app/views.py` calls them. The API never imports `wagtail_hooks` (imports Wagtail admin machinery) and never reimplements the checks.
- `GET /api/app/me/` gains `permissions: {members_add, members_change, members_delete, reasons: {…}}` — the SPA reads capability from the server, never re-derives rules in TypeScript.
- Hiding a control is never the enforcement. Every write view re-checks on the server; UI gating exists only to avoid dead buttons.
- AGENTS.md rule "NEVER call `Members.save()` from these views" applies to the read endpoints it was written for. A write endpoint's job is exactly that call; the invariant it protects is that GETs stay free of controller side effects.
- Out-of-scope target → **404, not 403**: `member_qs` first, then permission check, so a foreign member is indistinguishable from a missing one (V3).

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
SPA member writes — FBC `JsonResponse`, `@login_required` + `@never_cache`, addressed by the ZeroTier `member_id` string (matching `member_telemetry`/`member_peers`, not the integer PK):
- `POST /api/app/members/` — adopt. 403 with `rule` on RBAC denial before anything is read; 400 on a controller-answered-absent `member_id`, duplicate row, or `clean()` failure; **502** when the controller could not be reached (V43). The created row's controller fields are seeded from `get_member_info()`, never from model defaults (V41).
- `GET|PATCH|DELETE /api/app/members/<member_id>/` — single member read (the edit form loads current values, never trusts the list row); `DELETE` accepts `?force=true` per §C.
- `GET /api/app/networks/<network_id>/controller-members/` — picker proxy over `Zerotier.list_members()`; returns controller members with no `Members` row for that network, each with its controller `authorized`/`ipAssignments` so the form can prefill. Read-only: creates and reconciles nothing (V39). A controller failure is 502, never an empty list (V44).
- `GET /api/app/me/` — adds the `permissions` block consumed by the SPA.
SPA UI: "Add" on `frontend/pages/members/index.vue`; edit/delete on `frontend/pages/members/[memberId].vue`.

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
- V32. Member mutations go only through `Members.save()` / `Members.delete()`. A view that persists member fields by any other route (`queryset.update()`, raw SQL, a bypass flag) is a defect: the controller write and the DB write must be the same decision. (B1, B6)
- V33. Every member write view validates with `full_clean()` before `save()`. `Members.save()` does not call it, so an unvalidated write from the API can create rows the admin would reject.
- V34. Member write permission has exactly one implementation, `members/permissions.py`. `members/wagtail_hooks.py` and `app/views.py` both call it; neither reimplements the gates. Divergence between the two surfaces is the bug this prevents.
- V35. Server-side RBAC precedes every UI gate: a write the caller may not perform returns 403 with a `rule` code regardless of whether any button was rendered.
- V36. Member write scope is `member_qs(request)`. A `member_id` outside it returns 404, never 403 — the response must not confirm that a foreign member exists.
- V37. Adoption requires the member to exist on the controller: the view resolves it via `get_member_info()` before creating the row, and rejects an ID the controller answered "absent" for (V43 draws the 400/502 line). The controller also *creates* arbitrary 10-char IDs on `POST /member/<id>` (live: `200`, then present in `list_members()`), so "exists" means "the controller accepted it", not "a node has joined".
- V38. Controller-refused deletion never silently drops the row and never leaves it permanently undeletable: plain `DELETE` returns 409, `?force=true` drops the row and logs. (extends V9 to the delete direction)
- V39. The controller-member picker is read-only. Listing controller members must not create `Members` rows, touch `MemberPeers`, or call any controller write — reconciliation is a worker concern, out of scope (§C).
- V40. `network` and `member_id` never change on an existing member row. A row represents one node on one controller.
- V41. Adopt seeds the new row from controller state — `is_authorized`, `is_bridge`, `is_no_auto_ip`, `ipaddress` from `get_member_info()` — and `Members.save()` must never flip a controller `authorized: false` to `true` as a side effect of adoption. Live: adopting a pending node with model defaults authorized it on net `71d2dcfd7c27b4b4` and reset `activeBridge`/`noAutoAssignIps` to `false` (§C create body, §I POST).
- V42. `?force=true` is the only persisted write that skips `Members.delete()`; it runs after a 409, records the controller refusal verbatim with actor + `member_id`, and never becomes the default path. V32's "no second write path" is bounded by this exception, not violated by it.
- V43. A controller read failure is never reported as a bad request: `{'status': 0}` from `get_member_info()`/`list_members()` maps to 502 with a transport reason; 400 "unknown member" is returned only when the controller answered and the member is absent. Requires a status-aware wrapper beside `Zerotier.query()` (`controllers/backend.py:27-40`) — live probe: unknown ID → HTTP 404 with empty body → `{'status': 0}`, indistinguishable from a dead controller.
- V44. The `list_members()` result is validated before iteration: a failure dict is an error, never a member list. Success is `dict[member_id -> int]`; failure is `{'status': 0}` whose sole key is `status`.
- V45. `(network, member_id)` uniqueness is enforced by a DB unique constraint, not only by `clean()`. Two concurrent adopts of the same ID must not create two rows.
- V46. `full_clean()` on `Members` resolves the current user through `crum` (`limit_choices_to_current_user`, `members/models.py:176`); write views run under `@login_required`, and tests must establish a current user or they fail with `AttributeError: 'NoneType' object has no attribute 'is_superuser'`.
- V47. No invariant or UI label claims a field reaches the controller that ZeroTier does not carry: `name`, `member_code`, `description`, `tags` are DB-only; only `ipaddress`, `is_authorized`, `is_bridge`, `is_no_auto_ip` round-trip (`controllers/backend.py:91`, live member object has no `name` key).
- V48. A write to a row whose controller member has vanished re-creates it on the controller: `Members.save()` → `set_member()` is a `POST` the controller accepts for any ID, so `PATCH` is not blocked by a degraded row. Views must not claim PATCH is controller-safe for a stranded row; the accepted behavior is recreate-and-record, never a silent 200 on a DB-only change.

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
| T19 | . | Extract member write rules from `MembersPermissionHelper` into `members/permissions.py` (`can_add_member`, `can_change_member`, `can_delete_member`, `member_write_denial`), keep quota + `GroupOrganizations` + `is_license_valid` + superuser-denial semantics, point `wagtail_hooks.py` at them | V34 |
| T20 | . | `GET /api/app/networks/<network_id>/controller-members/` — proxy `Zerotier.list_members()`, validate the result (failure → 502, V44), drop IDs that already have a `Members` row for that network, org-scope the network, include each remaining member's controller `authorized`/`ipAssignments`; no writes | V39, V44 |
| T21 | . | `POST /api/app/members/` adopt: org-scope network, `get_member_info()` distinguishes absent (400) from unreachable (502), seed `is_authorized`/`is_bridge`/`is_no_auto_ip`/`ipaddress` from the controller, `full_clean()`, `save()`; 400/403/404/502 per §C | V32, V33, V36, V37, V41, V43, V46 |
| T22 | . | `GET`/`PATCH`/`DELETE /api/app/members/<member_id>/` — single read; PATCH over the editable field set only (DB-only fields stay DB-only, V47); DELETE 409 then `?force=true` logging the controller refusal | V32, V38, V40, V42, V48 |
| T23 | . | Add `permissions` block to `GET /api/app/me/`; SPA store exposes it, Add/Edit/Delete controls gate on it and surface the `rule` reason on 403 | V35 |
| T24 | . | SPA: adopt form + network/controller-member pickers on `members/index.vue`; edit form + delete confirm on `members/[memberId].vue`; types in `frontend/types/api.ts`, fetchers in `frontend/utils/api.ts` | V35 |
| T25 | . | Tests in `app/tests.py`: RBAC matrix (superuser denied add/edit, perms denied, foreign org 404, quota hit), adopt happy path + controller-absent 400 + unreachable 502, adopt does not flip a controller `authorized: false`, picker failure is not a member list, PATCH pushes to controller via mock, DELETE 409 then force, controller failure leaves row intact; set a current user via `crum.set_current_user(user)` (top-level symbol, not `crum.middleware.*`) | V32, V33, V34, V36, V38, V41, V43, V44, V46 |
| T26 | . | Live verify on the nexus stack against a real controller: adopt an unauthorized node and confirm it stays unauthorized until explicitly authorized; edit IP + `is_bridge`/`is_no_auto_ip` and confirm the controller reflects them; delete and confirm the controller member is gone; confirm the picker never creates rows and returns 502 on a dead controller | V41, V42, V43, V44 |

## §B Bugs

| id | date | cause | fix |
|----|------|-------|-----|
| B2 | 2026-09-02 | §V6 conflates two `check_license` symbols; module fn returns dict + unguarded `lic_json[...]`/`b64decode` at `licenses/utils.py:81-86` raises | V8: split symbols, add input guards |
| B3 | 2026-09-02 | `Mqtt.save()` unguarded `packet_loss_split[2]`/`round_trip_string[1]` at `mqtt/models.py:96,105` IndexError on malformed telemetry — violates V4 | V7: guard index access |
| B1 | 2026-09-02 | `Members.save()`/`MemberPeers.save()`/`Members.delete()` call ZeroTier API unguarded (`members/models.py:297,309,270`); raw API exception propagates | V9: wrap, surface error to user, abort save |
| B4 | 2026-11-10 | SPA map plots `member.lat/lng` verbatim (`MapPanel.vue` `refreshMarkers`); no-geo members fall back to `GEO_WIDGET_DEFAULT_LOCATION` (`app/views.py:118` → `config/settings.py:313`), so N sites collapse into one pin | V14: `MarkerClusterer` count bubble, exact coords |
| B5 | 2026-11-10 | `MapPanel.vue:130` `if (!m.lat \|\| !m.lng) continue` treats coord `0` as missing — a member on the equator or prime meridian is silently unplotted | V20: null check |
| B6 | 2026-11-11 | `Members.save()` wrote the `MemberPeers` row but never set `self.peers`, so every member created through the admin kept `peers_id = NULL`; `sync_member_peers` also snapshotted `Members.objects.filter(is_authorized=True)` before its `while True`, so members created after daemon start never got a Redis peer key. Both paths empty → `is_online()` read OFFLINE for a node with a live ZeroTier path | V23, V25: link FK in `save()`, re-query per loop, guard per-member, make `is_online()` total; backfilled the one stranded row via `queryset.update()` (bypasses `Members.save()`) |
