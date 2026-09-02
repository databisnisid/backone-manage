# SPEC — backone-manage

## §G Goal

SD-WAN / ZeroTier network management platform. Django+Wagtail. Manage orgs, ZeroTier controllers, networks, members(nodes). Ingest MQTT telemetry, threshold-monitor members, create/resolve problems. Webfilter, RSA licenses, Zabbix, Headscale alt-controller. Admin UI pure Wagtail modeladmin.

## §C Constraints

- Python 3.12, Django 5.2.12, Wagtail 7.0.6. pip pinned `requirements.txt`. venv.
- DB single default — SQLite dev, MySQL/MariaDB prod (`DB_ENGINE`). `mysqlclient`.
- Redis cache/broker — db0 MQTT telemetry, db1 peer cache.
- ZeroTier = primary controller (`controllers/backend.py` Zerotier). Headscale = alt.
- MQTT via paho — 21-field semicolon payload on `backone/presence`.
- Admin UI only Wagtail modeladmin — no Django admin (admin.py stubs dead).
- Workers = cron functions (Docker `dockerize/cronjobs`), not Celery/APScheduler.
- Multi-tenancy by `accounts.User.organization` FK, `org_uuid`, `DEFAULT_ORGANIZATION_UUID`.
- Node.js required for rule compiler (`controllers/rule-compiler`).
- Auth: axes + mailauth passwordless + 2FA (`two_factor_custom`, gated `IS_2FA_ENABLE`).
- No pytest — Django unittest only. 14 empty tests.py placeholders.
- `save()` overrides push to external APIs in real time.

## §I Interact

Public HTTP routes (`config/urls.py`):
- `custom/` Django admin (dev only)
- `networks/` + `api/networks/` → networks.urls
- `api/members/` → members.urls (`get_all/`, `get_member/<id>/`, `get_member_by_net/<id>/<net>/`, `get_by_user/<user>/`, `get_by_org/<org>/`, `get_by_net/<net>/`, `get_by_net_mqtt/<net>/`)
- `api/webfilters/` → webfilters.urls (network/<id>/, member/<id>/)
- `api/licenses/` → licenses.urls (download/<id>/, handler/)
- `accounts/` → mailauth.urls
- `two/` → two_factor_custom.urls
- `login/` → CustomLoginView
- `/` Wagtail admin + docs; prometheus at root
- handler400/403/404/500 → config.customviews

CLI/management commands:
- `mqtt_presence`, `mqtt_presence_redis`, `mqtt_presence_redis_to_db`
- `sync_member_peers`, `ipinfo_list_peers`

Entrypoints (dockerize): `entrypoint.ds`(dev), `entrypoint_gunicorn.ds`(prod), `entrypoint_mqtt*.ds`, `entrypoint_crond.ds`, `entrypoint_sync_member_peers.ds`. Cron: `dockerize/cronjobs`.

External surfaces: ZeroTier API, Headscale API, Zabbix API (`zabbix-utils`), MQTT broker, Redis, ipinfo.io (`connectors/drivers/ipinfo_lite.py`), MQTT rcall topic (`connectors/drivers/mqtt.py`).

## §R Research

No research skill run — section omitted (right-size).

## §V Invariants

- V1. `Members.save()` surfaces ZeroTier API failure to the user — do not silently swallow; the DB write must not proceed with a stale/absent controller write. ? (policy set: surface to user)
- V2. Admin surface always via Wagtail modeladmin (`wagtail_hooks.py`) — never Django admin.
- V3. Multi-tenancy: member/network/problem queries scoped by org (`get_user()`, `org_uuid`); no cross-tenant leakage.
- V4. MQTT telemetry: 21-field semicolon payload parse must be tolerant to malformed/missing fields — no daemon crash.
- V5. Redis key namespace: db0 = MQTT telemetry, db1 = peer cache. No cross-collision.
- V6. License `check_license` + `is_license_valid` return bool on any input — never raise.
- V7. `Mqtt.save()` must guard index access on `packet_loss_string`/`round_trip_string` (`[2]`, `[1]`) — never IndexError on malformed telemetry. (guards V4 gap)
- V8. `Licenses.check_license()` (model method) returns `(bool, datetime, msg)`; module-level `licenses.utils.check_license(lic_json)` returns `{status, msg}` — these are separate symbols, never assume either is "never-raise" without input guards. (fixes V6)
- V9. ZeroTier API calls in `Members.save`/`MemberPeers.save`/`Members.delete` must validate controller success — `Zerotier.query()` swallows `RequestException` and returns `{'status': 0}` (`controllers/backend.py:37-38`); a failure result must surface a user-facing error and abort the save, so local DB row never diverges from controller state. JSON-decode failure on non-JSON response (`request.json()` at `backend.py:35`, not a RequestException) must also be caught. (policy: surface error to user, per user decision 2026-09-02)

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

## §B Bugs

| id | date | cause | fix |
|----|------|-------|-----|
| B2 | 2026-09-02 | §V6 conflates two `check_license` symbols; module fn returns dict + unguarded `lic_json[...]`/`b64decode` at `licenses/utils.py:81-86` raises | V8: split symbols, add input guards |
| B3 | 2026-09-02 | `Mqtt.save()` unguarded `packet_loss_split[2]`/`round_trip_string[1]` at `mqtt/models.py:96,105` IndexError on malformed telemetry — violates V4 | V7: guard index access |
| B1 | 2026-09-02 | `Members.save()`/`MemberPeers.save()`/`Members.delete()` call ZeroTier API unguarded (`members/models.py:297,309,270`); raw API exception propagates | V9: wrap, surface error to user, abort save |
