import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

WTF_CSRF_ENABLED = False

# use something like os.urandom(24) for productional uses.
SECRET_KEY = 'my precious'

SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_ECHO = True
