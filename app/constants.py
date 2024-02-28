import os
import urllib.parse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

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

SERVER_PRIVATE_KEY = os.path.join(APP_ROOT, "server_private_key.asc")
SERVER_PRIVATE_KEY_PW = os.getenv('SERVER_KEY_PW')
SERVER_PUBLIC_KEY = os.path.join(APP_ROOT, "server_public_key.asc")

TEMPLATE_FOLDER = '{}templates'.format(APP_ROOT)

conf = ConnectionConfig(
    MAIL_USERNAME="securepurchaseorder@outlook.com",
    MAIL_PASSWORD="+c[B.-cb[3F*@V!UeX.R",
    MAIL_FROM="securepurchaseorder@outlook.com",
    MAIL_FROM_NAME="Secure Company Purchase Order",
    MAIL_PORT=587,
    MAIL_SERVER="smtp-mail.outlook.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=TEMPLATE_FOLDER
)
