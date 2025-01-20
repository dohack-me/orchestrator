import uuid
from app import dependencies, util
from app.main import client
from app.environment import base_url, network_name
from fastapi import APIRouter
from fastapi import Response, Depends, status
from pydantic import BaseModel
import docker.errors

router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(dependencies.get_key)]
)

class CreateServiceModel(BaseModel):
    image: str
    tag: str = "latest"


@router.post("/service")
async def create(
        body: CreateServiceModel,
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
                f"traefik.http.routers.http-{container_id}.rule": f"Host(`{url}` && PathPrefix(`/`))",
                f"traefik.http.routers.https-{container_id}.entrypoints": "https",
                f"traefik.http.routers.https-{container_id}.rule": f"Host(`{url}`)",
                f"traefik.http.routers.https-{container_id}.tls.certresolver": "letsencrypt"
            }
        )
        return {
            "id": container_id,
            "url": "https://" + url
        }
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR