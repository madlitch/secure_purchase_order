from dotenv import load_dotenv

import os
import urllib.parse

load_dotenv('.env')

APP_ROOT = "./"

# database info
DB_USER = os.getenv('POSTGRES_USER')
DB_KEY = urllib.parse.quote(os.getenv('POSTGRES_PASSWORD'))
DB_SERVER = os.getenv('POSTGRES_SERVER')
DB_PORT = os.getenv('POSTGRES_PORT')
DB_DB = os.getenv('POSTGRES_DB')
DB_URL = "postgresql://{}:{}@db:{}/{}".format(DB_USER, DB_KEY, DB_PORT, DB_DB)

SECRET_KEY = os.getenv('SECRET_KEY')
