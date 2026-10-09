from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR.parent / ".env")
SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-development-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "corsheaders", "rest_framework", "drf_spectacular", "rest_framework_simplejwt.token_blacklist",
    "modules.accounts", "modules.profiles", "modules.resumes", "modules.exports",
    "modules.billing", "modules.analytics", "modules.support",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.PrivateApiNoStoreMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.debug", "django.template.context_processors.request",
              "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": env.db("DATABASE_URL", default="postgresql://kabulcv:kabulcv-local-only@db:5432/kabulcv")}
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("fa", "Dari"), ("ps", "Pashto")]
TIME_ZONE = env("TIME_ZONE", default="Asia/Kabul")
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "private_media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:53000"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:53000"])
REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
                  "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema", "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
                  "PAGE_SIZE": 20, "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
                  "DEFAULT_THROTTLE_RATES": {"registration": "5/hour", "activation": "10/hour", "login": "10/minute", "refresh": "60/minute", "recovery": "5/hour", "preview": "30/hour", "export": "20/hour", "contact": "5/hour", "page_view": "60/minute"},
                  "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler"}
SPECTACULAR_SETTINGS = {"TITLE": "KabulCV API", "VERSION": "1.0.0", "SERVE_INCLUDE_SCHEMA": False}
CELERY_BROKER_URL = env("REDIS_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_TRACK_STARTED = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="mailpit")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="KabulCV <noreply@kabulcv.local>")
PUBLIC_APP_URL = env("PUBLIC_APP_URL", default="http://localhost:53000")
# Payment launch stays closed until an approved merchant and a supported adapter exist.
PAYMENTS_ENABLED = env.bool("PAYMENTS_ENABLED", default=False)
PAYMENT_MERCHANT_APPROVED = env.bool("PAYMENT_MERCHANT_APPROVED", default=False)
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default="")
PAYMENT_API_KEY = env("PAYMENT_API_KEY", default="")
PAYMENT_WEBHOOK_SECRET = env("PAYMENT_WEBHOOK_SECRET", default="")
PAYMENT_ADAPTER_READY = False
SUPPORT_EMAIL = env("SUPPORT_EMAIL", default="")
SUPPORT_WHATSAPP_URL = env("SUPPORT_WHATSAPP_URL", default="")
SUPPORT_TELEGRAM_URL = env("SUPPORT_TELEGRAM_URL", default="")
SUPPORT_OFFICE_ADDRESS = env("SUPPORT_OFFICE_ADDRESS", default="")

from datetime import timedelta
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=5), "REFRESH_TOKEN_LIFETIME": timedelta(days=7), "ROTATE_REFRESH_TOKENS": True, "BLACKLIST_AFTER_ROTATION": True, "AUTH_HEADER_TYPES": ("Bearer",)}
JWT_REFRESH_COOKIE = "kabulcv_refresh"
JWT_REFRESH_COOKIE_PATH = "/api/v1/accounts/auth/"
JWT_COOKIE_SECURE = not DEBUG
JWT_COOKIE_SAMESITE = "Lax"
CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax"

CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": env("CACHE_URL", default="redis://redis:6379/1")}}

PASSWORD_RESET_TIMEOUT = 60 * 60
