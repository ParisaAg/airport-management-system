import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def required_env(name):
    value = os.getenv(name)

    if not value:
        raise ImproperlyConfigured(
            f"Required environment variable {name} is missing."
        )

    return value


SECRET_KEY = required_env("SECRET_KEY")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")  # noqa: F405

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS must contain at least one host."
    )

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": required_env("DB_NAME"),
        "USER": required_env("DB_USER"),
        "PASSWORD": required_env("DB_PASSWORD"),
        "HOST": required_env("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {
            "sslmode": os.getenv("DB_SSLMODE", "require"),
        },
    }
}

CSRF_TRUSTED_ORIGINS = env_list(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS"
)

SECURE_SSL_REDIRECT = env_bool(  # noqa: F405
    "SECURE_SSL_REDIRECT",
    True,
)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = int(
    os.getenv("SECURE_HSTS_SECONDS", "31536000")
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"