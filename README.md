# BackOne Manage - Virtual Network

## Installation
	virtualenv venv -p python3
	source venv/bin/activate
	pip install -r requirements.txt
	python manage.py migrate
	python manage createsuperuser

## Running
	- Modify .env -> Copy from env.example
	- source /venv/bin/activate
	- ./start.ds (use screen to run as daemon)

## Settings
	- Login as superuser
	- Create Controllter
	- Create Features
	- Create Organizations
	- Create user with Organizations
	
## MQTT
	- Running MQTT workers


## Frontend (Nuxt SPA at /app/)

Dedicated Nuxt 4.5.2 SPA serving dashboard / map / members / telemetry / networks views under the `/app/` path prefix. Django stays auth + API backend (`/api/app/*` read-only endpoints); Wagtail modeladmin untouched.

### Dev

```bash
# backend (IS_CACHE=True avoids Redis dead-connection errors without a broker)
IS_CACHE=True python manage.py runserver 0.0.0.0:8008

# frontend (proxies /api, /accounts, /login, /two, /custom, /documents -> :8008)
cd frontend
npm install
cp .env.example .env   # set NUXT_PUBLIC_GOOGLE_MAPS_APIKEY etc.
npm run dev            # http://localhost:3000/app/
```

Login via Django mailauth session; the SPA redirects unauthenticated users to `/login/?next=/app/…`.

### Prod (separate container, static only)

```bash
cd frontend
docker build -t backone-frontend .
docker run -d --name backone-frontend -p 80:80 \
  -e DJANGO_UPSTREAM=http://django:8008 \
  backone-frontend
```

nginx serves the generated static bundle at `/app/` and proxies `/api/`, `/accounts/`, `/two/`, `/login/`, `/logout/`, `/custom/`, `/documents/` to the Django upstream. Override `DJANGO_UPSTREAM` per environment.

Google Maps keyless dev shows gray tiles — set `NUXT_PUBLIC_GOOGLE_MAPS_APIKEY` (and `NUXT_PUBLIC_MAP_CENTER`/`NUXT_PUBLIC_MAP_ZOOM`/`NUXT_PUBLIC_MAP_REFRESH_INTERVAL`) in `frontend/.env`.

Separate-domain frontend (optional): set `CORS_ALLOW_ALL_ORIGINS=false` + `CORS_ALLOWED_ORIGINS` on Django (default preserves old allow-all).

