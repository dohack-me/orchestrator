import docker
from fastapi import FastAPI
from psycopg_pool import ConnectionPool

from app.environment import authenticate, registry, registry_username, registry_password, database_url

app = FastAPI()
client = docker.from_env()
pool = ConnectionPool(database_url)

if authenticate:
    client.login(username=registry_username, password=registry_password, registry=registry)

from app.instances import database, listener, scheduler

database.sync_database()
listener.init_listener()
scheduler.init_schedulers()

from app import routes

app.include_router(routes.ping.router)
app.include_router(routes.images.router)
