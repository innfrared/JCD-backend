"""
Django settings for jasmine_backend project.
"""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get('DEBUG', 'False') == 'True'
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-only-key'
    else:
        raise RuntimeError('SECRET_KEY environment variable is required when DEBUG=False')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        'ALLOWED_HOSTS',
        'localhost,127.0.0.1,jcd-backend.onrender.com'
    ).split(',')
    if host.strip()
]

APPEND_SLASH = False

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'src.infrastructure.db',
    'storages',
]

AUTH_USER_MODEL = 'db.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'config.security_middleware.SecurityHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            ssl_require=True,
        )
    }

    db_conn_max_age = os.environ.get('DB_CONN_MAX_AGE')
    if db_conn_max_age is not None:
        DATABASES['default']['CONN_MAX_AGE'] = int(db_conn_max_age)
    else:
        DATABASES['default']['CONN_MAX_AGE'] = 600

    if 'pooler.supabase.com' in DATABASE_URL:
        DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = (
            os.environ.get('DB_DISABLE_SERVER_SIDE_CURSORS', 'True') == 'True'
        )
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

CACHE_BACKEND = os.environ.get('CACHE_BACKEND')
CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT_SECONDS', '3600'))
_CACHE_MAX_ENTRIES = int(os.environ.get('CACHE_MAX_ENTRIES', '10000'))

if CACHE_BACKEND:
    CACHES = {
        'default': {
            'BACKEND': CACHE_BACKEND,
            'LOCATION': os.environ.get('CACHE_LOCATION', ''),
            'TIMEOUT': CACHE_TIMEOUT,
            'OPTIONS': {
                'MAX_ENTRIES': _CACHE_MAX_ENTRIES,
            },
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'jcd-default',
            'TIMEOUT': CACHE_TIMEOUT,
            'OPTIONS': {
                'MAX_ENTRIES': _CACHE_MAX_ENTRIES,
            },
        }
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'catalog.timing': {
            'handlers': ['console'],
            'level': os.environ.get('CATALOG_TIMING_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

USE_SUPABASE_S3_MEDIA = os.environ.get('USE_SUPABASE_S3_MEDIA', 'False') == 'True'

if USE_SUPABASE_S3_MEDIA:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    SUPABASE_PROJECT_ID = os.environ['SUPABASE_PROJECT_ID']
    SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'media')

    AWS_S3_ENDPOINT_URL = f'https://{SUPABASE_PROJECT_ID}.supabase.co/storage/v1/s3'
    AWS_ACCESS_KEY_ID = os.environ['SUPABASE_S3_ACCESS_KEY']
    AWS_SECRET_ACCESS_KEY = os.environ['SUPABASE_S3_SECRET_KEY']
    AWS_STORAGE_BUCKET_NAME = SUPABASE_BUCKET
    AWS_S3_REGION_NAME = 'us-east-1'
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False

    MEDIA_URL = (
        f'https://{SUPABASE_PROJECT_ID}.supabase.co/storage/v1/object/public/'
        f'{SUPABASE_BUCKET}/'
    )
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'interfaces.rest.shared.authentication.CookieJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('DRF_THROTTLE_ANON', '120/min'),
        'user': os.environ.get('DRF_THROTTLE_USER', '600/min'),
        'auth_login': os.environ.get('DRF_THROTTLE_AUTH_LOGIN', '10/min'),
        'auth_register': os.environ.get('DRF_THROTTLE_AUTH_REGISTER', '5/min'),
        'auth_refresh': os.environ.get('DRF_THROTTLE_AUTH_REFRESH', '30/min'),
        'auth_logout': os.environ.get('DRF_THROTTLE_AUTH_LOGOUT', '30/min'),
        'catalog_list': os.environ.get('DRF_THROTTLE_CATALOG_LIST', '120/min'),
        'homepage': os.environ.get('DRF_THROTTLE_HOMEPAGE', '120/min'),
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=int(os.environ.get('SIMPLE_JWT_ACCESS_MINUTES', '15'))
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=int(os.environ.get('SIMPLE_JWT_REFRESH_DAYS', '7'))
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

AUTH_COOKIE_SECURE = os.environ.get(
    'AUTH_COOKIE_SECURE',
    'True' if not DEBUG else 'False',
) == 'True'
AUTH_COOKIE_SAMESITE = os.environ.get(
    'AUTH_COOKIE_SAMESITE',
    'None' if not DEBUG else 'Lax',
)
AUTH_COOKIE_DOMAIN = os.environ.get('AUTH_COOKIE_DOMAIN') or None
AUTH_ACCESS_COOKIE_NAME = os.environ.get('AUTH_ACCESS_COOKIE_NAME', 'jc_access')
AUTH_REFRESH_COOKIE_NAME = os.environ.get('AUTH_REFRESH_COOKIE_NAME', 'jc_refresh')
AUTH_ACCESS_COOKIE_PATH = os.environ.get('AUTH_ACCESS_COOKIE_PATH', '/')
AUTH_REFRESH_COOKIE_PATH = os.environ.get('AUTH_REFRESH_COOKIE_PATH', '/api/auth/')

FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN')
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in (
        os.environ.get('FRONTEND_ORIGINS')
        or FRONTEND_ORIGIN
        or 'http://localhost:3000,http://localhost:5173'
    ).split(',')
    if origin.strip()
]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = FRONTEND_ORIGINS
CORS_ALLOW_CREDENTIALS = True

if CORS_ALLOW_CREDENTIALS and ('*' in CORS_ALLOWED_ORIGINS or CORS_ALLOW_ALL_ORIGINS):
    raise RuntimeError(
        'Credentialed CORS requests require explicit origins; wildcard is not allowed.'
    )

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
] or FRONTEND_ORIGINS

CSRF_COOKIE_SECURE = AUTH_COOKIE_SECURE
CSRF_COOKIE_SAMESITE = AUTH_COOKIE_SAMESITE
CSRF_COOKIE_DOMAIN = AUTH_COOKIE_DOMAIN
SESSION_COOKIE_SECURE = AUTH_COOKIE_SECURE
SESSION_COOKIE_SAMESITE = AUTH_COOKIE_SAMESITE
SESSION_COOKIE_DOMAIN = AUTH_COOKIE_DOMAIN

if AUTH_COOKIE_SAMESITE == 'None' and not AUTH_COOKIE_SECURE:
    raise RuntimeError(
        'AUTH_COOKIE_SECURE must be True when AUTH_COOKIE_SAMESITE=None.'
    )
if not DEBUG and AUTH_COOKIE_SAMESITE != 'None':
    raise RuntimeError(
        'Cross-site production auth requires AUTH_COOKIE_SAMESITE=None.'
    )

SECURE_SSL_REDIRECT = os.environ.get(
    'SECURE_SSL_REDIRECT',
    'True' if not DEBUG else 'False',
) == 'True'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = int(
    os.environ.get('SECURE_HSTS_SECONDS', '31536000' if not DEBUG else '0')
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    'True' if not DEBUG else 'False',
) == 'True'
SECURE_HSTS_PRELOAD = os.environ.get(
    'SECURE_HSTS_PRELOAD',
    'True' if not DEBUG else 'False',
) == 'True'

SECURITY_CSP_REPORT_ONLY = os.environ.get(
    'SECURITY_CSP_REPORT_ONLY',
    "default-src 'self'",
)

DATA_UPLOAD_MAX_MEMORY_SIZE = int(
    os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', str(2 * 1024 * 1024))
)
FILE_UPLOAD_MAX_MEMORY_SIZE = int(
    os.environ.get('FILE_UPLOAD_MAX_MEMORY_SIZE', str(2 * 1024 * 1024))
)