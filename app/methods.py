from uuid import UUID
from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.sql import select, insert, update, or_, delete
from sqlalchemy import func
from pgpy import PGPKey, PGPMessage
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm

import pgpy
import os.path
import aiofiles
import requests

import auth
import tables
import exceptions
import models

from database import database
from constants import MEDIA_ROOT


async def create_user(user: models.UserIn):
    query = tables.users.select().where(tables.users.c.email == user.email)
    existing_user = await database.execute(query)
    if existing_user:
        raise exceptions.API_409_USERNAME_CONFLICT_EXCEPTION
    else:
        async with (database.transaction()):
            try:
                key = PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 2048)
                uid = pgpy.PGPUID.new(user.first_name + ' ' + user.last_name, email=user.email)
                key.add_uid(uid, usage={KeyFlags.Sign, KeyFlags.EncryptCommunications},
                            hashes=[HashAlgorithm.SHA256], ciphers=[SymmetricKeyAlgorithm.AES256],
                            compression=[CompressionAlgorithm.ZLIB])

                query = tables.users.insert().values(
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    password=auth.get_password_hash(user.password),
                    public_key=str(key.pubkey)
                )
                user_id = await database.execute(query)

                salt = await auth.gensalt()

                derived_key = await auth.get_derived_key(user.password, salt)

                key.protect(derived_key, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)

                query = tables.private_keys.insert().values(
                    user_id=user_id,
                    private_key=str(key),
                    salt=str(salt)
                )
                await database.execute(query)
            except Exception as e:
                print(e)
                await database.rollback()
