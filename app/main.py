from fastapi import FastAPI
import docker
app = FastAPI()
client = docker.from_env()

from app import routes
app.include_router(routes.ping.router)
app.include_router(routes.websites.router)
app.include_router(routes.sockets.router)