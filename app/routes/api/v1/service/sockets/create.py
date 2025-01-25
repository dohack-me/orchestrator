import uuid
from app import dependencies, util
from app.main import client
from app.environment import network_name
from fastapi import APIRouter
from fastapi import Response, Depends, status
from pydantic import BaseModel
import docker.errors

router = APIRouter(
    prefix="/api/v1/service",
    dependencies=[Depends(dependencies.get_key)]
)

class CreateSocketModel(BaseModel):
    image: str
    tag: str = "latest"


@router.post("/socket")
async def create(
        body: CreateSocketModel,
        response: Response,
):
    try:
        if not util.image_exists(f"{body.image}:{body.tag}"):
            client.images.pull(body.image, body.tag)

        container_id = str(uuid.uuid4())
        container = client.containers.run(
            image=f"{body.image}:{body.tag}",
            name=container_id,
            auto_remove=True,
            detach=True,
            publish_all_ports=True,
            privileged=True,
            network=network_name,
        )
        container.reload()
        ports = {}
        for container_port, host_info in container.ports.items():
            ports.update({container_port.split("/")[0]: host_info[0]["HostPort"]})
        return {
            "id": container_id,
            "ports": ports
        }
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR