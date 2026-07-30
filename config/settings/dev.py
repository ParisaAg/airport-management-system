import os

from .base import *  # noqa: F403


DEBUG = True

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "development-only-insecure-secret-key",
)

ALLOWED_HOSTS = env_list(  # noqa: F405
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1",
)

if os.getenv("DB_ENGINE", "postgresql").lower() == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "airport_ops"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"