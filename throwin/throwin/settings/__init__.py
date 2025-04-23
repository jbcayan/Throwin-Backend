from decouple import config

PRODUCTION = config("PRODUCTION", default=False, cast=bool)
DEVELOPMENT = config("DEVELOPMENT", default=True, cast=bool)

if PRODUCTION:
    from .production import *
elif DEVELOPMENT:
    from .development import *
else:
    from .local import *

# Session Settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Store sessions in the database
SESSION_COOKIE_AGE = 60*60  # 1 hour (60 minutes * 60 seconds)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expire session when the browser is closed
SESSION_SAVE_EVERY_REQUEST = True  # Refresh session expiry on each request
