import os.path

from sqlalchemy.sql import delete

from database import database
from constants import APP_ROOT

import tables


async def reset_database():
    print("Resetting database...")
    await database.execute(delete(tables.post_images))
    await database.execute(delete(tables.post_locations))
    await database.execute(delete(tables.likes))
    await database.execute(delete(tables.comments))
    await database.execute(delete(tables.posts))
    await database.execute(delete(tables.following))
    await database.execute(delete(tables.followers))
    await database.execute(delete(tables.user_credentials))
    await database.execute(delete(tables.users))

    with open(os.path.join(APP_ROOT, "data", "users.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    with open(os.path.join(APP_ROOT, "data", "user_credentials.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    with open(os.path.join(APP_ROOT, "data", "followers.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    with open(os.path.join(APP_ROOT, "data", "following.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    with open(os.path.join(APP_ROOT, "data", "posts.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    with open(os.path.join(APP_ROOT, "data", "comments.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    with open(os.path.join(APP_ROOT, "data", "likes.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    with open(os.path.join(APP_ROOT, "data", "post_locations.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    with open(os.path.join(APP_ROOT, "data", "post_images.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    print("Database Reset Complete")
