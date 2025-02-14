import uuid
import warnings

import docker.errors
from fastapi import APIRouter
from fastapi import Response, Depends, status
from pydantic import BaseModel

from app import dependencies, util
from app.main import client
from app.environment import network_name, base_url

router = APIRouter(
    prefix="/api/v1/service/socket",
    dependencies=[Depends(dependencies.get_key)]
)

class CreateSocketModel(BaseModel):
    image: str
    tag: str = "latest"


@router.post("/")
async def create(
        body: CreateSocketModel,
        response: Response,
):
    try:
        if not util.image_exists(f"{body.image}:{body.tag}"):
            client.images.pull(body.image, body.tag)

        container_id = str(uuid.uuid4())
        url = base_url.replace("*", container_id[:8])

        container = client.containers.run(
            image=f"{body.image}:{body.tag}",
            name=container_id,
            auto_remove=True,
            detach=True,
            privileged=True,
            network=network_name,
            labels={
                "traefik.enable": "true",
                f"traefik.tcp.routers.tcp-{container_id}.entrypoints": "tcp",
                f"traefik.tcp.routers.tcp-{container_id}.rule": f"HostSNI(`{url}`)",
                f"traefik.tcp.routers.tcp-{container_id}.tls": "true",
                f"traefik.tcp.routers.tcp-{container_id}.tls.certresolver": "letsencrypt",
                f"traefik.tcp.routers.tcp-{container_id}.tls.domains[0].main": base_url
            }
        )
        container.reload()
        return {
            "id": container_id,
            "url": url
        }
    except docker.errors.APIError as exception:
        warnings.warn(str(exception))
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