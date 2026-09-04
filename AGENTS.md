# Repository Guidelines

## Project Overview

**backone-manage** is a Django/Wagtail-based SD-WAN / ZeroTier network management platform. It manages organizations, ZeroTier controllers, networks, and member nodes; ingests MQTT device telemetry; runs threshold-based monitoring that creates/resolves member problems; manages web filtering, RSA-encrypted licenses, Zabbix integration, and a Headscale (Tailscale) alternative-controller path. Admin UI is entirely Wagtail CMS modeladmin.

---

## Architecture & Data Flow

```
┌───────────────┐   ┌───────────────┐   ┌──────────────┐
│  ZeroTier API │   │ Headscale API │   │   MQTT       │
│  (controllers)│   │ (alt. control)│   │   broker     │
└──────┬────────┘   └──────┬────────┘   └──────┬───────┘
       │  save() overrides │  workers (cron)   │ mqtt_presence daemon
       ▼                   ▼                   ▼
       │      ┌──────────────────────────────┐ │
       │      │      Django / Wagtail        │ │
       │      │  accounts · members ·        │ │
       │      │  networks · controllers ·    │ │
       │      │  monitor · mqtt · problems · │ │
       │      │  webfilters · licenses ·     │ │
       │      │  zabbix · headscale ·        │ │
       │      │  connectors · dashboard      │ │
       │      └───────────────┬──────────────┘ │
       │                      │                │
       └──────────┬───────────┼──────────┬─────┘
                  ▼           ▼          ▼
           ┌───────────┐ ┌────────┐ ┌────────┐
           │  App DB   │ │ Redis  │ │ Zabbix │
           │(MySQL prod│ │(db0 MQTT││        │
           │ SQLite dev│ │ db1 peer)│        │
           └───────────┘ └────────┘ └────────┘
```


**Data flow:**
1. **ZeroTier (primary controller)**: `controllers/backend.py` `Zerotier` class wraps the ZeroTier API. Model `save()` overrides (esp. `members/models.py`) push changes (members, network rules) to the controller in real time. Import/sync helpers in `controllers/workers.py`.
2. **MQTT telemetry (two pipelines)**: direct path — `mqtt_presence.py` subscribes to `backone/presence`, parses the 21-field semicolon payload into the `Mqtt` model (linked to `Members` via FK). Redis-buffered path — `mqtt_presence_redis.py` writes raw payload JSON to Redis (with TTL), then `mqtt_presence_redis_to_db.py` scans keys, deserializes, and upserts `Mqtt`. `mqtt/redis.py` serves cached reads (db0 MQTT telemetry, db1 peer cache).
3. **Monitoring**: `monitor/workers.py` `monitor_members()` iterates members, evaluates threshold rules (`MonitorRules`) against telemetry, and creates/resolves `MemberProblems`. Operational windows in `MonitorItems`/`OperationalTime`.
4. **Network cascade**: `networks/signals.py` `post_save` on `Networks` cascades user/org to members, routes, and rules, and auto-creates routes/rules. Node.js CLI compiles network rules to ZeroTier JSON.
5. **Cron**: `dockerize/cronjobs` schedules the `*_workers.py` sync functions (ZeroTier peer sync every 5 min, member monitoring every 5 min, offline deauth hourly, Zabbix sync daily, quota check 4 h, IPInfo enrichment daily, etc.).

---

## Key Directories

| Directory | Purpose |
|---|---|
| `config/` | Settings, URL routing, custom views, middleware, logging, Gunicorn config |
| `accounts/` | Custom `User` model (AbstractUser + Organization FK), Organizations, Features (license tier flags), multi-tenancy |
| `members/` | Core `Members` entity (1147-line model): ZeroTier sync in `save()`, telemetry accessors, IP validation, quota parsing; FBC JSON API views; read-only DRF serializer |
| `networks/` | Networks, NetworkRoutes, NetworkRules; cascading signals; rule compilation to ZeroTier format |
| `controllers/` | Controllers model (ZeroTier URI + token), `backend.py` Zerotier client, `workers.py` import/sync |
| `headscale/` | HS_Users, HS_Nodes, HS_Preauthkeys; Headscale as alternative controller; workers pull from Headscale API |
| `monitor/` | MonitorItems, MonitorRules, OperationalTime; `workers.py` + `utils.py` threshold checking |
| `problems/` | MemberProblems (unsolved/solved managers), ProblemUpdate (progress notes via ParentalKey) |
| `mqtt/` | Mqtt telemetry model, Redis helpers, Paho presence daemon, Redis→DB persistence |
| `webfilters/` | WebFilters (black/white domain lists), WebFiltersOrg, WebFiltersMembers |
| `licenses/` | License (RSA-encrypted) model: node_id, org_uuid, controller_token validation; `utils.py` decoder |
| `zabbix/` | ZabbixConfigs (API endpoint), ZabbixNetworks (M2M to Networks); API via `zabbix-utils` |
| `problems/`, `connectors/` | Problem tracking; external connectors — `drivers/` (`headscale.py` API client, `ipinfo_lite.py` ASN/geo lookup, `mqtt.py` remote-call), `redis_ipinfo.py` cached ASN |
| `dashboard/` | CMS dashboard: summary/statistics panels, chart template tags |
| `two_factor_custom/` | Custom 2FA (email OTP setup, backup tokens) |
| `mailauth/` | Passwordless email-login (HMAC-signed login tokens); `mailauth.contrib.admin` for admin login |
| `templates/` | Shared templates: wagtailadmin overrides, auth skins, error pages, dashboard/map templates |
| `dockerize/` | Production Dockerfiles, `cronjobs`, docker env |
| `scripts/` | Utility shell scripts (`zt_member_peers.ds`, `dump_data.ds`) |

---

## Development Commands

```bash
# Environment
source venv/bin/activate
cp env.sample .env            # configure required env vars

# Development server
python manage.py runserver 0.0.0.0:8008
# or gunicorn (start.ds)
./start.ds

# Database
python manage.py migrate
python manage.py createsuperuser

# Management commands
python manage.py mqtt_presence                  # Paho MQTT subscriber daemon -> Mqtt model
python manage.py mqtt_presence_redis            # MQTT listener -> raw JSON in Redis (stage 1)
python manage.py mqtt_presence_redis_to_db      # Redis presence scan -> Mqtt model (stage 2)
python manage.py sync_member_peers              # Get ZeroTier peers per member, cache JSON in Redis
python manage.py ipinfo_list_peers              # Resolve member IPs via ipinfo.io -> ASN/geo Redis cache

# Static files
python manage.py collectstatic --noinput

# Type checking
pyright                      # (pyrightconfig.json, venvPath=., venv=venv)
```

---

## Code Conventions & Common Patterns

### Architecture patterns
- **ZeroTier first, Headscale alternative**: `controllers/backend.py` `Zerotier` is the canonical controller client; `headscale/` mirrors it for tailscale-style control planes.
- **`save()` override for side effects**: `Members.save()` (and controller/network saves) push changes to external services (ZeroTier API) on every write. Editing these models triggers real-time sync — beware unintended API calls.
- **Function-based JSON views**: API endpoints (e.g. `members/views.py`) are plain Django FBVs returning `JsonResponse`, not DRF viewsets. Only `members/serializers.py` is DRF (read-only nested `Mqtt`). Match this if adding endpoints.
- **Wagtail modeladmin hooks**: Admin UI lives in each app's `wagtail_hooks.py` via ModelAdmin + custom `PermissionHelper`/`ButtonHelper` for role-based access (org scoping). `admin.py` files are empty stubs — do not build Django admin.
- **Multi-tenancy by Organization**: `accounts.User.organization` FK; most models carry an org/uuid link (e.g. `org_uuid`, `DEFAULT_ORGANIZATION_UUID` env). `config/utils.py` `get_user()`/`to_list()` are common helpers.
- **Cron-driven background work**: `*_workers.py` expose plain functions; Docker crontab (`dockerize/cronjobs`) invokes them via `manage.py shell`. No Celery, no APScheduler.
- **Telemetry model pattern**: `Mqtt` stores a snapshot; per-metric parsers (CPU, memory, quota) live on the model; `mqtt/redis.py` serves cached reads. `MonitorRules` define thresholds applied in `monitor/utils.py`.

### Naming
- snake_case functions/variables; CamelCase models.
- Apps mirror ZeroTier vocabulary: `members` (nodes/peers), `networks` (ZeroTier networks), `controllers` (ZeroTier controllers).
- Management commands: `zt_*` and `sync_*` prefixes for controller/import work.
- `workers.py` = cron-callable sync functions; `backend.py` = external API client class; `wagtail_hooks.py` = modeladmin/panel registration.

### Error handling
- Use `django.core.exceptions.ObjectDoesNotExist`; duck-typing with `try/except` around external API calls.
- External-service failures (ZeroTier, Zabbix, MQTT) are caught and logged, not raised into views.

---

## Important Files

| File | Role |
|---|---|
| `config/settings.py` | Settings, ~100 env vars, middleware stack, auth backends, DB config, MQTT/Redis/Headscale/Zabbix config |
| `config/urls.py` | Root URL config; `accounts/` → `mailauth.urls` |
| `config/customviews.py` | Custom login views (mailauth/two-factor wiring) |
| `config/middlewares.py` | Custom middleware |
| `config/utils.py` | Shared helpers: `get_user()`, `to_list()` |
| `config/logging.py` | HostnameFilter + auth-event logging to syslog |
| `accounts/models.py` | User, Organizations, Features, GroupOrganizations, Devices |
| `members/models.py` | Core Members model + ZeroTier sync in `save()` (~1147 lines) |
| `members/views.py` | FBC JSON API views (member queries, map data) |
| `members/serializers.py` | Read-only DRF serializer (nested Mqtt) |
| `networks/models.py` + `signals.py` | Networks/routes/rules + cascade signals |
| `controllers/backend.py` | `Zerotier` API client class |
| `controllers/workers.py` | ZeroTier import/sync, peer refresh, periodic sync |
| `controllers/rule-compiler/` | Node.js CLI: compiles NetworkRules to ZeroTier JSON |
| `mqtt/models.py`, `mqtt/redis.py`, `mqtt/redis_to_db.py` | Telemetry model + Redis caching + persistence |
| `monitor/models.py`, `monitor/workers.py`, `monitor/utils.py` | Threshold monitoring |
| `problems/models.py` | MemberProblems, ProblemUpdate |
| `licenses/models.py` + `utils.py` | RSA-encrypted license validation/decoding |
| `headscale/models.py`, `headscale/workers.py` | Headscale alternative controller |
| `zabbix/models.py` | Zabbix config/network mapping |
| `webfilters/views.py` + `urls.py` | FBC API: get_webfilter_by_network/member (`/api/network/<id>/`, `/member/<id>/`) |
| `connectors/drivers/` | `headscale.py` API client, `ipinfo_lite.py` ASN lookup, `mqtt.py` remote-call (`MQTT_TOPIC_RCALL`) |
| `connectors/redis_ipinfo.py` | `get_as_name(ip)` — cached ASN from Redis |
| `dashboard/wagtail_hooks.py`, `summary_panels.py`, `statistic_panels.py` | CMS dashboard panels |
| `two_factor_custom/core.py` | 2FA core (email OTP, backup tokens) |
| `mailauth/` (backends, signing, views) | Passwordless email login + HMAC token signing |
| `requirements.txt` | Python deps (pinned) |
| `env.sample` | Env variable template |
| `manage.py` | Django entry point |

---

## Runtime & Tooling Preferences

- **Runtime**: Python 3.12 (venv at `/venv`), no Poetry/Pipenv.
- **Framework**: Django **5.2.12** + Wagtail **7.0.6**.
- **DB**: single default DB, engine from `DB_ENGINE` env — SQLite default (dev, `db.sqlite3`), MySQL/MariaDB in production (via `mysqlclient`). `psycopg2-binary` present for PostgreSQL option. Multi-DB blocks are commented out.
- **Cache/Broker**: Redis (`django-redis`, `hiredis`) — db 0 MQTT telemetry, db 1 peer cache.
- **Web server**: Gunicorn 20.1.0 (`config/gunicorn.py` / `gunicorn_docker.py`, bind `0.0.0.0:8008`, 5 sync workers). ASGI present (`config/asgi.py`) but not used in prod.
- **Package manager**: pip, pinned `requirements.txt`.
- **Type checker**: Pyright (`venvPath=./venv`, no strict mode).
- **No linter/formatter** configured — match existing style.
- **MQTT**: Paho `paho-mqtt==1.6.1`; broker external via `MQTT_BROKER_HOST`.
- **Monitoring**: `zabbix-utils` client; `django-prometheus` for metrics.
- **Deployment**: Docker multi-entrypoint (dev `entrypoint.ds`, prod `entrypoint_gunicorn.ds`, plus MQTT/cron/sync entrypoints). `dockerize/cronjobs` schedules workers.

---

## Testing & QA

- **Framework**: Django's built-in `unittest`/`django.test.TestCase`. No pytest installed.
- **Status**: No meaningful tests. All 14 app `tests.py` files are placeholders (`from django.test import TestCase` only). Only fixture in repo is `controllers/fixtures/controllers.json` (data, not test fixture).
- **Run**: `python manage.py test` (SQLite test DB when env unset).
- **Coverage**: None configured. No CI/CD pipeline (no GitHub Actions/GitLab/Buildkite).
- **Verification today** is manual: Wagtail admin, `manage.py` management commands, Docker deployment.
- **When adding tests**: Use Django `TestCase`; mock external APIs (ZeroTier, Zabbix, MQTT, Headscale); test model `save()` side effects and `monitor/utils.py` threshold logic which are currently untested.
- **Multiple DBs / external deps**: unit tests should target pure logic (`monitor/utils.py`, `licenses/utils.py`, rule compiler) that needs no live services.

---

## Environment Variables

See `env.sample` for full template (~40+ vars). Key groups:

```
# Django
DJANGO_SECRET_KEY, DJANGO_SETTINGS_MODULE, DEBUG

# Database
DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Redis
REDIS_HOST, REDIS_PORT
# MQTT
MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_TOPIC

# ZeroTier controllers
# Headscale
HEADSCALE_URL, HEADSCALE_API_KEY
# Zabbix
ZABBix_* (endpoint, user, password)
# 2FA / auth
IS_MAILAUTH_NO_PASSWORD, MAILAUTH_*, WAGTAILUSERS_PASSWORD_ENABLED
# Org
DEFAULT_ORGANIZATION_UUID
# Misc
GOOGLE_MAPS key (map dashboard), RTTY, syslog, quotas, license features
```

---

## Gotchas for AI Assistants

1. **`Members.save()` hits ZeroTier API** — editing members in code/migrations triggers real-time controller sync with side effects. Wrap or call field-level `.update()` when you must avoid API calls.
2. **Admin is Wagtail modeladmin**, not Django admin. Modify UI via `wagtail_hooks.py` + PermissionHelper/ButtonHelper. `admin.py` stubs are dead code.
3. **API style is Django FBC `JsonResponse`**, not DRF. Only `members/serializers.py` is DRF. Match FBC for new endpoints.
4. **Workers are cron functions**, not APScheduler/Celery. New background tasks = function in `*_workers.py` + entry in `dockerize/cronjobs`.
5. **Node.js rule compiler**: `controllers/rule-compiler/` compiles NetworkRules to ZeroTier JSON — requires Node at runtime (Node.js installed in Docker image).
6. **Empty tests everywhere** — write your own; don't expect an existing suite.
7. **`.ds` files are Docker Compose entrypoints**, not plain shell to exec directly.
8. **Multi-tenancy**: every query touching members/networks/problems should scope by org (`get_user()`, `org_uuid`, `DEFAULT_ORGANIZATION_UUID`).
9. **`.env` is gitignored** — use `env.sample`. Never commit `.env` or `db.sqlite3`.
10. **DRF serializer is read-only** — no write path there.
11. **Redis dual-purpose** — db0 MQTT telemetry, db1 peer cache; don't collide keys.
12. **`config/utils.py`** (`get_user()`, `to_list()`) is the shared-helper home. Prefer adding helpers there over new modules.
13. **Nuxt frontend (`frontend/`)**: Nuxt 4.5.2 SPA (Vue 3, Pinia, Tailwind v4, ECharts), `ssr: false`, `app.baseURL: "/app/"`, static via `nuxi generate`. Django = auth + API backend; read-only org-scoped `/api/app/*` FBVs in `app/` (`@login_required` + `@never_cache` — cache middleware leaks cross-user otherwise). NEVER call `Members.save()` from these views. Dev: `npm run dev` proxies `/api`, `/accounts`, `/login`, `/two`, `/custom`, `/documents` → Django `:8008`; backend needs `IS_CACHE=True` (no Redis) or live Redis. Prod: `frontend/Dockerfile` → nginx static + proxy to Django (`DJANGO_UPSTREAM` env, default `http://django:8008`). Google Maps keyless dev = gray tiles.
