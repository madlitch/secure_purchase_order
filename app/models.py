from pydantic import BaseModel
from typing import Optional, Any, List, Dict
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
    comments: int
    likes: int


class UserOut(BaseModel):
    username: str
    full_name: str
    bio: str
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


class Location(BaseModel):
    lat: float
    lon: float


class PostIn(BaseModel):
    content: str
    location: Location


class CommentIn(BaseModel):
    post_id: UUID
    content: str
