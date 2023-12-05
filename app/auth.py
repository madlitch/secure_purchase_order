from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import UserAuthIn, User, TokenData
from tables import users, user_credentials
from database import database
from sqlalchemy.sql import select

import bcrypt
import exceptions
import constants

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, salt, hashed_password):
    # Compares a plain password (with added salt) with a stored hashed password to validate user credentials.
    return pwd_context.verify(plain_password + salt, hashed_password)


def get_password_hash(password_and_salt):
    # Hashes a password combined with salt using bcrypt, used for securely storing user passwords.
    return pwd_context.hash(password_and_salt)


def gen_salt():
    # Generates a salt string using bcrypt, enhancing the security of the hashed passwords.
    return str(bcrypt.gensalt(10))


async def get_user(username: str):
    # Retrieves a user's authentication information from the database, including their hashed password and salt.
    query = select([users.join(user_credentials, users.c.username == user_credentials.c.username)]).where(
        users.c.username == username.lower())
    user = await database.fetch_one(query)
    if user:
        return UserAuthIn(**user)


async def authenticate_user(username: str, password: str):
    # Authenticates a user by verifying their password. Returns the user if authentication is successful.
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.salt, user.hashed_password):
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


async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Extracts and verifies the JWT token to retrieve the current user's information. Throws an exception if the token
    # is invalid.
    try:
        payload = jwt.decode(token, constants.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise exceptions.API_401_CREDENTIALS_EXCEPTION
        token_data = TokenData(username=username)
    except JWTError:
        raise exceptions.API_401_CREDENTIALS_EXCEPTION
    user = await get_user(username=token_data.username)
    if user is None:
        raise exceptions.API_401_CREDENTIALS_EXCEPTION
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # Retrieves the current active user based on the provided user context. This is used in the route handlers
    # to get the user making the request.
    return current_user


async def login(form_data):
    # Authenticates a user based on their login credentials. If successful, generates and returns a JWT access token;
    # otherwise, raises an HTTP exception.
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
