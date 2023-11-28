from uuid import UUID

from aiohttp import FormData

from database import database
from constants import MEDIA_ROOT, COMMUNITY, SERVER_ADDRESS
from sqlalchemy.sql import select, insert

import os.path
import tables
import aiohttp
import models


async def get_url(community, endpoint):
    # mock placeholder
    if community == 'stringshare.ca':
        return '{}:{}/{}'.format(SERVER_ADDRESS, '8080', endpoint)
    else:

        return '{}:{}/{}'.format(SERVER_ADDRESS, '8081', endpoint)


async def make_post_request(url, json):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json) as resp:
            response = await resp.json()
            return response


async def make_post_request_params(url, params, data):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params, data=data) as resp:
            response = await resp.json()
            return response


async def make_get_request(url, json=None, data=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=data, json=json) as resp:
            response = await resp.json()
            return response


def is_user_in_community(username: str):
    if '@' + COMMUNITY in username:
        return True
    else:
        return False


async def search_community(search_query: str, user: models.User):
    username, community = search_query.split('@')
    url = await get_url(community, 'server/search')
    json = {
        'username': user.username,
        'full_name': user.full_name,
        'search_query': username
    }
    return await make_get_request(url, json=json)


async def create_foreign_user(user: models.ServerUser):
    query = tables.users.select().where(tables.users.c.username == user['username'])
    existing_user = await database.execute(query)
    if not existing_user:
        query = insert(tables.users).values(
            username=user['username'],
            full_name=user['full_name'],
            avatar_url=user['avatar_url'],
            bio=user['bio']
        )
        await database.execute(query)


async def follow_user(username: str, user: models.User):
    _, community = username.split('@')
    query = select([tables.users]).where(tables.users.c.username == user.username)
    usr = await database.fetch_one(query)
    url = await get_url(community, 'server/follow')
    json = {
        'username': username,
        'user': {
            'username': usr.username,
            'full_name': usr.full_name,
            'avatar_url': usr.avatar_url,
            'bio': usr.bio,
        }
    }
    foreign_user = await make_post_request(url, json=json)
    await create_foreign_user(foreign_user)


async def propagate_post(post_id: UUID, post: str, latitude: float, longitude: float, user: models.User,
                         photo_url: str = None):
    query = select([tables.following_communities.c.community]).where(
        tables.following_communities.c.username == user.username
    )
    communities = await database.fetch_all(query)
    data = FormData()
    if photo_url:
        data.add_field(
            'photo',
            open(os.path.join(MEDIA_ROOT, photo_url), 'rb'),
            filename=os.path.join(MEDIA_ROOT, photo_url)
        )
    params = {
        'post_id': str(post_id),
        'post': post,
        'latitude': latitude,
        'longitude': longitude,
        'username': user.username,
    }
    for community in communities:
        url = await get_url(community, 'server/post')
        await make_post_request_params(url=url, params=params, data=data)


async def propagate_comment(comment: models.Comment, user: models.User, author: str):
    _, community = author.split('@')
    query = select([tables.users]).where(tables.users.c.username == user.username)
    usr = await database.fetch_one(query)
    url = await get_url(community, 'server/comment')
    json = {
        'comment': {
            'post_id': str(comment.post_id),
            'content': comment.content
        },
        'user': {
            'username': usr.username,
            'full_name': usr.full_name,
            'avatar_url': usr.avatar_url,
            'bio': usr.bio,
        }
    }
    await make_post_request(url, json=json)


async def propagate_like(post_id: UUID, user: models.User, author: str):
    _, community = author.split('@')
    query = select([tables.users]).where(tables.users.c.username == user.username)
    usr = await database.fetch_one(query)
    url = await get_url(community, 'server/like')
    json = {
        'post_id': str(post_id),
        'user': {
            'username': usr.username,
            'full_name': usr.full_name,
            'avatar_url': usr.avatar_url,
            'bio': usr.bio,
        }
    }
    await make_post_request(url, json=json)
