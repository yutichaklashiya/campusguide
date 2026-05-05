from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-li#1a3$&l=ext(f36!ty^bz53c^p+_spyvhsbnt1p1za3wv-wt'

DEBUG = True

ALLOWED_HOSTS = []


# ✅ Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'main_app',
]


# ✅ MIDDLEWARE (IMPORTANT CHANGE)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.locale.LocaleMiddleware',  # 🔥 ADD THIS

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'CampusGuide.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # 🔥 ADD THIS
            ],
        },
    },
]


WSGI_APPLICATION = 'CampusGuide.wsgi.application'


# ✅ Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ✅ Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


from django.utils.translation import gettext_lazy as _

# 🔥🔥🔥 INTERNATIONALIZATION (MAIN PART)

LANGUAGE_CODE = 'en'   # default language

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True
USE_TZ = True

# ✅ Supported languages
LANGUAGES = [
    ('en', _('English')),
    ('hi', _('Hindi')),
    ('gu', _('Gujarati')),
]

# ✅ ADD THIS: Store language in session
LANGUAGE_COOKIE_NAME = 'django_language'
LANGUAGE_SESSION_KEY = 'django_language'

EXTRA_LANG_INFO = {
    'gu': {
        'bidi': False,
        'code': 'gu',
        'name': 'Gujarati',
        'name_local': 'ગુજરાતી',
    },
}

import django.conf.locale
LANG_INFO = django.conf.locale.LANG_INFO.copy()
LANG_INFO.update(EXTRA_LANG_INFO)
django.conf.locale.LANG_INFO = LANG_INFO

# ✅ Translation files location
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]


# ✅ Static files
STATIC_URL = '/static/'


# ✅ Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ✅ Login
LOGIN_URL = 'login'


# ✅ Email config
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'officalcampusguide@gmail.com'
EMAIL_HOST_PASSWORD = 'fcikconxaodrzthy'
EMAIL_SUBJECT_PREFIX = ''
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER