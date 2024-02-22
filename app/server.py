from fastapi import FastAPI, Depends, status, Request, UploadFile, BackgroundTasks, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm

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

app = FastAPI()

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


# Util --

@app.get("/reset_database")
async def reset_database():
    await helper.reset_database()


@app.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_user(user: models.UserIn):
    await methods.create_user(user)


@app.get("/util")
async def util():
    pass


# Auth --

@app.post("/token", response_model=models.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = await auth.login(form_data)
    return token


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test", response_class=HTMLResponse)
async def test(request: Request, current_user: models.User = Depends(auth.get_current_active_user)):
    print(current_user)
    return templates.TemplateResponse("index.html", {"request": request})
