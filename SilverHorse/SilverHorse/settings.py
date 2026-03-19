from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-_wp52%!cajfytr2byn6z$zcbr^nb(xs6$a-ypnc3ziqqso=mw7'
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
    'django.contrib.sites',  # обов'язково для allauth

    # Сторонні додатки
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Ваші додатки
    'main',
    'userspace',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # для нових версій allauth
]

ROOT_URLCONF = 'SilverHorse.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # можна додати глобальну папку templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',  # обов'язково для allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'userspace.context_processors.currency_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'SilverHorse.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'silverhorse',
        'USER': 'root',
        'PASSWORD': '14142007Aa',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'uk'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----- Налаштування аутентифікації та allauth -----

# ID сайту для django.contrib.sites (потрібно для allauth)
SITE_ID = 1

# Бекенди аутентифікації
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Налаштування перенаправлення після входу/виходу
LOGIN_REDIRECT_URL = '/dashboard/dashboard/'  # прямий шлях (не ім'я URL)
LOGOUT_REDIRECT_URL = 'home'                  # якщо home — це name='home' у urls.py

# ----- Основні налаштування allauth -----
ACCOUNT_AUTHENTICATION_METHOD = 'email'       # вхід за email замість username
ACCOUNT_EMAIL_REQUIRED = True                 # email обов'язковий
ACCOUNT_EMAIL_VERIFICATION = 'none'           # не вимагати підтвердження email
ACCOUNT_USERNAME_REQUIRED = False             # не вимагати username

# ----- Налаштування для соціальних акаунтів (Google) -----
SOCIALACCOUNT_AUTO_SIGNUP = True              # автоматична реєстрація без форми
SOCIALACCOUNT_EMAIL_REQUIRED = True           # вимагати email від Google
SOCIALACCOUNT_QUERY_EMAIL = True              # запитувати email у Google
SOCIALACCOUNT_LOGIN_ON_GET = True


SOCIALACCOUNT_EMAIL_AUTHENTICATION = True   # для нових версій allauth (0.57+)

# Якщо ви створили власний адаптер, розкоментуйте:
# SOCIALACCOUNT_ADAPTER = 'userspace.adapters.MySocialAccountAdapter'