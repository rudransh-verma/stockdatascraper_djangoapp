import os
import environ

# BASE_DIR waise hi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1) .env support
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# 2) Secret key & debug via env
SECRET_KEY='t%u(m!n#5b=f%q6#)4e&iv^t+f7*t$yy%(whi0iu@eh6v9oytd'

DEBUG = False

# 3) Hosts
ALLOWED_HOSTS= 103.110.127.209

# 4) Apps (add security + whitenoise if serving static)
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'scraper',
]

# 5) Middleware: security + whitenoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# 6) URLs & WSGI
ROOT_URLCONF = 'stockproject.urls'
WSGI_APPLICATION = 'stockproject.wsgi.application'

# 7) Templates: minimal context processors so render bhi ho
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # agar custom templates hain toh yahan add kar
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
            ],
        },
    },
]

# 8) Database: default sqlite, par env se switch kar sakta hai
DATABASES = {
    'default': env.db(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    )
}

# 9) Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# agar development mein local static dir bhi chahiye:
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'scraper', 'static')]

# 10) Whitenoise storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 11) Security headers (optional but recommended)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000  # 1 saal
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
