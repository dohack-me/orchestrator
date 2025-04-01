from fastapi import FastAPI
import docker
app = FastAPI()
client = docker.from_env()

from app.environment import authenticate, registry, registry_username, registry_password
if authenticate:
    client.login(username=registry_username, password=registry_password, registry=registry)

from app import database

database.init_database()

from app import routes
app.include_router(routes.ping.router)
app.include_router(routes.services.router)
app.include_router(routes.images.router)