import os
import urllib.parse

# Gets all the relevant environment variables for the application, and defines some app-wide constants

APP_ROOT = "./"
MEDIA_ROOT = os.path.join(APP_ROOT, 'media')
DATA_ROOT = os.path.join(APP_ROOT, 'data')

# database info
DB_USER = os.getenv('POSTGRES_USER')
DB_KEY = urllib.parse.quote(os.getenv('POSTGRES_PASSWORD'))
DB_SERVER = os.getenv('POSTGRES_SERVER')
DB_PORT = os.getenv('POSTGRES_PORT')
DB_DB = os.getenv('POSTGRES_DB')
DB_URL = "postgresql://{}:{}@db:{}/{}".format(DB_USER, DB_KEY, DB_PORT, DB_DB)

SERVER_ADDRESS = os.getenv('SERVER_ADDRESS')
SERVER_PORT = os.getenv('PORT')
SECRET_KEY = os.getenv('SECRET_KEY')
