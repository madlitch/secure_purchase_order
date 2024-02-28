import uuid

import pgpy
import json
import os.path
import aiofiles
import requests

from uuid import UUID
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi import Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.sql import select, insert, update, or_, delete
from sqlalchemy import func
from pgpy import PGPKey, PGPMessage
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm
from typing import List
from datetime import datetime, timedelta

import auth
import tables
import exceptions
import models
import constants

from database import database
from constants import MEDIA_ROOT


async def create_user(first_name: str, last_name: str, role: str, email: str, password: str):
    query = tables.users.select().where(tables.users.c.email == email)
    existing_user = await database.execute(query)
    if existing_user:
        raise exceptions.API_409_USERNAME_CONFLICT_EXCEPTION
    else:
        async with (database.transaction()):
            try:
                key = PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 2048)
                uid = pgpy.PGPUID.new(first_name + ' ' + last_name, email=email)
                key.add_uid(uid, usage={KeyFlags.Sign, KeyFlags.EncryptCommunications},
                            hashes=[HashAlgorithm.SHA256], ciphers=[SymmetricKeyAlgorithm.AES256],
                            compression=[CompressionAlgorithm.ZLIB])

                query = tables.users.insert().values(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=auth.get_password_hash(password),
                    public_key=str(key.pubkey)
                )
                user_id = await database.execute(query)

                salt = await auth.gensalt()

                derived_key = await auth.get_derived_key(password, salt)

                key.protect(derived_key, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)

                query = tables.private_keys.insert().values(
                    user_id=user_id,
                    private_key=str(key),
                    salt=salt.decode('utf-8')
                )
                await database.execute(query)

                query = tables.user_roles.insert().values(
                    user_id=user_id,
                    role_name=role
                )
                await database.execute(query)
            except Exception as e:
                print(e)
                await database.rollback()


async def delete_user(user_id):
    query = tables.users.delete().where(tables.users.c.user_id == user_id)
    await database.execute(query)


async def get_private_key_and_salt(user_id):
    query = tables.private_keys.select().where(tables.private_keys.c.user_id == user_id)
    pkey = await database.fetch_one(query)
    return pkey['private_key'], pkey['salt']


async def get_users():
    query = select([tables.users, tables.roles]).select_from(
        tables.users.join(tables.user_roles).join(tables.roles)
    )
    return await database.fetch_all(query)


async def get_public_key(user_id):
    query = select([tables.users.c.public_key]).where(tables.users.c.user_id == user_id)
    return await database.execute(query)


async def get_users_by_role(role_name: str):
    query = select([tables.users]).select_from(
        tables.users.join(tables.user_roles).join(tables.roles)
    ).where(tables.roles.c.role_name == role_name)
    return await database.fetch_all(query)


async def get_purchase_order(po_id: uuid):
    query = select([tables.purchase_orders]).where(tables.purchase_orders.c.purchase_order_id == po_id)
    return await database.fetch_one(query)


async def get_purchase_orders_by_user(user):
    sender = tables.users.alias('sender')
    recipient = tables.users.alias('receiver')

    if user['role'] == "Admin":
        query = select([
            tables.purchase_orders,
            sender.c.first_name.label('sender_first_name'),
            sender.c.last_name.label('sender_last_name'),
            recipient.c.first_name.label('receiver_first_name'),
            recipient.c.last_name.label('receiver_last_name'),
        ]).select_from(
            tables.purchase_orders
            .join(sender, tables.purchase_orders.c.sender_id == sender.c.user_id)
            .join(recipient, tables.purchase_orders.c.recipient_id == recipient.c.user_id)
        )
        return await database.fetch_all(query)
    else:
        query = select([
            tables.purchase_orders,
            sender.c.first_name.label('sender_first_name'),
            sender.c.last_name.label('sender_last_name'),
            recipient.c.first_name.label('receiver_first_name'),
            recipient.c.last_name.label('receiver_last_name'),
        ]).select_from(
            tables.purchase_orders
            .join(sender, tables.purchase_orders.c.sender_id == sender.c.user_id)
            .join(recipient, tables.purchase_orders.c.recipient_id == recipient.c.user_id)
        ).where(
            or_(
                tables.purchase_orders.c.sender_id == user['user_id'],
                tables.purchase_orders.c.recipient_id == user['user_id'],
            )
        )
        return await database.fetch_all(query)


async def download_private_key(user, password: str):
    private_key, salt = await get_private_key_and_salt(user['user_id'])
    derived_key = await auth.get_derived_key(password, salt.encode('utf-8'))
    print(derived_key.decode('utf-8'))
    user_private_key = PGPKey()
    user_private_key.parse(private_key)
    assert user_private_key.is_unlocked is False

    try:
        with user_private_key.unlock(derived_key):
            key = str(user_private_key)
            name = "{}_{}".format(user['first_name'], user['last_name'])

            def iterfile():
                yield key

            return StreamingResponse(iterfile(), media_type="application/pgp-keys", headers={
                "Content-Disposition": "attachment; filename={}_private_key.asc".format(name)
            })
    except Exception as e:
        # TODO handle error for wrong password
        raise e


async def download_public_key(user_id):
    user = await auth.get_user_by_id(user_id)
    key = str(await get_public_key(user['user_id']))
    name = "{}_{}".format(user['first_name'], user['last_name'])

    def iterfile():
        yield key

    return StreamingResponse(iterfile(), media_type="application/pgp-keys", headers={
        "Content-Disposition": "attachment; filename={}_public_key.asc".format(name)
    })


async def send_email(sender, body, recipient):
    message = MessageSchema(
        subject="Purchase Order Request from {}".format(sender),
        recipients=[recipient],
        body=str(body),
        subtype=MessageType.plain)

    fm = FastMail(constants.conf)
    await fm.send_message(message)


def format_purchase_order(data, review_url):
    formatted_text = f"Purchase Order Summary\n"
    formatted_text += f"Date Requested: {data['readable_timestamp']}\n\n"
    formatted_text += f"Requested by: {data['sender_name']}\n"
    formatted_text += f"Sent to: {data['recipient_name']}\n\n"
    formatted_text += "Supplier Information:\n"
    formatted_text += f"Name: {data['purchase_order']['supplier_name']}\n"
    formatted_text += f"Contact: {data['purchase_order']['supplier_contact']}\n"
    formatted_text += f"Address: {data['purchase_order']['supplier_address']}\n\n"
    formatted_text += "Items Ordered:\n"

    for idx, item in enumerate(data['purchase_order']['items'], start=1):
        formatted_text += f"Item {idx}:\n"
        formatted_text += f"  - Details: {item['item_details']}\n"
        formatted_text += f"  - Number: {item['item_number']}\n"
        formatted_text += f"  - Quantity: {item['item_quantity']}\n"
        formatted_text += f"  - Price: ${item['item_price']}\n"
        formatted_text += f"  - URL: {item['item_url']}\n\n"

    formatted_text += f"Review Purchase Order: {review_url}\n"

    return formatted_text


async def submit_purchase_order(
        request: Request,
        templates,
        user: models.UserSys,
        supervisor_id: str,
        supplier_name: str,
        supplier_contact: str,
        supplier_address: str,
        item_number: List[str],
        item_quantity: List[int],
        item_price: List[float],
        item_url: List[str],
        item_details: List[str],
        password: str
):
    items = [
        {
            "item_number": num,
            "item_quantity": qty,
            "item_price": price,
            "item_url": url,
            "item_details": details,
        }
        for num, qty, price, url, details in zip(item_number, item_quantity, item_price, item_url, item_details)
    ]

    sender = await auth.get_user_by_id(user['user_id'])
    recipient = await auth.get_user_by_id(supervisor_id)

    purchase_order = {
        "supplier_name": supplier_name,
        "supplier_contact": supplier_contact,
        "supplier_address": supplier_address,
        "items": items
    }
    sender_name = "{} {}".format(sender.first_name, sender.last_name)
    recipient_name = "{} {}".format(recipient.first_name, recipient.last_name)

    time = datetime.utcnow()

    data = {
        "sender_name": sender_name,
        "recipient_name": recipient_name,
        "purchase_order": purchase_order,
        "created_timestamp": time.isoformat(),
        "readable_timestamp": time.strftime("%B %d, %Y, %H:%M")
    }

    recipient_public_key = PGPKey()
    recipient_public_key.parse(recipient.public_key)

    private_key, salt = await get_private_key_and_salt(sender.user_id)

    derived_key = await auth.get_derived_key(password, salt.encode('utf-8'))

    sender_private_key = PGPKey()
    sender_private_key.parse(private_key)
    assert sender_private_key.is_unlocked is False

    server_private_key, _ = pgpy.PGPKey.from_file(constants.SERVER_PRIVATE_KEY)
    assert server_private_key.is_unlocked is False

    try:
        with sender_private_key.unlock(derived_key):
            with server_private_key.unlock(constants.SERVER_PRIVATE_KEY_PW):
                po_id = uuid.uuid4()
                email_content = PGPMessage.new(
                    format_purchase_order(data, "{}/purchase_orders/{}".format(constants.SERVER_ADDRESS, po_id)))

                email_content |= server_private_key.sign(email_content)
                email_content |= sender_private_key.sign(email_content)
                encrypted_signed_email = recipient_public_key.encrypt(email_content)

                json_content = PGPMessage.new(json.dumps(data))

                json_content |= server_private_key.sign(json_content)
                json_content |= sender_private_key.sign(json_content)
                encrypted_signed_json = recipient_public_key.encrypt(json_content)

                query = tables.purchase_orders.insert().values(
                    purchase_order_id=po_id,
                    sender_id=sender.user_id,
                    recipient_id=recipient.user_id,
                    email_content=str(encrypted_signed_email),
                    json_content=str(encrypted_signed_json),
                )
                await database.execute(query)

                query = select([tables.purchase_orders.c.purchase_order_number]).where(
                    tables.purchase_orders.c.purchase_order_id == po_id
                )
                po_number = await database.execute(query)

                await send_email(
                    sender=sender_name,
                    body=str(encrypted_signed_email),
                    recipient=recipient.email
                )
                del derived_key
                del private_key

                return templates.TemplateResponse("message.html", {
                    "request": request,
                    "user": user,
                    "title": "Submit Success",
                    "header": "Success",
                    "message": "Purchase Order #{} Successfully Submitted".format(po_number)
                })
    except Exception as e:
        # TODO add logic that catches wrong password
        raise e


def prepare_items_with_index(items):
    for index, item in enumerate(items, start=1):
        item['index'] = index
    return items


async def view_purchase_order(request, templates, po_id, user, password: str):
    po = await get_purchase_order(po_id)
    sender = await auth.get_user_by_id(po.sender_id)

    private_key, salt = await get_private_key_and_salt(user['user_id'])
    derived_key = await auth.get_derived_key(password, salt.encode('utf-8'))
    user_private_key = PGPKey()
    user_private_key.parse(private_key)

    sender_public_key = PGPKey()
    sender_public_key.parse(sender.public_key)
    server_public_key, _ = pgpy.PGPKey.from_file(constants.SERVER_PUBLIC_KEY)

    assert user_private_key.is_unlocked is False

    try:
        with user_private_key.unlock(derived_key):
            message = PGPMessage.from_blob(po.json_content)

            decrypted_message = user_private_key.decrypt(message)

            content = json.loads(decrypted_message.message)
            items = prepare_items_with_index(content['purchase_order']['items'])

            return templates.TemplateResponse("purchase_order.html", {
                "request": request,
                "user": user,
                "title": "Purchase Order {}".format(po.purchase_order_number),
                "header": "Purchase Order {}".format(po.purchase_order_number),
                "data": content,
                "valid_sender_signature": bool(sender_public_key.verify(decrypted_message)),
                "valid_server_signature": bool(server_public_key.verify(decrypted_message)),
                "items": items

            })

    except Exception as e:
        # TODO handle error for wrong password
        raise e
