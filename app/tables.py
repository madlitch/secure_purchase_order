from sqlalchemy import Column, Integer, String, Boolean, Table, MetaData, Enum, Float, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

users = (
    Table('users', metadata,
          # Column('user_id', UUID, primary_key=True, server_default=func.gen_random_uuid()),
          Column('username', String(100), primary_key=True),
          Column('full_name', String(100)),
          Column('avatar_url', String(500)),  # needs to be constant if user is stored on other servers
          Column('bio', String(500)),
          # Column('server', String(100)),
          ))

user_credentials = (
    Table('user_credentials', metadata,
          Column('username', String(100), ForeignKey('users.username'), primary_key=True, unique=True),
          Column('hashed_password', String(100)),
          Column('salt', String(64)),
          Column('disabled', Boolean, default=False),
          Column('date_created', DateTime, server_default=func.now())
          ))

posts = (
    Table('posts', metadata,
          Column('post_id', UUID, primary_key=True, server_default=func.gen_random_uuid()),
          Column('username', String(100), ForeignKey('users.username')),
          Column('content', String(1000)),
          Column('date_posted', DateTime, server_default=func.now())
          ))

post_locations = (
    Table('post_locations', metadata,
          Column('post_id', UUID, ForeignKey('posts.post_id'), primary_key=True),
          Column('latitude', Float),
          Column('longitude', Float),
          ))

post_images = (
    Table('post_images', metadata,
          Column('post_id', UUID, ForeignKey('posts.post_id'), primary_key=True),
          Column('image_url', String(500), primary_key=True),
          ))

likes = (
    Table('likes', metadata,
          Column('post_id', UUID, ForeignKey('posts.post_id'), primary_key=True),
          Column('username', ForeignKey('users.username'), primary_key=True),
          ))

comments = (
    Table('comments', metadata,
          Column('comment_id', UUID, primary_key=True, server_default=func.gen_random_uuid()),
          Column('post_id', UUID, ForeignKey('posts.post_id')),
          Column('username', String(100), ForeignKey('users.username')),
          Column('content', String(1000)),
          Column('date_posted', DateTime, server_default=func.now())
          ))

followers = (
    Table('followers', metadata,
          Column('user', String(100), ForeignKey('users.username'), primary_key=True),
          Column('follower', String(100), primary_key=True),
          ))

following = (
    Table('following', metadata,
          Column('user', String(100), ForeignKey('users.username'), primary_key=True),
          Column('following', String(100), primary_key=True),
          ))
