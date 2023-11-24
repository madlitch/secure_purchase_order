from pydantic import BaseModel
from typing import Optional, Any, List, Dict
from uuid import UUID

import datetime
import enum


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


class SearchUser(User):
    is_following: bool
    avatar_url: str


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
    latitude: float
    longitude: float
    comments: int
    likes: int


class Location(BaseModel):
    latitude: float
    longitude: float


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


class ActivityAction(enum.Enum):
    follow = 0
    like = 1
    comment = 2


class ActivityOut(BaseModel):
    action_user: str
    action: str
    full_name: str
    avatar_url: str
    post_id: Optional[UUID]
