from decouple import config

PRODUCTION = config("PRODUCTION", default=False, cast=bool)

if PRODUCTION:
    from .production import *
else:
    from .local import *
