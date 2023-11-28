from dotenv import load_dotenv
import os
import urllib.parse

APP_ROOT = "./"
MEDIA_ROOT = APP_ROOT + "media/"
DATA_ROOT = APP_ROOT + "data/stringshare/"

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

COMMUNITY = os.getenv('COMMUNITY')


