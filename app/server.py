import uuid
from uuid import UUID

from fastapi import FastAPI, Depends, status, Request, UploadFile, BackgroundTasks, Form, Response, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

import time
import logging
import random
import string
import helper

import models
import database
import methods
import auth
import constants


async def not_found(request: Request, user: models.User = Depends(auth.get_current_user)):
    return templates.TemplateResponse("message.html", {
        "request": request,
        "user": user,
        "title": "Not Found",
        "header": "404",
        "message": "Not Found"
    })


exceptions_handler = {
    404: not_found
}

app = FastAPI(exception_handlers=exceptions_handler)

# Configure logging to file 'info.log' with INFO level.
logging.basicConfig(filename='log.log', level=logging.INFO)
logger = logging.getLogger(__name__)


@app.middleware('http')
async def log_requests(request: Request, call_next):
    # Middleware to log HTTP requests. Generates a unique ID for each request and logs the request path and
    # processing time.
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
    return response


@app.on_event("startup")
async def startup():
    # Startup event handler to connect to the database when the application starts.
    await database.database.connect()


@app.on_event("shutdown")
async def shutdown():
    # Shutdown event handler to disconnect from the database when the application stops.
    await database.database.disconnect()


app.mount("/static", StaticFiles(directory="{}static".format(constants.APP_ROOT)), name="static")
templates = Jinja2Templates(directory="{}templates".format(constants.APP_ROOT))


def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object to a string using a specified format."""
    if value is None:
        return ""
    return value.strftime(format)


templates.env.filters['format_datetime'] = format_datetime


# Util --

@app.get("/reset_database")
async def reset_database():
    # await methods.send_email()
    await helper.reset_database()


# Auth --

@app.post("/token", response_model=models.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = await auth.login_for_access_token(form_data)
    return token


@app.post("/login", response_class=HTMLResponse)
async def login_for_access_cookie(username: str = Form(...), password: str = Form(...)):
    return await auth.login_for_access_cookie(username, password)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request, user: models.User = Depends(auth.get_current_user)):
    return templates.TemplateResponse("login.html", {"request": request, "user": user})


@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request, ):
    response = templates.TemplateResponse("message.html", {
        "request": request,
        "title": "Logout Success",
        "header": "Success",
        "message": "You have successfully logged out."
    })
    response.delete_cookie("access_token")
    return response


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request, user: models.User = Depends(auth.get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/users", response_class=HTMLResponse)
async def users(request: Request, user: models.User = Depends(auth.get_current_user)):
    if user:
        users = await methods.get_users()

        return templates.TemplateResponse("users.html", {
            "request": request,
            "user": user,
            "title": "Users",
            "users": users
        })
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.get("/create_user", response_class=HTMLResponse)
async def create_user(request: Request, user: models.User = Depends(auth.get_current_user)):
    if user:
        return templates.TemplateResponse("create_user.html", {
            "request": request,
            "user": user,
            "title": "Create User"
        })
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.post("/create_user", response_class=HTMLResponse)
async def create_user(
        request: Request,
        user: models.UserSys = Depends(auth.get_current_user),
        role: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)
):
    await methods.create_user(
        first_name,
        last_name,
        role,
        email,
        password
    )
    success_message = "User successfully created."

    return templates.TemplateResponse("message.html", {
        "request": request,
        "user": user,
        "title": "User Creation",
        "header": "Success",
        "message": success_message
    })


@app.get("/delete_user")
async def download_public_key(request: Request, user_id: UUID, user: models.User = Depends(auth.get_current_user)):
    if user and user['role'] == "Admin":
        await methods.delete_user(user_id)

    return templates.TemplateResponse("message.html", {
        "request": request,
        "user": user,
        "title": "User Creation",
        "header": "Success",
        "message": "User successfully deleted"
    })


@app.get("/public_key", response_class=HTMLResponse)
async def public_key(request: Request, user_id: UUID, user: models.User = Depends(auth.get_current_user)):
    if user:
        public_key = await methods.get_public_key(user_id)
        return PlainTextResponse(public_key)
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.get("/download_public_key", response_class=HTMLResponse)
async def download_public_key(request: Request, user_id: UUID, user: models.User = Depends(auth.get_current_user)):
    if user:
        return await methods.download_public_key(user_id)
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.get("/private_key", response_class=HTMLResponse)
async def private_key(request: Request, user: models.User = Depends(auth.get_current_user)):
    if user:
        return templates.TemplateResponse("check_password.html", {
            "request": request,
            "user": user,
            "title": "Download Private Key",
            "action": "/download_private_key"
        })
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.post("/download_private_key")
async def private_key(request: Request, user: models.User = Depends(auth.get_current_user), password: str = Form(...)):
    if user:
        return await methods.download_private_key(user, password, request, templates)
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.get("/derived_key")
async def a(request: Request, password: str, user: models.User = Depends(auth.get_current_user)):
    if user:
        _, salt = await methods.get_private_key_and_salt(user['user_id'])

        derived_key = await auth.get_derived_key(password, salt.encode('utf-8'))
        print(derived_key.decode('utf-8'))
        # TODO find way to display the derived key
        # return await methods.download_private_key(user, password)
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.get("/purchase_orders", response_class=HTMLResponse)
async def purchase_orders(request: Request, user: models.User = Depends(auth.get_current_user)):
    if user:
        pos = await methods.get_purchase_orders_by_user(user)

        return templates.TemplateResponse("purchase_orders.html", {
            "request": request,
            "user": user,
            "title": "Purchase Orders",
            "purchase_orders": pos
        })
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.get("/purchase_orders/{po_id}", response_class=HTMLResponse)
async def purchase_orders(request: Request, po_id: uuid.UUID, user: models.User = Depends(auth.get_current_user)):
    if user:
        po = await methods.get_purchase_order(po_id)

        if user['user_id'] == po.recipient_id or user['user_id'] == po.sender_id or user['user_id'] == po.purchaser_id:
            return templates.TemplateResponse("check_password.html", {
                "request": request,
                "user": user,
                "title": "View Purchase Order",
                "action": "/view_purchase_order/{}".format(po_id)
            })
        else:
            return await methods.message(request, user, templates, "Not Authorized",
                                         "You are not authorized to view this purchase.")
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.get("/new_purchase_order", response_class=HTMLResponse)
async def purchase(request: Request, user: models.User = Depends(auth.get_current_user)):
    if user:
        supervisors = await methods.get_users_by_role("Supervisor")
        return templates.TemplateResponse("new_purchase_order.html", {
            "request": request,
            "user": user,
            "supervisors": supervisors
        })
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.post("/view_purchase_order/{po_id}", response_class=HTMLResponse)
async def purchase_orders(
        request: Request,
        po_id: uuid.UUID,
        user: models.User = Depends(auth.get_current_user),
        password: str = Form(...)
):
    if user:
        po = await methods.get_purchase_order(po_id)

        if user['user_id'] == po.recipient_id or user['user_id'] == po.sender_id or user['user_id'] == po.purchaser_id:
            return await methods.view_purchase_order(request, templates, po_id, user, password)
        else:
            return await methods.message(request, user, templates, "Not Authorized",
                                         "You are not authorized to view this purchase.")
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.post("/review_purchase_order/{po_id}", response_class=HTMLResponse)
async def purchase_orders(
        request: Request,
        po_id: uuid.UUID,
        user: models.User = Depends(auth.get_current_user),
        purchaser_id: uuid.UUID = Form(...),
        accept: bool = Form(...),
        password: str = Form(...)
):
    if user:
        po = await methods.get_purchase_order(po_id)

        if user['user_id'] == po.recipient_id:
            return await methods.review_purchase_order(request, templates, po_id, user, purchaser_id, password, accept)
        else:
            return await methods.message(request, user, templates, "Not Authorized",
                                         "You are not authorized to view this purchase.")
    else:
        return await methods.message(request, user, templates, "Not Authenticated", "Please login first.")


@app.post("/purchase")
async def submit_order(
        request: Request,
        user: models.UserSys = Depends(auth.get_current_user),
        supervisor_id: str = Form(...),
        supplier_name: str = Form(...),
        supplier_contact: str = Form(...),
        supplier_address: str = Form(...),
        item_number: List[str] = Form(...),
        item_quantity: List[int] = Form(...),
        item_price: List[float] = Form(...),
        item_url: List[str] = Form(...),
        item_details: List[str] = Form(...),
        password: str = Form(...)
):
    return await methods.submit_purchase_order(
        request,
        templates,
        user,
        supervisor_id,
        supplier_name,
        supplier_contact,
        supplier_address,
        item_number,
        item_quantity,
        item_price,
        item_url,
        item_details,
        password
    )


@app.post("/client/comment", status_code=status.HTTP_201_CREATED)
async def create_comment(comment: str, current_user: models.User = Depends(auth.get_current_user_from_token)):
    return await methods.create_comment(comment, current_user)
