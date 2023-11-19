from sqlalchemy.sql import select, insert
from sqlalchemy import func

from auth import get_password_hash
from database import database
from constants import APP_ROOT

import tables
import json
import random


async def helper():
    query = select(tables.posts.c.post_id)
    posts = await database.fetch_all(query)

    f = open(APP_ROOT + "/mock_data/post_locations.json")
    json_posts = json.load(f)

    for i in range(0, len(posts)):
        json_posts[i]['post_id'] = str(posts[i]['post_id'])

    obj = json.dumps(json_posts, indent=4)
    with open(APP_ROOT + "/mock_data/post_locations.json", "w") as outfile:
        outfile.write(obj)


async def gen_mock_passwords():
    f = open(APP_ROOT + "/mock_data/users.json")
    users = json.load(f)

    for user in users:
        user['password'] = user['username']
        user['hashed_password'] = get_password_hash(user['username'] + user['salt'])

    obj = json.dumps(users, indent=4)
    with open(APP_ROOT + "/mock_data/users.json", "w") as outfile:
        outfile.write(obj)


async def gen_posts():
    print('creating posts')
    f = open(APP_ROOT + "/mock_data/posts.json")
    posts = json.load(f)

    f = open(APP_ROOT + "/mock_data/users.json")
    users = json.load(f)

    for i in range(len(posts)):
        posts[i]['username'] = users[i % len(users)]['username']

    obj = json.dumps(posts, indent=4)
    with open(APP_ROOT + "/mock_data/posts.json", "w") as outfile:
        outfile.write(obj)


async def gen_comments():
    print('creating comments')

    f = open(APP_ROOT + "/mock_data/comments.json")
    comments = json.load(f)

    query = tables.posts.select()
    posts = await database.fetch_all(query)

    # query = tables.users.select().order_by(tables.users.c.username.asc())
    query = tables.users.select()
    users = await database.fetch_all(query)

    for i in range(len(comments)):
        comments[i]['username'] = users[random.randint(0, len(users) - 1)]['username']
        comments[i]['post_id'] = str(posts[i % len(posts)]['post_id'])

    obj = json.dumps(comments, indent=4)
    with open(APP_ROOT + "/mock_data/comments.json", "w") as outfile:
        outfile.write(obj)


async def create_followings():
    print('creating followings')
    query = select([tables.users.c.username]).select_from(tables.users)
    users = await database.fetch_all(query)
    following_list = []
    for user in users:
        for i in range(3):
            random_user = users[random.randint(0, len(users) - 1)]
            if random_user is not user:
                following = {'user': user['username'], 'following': random_user['username']}
                if following not in following_list:
                    following_list.append(following)
                else:
                    print('following already in list')

    obj = json.dumps(following_list, indent=4)
    with open(APP_ROOT + "/mock_data/following.json", "w") as outfile:
        outfile.write(obj)


async def create_followers():
    print('creating followers')
    query = select([tables.users.c.username]).select_from(tables.users)
    users = await database.fetch_all(query)
    follower_list = []
    for user in users:
        for i in range(3):
            random_user = users[random.randint(0, len(users) - 1)]
            if random_user is not user:
                follower = {'user': user['username'], 'follower': random_user['username']}
                if follower not in follower_list:
                    follower_list.append(follower)
                else:
                    print('follower already in list')

    obj = json.dumps(follower_list, indent=4)
    with open(APP_ROOT + "/mock_data/follower.json", "w") as outfile:
        outfile.write(obj)


async def create_likes():
    print('creating likes')
    query = select([tables.posts.c.post_id]).select_from(tables.posts)
    posts = await database.fetch_all(query)
    query = select([tables.users.c.username]).select_from(tables.users)
    users = await database.fetch_all(query)

    likes = []
    for post in posts:
        for i in range(3):
            like = {'username': users[random.randint(0, len(users) - 1)]['username'], 'post_id': str(post['post_id'])}
            if like not in likes:
                likes.append(like)
            else:
                print('like already in list')

    obj = json.dumps(likes, indent=4)
    with open(APP_ROOT + "/mock_data/likes.json", "w") as outfile:
        outfile.write(obj)


async def populate_mock_data():
    query = select([func.count()]).select_from(tables.users)
    count = await database.execute(query)
    if count == 0:
        print('no users in database. uploading mock user data...')
        f = open(APP_ROOT + "/mock_data/users.json")
        data = json.load(f)
        user_data = [{k: v for k, v in row.items() if k in ['username', 'full_name', 'bio']} for row in data]
        query = insert(tables.users)
        async with database.transaction():
            await database.execute_many(query, user_data)

        credential_data = [{k: v for k, v in row.items() if k in ['username', 'hashed_password', 'salt']} for row in
                           data]

        query = insert(tables.user_credentials)
        async with database.transaction():
            await database.execute_many(query, credential_data)

    query = select([func.count()]).select_from(tables.followers)
    count = await database.execute(query)
    if count == 0:
        print('no followers in database. uploading mock user data...')
        f = open(APP_ROOT + "/mock_data/followers.json")
        data = json.load(f)
        query = insert(tables.followers)
        async with database.transaction():
            await database.execute_many(query, data)

    query = select([func.count()]).select_from(tables.following)
    count = await database.execute(query)
    if count == 0:
        print('no followings in database. uploading mock user data...')
        f = open(APP_ROOT + "/mock_data/following.json")
        data = json.load(f)
        query = insert(tables.following)
        async with database.transaction():
            await database.execute_many(query, data)

    query = select([func.count()]).select_from(tables.posts)
    count = await database.execute(query)
    if count == 0:
        print('no posts in database. uploading mock user data...')
        f = open(APP_ROOT + "/mock_data/posts.json")
        data = json.load(f)
        post_data = [{k: v for k, v in row.items() if k in ['username', 'content', 'post_id']} for row in data]
        query = insert(tables.posts)
        async with database.transaction():
            await database.execute_many(query, post_data)

    query = select([func.count()]).select_from(tables.comments)
    count = await database.execute(query)
    if count == 0:
        print('no comments in database. uploading mock user data...')
        f = open(APP_ROOT + "/mock_data/comments.json")
        data = json.load(f)
        comment_data = [{k: v for k, v in row.items() if k in ['username', 'content', 'post_id']} for row in data]
        query = insert(tables.comments)
        async with database.transaction():
            await database.execute_many(query, comment_data)

    query = select([func.count()]).select_from(tables.likes)
    count = await database.execute(query)
    if count == 0:
        print('no likes in database. uploading mock user data...')
        f = open(APP_ROOT + "/mock_data/likes.json")
        data = json.load(f)
        query = insert(tables.likes)
        async with database.transaction():
            await database.execute_many(query, data)

    query = select([func.count()]).select_from(tables.post_locations)
    count = await database.execute(query)
    if count == 0:
        print('no locations in database. uploading mock user data...')
        f = open(APP_ROOT + "/mock_data/post_locations.json")
        data = json.load(f)
        query = insert(tables.post_locations)
        async with database.transaction():
            await database.execute_many(query, data)
