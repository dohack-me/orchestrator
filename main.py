import random
import string
import docker.errors
from fastapi import FastAPI, Response, status
from pydantic import BaseModel
import os
import uuid
import util

class CreateServiceModel(BaseModel):
    image: str
    tag: str = "latest"

class DeleteServiceModel(BaseModel):
    id: str
app = FastAPI()
client = docker.from_env()
base = os.getenv('BASE_URL')
if base is None:
    raise Exception('Base URL environment variable not set')
if base.count("*") != 1:
    raise Exception('Base URL does not have exactly 1 asterisk')

if not util.container_exists(client, "proxy"):
    print("Could not find proxy container. Creating it now...")
    client.images.pull("traefik", "latest")
    client.containers.run(
        image="traefik",
        name="proxy",
        restart_policy={"Name": "always"},
        detach=True,
        command="--api.insecure=true --providers.docker",
        ports={'80/tcp':80, "8080/tcp":8080},
        volumes=["/var/run/docker.sock:/var/run/docker.sock"]
    )
    print("Created proxy container.")

@app.get("/")
async def root():
    return "Healthy"

@app.post("/api/v1/service")
async def create(body: CreateServiceModel, response: Response):
    try:
        client.images.pull(body.image, body.tag)
        container_id = str(uuid.uuid4())
        client.containers.run(
            image=body.image,
            name=container_id,
            auto_remove=True,
            detach=True,
            labels=["traefik.http.routers.{}.rule=Host(`{}`)".format(container_id, base.replace("*", container_id[:8]))]
        )
        return container_id
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

@app.delete("/api/v1/service")
async def delete(body: DeleteServiceModel, response: Response):
    try:
        container = client.containers.get(body.id)
        container.stop()
    except docker.errors.NotFound:
        response.status_code = status.HTTP_404_NOT_FOUND
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR