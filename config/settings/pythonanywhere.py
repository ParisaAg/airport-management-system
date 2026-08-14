import os

from django.core.exceptions import (
    ImproperlyConfigured,
)

from .base import *  # noqa: F403


def required_env(name):
    value = os.getenv(
        name,
        "",
    ).strip()

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

ALLOWED_HOSTS = [
    "parisaaghaei.pythonanywhere.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://parisaaghaei.pythonanywhere.com",
]


DATABASES = {
    "default": {
        "ENGINE": (
            "django.db.backends.sqlite3"
        ),
        "NAME": (
            BASE_DIR  # noqa: F405
            / "db.pythonanywhere.sqlite3"
        ),
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


SECURE_SSL_REDIRECT = True

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

SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = (
    "same-origin"
)

X_FRAME_OPTIONS = "DENY"


LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
).upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": (
                "logging.StreamHandler"
            ),
        },
    },
    "root": {
        "handlers": [
            "console",
        ],
        "level": LOG_LEVEL,
    },
}