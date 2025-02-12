import uuid

import docker.errors
from fastapi import APIRouter
from fastapi import Response, Depends, status
from pydantic import BaseModel

from app import dependencies, util
from app.main import client
from app.environment import base_url, network_name

router = APIRouter(
    prefix="/api/v1/service/website",
    dependencies=[Depends(dependencies.get_key)]
)

class CreateWebsiteModel(BaseModel):
    image: str
    tag: str = "latest"


@router.post("/")
async def create(
        body: CreateWebsiteModel,
        response: Response,
):
    try:
        if not util.image_exists(f"{body.image}:{body.tag}"):
            client.images.pull(body.image, body.tag)

        container_id = str(uuid.uuid4())
        url = base_url.replace("*", container_id[:8])
        client.containers.run(
            image=body.image,
            name=container_id,
            auto_remove=True,
            detach=True,
            network=network_name,
            labels={
                "traefik.enable": "true",
                f"traefik.http.routers.http-{container_id}.entrypoints": "http",
                f"traefik.http.routers.http-{container_id}.rule": f"Host(`{url}`)",
            }
        )
        return {
            "id": container_id,
            "url": "https://" + url
        }
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


@router.delete("/{service_id}/")
async def delete(
        service_id: str,
        response: Response
):
    try:
        container = client.containers.get(service_id)
        container.stop()
    except docker.errors.NotFound:
        response.status_code = status.HTTP_404_NOT_FOUND
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR