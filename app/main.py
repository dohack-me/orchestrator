from fastapi import FastAPI
import docker
app = FastAPI()
client = docker.from_env()

from app import util, init
from app.routes import ping
from app.routes.api.v1 import create, delete
from app.environment import network_name, skip_proxy

if not util.network_exists(network_name):
    init.create_network()

if skip_proxy.lower() != "true":
    if not util.container_exists("proxy"):
        init.create_proxy()

app.include_router(ping.router)
app.include_router(create.router)
app.include_router(delete.router)
