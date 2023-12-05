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
    # Constructs a URL for a given community and endpoint. It's a utility function used to dynamically generate URLs
    # for different communities. This is currently hardcoded for demonstration purposes.
    if community == 'stringshare.ca':
        return '{}:{}/{}'.format(SERVER_ADDRESS, '8080', endpoint)
    else:
        return '{}:{}/{}'.format(SERVER_ADDRESS, '8081', endpoint)


async def make_post_request_json(url, json):
    # Makes an HTTP POST request to a specified URL with JSON data. It's a generic function to send data to servers and
    # receive a response.
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json) as resp:
            response = await resp.json()
            return response


async def make_post_request_params(url, params, data):
    # Sends an HTTP POST request with both URL parameters and data payload. It's used when both URL parameters and data
    # need to be sent in a request.
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params, data=data) as resp:
            response = await resp.json()
            return response


async def make_get_request(url, json=None, data=None):
    # Makes an HTTP GET request to a specified URL. It can optionally include JSON data or URL parameters, and is used
    # to retrieve data from servers.
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=data, json=json) as resp:
            response = await resp.json()
            return response


def is_user_in_community(username: str):
    # Checks if a user's username includes the current community's domain, indicating whether the user is part of the
    # current community.
    if '@' + COMMUNITY in username:
        return True
    else:
        return False


async def search_community(search_query: str, user: models.User):
    # Performs a search in a remote community. It constructs a URL for the search endpoint and sends a request with the
    # search query.
    username, community = search_query.split('@')
    url = await get_url(community, 'server/search')
    json = {
        'username': user.username,
        'full_name': user.full_name,
        'search_query': username
    }
    return await make_get_request(url, json=json)


async def create_foreign_user(user: models.ServerUser):
    # Adds a user from a foreign community to the local database, if they do not already exist.
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
    # Initiates a follow request to a user in a foreign community. It sends a request to the foreign community's server
    # to follow a user and updates the local database.
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
    foreign_user = await make_post_request_json(url, json=json)
    await create_foreign_user(foreign_user)


async def propagate_post(post_id: UUID, post: str, latitude: float, longitude: float, user: models.User,
                         photo_url: str = None):
    # Propagates a post to other communities. It sends the post data, including optional photo, to all communities that
    # the user's community is following.
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
        url = await get_url(community.community, 'server/post')
        await make_post_request_params(url=url, params=params, data=data)


async def propagate_comment(comment: models.Comment, user: models.User, author: str):
    # Sends a user's comment to the author's community if the author is from a foreign community. It ensures comments
    # are shared across community boundaries.
    _, community = author.split('@')
    if community == COMMUNITY:
        return
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
    await make_post_request_json(url, json=json)


async def propagate_like(post_id: UUID, user: models.User, author: str):
    # Propagates a 'like' action on a post to the author's community if the author is from a foreign community,
    # ensuring likes are shared across communities.
    _, community = author.split('@')
    if community == COMMUNITY:
        return
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
    await make_post_request_json(url, json=json)
