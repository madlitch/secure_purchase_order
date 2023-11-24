from fastapi import UploadFile
from sqlalchemy.sql import select, insert, update, or_
from sqlalchemy import func

from database import database
from constants import MEDIA_ROOT, COMMUNITY

import os.path
import auth
import tables
import aiofiles
import requests
import exceptions
import models


async def create_user(user: models.UserIn):
    if "@" + COMMUNITY not in user.username:
        user.username = user.username + "@" + COMMUNITY
    user.username = user.username.lower()
    query = tables.users.select().where(tables.users.c.username == user.username)
    existing_user = await database.execute(query)
    if existing_user:
        raise exceptions.API_409_USERNAME_CONFLICT_EXCEPTION
    else:
        async with (database.transaction()):
            try:
                salt = auth.gen_salt()
                query = tables.users.insert().values(
                    username=user.username,
                    full_name=user.full_name,
                    avatar_url=await create_avatar(user)
                )
                await database.execute(query)
                query = tables.user_credentials.insert().values(
                    username=user.username,
                    hashed_password=auth.get_password_hash(user.password + salt),
                    salt=salt,
                    disabled=False
                )
                await database.execute(query)
            except Exception as e:
                print(e)
            # await database.rollback()


async def create_avatar(user: models.User):
    params = {
        "name": user.full_name,
        "background": "random"
    }
    avatar = requests.get('https://ui-avatars.com/api/', params=params)
    async with aiofiles.open(os.path.join(MEDIA_ROOT, (user.username + ".png")), "wb") as out_file:
        await out_file.write(avatar.content)
    return user.username + ".png"


async def get_user(username: str):
    query = tables.users.select().where(tables.users.c.username == username)
    user = await database.fetch_one(query)
    if user:
        return user
    else:
        raise exceptions.API_404_NOT_FOUND_EXCEPTION


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
        tables.users.c.avatar_url,
        func.coalesce(comments_subquery.c.comments, 0).label('comments'),
        func.coalesce(likes_subquery.c.likes, 0).label('likes'),
        tables.post_images.c.image_url,
        tables.post_locations.c.latitude,
        tables.post_locations.c.longitude
    ]).select_from(
        tables.posts
        .join(tables.users, tables.users.c.username == tables.posts.c.username)
        .outerjoin(comments_subquery, comments_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(likes_subquery, likes_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(tables.post_images, tables.post_images.c.post_id == tables.posts.c.post_id)
        .outerjoin(tables.post_locations, tables.post_locations.c.post_id == tables.posts.c.post_id)
    ).where(
        tables.posts.c.username == username
    ).order_by(
        tables.posts.c.date_posted.desc()
    )

    posts = await database.fetch_all(query)
    return {**profile, 'posts': posts}


async def get_activity(user: models.User):
    query = select([
        tables.activity,
        tables.users.c.full_name,
        tables.users.c.avatar_url
    ]).select_from(
        tables.activity
        .join(tables.users, tables.users.c.username == tables.activity.c.action_user)
    ).where(tables.activity.c.user == user.username)
    return await database.fetch_all(query)


async def search_users(search_query: str, user: models.User):
    following_subquery = select([
        tables.following.c.following,
        func.bool_or(tables.following.c.user == user.username).label('is_following')
    ]).group_by(tables.following.c.following).subquery()

    query = select([
        tables.users.c.username,
        tables.users.c.full_name,
        tables.users.c.avatar_url,
        following_subquery.c.is_following
    ]).select_from(
        tables.users
        .outerjoin(following_subquery, tables.users.c.username == following_subquery.c.following)
    ).where(
        or_(
            tables.users.c.username.like("%" + search_query + "%"),
            tables.users.c.full_name.like("%" + search_query + "%"),
        )
    )
    return await database.fetch_all(query)


async def get_followers(user: models.User):
    query = select(tables.followers).where(tables.followers.c.user == user.username)
    followers = await database.fetch_all(query)
    return followers


async def get_following(user: models.User):
    query = select(tables.following.c.following).where(tables.following.c.user == user.username)
    following = await database.fetch_all(query)
    return following


async def get_follower_count(user: models.User):
    query = select([func.count()]).select_from(tables.followers).where(tables.followers.c.user == user.username)
    followers = await database.execute(query)
    return followers


async def get_following_count(user: models.User):
    query = select([func.count()]).select_from(tables.following).where(tables.following.c.user == user.username)
    following = await database.execute(query)
    return following


async def create_bio(bio, user):
    query = update(tables.users).where(tables.users.c.username == user.username).values(bio=bio)
    await database.execute(query)


async def update_avatar(photo: UploadFile, user: models.User):
    _, extension = os.path.splitext(photo.filename)
    url = str(user.username) + extension
    async with aiofiles.open(os.path.join(MEDIA_ROOT, url), "wb") as out_file:
        await out_file.write(photo.file.read())
    query = update(tables.users).where(tables.users.c.username == user.username).values(avatar_url=url)
    await database.execute(query)


async def get_post(post_id: models.UUID):
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
        tables.post_images.c.image_url,
        tables.post_locations.c.latitude,
        tables.post_locations.c.longitude
    ]).select_from(
        tables.posts
        .join(tables.users, tables.posts.c.username == tables.users.c.username)
        .outerjoin(comments_subquery, comments_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(likes_subquery, likes_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(tables.post_images, tables.post_images.c.post_id == tables.posts.c.post_id)
        .outerjoin(tables.post_locations, tables.post_locations.c.post_id == tables.posts.c.post_id)
    ).where(
        tables.posts.c.post_id == post_id
    )
    feed = await database.fetch_one(query)
    return feed


async def get_feed(user: models.User):
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
        tables.post_images.c.image_url,
        tables.post_locations.c.latitude,
        tables.post_locations.c.longitude
    ]).select_from(
        tables.following
        .join(tables.posts, tables.following.c.following == tables.posts.c.username)
        .join(tables.users, tables.posts.c.username == tables.users.c.username)
        .outerjoin(comments_subquery, comments_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(likes_subquery, likes_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(tables.post_images, tables.post_images.c.post_id == tables.posts.c.post_id)
        .outerjoin(tables.post_locations, tables.post_locations.c.post_id == tables.posts.c.post_id)
    ).where(
        tables.following.c.user == user.username
    ).order_by(
        tables.posts.c.date_posted.desc()
    )
    feed = await database.fetch_all(query)
    return feed


async def get_post_likes(post_id: models.UUID):
    query = tables.likes.select().where(tables.likes.c.post_id == post_id)
    likes = await database.fetch_all(query)
    return likes


async def get_post_comments(post_id: models.UUID):
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


async def create_post(post: str, latitude: float, longitude: float, photo: UploadFile, user: models.User):
    async with (database.transaction()):
        try:
            post_query = insert(tables.posts).values(username=user.username, content=post)
            post_id = await database.execute(post_query)
            if photo:
                _, extension = os.path.splitext(photo.filename)
                url = str(post_id) + extension
                async with aiofiles.open(os.path.join(MEDIA_ROOT, url), "wb") as out_file:
                    await out_file.write(photo.file.read())
                image_query = insert(tables.post_images).values(post_id=post_id, image_url=url)
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


async def follow_user(username: str, user: models.User):
    async with (database.transaction()):
        try:
            query = insert(tables.following).values(user=user.username, following=username)
            await database.execute(query)
            query = insert(tables.followers).values(user=username, follower=user.username)
            await database.execute(query)
        except Exception as e:
            print(e)
            # await database.rollback()
    await log_action(user, models.ActivityAction.follow, username=username)


async def create_comment(comment: models.CommentIn, user: models.User):
    query = insert(tables.comments).values(
        post_id=comment.post_id,
        username=user.username,
        content=comment.content
    )
    await database.execute(query)
    await log_action(user, models.ActivityAction.comment, post_id=comment.post_id)


async def create_like(post_id: models.UUID, user: models.User):
    query = insert(tables.likes).values(
        post_id=post_id,
        username=user.username
    )
    await database.execute(query)
    await log_action(user, models.ActivityAction.like, post_id=post_id)


async def get_post_author(post_id: models.UUID):
    query = select([
        tables.posts.c.post_id,
        tables.users.c.username
    ]).select_from(
        tables.posts
        .join(tables.users, tables.posts.c.username == tables.users.c.username)
    ).where(
        tables.posts.c.post_id == post_id
    )
    return await database.fetch_one(query)


async def log_action(action_user: models.User, action: models.ActivityAction, username: str = None,
                     post_id: models.UUID = None):
    if username is None and post_id is not None:
        author = await get_post_author(post_id)
        query = insert(tables.activity).values(
            user=author.username,
            action_user=action_user.username,
            action=action,
            post_id=post_id
        )
        await database.execute(query)
    elif username is not None and action is models.ActivityAction.follow:
        query = insert(tables.activity).values(
            user=username,
            action_user=action_user.username,
            action=action
        )
        await database.execute(query)
