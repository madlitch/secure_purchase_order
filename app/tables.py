from sqlalchemy import Column, Integer, String, Boolean, Table, MetaData, Enum, Float, ForeignKey, DateTime, func, TEXT
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

users = (
    Table('users', metadata,
          Column('user_id', UUID, primary_key=True, server_default=func.gen_random_uuid()),
          Column('email', String(100), unique=True),
          Column('first_name', String(100)),
          Column('last_name', String(100)),
          Column('public_key', TEXT),
          Column('password', TEXT),
          Column('date_created', DateTime, server_default=func.now()),
          Column('date_updated', DateTime, server_default=func.now()),
          ))

private_keys = (
    Table('private_keys', metadata,
          Column('user_id', UUID, ForeignKey('users.user_id', ondelete='cascade'), primary_key=True,
                 unique=True),
          Column('private_key', TEXT),
          Column('derived_key', TEXT),
          Column('salt', TEXT),
          ))

roles = (
    Table('roles', metadata,
          Column('role_name', String(100), primary_key=True,),
          ))

user_roles = (
    Table('user_roles', metadata,
          Column('role_name', String(100), ForeignKey('roles.role_name', ondelete='cascade'), primary_key=True),
          Column('user_id', UUID, ForeignKey('users.user_id', ondelete='cascade'), primary_key=True),
          ))

messages = (
    Table('messages', metadata,
          Column('message_id', UUID, primary_key=True, server_default=func.gen_random_uuid()),
          Column('sender_id', UUID, ForeignKey('users.user_id', ondelete='cascade')),
          Column('recipient_id', UUID, ForeignKey('users.user_id', ondelete='cascade')),
          Column('message_content', TEXT),
          Column('signature', TEXT),
          Column('sent_timestamp', DateTime, server_default=func.now()),
          Column('received_timestamp', DateTime),
          Column('signed_timestamp', DateTime),
          ))
