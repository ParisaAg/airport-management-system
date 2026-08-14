import os

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


DEBUG = False

SECRET_KEY = required_env(
    "SECRET_KEY"
)

ALLOWED_HOSTS = env_list(  # noqa: F405
    "ALLOWED_HOSTS"
)

RENDER_EXTERNAL_HOSTNAME = (
    os.getenv(
        "RENDER_EXTERNAL_HOSTNAME",
        "",
    )
    .strip()
)

if (
    RENDER_EXTERNAL_HOSTNAME
    and RENDER_EXTERNAL_HOSTNAME
    not in ALLOWED_HOSTS
):
    ALLOWED_HOSTS.append(
        RENDER_EXTERNAL_HOSTNAME
    )

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        (
            "ALLOWED_HOSTS must contain "
            "at least one host."
        )
    )


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
        "CONN_MAX_AGE": int(
            os.getenv(
                "DB_CONN_MAX_AGE",
                "60",
            )
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


CSRF_TRUSTED_ORIGINS = env_list(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS"
)

RENDER_EXTERNAL_URL = (
    os.getenv(
        "RENDER_EXTERNAL_URL",
        "",
    )
    .strip()
    .rstrip("/")
)

if (
    RENDER_EXTERNAL_URL
    and RENDER_EXTERNAL_URL
    not in CSRF_TRUSTED_ORIGINS
):
    CSRF_TRUSTED_ORIGINS.append(
        RENDER_EXTERNAL_URL
    )

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

X_FRAME_OPTIONS = "DENY"

SECURE_REFERRER_POLICY = (
    "same-origin"
)


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