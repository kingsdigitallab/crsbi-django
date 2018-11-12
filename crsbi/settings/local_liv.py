from .base import *  # noqa

ALLOWED_HOSTS = ['crsbi.kdl.kcl.ac.uk']

INTERNAL_IPS = INTERNAL_IPS + ['']

DATABASES = {
    'default': {
        'ENGINE': db_engine,
        'NAME': 'app_crsbi3_liv',
        'USER': 'app_crsbi3',
        'PASSWORD': '',
        'HOST': ''
    },
}

SECRET_KEY = ''
