"""
Django settings for manager project.

Generated by 'django-admin startproject' using Django 3.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""


"""
DO NOT EDIT THIS FILE

Settings can be changed by creating a settings_local.py in this directory.
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%u=!8^4b2kkj(&%#%7)3+il456u2zqkaw(6an7$px%_7e&-=-6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
        "127.0.0.1",
        "::1",
        "134.102.188.104",
        "localhost"
        ]


# Application definition

INSTALLED_APPS = [
    'omnetppManager.apps.OmnetppmanagerConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'formtools',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'omnetppManager.processors.get_general',
            ],
        },
    },
]

WSGI_APPLICATION = 'manager.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

LOGIN_REDIRECT_URL = '/'

MEDIA_ROOT = str(os.path.abspath(os.path.join(os.getcwd(), "uploads")))

# Settings for the omnetpp.ini upload
OMNETPPINI_MAX_FILESIZE = 100*1024 # 100 kb
OMNETPPINI_ALLOWED_MIMETYPE = [
        "application/x-wine-extension-ini",
        "application/octet-stream",
        "text/plain",
        ]

DEFAULT_SIMULATION_TIMEOUT = "12h"

# Sender mail address
DEFAULT_SENDER_MAIL_ADDRESS = "server@comnets.uni-bremen.de"

# Base title for the webpage
DEFAULT_MAIN_TITLE = "OPS on the bench"

# Redis connection setup
REDIS_DB_HOST       = "localhost"
REDIS_DB_PORT       = 6379
REDIS_DB_PASSWORD   = None


# Overwrite settings by local ones (if available)
try:
    from .settings_local import *
except ImportError as e:
    pass

