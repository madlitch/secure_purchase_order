import os.path

from sqlalchemy.sql import delete, select, insert, update
from database import database

from constants import DATA_ROOT

import tables
import auth
import methods
import models


# This file is for helper methods, used for utility purposes


async def reset_database():
    # Resets the database by deleting all existing data from the tables and re-populating them using SQL files stored
    # in DATA_ROOT. This function is used for initializing or restoring the database to a default state.
    # print("Resetting database...")
    # await database.execute(delete(tables.communities))
    # await database.execute(delete(tables.following_communities))
    # await database.execute(delete(tables.activity))
    # await database.execute(delete(tables.post_images))
    # await database.execute(delete(tables.post_locations))
    # await database.execute(delete(tables.likes))
    # await database.execute(delete(tables.comments))
    # await database.execute(delete(tables.posts))
    # await database.execute(delete(tables.following))
    # await database.execute(delete(tables.followers))
    # await database.execute(delete(tables.user_credentials))
    # await database.execute(delete(tables.users))
    #
    # with open(os.path.join(DATA_ROOT, "users.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)
    #
    # with open(os.path.join(DATA_ROOT, "user_credentials.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)
    #
    # with open(os.path.join(DATA_ROOT, "followers.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)
    #
    # with open(os.path.join(DATA_ROOT, "following.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)
    #
    # with open(os.path.join(DATA_ROOT, "posts.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)
    #
    # with open(os.path.join(DATA_ROOT, "comments.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)
    #
    # with open(os.path.join(DATA_ROOT, "likes.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)
    #
    # with open(os.path.join(DATA_ROOT, "post_locations.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)
    #
    # with open(os.path.join(DATA_ROOT, "post_images.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)
    #
    # with open(os.path.join(DATA_ROOT, "activity.sql"), 'r') as file:
    #     user_commands = file.read()
    #     await database.execute(user_commands)

    print("Database Reset Complete")