import os.path
from uuid import uuid4

from database import database
from fastapi import UploadFile
from models import *
from sqlalchemy.sql import select, and_, insert, update
from sqlalchemy import func
from exceptions import *
from constants import MEDIA_ROOT

import auth
import tables
import constants
import mimetypes
import aiofiles
import base64


async def create_user(user: UserIn):
    user.username = user.username.lower()
    query = tables.users.select().where(tables.users.c.username == user.username)
    existing_user = await database.execute(query)
    if existing_user:
        raise API_409_USERNAME_CONFLICT_EXCEPTION
    else:
        salt = auth.gen_salt()
        query = tables.users.insert().values(
            username=user.username,
            full_name=user.full_name,
        )
        await database.execute(query)
        query = tables.user_credentials.insert().values(
            username=user.username,
            hashed_password=auth.get_password_hash(user.password + salt),
            salt=salt,
            disabled=False
        )
        await database.execute(query)
        return {"Post": "Success"}


async def get_user(username: str):
    query = tables.users.select().where(tables.users.c.username == username)
    user = await database.fetch_one(query)
    if user:
        return user
    else:
        raise API_404_NOT_FOUND_EXCEPTION


async def get_user_profile(username: str):
    followers_subquery = select([
        tables.followers.c.user,
        func.count().label('followers')
    ]).group_by(tables.followers.c.user).subquery()

    following_subquery = select([
        tables.following.c.user,
        func.count().label('following')
    ]).group_by(tables.following.c.user).subquery()

    profile_query = select([
        tables.users,
        func.coalesce(followers_subquery.c.followers, 0).label('followers'),
        func.coalesce(following_subquery.c.following, 0).label('following')
    ]).select_from(
        tables.users
        .outerjoin(followers_subquery, followers_subquery.c.user == tables.users.c.username)
        .outerjoin(following_subquery, following_subquery.c.user == tables.users.c.username)
    ).where(
        tables.users.c.username == username
    )

    profile = await database.fetch_one(profile_query)

    comments_subquery = select([
        tables.comments.c.post_id,
        func.count().label('comments')
    ]).group_by(tables.comments.c.post_id).subquery()

    likes_subquery = select([
        tables.likes.c.post_id,
        func.count().label('likes')
    ]).group_by(tables.likes.c.post_id).subquery()

    query = select([
        tables.posts,
        tables.users.c.username,
        tables.users.c.full_name,
        func.coalesce(comments_subquery.c.comments, 0).label('comments'),
        func.coalesce(likes_subquery.c.likes, 0).label('likes')
    ]).select_from(
        tables.posts
        .join(tables.users, tables.users.c.username == tables.posts.c.username)
        .outerjoin(comments_subquery, comments_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(likes_subquery, likes_subquery.c.post_id == tables.posts.c.post_id)
    ).where(
        tables.posts.c.username == username
    ).order_by(
        tables.posts.c.date_posted.desc()
    )

    posts = await database.fetch_all(query)
    return {**profile, 'posts': posts}


async def get_followers(user: User):
    query = select(tables.followers).where(tables.followers.c.user == user.username)
    followers = await database.fetch_all(query)
    return followers


async def get_following(user: User):
    query = select(tables.following.c.following).where(tables.following.c.user == user.username)
    following = await database.fetch_all(query)
    return following


async def get_follower_count(user: User):
    query = select([func.count()]).select_from(tables.followers).where(tables.followers.c.user == user.username)
    followers = await database.execute(query)
    return followers


async def get_following_count(user: User):
    query = select([func.count()]).select_from(tables.following).where(tables.following.c.user == user.username)
    following = await database.execute(query)
    return following


async def create_bio(bio, user):
    query = update(tables.users).where(tables.users.c.username == user.username).values(
        bio=bio,
    )
    await database.execute(query)


async def update_avatar(file: UploadFile, user: User):
    extension = mimetypes.guess_extension(file.content_type)
    async with aiofiles.open(MEDIA_ROOT + user.username + str(extension), "wb") as out_file:
        content = await file.read()
        await out_file.write(content)


async def get_feed(user: User):
    comments_subquery = select([
        tables.comments.c.post_id,
        func.count().label('comments')
    ]).group_by(tables.comments.c.post_id).subquery()

    likes_subquery = select([
        tables.likes.c.post_id,
        func.count().label('likes')
    ]).group_by(tables.likes.c.post_id).subquery()

    query = select([
        tables.posts,
        tables.users,
        func.coalesce(comments_subquery.c.comments, 0).label('comments'),
        func.coalesce(likes_subquery.c.likes, 0).label('likes'),
        tables.post_images.c.image_url
    ]).select_from(
        tables.following
        .join(tables.posts, tables.following.c.following == tables.posts.c.username)
        .join(tables.users, tables.posts.c.username == tables.users.c.username)
        .outerjoin(comments_subquery, comments_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(likes_subquery, likes_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(tables.post_images, tables.post_images.c.post_id == tables.posts.c.post_id)
    ).where(
        tables.following.c.user == user.username
    ).order_by(
        tables.posts.c.date_posted.desc()
    )
    feed = await database.fetch_all(query)
    return feed


async def get_post_likes(post_id: UUID):
    query = tables.likes.select().where(tables.likes.c.post_id == post_id)
    likes = await database.fetch_all(query)
    return likes


async def get_post_comments(post_id: UUID):
    query = select([
        tables.comments,
        tables.users
    ]).select_from(
        tables.comments
        .join(tables.users, tables.comments.c.username == tables.users.c.username)
    ).where(
        tables.comments.c.post_id == post_id
    ).order_by(
        tables.comments.c.date_posted.desc()
    )
    comments = await database.fetch_all(query)
    return comments


async def create_post(post: str, latitude: float, longitude: float, photo: UploadFile, user: User):
    async with (database.transaction()):
        try:
            post_query = insert(tables.posts).values(username=user.username, content=post)
            post_id = await database.execute(post_query)
            if photo:
                _, extension = os.path.splitext(photo.filename)
                thing = str(post_id) + extension
                async with aiofiles.open(MEDIA_ROOT + str(post_id) + extension, "wb") as out_file:
                    await out_file.write(photo.file.read())
                image_query = insert(tables.post_images).values(post_id=post_id, image_url=thing)
                await database.execute(image_query)

            location_query = insert(
                tables.post_locations
            ).values(post_id=post_id,
                     latitude=latitude,
                     longitude=longitude)
            await database.execute(location_query)

        except Exception as e:
            print(e)
            # await database.rollback()


async def create_comment(comment: CommentIn, user: User):
    query = insert(tables.comments).values(
        post_id=comment.post_id,
        username=user.username,
        content=comment.content
    )
    await database.execute(query)


async def create_like(post_id: UUID, user: User):
    query = insert(tables.likes).values(
        post_id=post_id,
        username=user.username
    )
    await database.execute(query)
