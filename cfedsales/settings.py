"""
Django settings for cfedsales project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-mp&!t#8m1-mq$nl53is#xuwq0cn@m1cg-h67pq2$why_mq$ti+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  
    'rest_framework',
    'django_rq',
    'sales',
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

ROOT_URLCONF = 'cfedsales.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'cfedsales.wsgi.application'


# Database
# djangosales/settings.py
import os

# Dynamically configured database shards
DATABASES = {
    'default': {
        'ENGINE': 'timescale.db.backends.postgresql',
        'NAME': os.getenv('CENTRAL_DB_NAME', 'central_sales_db'),
        'USER': os.getenv('DB_USER', 'django'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'secure_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Generate shard databases dynamically
def generate_shard_databases(retails):
    shards = {}
    for i in retails:
        shards[f'shard_{i}'] = {
            'ENGINE': 'timescale.db.backends.postgresql',
            'NAME': f'retail_point_shard_{i}',
            'USER': os.getenv('DB_USER', 'django'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'secure_password'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    return shards
RETAIL_IDS = [
    81, 115, 116, 119, 68, 82, 69, 83, 70, 117, 71, 85, 72, 113, 73, 
    77, 78, 79, 80, 86, 87, 88, 89, 90, 91, 92, 94, 95, 96, 97, 98, 
    99, 100, 101, 102, 103, 104, 105, 106, 108, 109, 110, 111, 118, 
    74, 93, 75, 114
]
DATABASES.update(generate_shard_databases(RETAIL_IDS))

# Database Routing
DATABASE_ROUTERS = ['sales.router.ShardedDatabaseRouter']

# RQ Configuration
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    },
    'sales_processing': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 1,
    },
    'day_close': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 2,
    },
    'send_summary': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 3,
    }
}
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# djangosales/settings.py
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
