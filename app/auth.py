from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from passlib.context import CryptContext

from models import UserAuthIn, User, TokenData
from tables import users, roles, user_roles
from database import database
from sqlalchemy.sql import select
from hashlib import sha256
from base64 import urlsafe_b64encode

import bcrypt
import exceptions
import constants

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300
SALT_ROUNDS = 12

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    # Compares a plain password (with added salt) with a stored hashed password to validate user credentials.
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password):
    # Hashes a password combined with salt using bcrypt, used for securely storing user passwords.
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(SALT_ROUNDS)).decode('utf-8')


async def get_user_by_id(user_id: str):
    query = select([users]).where(
        users.c.user_id == user_id)
    user = await database.fetch_one(query)
    return user


async def get_user_by_email(email: str):
    query = select(users).where(
        users.c.email == email.lower())
    user = await database.fetch_one(query)
    return user


async def get_user_with_roles(email: str):
    query = select([users]).where(users.c.email == email.lower())
    user_result = await database.fetch_one(query)

    if user_result:
        user = dict(user_result)
        role_query = select([roles]).select_from(
            roles.join(user_roles, roles.c.role_name == user_roles.c.role_name)
        ).where(user_roles.c.user_id == user['user_id'])
        role = await database.fetch_one(role_query)

        if role:
            user['role'] = role['role_name']
        else:
            user['role'] = 'User'

        return user
    return None


async def authenticate_user(email: str, password: str):
    # Authenticates a user by verifying their password. Returns the user if authentication is successful.
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # Creates a JWT access token with an optional expiry time. This token is used for secure user sessions.
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, constants.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(token, constants.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = TokenData(email=email)
    except JWTError:
        return None
    user = await get_user_with_roles(email=token_data.email)
    if user is None:
        return None
    return user


async def get_current_user_from_token(token: str = Depends(oauth2_scheme)):
    # Extracts and verifies the JWT token to retrieve the current user's information. Throws an exception if the token
    # is invalid.
    try:
        payload = jwt.decode(token, constants.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise exceptions.API_401_CREDENTIALS_EXCEPTION
        token_data = TokenData(username=email)
    except JWTError:
        raise exceptions.API_401_CREDENTIALS_EXCEPTION
    user = await get_user_with_roles(email=token_data.email)
    if user is None:
        raise exceptions.API_401_CREDENTIALS_EXCEPTION
    return user


async def login_for_access_token(form_data):
    # Authenticates a user based on their login credentials. If successful, generates and returns a JWT access token;
    # otherwise, raises an HTTP exception.
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


async def login_for_access_cookie(username: str, password: str):
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)

    return response


async def get_derived_key(password, salt):
    bcrypt_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    sha256_hash = sha256(bcrypt_hash).digest()
    key = urlsafe_b64encode(sha256_hash)

    return key


async def gensalt():
    return bcrypt.gensalt(SALT_ROUNDS)
