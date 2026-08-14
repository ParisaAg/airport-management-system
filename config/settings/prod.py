import os

import dj_database_url
from django.core.exceptions import (
    ImproperlyConfigured,
)

from .base import *  # noqa: F403


def required_env(name):
    value = os.getenv(name)

    if not value:
        raise ImproperlyConfigured(
            (
                "Required environment variable "
                f"{name} is missing."
            )
        )

    return value


def add_unique(items, value):
    value = value.strip()

    if value and value not in items:
        items.append(value)


DEBUG = False

SECRET_KEY = required_env(
    "SECRET_KEY"
)


# -------------------------------------------------
# Allowed hosts
# -------------------------------------------------

ALLOWED_HOSTS = env_list(  # noqa: F405
    "ALLOWED_HOSTS"
)

RENDER_EXTERNAL_HOSTNAME = os.getenv(
    "RENDER_EXTERNAL_HOSTNAME",
    "",
).strip()

add_unique(
    ALLOWED_HOSTS,
    RENDER_EXTERNAL_HOSTNAME,
)

VERCEL_HOSTNAMES = (
    os.getenv(
        "VERCEL_URL",
        "",
    ),
    os.getenv(
        "VERCEL_PROJECT_PRODUCTION_URL",
        "",
    ),
)

for hostname in VERCEL_HOSTNAMES:
    add_unique(
        ALLOWED_HOSTS,
        hostname,
    )

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        (
            "ALLOWED_HOSTS must contain "
            "at least one host."
        )
    )


# -------------------------------------------------
# Database
# -------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()

DB_CONN_MAX_AGE = int(
    os.getenv(
        "DB_CONN_MAX_AGE",
        "60",
    )
)

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=DB_CONN_MAX_AGE,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": (
                "django.db.backends.postgresql"
            ),
            "NAME": required_env(
                "DB_NAME"
            ),
            "USER": required_env(
                "DB_USER"
            ),
            "PASSWORD": required_env(
                "DB_PASSWORD"
            ),
            "HOST": required_env(
                "DB_HOST"
            ),
            "PORT": os.getenv(
                "DB_PORT",
                "5432",
            ),
            "CONN_MAX_AGE": (
                DB_CONN_MAX_AGE
            ),
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "sslmode": os.getenv(
                    "DB_SSLMODE",
                    "require",
                ),
            },
        }
    }


# -------------------------------------------------
# Static files
# -------------------------------------------------

MIDDLEWARE.insert(  # noqa: F405
    1,
    (
        "whitenoise.middleware."
        "WhiteNoiseMiddleware"
    ),
)

STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage."
            "FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}


# -------------------------------------------------
# CSRF trusted origins
# -------------------------------------------------

CSRF_TRUSTED_ORIGINS = env_list(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS"
)

RENDER_EXTERNAL_URL = os.getenv(
    "RENDER_EXTERNAL_URL",
    "",
).strip().rstrip("/")

add_unique(
    CSRF_TRUSTED_ORIGINS,
    RENDER_EXTERNAL_URL,
)

for hostname in VERCEL_HOSTNAMES:
    hostname = hostname.strip()

    if hostname:
        add_unique(
            CSRF_TRUSTED_ORIGINS,
            f"https://{hostname}",
        )


# -------------------------------------------------
# HTTPS and browser security
# -------------------------------------------------

SECURE_SSL_REDIRECT = env_bool(  # noqa: F405
    "SECURE_SSL_REDIRECT",
    True,
)

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

USE_X_FORWARDED_HOST = True

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_HSTS_SECONDS = int(
    os.getenv(
        "SECURE_HSTS_SECONDS",
        "31536000",
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = (
    "same-origin"
)

X_FRAME_OPTIONS = "DENY"


# -------------------------------------------------
# Logging
# -------------------------------------------------

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
).upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "production": {
            "format": (
                "{asctime} {levelname} "
                "{name} {message}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": (
                "logging.StreamHandler"
            ),
            "formatter": "production",
        },
    },
    "root": {
        "handlers": [
            "console",
        ],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": [
                "console",
            ],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": [
                "console",
            ],
            "level": "WARNING",
            "propagate": False,
        },
    },
}