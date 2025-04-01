import uuid
import warnings

import docker.errors
from fastapi import APIRouter
from fastapi import Response, Depends, status

from app import dependencies, util, database
from app.main import client
from app.environment import network_name
from app.models import ImageModel

router = APIRouter(
    prefix="/api/v1/service/socket",
    dependencies=[Depends(dependencies.get_key)]
)

@router.post("/")
async def create(
        body: ImageModel,
        response: Response,
):
    try:
        if not util.image_exists(f"{body.image}:{body.tag}"):
            client.images.pull(body.image, body.tag)

        service_id = str(uuid.uuid4())
        container = client.containers.run(
            image=f"{body.image}:{body.tag}",
            name=service_id,
            auto_remove=True,
            detach=True,
            publish_all_ports=True,
            privileged=True,
            network=network_name,
        )
        container.reload()
        port = int(list(container.ports.values())[0][0]["HostPort"])
        database.create_row(service_id)
        return {
            "id": service_id,
            "port": port
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
        database.delete_row(service_id)
    except docker.errors.NotFound:
        response.status_code = status.HTTP_404_NOT_FOUND
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR