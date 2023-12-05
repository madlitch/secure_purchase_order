from uuid import UUID

from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.sql import select, insert, update, or_, delete
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
import network

# Predefined SQL Queries
comments_subquery = select([
    tables.comments.c.post_id,
    func.count().label('comments')
]).group_by(tables.comments.c.post_id).subquery()

likes_subquery = select([
    tables.likes.c.post_id,
    func.count().label('likes')
]).group_by(tables.likes.c.post_id).subquery()


async def create_user(user: models.UserIn):
    # Adds a new user to the database. It appends the community domain to the username (if not there already),
    # checks for existing users with the same username, and then inserts the new user's details.
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
                await database.rollback()


async def create_avatar(user: models.User):
    # Generates an avatar for a given user using an external avatar service and saves it to the server.
    params = {
        "name": user.full_name,
        "background": "random"
    }
    avatar = requests.get('https://ui-avatars.com/api/', params=params)
    async with aiofiles.open(os.path.join(MEDIA_ROOT, (user.username + ".png")), "wb") as out_file:
        await out_file.write(avatar.content)
    return user.username + ".png"


async def get_user(username: str):
    # Retrieves details of a user based on their username. Raises a not found exception if the user doesn't exist.
    query = tables.users.select().where(tables.users.c.username == username)
    user = await database.fetch_one(query)
    if user:
        return user
    else:
        raise exceptions.API_404_NOT_FOUND_EXCEPTION


async def get_user_profile(username: str, user: models.User):
    # Fetches a user's profile information, including follower and following counts, and their posts.
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

    liked_subquery = select([
        tables.likes.c.post_id,
        func.bool_or(tables.likes.c.username == user.username).label('liked')
    ]).group_by(tables.likes.c.post_id).subquery()

    query = select([
        tables.posts,
        tables.users.c.username,
        tables.users.c.full_name,
        tables.users.c.avatar_url,
        func.coalesce(comments_subquery.c.comments, 0).label('comments'),
        func.coalesce(likes_subquery.c.likes, 0).label('likes'),
        func.coalesce(liked_subquery.c.liked, False).label('liked'),
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
    # Retrieves a list of activities (like comments, likes) associated with a user.
    query = select([
        tables.activity,
        tables.users.c.full_name,
        tables.users.c.avatar_url
    ]).select_from(
        tables.activity
        .join(tables.users, tables.users.c.username == tables.activity.c.action_user)
    ).where(tables.activity.c.user == user.username).order_by(
        tables.activity.c.datetime.desc()
    )
    return await database.fetch_all(query)


async def search_users(search_query: str, user: models.User):
    # Searches for users based on a query string. If the query contains '@', it also searches in the community.
    if '@' in search_query and not network.is_user_in_community(search_query):
        return await network.search_community(search_query, user)
    else:
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
    # Retrieves a list of followers for a given user.
    query = select(tables.followers).where(tables.followers.c.user == user.username)
    followers = await database.fetch_all(query)
    return followers


async def get_following(user: models.User):
    # Retrieves a list of users that the given user is following.
    query = select(tables.following.c.following).where(tables.following.c.user == user.username)
    following = await database.fetch_all(query)
    return following


async def get_follower_count(user: models.User):
    # Counts the number of followers a user has.
    query = select([func.count()]).select_from(tables.followers).where(tables.followers.c.user == user.username)
    followers = await database.execute(query)
    return followers


async def get_following_count(user: models.User):
    # Counts the number of users a given user is following.
    query = select([func.count()]).select_from(tables.following).where(tables.following.c.user == user.username)
    following = await database.execute(query)
    return following


async def create_bio(bio, user):
    # Updates the biography of a user.
    query = update(tables.users).where(tables.users.c.username == user.username).values(bio=bio)
    await database.execute(query)


async def update_avatar(photo: UploadFile, user: models.User):
    # Updates a user's avatar with a new photo.
    _, extension = os.path.splitext(photo.filename)
    url = str(user.username) + extension
    async with aiofiles.open(os.path.join(MEDIA_ROOT, url), "wb") as out_file:
        await out_file.write(photo.file.read())
    query = update(tables.users).where(tables.users.c.username == user.username).values(avatar_url=url)
    await database.execute(query)


async def get_post(post_id: UUID, user: models.User):
    # Retrieves a specific post by its ID, along with associated data like comments and likes.
    liked_subquery = select([
        tables.likes.c.post_id,
        func.bool_or(tables.likes.c.username == user.username).label('liked')
    ]).group_by(tables.likes.c.post_id).subquery()

    query = select([
        tables.posts,
        tables.users,
        func.coalesce(comments_subquery.c.comments, 0).label('comments'),
        func.coalesce(likes_subquery.c.likes, 0).label('likes'),
        func.coalesce(liked_subquery.c.liked, False).label('liked'),
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
    # Fetches the social media feed for a user, showing posts from users they follow.
    liked_subquery = select([
        tables.likes.c.post_id,
        func.bool_or(tables.likes.c.username == user.username).label('liked')
    ]).group_by(tables.likes.c.post_id).subquery()

    query = select([
        tables.posts,
        tables.users,
        func.coalesce(comments_subquery.c.comments, 0).label('comments'),
        func.coalesce(likes_subquery.c.likes, 0).label('likes'),
        func.coalesce(liked_subquery.c.liked, False).label('liked'),
        tables.post_images.c.image_url,
        tables.post_locations.c.latitude,
        tables.post_locations.c.longitude
    ]).select_from(
        tables.following
        .join(tables.posts, tables.following.c.following == tables.posts.c.username)
        .join(tables.users, tables.posts.c.username == tables.users.c.username)
        .outerjoin(comments_subquery, comments_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(likes_subquery, likes_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(liked_subquery, liked_subquery.c.post_id == tables.posts.c.post_id)
        .outerjoin(tables.post_images, tables.post_images.c.post_id == tables.posts.c.post_id)
        .outerjoin(tables.post_locations, tables.post_locations.c.post_id == tables.posts.c.post_id)
    ).where(
        tables.following.c.user == user.username
    ).order_by(
        tables.posts.c.date_posted.desc()
    )
    feed = await database.fetch_all(query)
    return feed


async def get_post_likes(post_id: UUID):
    # Retrieves all likes for a specific post.
    query = tables.likes.select().where(tables.likes.c.post_id == post_id)
    likes = await database.fetch_all(query)
    return likes


async def get_post_comments(post_id: UUID):
    # Retrieves all comments for a specific post.
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
    # Creates a new post with location data and optional photo, then propagates it in the network.
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
                await network.propagate_post(post_id, post, latitude, longitude, user, url)
            else:
                await network.propagate_post(post_id, post, latitude, longitude, user, None)

            location_query = insert(
                tables.post_locations
            ).values(post_id=post_id,
                     latitude=latitude,
                     longitude=longitude)
            await database.execute(location_query)
        except Exception as e:
            print(e)
            await database.rollback()


async def server_create_post(post_id: str, post: str, latitude: float, longitude: float, photo: UploadFile,
                             username: str):
    # Handles post creation on the server side, particularly for posts received from other servers in the network.
    async with (database.transaction()):
        try:
            post_query = insert(tables.posts).values(post_id=post_id, username=username, content=post)
            await database.execute(post_query)
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
            await database.rollback()


async def follow_user(username: str, user: models.User):
    # Allows a user to follow another user. Handles following users in the local community as well as other communities.
    if '@' in username and not network.is_user_in_community(username):
        await network.follow_user(username, user)
    async with (database.transaction()):
        try:
            query = insert(tables.following).values(user=user.username, following=username)
            await database.execute(query)
            query = insert(tables.followers).values(user=username, follower=user.username)
            await database.execute(query)
        except Exception as e:
            print(e)
            await database.rollback()
    await log_action(user, models.ActivityAction.follow, username=username)


async def server_follow_user(username: str, user: models.ServerUser):
    # Handles the propagation logic for a user following another user, especially in the context of distributed
    # communities.
    query = tables.users.select().where(tables.users.c.username == user.username)
    existing_user = await database.execute(query)
    if not existing_user:
        query = insert(tables.users).values(
            username=user.username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            bio=user.bio
        )
        await database.execute(query)
    async with (database.transaction()):
        try:
            community = user.username.split('@')[1]  # get following user's community
            query = insert(tables.communities).values(
                url=community
            )
            await database.execute(query)
            query = insert(tables.following_communities).values(
                username=username,  # local user
                community=community
            )
            await database.execute(query)
        except Exception as e:
            print(e)
            await database.rollback()

    async with (database.transaction()):
        try:
            query = insert(tables.following).values(user=user.username, following=username)
            await database.execute(query)
            query = insert(tables.followers).values(user=username, follower=user.username)
            await database.execute(query)
        except Exception as e:
            print(e)
            await database.rollback()
    await log_action(user, models.ActivityAction.follow, username=username)
    query = select([tables.users]).where(tables.users.c.username == username)
    return await database.fetch_one(query)


async def create_comment(comment: models.Comment, user: models.User):
    # Adds a comment to a post and logs the action.
    query = insert(tables.comments).values(
        post_id=comment.post_id,
        username=user.username,
        content=comment.content
    )
    await database.execute(query)
    await log_action(user, models.ActivityAction.comment, post_id=comment.post_id)
    author = await get_post_author(comment.post_id)
    await network.propagate_comment(comment, user, author.username)


async def server_create_comment(comment: models.ServerComment):
    # Adds a propagated comment from another server to a post and logs the action.
    query = insert(tables.comments).values(
        post_id=comment.comment.post_id,
        username=comment.user.username,
        content=comment.comment.content
    )
    await database.execute(query)
    await log_action(comment.user, models.ActivityAction.comment, post_id=comment.comment.post_id)


async def create_like(post_id: UUID, user: models.User):
    # Allows a user to like or unlike a post. It updates the 'likes' table, logs the action, and propagates the like
    # in the network.
    existing_query = select([tables.likes]).where(
        tables.likes.c.post_id == post_id,
        tables.likes.c.username == user.username)
    existing = await database.fetch_one(existing_query)
    if existing:
        query = delete(tables.likes).where(
            tables.likes.c.post_id == post_id,
            tables.likes.c.username == user.username
        )
        await database.execute(query)
    else:
        query = insert(tables.likes).values(
            post_id=post_id,
            username=user.username
        )
        await database.execute(query)
        await log_action(user, models.ActivityAction.like, post_id=post_id)
    author = await get_post_author(post_id)
    await network.propagate_like(post_id, user, author.username)


async def server_create_like(like: models.ServerLike):
    # Similar to 'create_like', but for likes propagated from other servers in the distributed network.
    existing_query = select([tables.likes]).where(
        tables.likes.c.post_id == like.post_id,
        tables.likes.c.username == like.user.username)
    existing = await database.fetch_one(existing_query)
    if existing:
        query = delete(tables.likes).where(
            tables.likes.c.post_id == like.post_id,
            tables.likes.c.username == like.user.username
        )
        await database.execute(query)
    else:
        query = insert(tables.likes).values(
            post_id=like.post_id,
            username=like.user.username
        )
        await database.execute(query)
        await log_action(like.user, models.ActivityAction.like, post_id=like.post_id)


async def get_post_author(post_id: UUID):
    # Fetches the author of a specific post.
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
                     post_id: UUID = None):
    # Logs user actions (like follows, comments, likes) in the activity table for tracking user interactions in the
    # network.
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


async def get_photo(url: str = None):
    # Returns media if exists at that url
    path = os.path.join(MEDIA_ROOT, url)
    if os.path.isfile(path):
        return FileResponse(path)
    else:
        raise exceptions.API_404_NOT_FOUND_EXCEPTION
