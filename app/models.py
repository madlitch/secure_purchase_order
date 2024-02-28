from pydantic import BaseModel, EmailStr
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
    email: Optional[str] = None


# Users
class User(BaseModel):
    email: str
    first_name: str
    last_name: str


class UserIn(User):
    password: str


class UserSys(User):
    user_id: UUID


class UserAuthIn(User):
    password: str


class EmailSchema(BaseModel):
    email: List[EmailStr]
    body: str
    subject: str