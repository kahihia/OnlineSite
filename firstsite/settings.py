# coding: utf-8
"""
Django settings for firstsite project.

Generated by 'django-admin startproject' using Django 1.10.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
import redis


connection = None


def connect_to_redis():
    global connection
    if connection == None:
        print "set connection"
        connection = redis.StrictRedis(host='localhost', port=6379, db=0)
    # print connection.keys('*')
    print "connect to redis called"
    return connection

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '_=qlig@6jvf%qpp5+#+ts9m$!5!zl^ioi7pfsw1y%_h50$kcdd'
OPENEXCHANGERATES_APP_ID = "444ee7425aa646c0a789ef4a900013ee"

# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = True

ALLOWED_HOSTS = []


# ALLOWED_HOSTS = ['.rizpardakht.com','www.rizpardakht.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'currencies',
    'conversion',
    'interpay',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'session_security',
    'manager',
    'captcha',
    'rest_framework',
    'rest_framework.authtoken'
]

SITE_ID=1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'firstsite.urls'
# AUTO_LOGOUT_DELAY = 30
SESSION_COOKIE_AGE = 30 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# SESSION_IDLE_TIMEOUT = 20
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
# SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_SECURITY_WARN_AFTER = 28 * 60
SESSION_SECURITY_EXPIRE_AFTER = 30 * 60
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
		        'currencies.context_processors.currencies',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                "django.template.context_processors.media",

            ],
            # 'loaders': [
            #     'django_jinja.loaders.AppLoader',
            #     'django_jinja.loaders.FileSystemLoader',
            # ]
        },
    },
]

WSGI_APPLICATION = 'firstsite.wsgi.application'
# SERVERSET
# MEDIA_ROOT = '/home/salman/firstsite/media/'


MEDIA_ROOT = '/home/sepehr/firstsite/media/'
MEDIA_URL = '/media/'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin and to ensure compatibility with other packages
    'django.contrib.auth.backends.ModelBackend',
    # 'allauth' specific authentication methods
    'allauth.account.auth_backends.AuthenticationBackend',
)



#SERVERSET
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.mysql',
#        'NAME': 'rizpardakht',
#        'USER': 'riz',
#        'PASSWORD': 'riz321',
#        'HOST': 'localhost',
#        'PORT': '',        
#    }
#}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}




# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-gb'
ugettext = lambda s: s

#TIME_ZONE = 'UTC'
TIME_ZONE = 'Iran'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static")

from django.utils.translation import ugettext_lazy as _ut
LANGUAGES = (
    ('en-gb', _ut('English')),
    ('fa-ir',_ut('Persian')),
)
MEDIA_ROOT = 'interpay/static/interpay/media/'
MEDIA_URL = '/interpay/static/interpay/media/'
STATIC_URL = '/static/'
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)
LOGIN_URL = '/login/'
LOGOUT_URL = '/login/'
# serverset change sepehr to salman
STATICFILES_DIRS = [
    '/home/sepehr/firstsite/interpay/static',
]
prefix_default_language = False
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'logging.NullHandler',
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': "../OnlineSite/interpay/static/example.log",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console':{
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'WARN',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'interpay': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    }
}
#
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://127.0.0.1:6379/1",
#         "OPTIONS": {
# 				'PARSER_CLASS': 'redis.connection.HiredisParser',
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#             "PASSWORD": "interpass"
#         }
#     }
# }
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'auth.smtp.1and1.co.uk'
EMAIL_HOST_USER = 'info@rizpal.com'
EMAIL_HOST_PASSWORD = 'Arman_Naeimian'
EMAIL_PORT = 587

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
}
