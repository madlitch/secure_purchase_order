from pydantic import BaseModel
from typing import Optional, Any, List, Dict
from pydantic.types import Base64Str
import enum
import datetime
from uuid import UUID


# Auth
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Users
class User(BaseModel):
    username: str
    full_name: str


class UserAvatarIn(User):
    avatar_url: str


class UserIn(User):
    password: str


class UserAuthIn(User):
    username: str
    hashed_password: str
    salt: str


class PostOut(BaseModel):
    post_id: UUID
    username: str
    full_name: str
    content: str
    date_posted: datetime.datetime
    avatar_url: Optional[str]
    image_url: Optional[str]
    comments: int
    likes: int


class Location(BaseModel):
    latitude: float
    longitude: float


# class PostIn(BaseModel):
#     content: str
#     location: Location
#
# class PostIn(BaseModel):
#     content: str
#     image: Optional[Base64Str]
#     location: Location


class UserOut(BaseModel):
    username: str
    full_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    followers: int
    following: int
    posts: List[PostOut]


class CommentOut(BaseModel):
    comment_id: UUID
    username: str
    content: str
    avatar_url: Optional[str]
    date_posted: datetime.datetime


class FollowingOut(BaseModel):
    following: str


class FollowerOut(BaseModel):
    follower: str


class LikeOut(BaseModel):
    username: str



class CommentIn(BaseModel):
    post_id: UUID
    content: str
