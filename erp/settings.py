"""Configuration Django de l'ERP.

La base de données est choisie via la variable d'environnement DB_ENGINE :
  - sqlite      (par défaut, développement)
  - postgresql  (production web)
  - mssql       (SQL Server, environnement Windows / Sage)
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file():
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    return env(key, str(default)).lower() in ("1", "true", "yes", "on")


SECRET_KEY = env("SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# Hébergement Render (version en ligne de test) : le nom d'hôte public est fourni par la plateforme
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "rest_framework",
    "rest_framework.authtoken",
    "apps.core",
    "apps.commercial",
    "apps.comptabilite",
    "apps.reporting",
    "apps.transport",
    "apps.echanges",
    "apps.garage",
    "apps.personnel",
    "apps.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",       # fichiers statiques servis sans serveur web séparé
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "apps.core.middleware.AutorisationsMiddleware",      # Fichier › Autorisations d'accès
    "apps.core.journal.RequeteCouranteMiddleware",       # utilisateur du journal des événements
    "apps.core.selection.SelectionMiddleware",           # fenêtre de sélection avant les états
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
# Les fenêtres internes du bureau (façon Sage) affichent les pages du logiciel dans des cadres : même site seulement
X_FRAME_OPTIONS = "SAMEORIGIN"


ROOT_URLCONF = "erp.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.societe",
            ],
        },
    },
]

WSGI_APPLICATION = "erp.wsgi.application"

DB_ENGINE = env("DB_ENGINE", "sqlite").lower()
if env("DATABASE_URL"):
    # postgresql://utilisateur:mot_de_passe@hôte:port/base (format des hébergeurs)
    from urllib.parse import unquote, urlsplit

    _url = urlsplit(env("DATABASE_URL"))
    DB_ENGINE = "postgresql"
    os.environ.update({"DB_NAME": _url.path.lstrip("/"), "DB_USER": unquote(_url.username or ""),
                       "DB_PASSWORD": unquote(_url.password or ""), "DB_HOST": _url.hostname or "",
                       "DB_PORT": str(_url.port or 5432)})
if DB_ENGINE == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "erp"),
            "USER": env("DB_USER", "erp"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", "5432"),
        }
    }
elif DB_ENGINE == "mssql":
    DATABASES = {
        "default": {
            "ENGINE": "mssql",
            "NAME": env("DB_NAME", "ERP"),
            "USER": env("DB_USER", ""),               # vide : authentification Windows
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", ""),               # vide : port de l'instance nommée
            "OPTIONS": {k: v for k, v in {
                # pyodbc avec le pilote ODBC 17/18 installé, ou « mssql_python » (pilote fourni, rien à installer)
                "python_driver": env("DB_PYTHON_DRIVER", ""),
                "driver": env("DB_DRIVER", ""),
                "extra_params": env("DB_EXTRA_PARAMS", "TrustServerCertificate=yes"),
            }.items() if v},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            # SQLITE_FICHIER : autre fichier de base, ex. pour un essai de reprise séparé (essai-janvier.sqlite3)
            "NAME": BASE_DIR / env("SQLITE_FICHIER", "db.sqlite3"),
            # Plusieurs postes du réseau local sur le même serveur : attendre un verrou plutôt qu'échouer,
            # et journal WAL (lectures pendant les écritures)
            "OPTIONS": {"timeout": 20, "init_command": "PRAGMA journal_mode=WAL;"},
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "fr"
TIME_ZONE = env("TIME_ZONE", "Africa/Douala")
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "core:portail"
LOGOUT_REDIRECT_URL = "login"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated",
                                   "apps.core.droits.DroitsMenusAPI"],          # autorisations d'accès par menu
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "COERCE_DECIMAL_TO_STRING": False,
}
