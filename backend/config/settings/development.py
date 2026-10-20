from .base import *

DEBUG = True

# In development, ensure SQLite can be used smoothly if local PostgreSQL is unavailable
try:
    if not USE_SQLITE and DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
        import psycopg2

        conn = psycopg2.connect(
            dbname=DATABASES["default"]["NAME"],
            user=DATABASES["default"]["USER"],
            password=DATABASES["default"]["PASSWORD"],
            host=DATABASES["default"]["HOST"],
            port=DATABASES["default"]["PORT"],
            connect_timeout=1,
        )
        conn.close()
except Exception:
    # Fallback to local SQLite for frictionless development and test runs
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

CELERY_TASK_ALWAYS_EAGER = True
