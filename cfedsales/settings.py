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
from dotenv import load_dotenv
from passlib.context import CryptContext
# Load .env file
load_dotenv()

# Get secret key from .env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")
# CryptContext for hashing
KEY_CRYPT_CONTEXT = CryptContext(
    schemes=['bcrypt'], 
    bcrypt__rounds=12
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['django-dev.ultsglobal.com', 'localhost', '127.0.0.1','192.168.64.3']
CSRF_TRUSTED_ORIGINS = [
    'https://django-dev.ultsglobal.com','http://localhost/','http://192.168.64.3/'
]
LOGIN_REDIRECT_URL = '/sales/dashboard/'
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  
    'rest_framework',
    'rest_framework.authtoken',
    'django_rq',
    'sales',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication'
    ],
}

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
        'PORT': os.getenv('DB_PORT', '6432'),
        'CONN_MAX_AGE': 30,     
        'CONN_HEALTH_CHECKS': True,
        'POOL': {
            'MAX_CONNECTIONS': 5,
            'TIMEOUT': 20
                 },
        'OPTIONS': {
                'application_name': "django_central",
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5,
                
            }
}
}

# Generate shard databases dynamically
def generate_shard_databases(retails):
    shards = {}
    base_config = {
        'ENGINE': 'timescale.db.backends.postgresql',
        'USER': os.getenv('DB_USER', 'django'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'secure_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': '6432',  # Ensure this is PgBouncer port
        'CONN_MAX_AGE': 30,  # Reduce connection age
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        }
    }
    
    for i in retails:
        config = base_config.copy()
        config['NAME'] = f'retail_point_shard_{i}'
        config['OPTIONS'] = base_config['OPTIONS'].copy()
        config['OPTIONS']['application_name'] = f'django_shard_{i}'
        shards[f'shard_{i}'] = config
    
    return shards
RETAIL_IDS = [
    81, 115, 116, 119, 68, 82, 69, 83, 70, 117, 71, 85, 72, 113, 73, 
    77, 78, 79, 80, 86, 87, 88, 89, 90, 91, 92, 94, 95, 96, 97, 98, 
    99, 100, 101, 102, 103, 104, 105, 106, 108, 109, 110, 111, 118, 
    74, 93, 75, 114,
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

STATIC_URL = '/static/'
STATIC_ROOT = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
