import databases
import sqlalchemy

from tables import metadata
from constants import *

database = databases.Database(DB_URL)
engine = sqlalchemy.create_engine(DB_URL, echo=False)
metadata.create_all(engine)
