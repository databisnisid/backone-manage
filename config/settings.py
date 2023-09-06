import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = str(os.getenv('SECRET_KEY', 'CHANGE-ME-SECRET'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
#DEVELOPMENT = os.getenv('DEVELOPMENT', 'False').lower() in ('true', '1', 't')


ALLOWED_HOSTS = [str(os.getenv('ALLOWED_HOSTS', '*'))]


# Application definition

INSTALLED_APPS = [
    'accounts',
    'dashboard',
    'controllers',
    'networks',
    'members',
    'mqtt',
    'connectors',
    'monitor',
    'qr_code',
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    'modelcluster',
    'taggit',
    'wagtailgeowidget',
    'wagtail_modeladmin',
    #'wagtail.contrib.modeladmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

MIDDLEWARE += ('wagtail.contrib.redirects.middleware.RedirectMiddleware',)
MIDDLEWARE += ('crum.CurrentRequestUserMiddleware',)

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}

DATABASES = {
    'default': {
        'ENGINE': str(os.getenv('DB_ENGINE')),
        'NAME': str(os.getenv('DB_NAME')),
        'USER': str(os.getenv('DB_USER')),
        'PASSWORD': str(os.getenv('DB_PASSWORD')),
        'HOST': str(os.getenv('DB_HOST')),
        'PORT': str(os.getenv('DB_PORT')),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Jakarta'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media File
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# SITE NAME
WAGTAIL_SITE_NAME = str(os.getenv('WAGTAIL_SITE_NAME', 'BackOne Manage'))

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
#WAGTAILADMIN_BASE_URL = "https://manage.backone.cloud"
WAGTAILADMIN_BASE_URL = str(os.getenv('WAGTAILADMIN_BASE_URL', 'https://manage.backone.cloud'))

ADDITIONAL_DOMAINS = str(os.getenv('ADDITIONAL_DOMAINS', 'https://mn.mysmartrouter.net'))

# CSRF
#CSRF_TRUSTED_ORIGINS = [WAGTAILADMIN_BASE_URL, ADDITIONAL_DOMAINS]
CSRF_TRUSTED_ORIGINS = [WAGTAILADMIN_BASE_URL, ADDITIONAL_DOMAINS]

#print(CSRF_TRUSTED_ORIGINS)

#CSRF_TRUSTED_ORIGINS += ADDITIONAL_DOMAINS
#for DOMAIN in ADDITIONAL_DOMAINS:
#    print(DOMAIN)
#    CSRF_TRUSTED_ORIGINS += DOMAIN



# Controller Rule Compiler
NODEJS = str(os.getenv('NODEJS', '/usr/bin/node'))
CLIJS = str(BASE_DIR) + '/controllers/rule-compiler/cli.js'

# User
AUTH_USER_MODEL = 'accounts.User'

# Custom Form
WAGTAIL_USER_EDIT_FORM = 'accounts.forms.CustomUserEditForm'
WAGTAIL_USER_CREATION_FORM = 'accounts.forms.CustomUserCreationForm'
WAGTAIL_USER_CUSTOM_FIELDS = ['organization']

# WAGTAIL 4.1
WAGTAIL_ENABLE_WHATS_NEW_BANNER = False

# MQTT
MQTT_USER = str(os.getenv('MQTT_USER'))
MQTT_PASS = str(os.getenv('MQTT_PASS'))
MQTT_HOST = str(os.getenv('MQTT_HOST', 'mqtt.backone.cloud'))
MQTT_PORT = str(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC_PRESENCE = str(os.getenv('MQTT_TOPIC_PRESENCE', 'backone/presence'))
MQTT_TOPIC_RCALL = str(os.getenv('MQTT_TOPIC_RCALL', 'backone/rcall'))

# Monitor
#MONITOR_DELAY = 720 # 12 minutes
MONITOR_DELAY = int(os.getenv('MONITOR_DELAY', '1800'))

# Online Status Delay
ONLINE_STATUS_DELAY = int(os.getenv('ONLINE_STATUS_DELAY', '1250'))

# SSH
SSH_DEFAULT_USER = str(os.getenv('SSH_DEFAULT_USER'))
SSH_DEFAULT_PASS = str(os.getenv('SSH_DEFAULT_PASS'))

# GOOGLE_MAPS
GOOGLE_MAPS_V3_APIKEY = str(os.getenv('GOOGLE_MAPS_V3_APIKEY'))
GEO_WIDGET_DEFAULT_LOCATION = {'lat': -6.175349682264274, 'lng': 106.82715256580741}
GEO_WIDGET_ZOOM = int(os.getenv('GEO_WIDGET_ZOOM', '15'))
MAP_CENTER = str(os.getenv('MAP_CENTER', 'lat: -1.233982000061532, lng: 116.83728437200422'))
MAP_ZOOM = int(os.getenv('MAP_ZOOM', 5))

# INTERCONNECT TO data.backone.cloud
DATA_URI_QUOTA = str(os.getenv('DATA_URI_QUOTA', 'https://data.backone.cloud/quota/'))

# QUOTA
QUOTA_GB_WARNING = int(os.getenv('QUOTA_GB_WARNING', 5))
QUOTA_DAY_WARNING = int(os.getenv('QUOTA_DAY_WARNING', 5))
