import os.path

from sqlalchemy.sql import delete, select, insert, update
from database import database

from constants import APP_ROOT, COMMUNITY

import tables
import auth
import methods
import models


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

    with open(os.path.join(APP_ROOT, "data", "activity.sql"), 'r') as file:
        user_commands = file.read()
        await database.execute(user_commands)

    print("Database Reset Complete")


async def helper():
    print(os.getenv('PORT'))
    print(COMMUNITY)


async def fix_followers():
    await database.execute(delete(tables.followers))
    query = select([tables.following])
    following = await database.fetch_all(query)
    for pair in following:
        await database.execute(insert(tables.followers).values(
            user=pair.following,
            follower=pair.user
        ))


async def populate_activity():
    likes_query = select([tables.likes])
    likes = await database.fetch_all(likes_query)

    for like in likes:
        author = await methods.get_post_author(like.post_id)
        query = insert(tables.activity).values(
            user=author.username,
            action_user=like.username,
            action=models.ActivityAction.like,
            post_id=like.post_id
        )
        await database.execute(query)

    comments_query = select([tables.likes])
    comments = await database.fetch_all(comments_query)

    for comment in comments:
        author = await methods.get_post_author(comment.post_id)
        query = insert(tables.activity).values(
            user=author.username,
            action_user=comment.username,
            action=models.ActivityAction.comment,
            post_id=comment.post_id
        )
        await database.execute(query)

    query = select([tables.followers])
    followers = await database.fetch_all(query)
    for pair in followers:
        await database.execute(insert(tables.activity).values(
            user=pair.user,
            action_user=pair.follower,
            action=models.ActivityAction.follow
        ))


async def update_password():
    q = select([tables.users])
    users = await database.fetch_all(q)
    for user in users:
        salt = auth.gen_salt()
        query = ((update(tables.user_credentials)
                 .where(tables.user_credentials.c.username == user.username))
                 .values(
            hashed_password=auth.get_password_hash("a" + salt),
            salt=salt,
            disabled=False
        ))
        await database.execute(query)
