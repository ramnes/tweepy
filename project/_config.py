import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

DATABASE = 'database.db'
WTF_CSRF_ENABLED = False

# use something like os.urandom(24) for productional uses.
SECRET_KEY = 'my precious'

DATABASE_PATH = os.path.join(BASE_DIR, DATABASE)

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_PATH
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True
