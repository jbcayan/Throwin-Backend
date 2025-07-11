# =========================
# Basic Imports and Path Setup
# =========================
import os
import dj_database_url
from datetime import timedelta
from pathlib import Path

from decouple import config

# =========================
# Paths and Base Directory
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# Security and Debug Settings
# =========================
# SECRET_KEY: Used for cryptographic signing, keep it secret in production.
# DEBUG: Should be False in production for security.
# ENABLE_SILK: Toggle for Silk profiling middleware.
# ALLOWED_HOSTS: List of allowed host/domain names.

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ENABLE_SILK = config("ENABLE_SILK", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")])

# =========================
# Application Definitions
# =========================
# DJANGO_APPS: Default Django apps.
# THIRD_PARTY_APPS: External packages used.
# PROJECT_APPS: Local apps for this project.
# INSTALLED_APPS: Combined list for Django.
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework",
    "versatileimagefield",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "django_celery_beat",
]

PROJECT_APPS = [
    'core.apps.CoreConfig',
    'common.apps.CommonConfig',
    'accounts.apps.AccountsConfig',
    "store.apps.StoreConfig",
    "payment_service.apps.PaymentServiceConfig",
    "notification.apps.NotificationConfig",
    "gacha.apps.GachaConfig",
    "review.apps.ReviewConfig",
]

if ENABLE_SILK:
    THIRD_PARTY_APPS += [
        "silk",
        "django_extensions",
    ]

if DEBUG:
    THIRD_PARTY_APPS += ["drf_spectacular"]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

# =========================
# Debug Toolbar Panels (Optional)
# =========================
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if ENABLE_SILK:
    MIDDLEWARE += [
        "silk.middleware.SilkyMiddleware",
    ]

ROOT_URLCONF = 'throwin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'throwin.wsgi.application'


# =========================
# Database Configuration
# =========================
# Switches between SQLite and PostgreSQL based on environment variable.

DATABASE_TYPE = config("DATABASE_TYPE", default="sqlite")
if DATABASE_TYPE == "sqlite":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:  # Assuming PostgreSQL as the other option
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME", default="throwin"),
            "USER": config("DB_USER", default="postgres"),
            "PASSWORD": config("DB_PASSWORD", default="postgres"),
            "HOST": config("DB_HOST", default="127.0.0.1"),
            "PORT": config("DB_PORT", default="5432")
        },
        "OPTIONS": {
            "sslmode": "require",  # Add this line if SSL is required
        },
    }
# =========================
# Password Validation
# =========================
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

# =========================
# Internationalization
# =========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Use WhiteNoise to serve static files efficiently in production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files (uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "accounts.User"

APPEND_SLASH = False

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # "https://sub.example.com",
]

CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://throwin-backend.onrender.com",
    "https://backend.throwin-glow.com",
]

SESSION_COOKIE_SECURE = False
CORS_ALLOW_CREDENTIALS = True

CSRF_USE_SESSIONS = True
# CSRF_COOKIE_DOMAIN = 'localhost:5173'
# CSRF_COOKIE_DOMAIN = 'core-sm.online'
CSRF_COOKIE_DOMAIN = None  # Defaults to the current domain


# SESSION_COOKIE_SAMESITE = "Lax"
# CSRF_COOKIE_SAMESITE = "Lax"


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "300/minute",
        "user": "1000/minute",
    },
    "DJANGO_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Throwin Project API',
    'DESCRIPTION': "This is a sample backend API for throwin. Based on a consumer can give tip or review to the restaurant stuff",
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=15),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

# Versatile Image settings
VERSATILEIMAGEFIELD_SETTINGS = {
    # The amount of time, in seconds, that references to created images
    # should be stored in the cache. Defaults to `2592000` (30 days)
    "cache_length": 2592000,
    # The name of the cache you'd like `django-versatileimagefield` to use.
    # Defaults to 'versatileimagefield_cache'. If no cache exists with the name
    # provided, the 'default' cache will be used instead.
    "cache_name": "versatileimagefield_cache",
    # The save quality of modified JPEG images. More info here:
    # https://pillow.readthedocs.io/en/latest/handbook/image-file-formats.html#jpeg
    # Defaults to 70
    "jpeg_resize_quality": 70,
    # The name of the top-level folder within storage classes to save all
    # sized images. Defaults to '__sized__'
    "sized_directory_name": "__sized__",
    # The name of the directory to save all filtered images within.
    # Defaults to '__filtered__':
    "filtered_directory_name": "__filtered__",
    # The name of the directory to save placeholder images within.
    # Defaults to '__placeholder__':
    "placeholder_directory_name": "__placeholder__",
    # Whether or not to create new images on-the-fly. Set this to `False` for
    # speedy performance but don't forget to 'pre-warm' to ensure they're
    # created and available at the appropriate URL.
    "create_images_on_demand": True,
    # A dot-notated python path string to a function that processes sized
    # image keys. Typically used to md5-ify the 'image key' portion of the
    # filename, giving each a uniform length.
    # `django-versatileimagefield` ships with two post processors:
    # 1. 'versatileimagefield.processors.md5' Returns a full length (32 char)
    #    md5 hash of `image_key`.
    # 2. 'versatileimagefield.processors.md5_16' Returns the first 16 chars
    #    of the 32 character md5 hash of `image_key`.
    # By default, image_keys are unprocessed. To write your own processor,
    # just define a function (that can be imported from your project's
    # python path) that takes a single argument, `image_key` and returns
    # a string.
    "image_key_post_processor": None,
    # Whether to create progressive JPEGs. Read more about progressive JPEGs
    # here: https://optimus.io/support/progressive-jpeg/
    "progressive_jpeg": False,
}

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'profile_image': [
        ('full_size', 'url'),
        ('small', 'thumbnail__400x400'),
        ('medium', 'thumbnail__600x600'),
        ('large', 'thumbnail__1000x1000')
    ],
    "store_logo": [
        ('full_size', 'url'),
        ('small', 'thumbnail__400x400'),
        ('medium', 'thumbnail__600x600'),
        ('large', 'thumbnail__1000x1000')
    ],
    "store_banner": [
        ('full_size', 'url'),
        ('small', 'thumbnail__400x400'),
        ('medium', 'thumbnail__600x600'),
        ('large', 'thumbnail__1000x1000')
    ],
    "restaurant_logo": [
        ('full_size', 'url'),
        ('small', 'thumbnail__400x400'),
        ('medium', 'thumbnail__600x600'),
        ('large', 'thumbnail__1000x1000')
    ],
    "restaurant_banner": [
        ('full_size', 'url'),
        ('small', 'thumbnail__400x400'),
        ('medium', 'thumbnail__600x600'),
        ('large', 'thumbnail__1000x1000')
    ],
}

GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET")

LINE_CHANNEL_ID = config("LINE_CHANNEL_ID")
LINE_CHANNEL_SECRET = config("LINE_CHANNEL_SECRET")

SOCIAL_AUTH_PASSWORD = config("SOCIAL_AUTH_PASSWORD")

EMAIL_BACKEND = config("EMAIL_BACKEND")
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT")
EMAIL_USE_TLS = config("EMAIL_USE_TLS")
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:5173")
SITE_DOMAIN = config("SITE_DOMAIN", default="http://localhost:8000")

SITE_NAME = "Throwin"

# For docker Redis Caching
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        # "LOCATION": "redis://localhost:6379",
        "LOCATION": "redis://redis_cache:6379",
    }
}