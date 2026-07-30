from .dev import *  # noqa: F403


SECRET_KEY = "test-only-secret-key"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = (
    "django.core.mail.backends.locmem.EmailBackend"
)