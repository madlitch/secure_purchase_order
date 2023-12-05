from sqlalchemy import Column, Integer, String, Boolean, Table, MetaData, Enum, Float, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

import models

# This file defines the schema for the database tables used.

# 'metadata': A container for all the table definitions.
# 'users': Stores user profiles with columns like username, full name, avatar URL, and bio.
# 'user_credentials': Contains user authentication data like hashed passwords and salts.
# 'posts': Holds user posts with a UUID identifier, content, and timestamp.
# 'post_locations': Stores geolocation data (latitude, longitude) for each post.
# 'post_images': Links posts to their associated images.
# 'likes': Tracks which users have liked which posts.
# 'comments': Stores comments made on posts along with the commenter's username and timestamp.
# 'followers' and 'following': Represent user relationships, indicating who follows and is followed by whom.
# 'activity': Logs user activities (likes, comments, follows) with an action type and associated post ID.
# 'communities': Lists different community URLs in the network.
# 'following_communities': Tracks which user a 'community' is following.


metadata = MetaData()

users = (
    Table('users', metadata,
          Column('username', String(100), primary_key=True),
          Column('full_name', String(100)),
          Column('avatar_url', String(500)),
          Column('bio', String(500)),
          ))

user_credentials = (
    Table('user_credentials', metadata,
          Column('username', String(100), ForeignKey('users.username', ondelete='cascade'), primary_key=True,
                 unique=True),
          Column('hashed_password', String(100)),
          Column('salt', String(64)),
          Column('disabled', Boolean, default=False),
          Column('date_created', DateTime, server_default=func.now())
          ))

posts = (
    Table('posts', metadata,
          Column('post_id', UUID, primary_key=True, server_default=func.gen_random_uuid()),
          Column('username', String(100), ForeignKey('users.username', ondelete='cascade')),
          Column('content', String(1000)),
          Column('date_posted', DateTime, server_default=func.now())
          ))

post_locations = (
    Table('post_locations', metadata,
          Column('post_id', UUID, ForeignKey('posts.post_id', ondelete='cascade'), primary_key=True),
          Column('latitude', Float),
          Column('longitude', Float),
          ))

post_images = (
    Table('post_images', metadata,
          Column('post_id', UUID, ForeignKey('posts.post_id', ondelete='cascade'), primary_key=True),
          Column('image_url', String(500), primary_key=True),
          ))

likes = (
    Table('likes', metadata,
          Column('post_id', UUID, ForeignKey('posts.post_id', ondelete='cascade'), primary_key=True),
          Column('username', ForeignKey('users.username', ondelete='cascade'), primary_key=True),
          ))

comments = (
    Table('comments', metadata,
          Column('comment_id', UUID, primary_key=True, server_default=func.gen_random_uuid()),
          Column('post_id', UUID, ForeignKey('posts.post_id', ondelete='cascade')),
          Column('username', String(100), ForeignKey('users.username', ondelete='cascade')),
          Column('content', String(1000)),
          Column('date_posted', DateTime, server_default=func.now())
          ))

followers = (
    Table('followers', metadata,
          Column('user', String(100), ForeignKey('users.username', ondelete='cascade'), primary_key=True),
          Column('follower', String(100), ForeignKey('users.username', ondelete='cascade'), primary_key=True),
          ))

following = (
    Table('following', metadata,
          Column('user', String(100), ForeignKey('users.username', ondelete='cascade'), primary_key=True),
          Column('following', String(100), ForeignKey('users.username', ondelete='cascade'), primary_key=True),
          ))

activity = (
    Table('activity', metadata,
          Column('action_id', UUID, primary_key=True, server_default=func.gen_random_uuid()),
          Column('user', String(100), ForeignKey('users.username', ondelete='cascade'), primary_key=True),
          Column('action_user', String(100), ForeignKey('users.username', ondelete='cascade')),
          Column('action', Enum(models.ActivityAction), primary_key=True, default=None),
          Column('post_id', ForeignKey('posts.post_id', ondelete='cascade'), default=None),
          Column('datetime', DateTime, server_default=func.now())
          ))

communities = (
    Table('communities', metadata,
          Column('url', String(100), primary_key=True),
          ))


following_communities = (
    Table('following_communities', metadata,
          Column('username', String(100), ForeignKey('users.username', ondelete='cascade'), primary_key=True),
          Column('community', String(100), ForeignKey('communities.url', ondelete='cascade'), primary_key=True),
          ))
