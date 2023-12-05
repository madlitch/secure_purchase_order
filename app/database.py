import databases
import sqlalchemy

from tables import metadata

import constants

# Initiates the database connection

database = databases.Database(constants.DB_URL)
engine = sqlalchemy.create_engine(constants.DB_URL, echo=False)
metadata.create_all(engine)
