from typing import Annotated
import docker.errors
from fastapi import FastAPI, Response, Header, status
from pydantic import BaseModel
import os
import uuid
import util

class CreateServiceModel(BaseModel):
    image: str
    tag: str = "latest"

class DeleteServiceModel(BaseModel):
    id: str

def assert_env(name):
    env = os.getenv(name)
    if env is None:
        raise RuntimeError("Environment variable {} is not set".format(name))
    return env

"""
Initialize global variables, including environment variables
"""
app = FastAPI()
client = docker.from_env()

base = assert_env("BASE_URL")
if base.count("*") > 1:
    raise Exception('Base URL has more than 1 asterisk')
secret_key = assert_env("SECRET_KEY")
network_name = assert_env('NETWORK_NAME')
skip_proxy = os.getenv("SKIP_PROXY")

"""
Handles proxy container and network
"""

if not util.network_exists(client, network_name):
    print("Could not find proxy network. Creating it now...")
    client.networks.create(
        name=network_name,
        driver="bridge",
    )
    print("Created proxy network.")

if skip_proxy is None or skip_proxy.lower() != "true":
    if not util.container_exists(client, "proxy"):
        print("Could not find proxy container. Creating it now...")
        client.images.pull("traefik", "latest")
        client.containers.run(
            image="traefik",
            name="proxy",
            restart_policy={"Name": "always"},
            detach=True,
            network="proxy",
            command="--providers.docker",
            ports={'80/tcp': 80},
            volumes=["/var/run/docker.sock:/var/run/docker.sock"]
        )
        print("Created proxy container.")

@app.get("/")
async def root():
    return "Healthy"

@app.post("/api/v1/service")
async def create(
        body: CreateServiceModel,
        response: Response,
        authorization: Annotated[str | None, Header()] = None
):
    if authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return
    if authorization != secret_key:
        response.status_code = status.HTTP_403_FORBIDDEN
        return
    try:
        client.images.pull(body.image, body.tag)
        container_id = str(uuid.uuid4())
        url = base.replace("*", container_id[:8])
        client.containers.run(
            image=body.image,
            name=container_id,
            auto_remove=True,
            detach=True,
            network=network_name,
            labels={
                "traefik.enable": "true",
                "traefik.http.routers.{}.rule".format(container_id): "Host(`{}`)".format(url),
            }
        )
        return {
            "id": container_id,
            "url": "http://" + url
        }
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

@app.delete("/api/v1/service")
async def delete(
        body: DeleteServiceModel,
        response: Response,
        authorization: Annotated[str | None, Header()] = None
):
    if authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return
    if authorization != secret_key:
        response.status_code = status.HTTP_403_FORBIDDEN
        return
    try:
        container = client.containers.get(body.id)
        container.stop()
    except docker.errors.NotFound:
        response.status_code = status.HTTP_404_NOT_FOUND
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR