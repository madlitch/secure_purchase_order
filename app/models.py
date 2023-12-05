from pydantic import BaseModel
from typing import Optional, Any, List, Dict
from uuid import UUID

import datetime
import enum


# These models define the data structures for various entities such as users, posts, comments, and authentication
# tokens. They are used for data validation, serialization, and deserialization, ensuring consistent and secure data
# handling throughout the application's different operations and interactions.


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
    is_following: Optional[bool]
    avatar_url: str


class UserAvatar(User):
    avatar_url: str


class UserIn(User):
    password: str


class UserAuthIn(User):
    hashed_password: str
    salt: str


class Post(User):
    post_id: UUID
    content: str
    date_posted: datetime.datetime
    latitude: float
    longitude: float


class PostOut(Post):
    avatar_url: Optional[str]
    image_url: Optional[str]
    comments: int
    likes: int
    liked: bool


class UserOut(User):
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


class Comment(BaseModel):
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


class ServerSearchUser(User):
    search_query: str


class ServerUser(User):
    avatar_url: str
    bio: str


class ServerFollowUser(BaseModel):
    username: str
    user: ServerUser


class ServerLike(BaseModel):
    post_id: UUID
    user: ServerUser


class ServerComment(BaseModel):
    comment: Comment
    user: ServerUser
