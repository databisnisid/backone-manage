import os
import redis
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = str(os.getenv("SECRET_KEY", "CHANGE-ME-SECRET"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
# DEVELOPMENT = os.getenv('DEVELOPMENT', 'False').lower() in ('true', '1', 't')


ALLOWED_HOSTS = [str(os.getenv("ALLOWED_HOSTS", "*"))]


# Application definition

INSTALLED_APPS = [
    #'headscale',
    # "sites_custom",
    "mailauth",
    "mailauth.contrib.admin",
    # "mailauth.contrib.user",
    # "mailauth.contrib.wagtail",
    "licenses",
    "webfilters",
    "accounts",
    "config.apps.CustomUsersAppConfig",
    "dashboard",
    "controllers",
    "networks",
    "members",
    "mqtt",
    "connectors",
    "monitor",
    "problems",
    "qr_code",
    "zabbix",
    #
    "corsheaders",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    # "wagtail.users",
    # "accounts",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "wagtailgeowidget",
    "wagtail_modeladmin",
    #'wagtail.contrib.modeladmin',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_email",  # <- for email capability.
    "two_factor",
    "two_factor.plugins.email",  # <- for email capability.
    "two_factor_custom",
]

AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesStandaloneBackend",
    # Django ModelBackend is the default authentication backend.
    "django.contrib.auth.backends.ModelBackend",
]

# The new access token based authentication backend
AUTHENTICATION_BACKENDS += ("mailauth.backends.MailAuthBackend",)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

MIDDLEWARE += ("wagtail.contrib.redirects.middleware.RedirectMiddleware",)
MIDDLEWARE += ("crum.CurrentRequestUserMiddleware",)
MIDDLEWARE += ("axes.middleware.AxesMiddleware",)
MIDDLEWARE += ("django_otp.middleware.OTPMiddleware",)

MIDDLEWARE += [
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
# }

DATABASES = {
    "default": {
        "ENGINE": str(os.getenv("DB_ENGINE", "django.db.backends.sqlite3")),
        "NAME": str(os.getenv("DB_NAME", "db.sqlite3")),
        "USER": str(os.getenv("DB_USER")),
        "PASSWORD": str(os.getenv("DB_PASSWORD")),
        "HOST": str(os.getenv("DB_HOST", "localhost")),
        "PORT": str(os.getenv("DB_PORT", "3306")),
    },
    # "default_ramdisk": {
    #    "ENGINE": str(os.getenv("DB_ENGINE_2", "django.db.backends.sqlite3")),
    #    "NAME": str(os.getenv("DB_NAME_2", "db.sqlite3-2")),
    #    "USER": str(os.getenv("DB_USER_2")),
    #    "PASSWORD": str(os.getenv("DB_PASSWORD_2")),
    #    "HOST": str(os.getenv("DB_HOST_2", "localhost")),
    #    "PORT": str(os.getenv("DB_PORT_2", "3306")),
    # },
    #    'headscale': {
    #        'ENGINE': str(os.getenv('HS_DB_ENGINE', 'django.db.backends.sqlite3')),
    #        'NAME': str(os.getenv('HS_DB_NAME', 'db.sqlite3.hs')),
    #        'USER': str(os.getenv('HS_DB_USER')),
    #        'PASSWORD': str(os.getenv('HS_DB_PASSWORD')),
    #        'HOST': str(os.getenv('HS_DB_HOST')),
    #        'PORT': str(os.getenv('HS_DB_PORT')),
    #    }
}

# DATABASE_ROUTERS = ["config.db_routers.MqttRouter"]


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Jakarta"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Media File
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# SITE NAME
WAGTAIL_SITE_NAME = str(os.getenv("WAGTAIL_SITE_NAME", "BackOne Manage"))

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
# WAGTAILADMIN_BASE_URL = "https://manage.backone.cloud"
WAGTAILADMIN_BASE_URL = str(
    os.getenv("WAGTAILADMIN_BASE_URL", "https://manage.backone.cloud")
)

# CSRF
# CSRF_TRUSTED_ORIGINS = [WAGTAILADMIN_BASE_URL, ADDITIONAL_DOMAINS]
# CSRF_TRUSTED_ORIGINS = [WAGTAILADMIN_BASE_URL, ADDITIONAL_DOMAIN_1, ADDITIONAL_DOMAIN_2]
CSRF_TRUSTED_ORIGINS = [WAGTAILADMIN_BASE_URL]

ADDITIONAL_DOMAINS = os.getenv(
    "ADDITIONAL_DOMAINS", "https://mn.guanghao-sdwan.id, https://manage.nexusnetwork.id"
)

domains_list = ADDITIONAL_DOMAINS.split(",")

for domain_list in domains_list:
    CSRF_TRUSTED_ORIGINS.append(domain_list.replace(" ", ""))

# Controller Rule Compiler
NODEJS = str(os.getenv("NODEJS", "/usr/bin/node"))
CLIJS = str(BASE_DIR) + "/controllers/rule-compiler/cli.js"

# User
AUTH_USER_MODEL = "accounts.User"


# Custom Form
# WAGTAIL_USER_EDIT_FORM = "accounts.forms.CustomUserEditForm"
# WAGTAIL_USER_CREATION_FORM = "accounts.forms.CustomUserCreationForm"
# WAGTAIL_USER_CUSTOM_FIELDS = ["organization"]

# WAGTAIL 4.2
WAGTAIL_ENABLE_WHATS_NEW_BANNER = False
WAGTAIL_ENABLE_UPDATE_CHECK = False

# MQTT
MQTT_USER = str(os.getenv("MQTT_USER"))
MQTT_PASS = str(os.getenv("MQTT_PASS"))
MQTT_HOST = str(os.getenv("MQTT_HOST", "mqtt.backone.cloud"))
MQTT_PORT = str(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_PRESENCE = str(os.getenv("MQTT_TOPIC_PRESENCE", "backone/presence"))
MQTT_TOPIC_RCALL = str(os.getenv("MQTT_TOPIC_RCALL", "backone/rcall"))

# MQTT_REDIS
MQTT_REDIS_HOST = str(os.getenv("MQTT_REDIS_HOST", "localhost"))
MQTT_REDIS_PORT = int(os.getenv("MQTT_REDIS_PORT", 6379))
MQTT_REDIS_DB = int(os.getenv("MQTT_REDIS_DB", 0))
MQTT_REDIS_SETEX = int(os.getenv("MQTT_REDIS_SETEX", 1800))
MQTT_REDIS_PREFIX = str(os.getenv("MQTT_REDIS_PREFIX", "backone"))

MQTT_REDIS_CONN = redis.Redis(
    host=MQTT_REDIS_HOST,
    port=MQTT_REDIS_PORT,
    db=MQTT_REDIS_DB,
    socket_timeout=1,
)

# Monitor
# MONITOR_DELAY = 720 # 12 minutes
MONITOR_DELAY = int(os.getenv("MONITOR_DELAY", "1800"))

# Online Status Delay
ONLINE_STATUS_DELAY = int(os.getenv("ONLINE_STATUS_DELAY", "1250"))

# SSH
SSH_DEFAULT_USER = str(os.getenv("SSH_DEFAULT_USER"))
SSH_DEFAULT_PASS = str(os.getenv("SSH_DEFAULT_PASS"))
# GROUP NAME which User must be in that GROUP
REMOTE_ACCESS_GROUP_NAME = os.getenv("REMOTE_ACCESS_GROUP_NAME", "RemoteAccess")

# GOOGLE_MAPS
GOOGLE_MAPS_V3_APIKEY = str(os.getenv("GOOGLE_MAPS_V3_APIKEY"))
GEO_WIDGET_DEFAULT_LOCATION = {"lat": -6.175349682264274, "lng": 106.82715256580741}
GEO_WIDGET_ZOOM = int(os.getenv("GEO_WIDGET_ZOOM", "15"))
MAP_CENTER = str(
    os.getenv("MAP_CENTER", "{lat: -1.233982000061532, lng: 116.83728437200422}")
)
MAP_ZOOM = int(os.getenv("MAP_ZOOM", 5))

# INTERCONNECT TO data.backone.cloud
DATA_URI_QUOTA = str(os.getenv("DATA_URI_QUOTA", "https://admin.backone.cloud/quota/"))

# QUOTA
QUOTA_GB_WARNING = int(os.getenv("QUOTA_GB_WARNING", 5))
QUOTA_DAY_WARNING = int(os.getenv("QUOTA_DAY_WARNING", 5))

# MAP DASHBOARD - IN SECONDS
MAP_REFRESH_INTERVAL = int(os.getenv("MAP_REFRESH_INTERVAL", 300))

# MONITOR MEMBER
MEMBER_NEW_PERIOD = int(os.getenv("MEMBER_NEW_PERIOD", 84600))

# AXES
AXES_COOLOFF_TIME = float(os.getenv("AXES_COOLOFF_TIME", 2))
AXES_RESET_ON_SUCCESS = True
# AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']
AXES_LOCKOUT_PARAMETERS = ["username"]
AXES_LOCKOUT_TEMPLATE = "axes/block.html"
AXES_IPWARE_PROXY_COUNT = int(os.getenv("AXES_IPWARE_PROXY_COUNT", 0))
# refer to the Django request and response objects documentation
AXES_IPWARE_META_PRECEDENCE_ORDER = [
    "X_FORWARDED_FOR",
    "HTTP_X_FORWARDED_FOR",
    "REMOTE_ADDR",
]

# HEADSCALE
HEADSCALE_URI = str(os.getenv("HEADSCALE_URI"))
HEADSCALE_KEY = str(os.getenv("HEADSCALE_KEY"))
HEADSCALE_ON = int(os.getenv("HEADSCALE_ON", 0))

# RTTY
RTTY_URI = str(os.getenv("RTTY_URI", "https://remote.manage.backone.cloud"))

# DELETE MEMBER PERIOD
MEMBER_DELETE_PERIOD = int(os.getenv("MEMBER_DELETE_PERIOD", 60))

IS_CACHE = os.getenv("IS_CACHE", "False").lower() not in ("true", "1", "t")
CACHE = {}
# REDIS CACHE
if IS_CACHE:
    CACHES = {
        "default": {
            "BACKEND": str(
                os.getenv(
                    "REDIS_BACKEND", "django.core.cache.backends.redis.RedisCache"
                )
            ),
            "LOCATION": str(os.getenv("REDIS_URL", "redis://localhost:6379/")),
            "KEY_PREFIX": str(os.getenv("REDIS_KEY_PREFIX", "backone")),
            "TIMEOUT": int(
                os.getenv("REDIS_TIMEOUT", 60 * 15)
            ),  # in seconds: 60 * 15 (15 minutes)
        }
    }

# SESSION TIMEOUT
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", 86400))
SESSION_EXPIRE_AT_BROWSER_CLOSE = os.getenv(
    "SESSION_EXPIRE_AT_BROWSER_CLOSE", "False"
).lower() in ("true", "1", "t")
SESSION_SAVE_EVERY_REQUEST = True


# ZABBIX
ZABBIX_URL = os.getenv("ZABBIX_URL", "localhost")
ZABBIX_TOKEN = os.getenv("ZABBIX_TOKEN", "zabbixToken")

# CORS
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = [
#    "https://example.com",
#    "https://sub.example.com",
#    "http://localhost:8080",
#    "http://127.0.0.1:9000",
# ]
# CORS_ALLOWED_ORIGIN_REGEXES = [
#    r"^https://\w+\.example\.com$",
# ]

# PROMETHEUS
MIDDLEWARE = (
    ["django_prometheus.middleware.PrometheusBeforeMiddleware"]
    + MIDDLEWARE
    + ["django_prometheus.middleware.PrometheusAfterMiddleware"]
)

INSTALLED_APPS += ["django_prometheus"]

PROMETHEUS_LATENCY_BUCKETS = (
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.25,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
    25.0,
    50.0,
    75.0,
    float("inf"),
)

PROMETHEUS_METRIC_NAMESPACE = os.getenv("PROMETHEUS_METRIC_NAMESPACE", "backone_manage")

# IPINFO LITE
IPINFO_LITE_TOKEN = os.getenv("IPINFO_LITE_TOKEN")
IPINFO_LITE_PREFIX = os.getenv("IPINFO_LITE_PREFIX", "ipinfo_lite")

# NEXUS FEATURE
DEAUTH_TIMER_MAX = int(os.getenv("DEAUTH_TIMER_MAX", 120))  # 5 * 24 hour

# LICENSE FEATURES
USE_LICENSE_FEATURES = int(os.getenv("USE_LICENSE_FEATURES", 0))

# DEVELOPMENT
IS_INSPECT_ENABLED = int(os.getenv("IS_INSPECT_ENABLED", 0))

# EMAIL SETTING
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 25))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() in ("true", "1", "t")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() in ("true", "1", "t")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@proit.id")

# LOGIN WITH EMAIL ONLY (NO PASSWORD IS REQUIRED)
IS_MAILAUTH_NO_PASSWORD = os.getenv("IS_MAILAUTH_NO_PASSWORD", "False").lower() in (
    "true",
    "1",
    "t",
)

# LOGIN 2MFA EMAIL
IS_2FA_ENABLE = os.getenv("IS_2FA_ENABLE", "False").lower() in ("true", "1", "t")
# How long profile page display before login to home (in milliseconds)
IS_2FA_PROFILE_TIMEOUT = int(os.getenv("IS_2FA_PROFILE_TIMEOUT", "500"))
LOGIN_REDIRECT_URL = os.getenv("LOGIN_REDIRECT_URL", "two_factor:profile")

# WAGTAILUSERS_PASSWORD_ENABLED = False

# Logging
parsed_url = urlparse(WAGTAILADMIN_BASE_URL)

SYSLOG_HOSTNAME = os.getenv("SYSLOG_HOSTNAME", parsed_url.hostname)
SYSLOG_ADDRESS = os.getenv("SYSLOG_ADDRESS", "/dev/null")  # Default to void
SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", 514))

# if SYSLOG_ADDRESS != "/dev/null":
#    SYSLOG_ADDRESS = (SYSLOG_ADDRESS, SYSLOG_PORT)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "add_hostname": {
            "()": "config.logging.HostnameFilter",  # Reference the custom filter class
        },
    },
    "formatters": {
        "verbose": {
            # "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "syslog_formatter": {
            # Format string to include the custom 'hostname' attribute
            "format": "%(asctime)s %(hostname)s %(name)s: %(message)s",
            "datefmt": "%b %d %H:%M:%S",
        },
    },
    "handlers": {
        "syslog": {
            "level": "INFO",
            "class": "logging.handlers.SysLogHandler",
            "filters": ["add_hostname"],  # Apply the filter
            "facility": "local7",  # Or another appropriate facility
            "formatter": "syslog_formatter",
            "address": SYSLOG_ADDRESS,
            # Or 'udp://localhost:514' for a remote server
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "syslog"],
        "level": "INFO",
    },
    "loggers": {
        "auth_event": {
            "handlers": ["console", "syslog"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console", "syslog"],
            "level": "INFO",
            "propagate": False,
        },
        "wagtail": {
            "handlers": ["console", "syslog"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Two Factor
# LOGIN_URL = "two_factor:login"

# this one is optional
# LOGIN_REDIRECT_URL = "two_factor:profile"

# Get IP from Traefik
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# The default meta precedence order (update as needed)
IPWARE_META_PRECEDENCE_ORDER = (
    "X_FORWARDED_FOR",  # Load balancers or proxies such as AWS ELB (default client is `left-most` [`<client>, <proxy1>, <proxy2>`])
    "HTTP_X_FORWARDED_FOR",  # Similar to X_FORWARDED_TO
    "HTTP_CLIENT_IP",  # Standard headers used by providers such as Amazon EC2, Heroku etc.
    "HTTP_X_REAL_IP",  # Standard headers used by providers such as Amazon EC2, Heroku etc.
    "HTTP_X_FORWARDED",  # Squid and others
    "HTTP_X_CLUSTER_CLIENT_IP",  # Rackspace LB and Riverbed Stingray
    "HTTP_FORWARDED_FOR",  # RFC 7239
    "HTTP_FORWARDED",  # RFC 7239
    "HTTP_CF_CONNECTING_IP",  # CloudFlare
    "X-CLIENT-IP",  # Microsoft Azure
    "X-REAL-IP",  # NGINX
    "X-CLUSTER-CLIENT-IP",  # Rackspace Cloud Load Balancers
    "X_FORWARDED",  # Squid
    "FORWARDED_FOR",  # RFC 7239
    "CF-CONNECTING-IP",  # CloudFlare
    "TRUE-CLIENT-IP",  # CloudFlare Enterprise,
    "FASTLY-CLIENT-IP",  # Firebase, Fastly
    "FORWARDED",  # RFC 7239
    "CLIENT-IP",  # Akamai and Cloudflare: True-Client-IP and Fastly: Fastly-Client-IP
    "REMOTE_ADDR",  # Default
)

# SYNC_MEMBER_PEERS_SLEEP
SYNC_MEMBER_PEERS_SLEEP = int(os.getenv("SYNC_MEMBER_PEERS_SLEEP", 60))
