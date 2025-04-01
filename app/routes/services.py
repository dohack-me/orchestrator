import uuid
import warnings

import docker.errors
from fastapi import APIRouter
from fastapi import Response, Depends, status

from app import dependencies, database
from app.main import client
from app.environment import network_name, base_url, public_host, authenticate
from app.models import ImageWithTypeModel, ServiceTypes

router = APIRouter(
    prefix="/api/v1/service",
    dependencies=[Depends(dependencies.get_key)]
)

@router.post("/")
async def create_service(
        body: ImageWithTypeModel,
        response: Response,
):
    try:
        if authenticate:
            client.images.pull(body.image, body.tag)
        service_id = str(uuid.uuid4())
        match body.type:
            case ServiceTypes.SOCKET:
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
                endpoint = f"nc {public_host} {port}"
            case ServiceTypes.WEBSITE:
                url = base_url.replace("*", service_id[:8])
                client.containers.run(
                    image=body.image,
                    name=service_id,
                    auto_remove=True,
                    detach=True,
                    network=network_name,
                    labels={
                        "traefik.enable": "true",
                        f"traefik.http.routers.http-{service_id}.entrypoints": "http",
                        f"traefik.http.routers.http-{service_id}.rule": f"Host(`{url}`)",
                        f"traefik.http.routers.https-{service_id}.entrypoints": "https",
                        f"traefik.http.routers.https-{service_id}.rule": f"Host(`{url}`)",
                        f"traefik.http.routers.https-{service_id}.tls": "true",
                        f"traefik.http.routers.https-{service_id}.tls.certresolver": "letsencrypt",
                        f"traefik.http.routers.https-{service_id}.tls.domains[0].main": base_url,
                    }
                )
                endpoint = f"https://{url}"
            case _:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return {
                    "message": f"Unknown service type: {body.type}",
                }
        expiry_time = database.create_service(service_id)
        return {
            "id": service_id,
            "endpoint": endpoint,
            "expiry": expiry_time,
        }
    except docker.errors.APIError as exception:
        warnings.warn(str(exception))
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

@router.put("/{service_id}/")
async def extend_socket(
        service_id: str,
        response: Response
):
    if not database.is_service(service_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {
            "message": f"Could not find service with ID {service_id}",
        }
    expiry_time = database.extend_service(service_id)
    return {
        "id": service_id,
        "expiry": expiry_time,
    }


@router.delete("/{service_id}/")
async def delete_service(
        service_id: str,
        response: Response
):
    try:
        container = client.containers.get(service_id)
        container.stop()
        database.delete_service(service_id)
    except docker.errors.NotFound:
        response.status_code = status.HTTP_404_NOT_FOUND
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR