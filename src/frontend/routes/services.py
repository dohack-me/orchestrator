import logging
import uuid

import docker.errors
from fastapi import APIRouter
from fastapi import Response, Depends, status

from src import util
from src.environment import authenticate
from src.frontend import dependencies
from src.frontend.models import ImageWithTypeModel, ServiceTypes
from src.main import backend

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
            backend.client.images.pull(body.image, body.tag)

        instance_id = str(uuid.uuid4())
        match body.type:
            case ServiceTypes.SOCKET:
                endpoint = backend.deployer.deploy_socket(body.image, body.tag, instance_id)
            case ServiceTypes.WEBSITE:
                endpoint = backend.deployer.deploy_website(body.image, body.tag, instance_id)
            case _:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return {
                    "message": f"Unknown service type: {body.type}",
                }

        expiry_time = util.get_expiry_time()
        backend.instances_table.create_instance(instance_id, expiry_time)
        backend.scheduler.start_instance_event(instance_id, expiry_time)
        return {
            "id": instance_id,
            "endpoint": endpoint,
            "expiry": expiry_time,
        }
    except docker.errors.APIError as exception:
        logging.error(exception)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


@router.get("/{instance_id}/")
async def get_service_expiry(
        instance_id: str,
        response: Response
):
    instance = backend.instances_table.read_instance(instance_id)
    if instance is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {
            "message": f"Could not find service with ID {instance_id}",
        }
    return {
        "id": instance_id,
        "expiry": instance.expiry,
    }


@router.put("/{instance_id}/")
async def extend_service(
        instance_id: str,
        response: Response
):
    instance = backend.instances_table.read_instance(instance_id)
    if instance is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {
            "message": f"Could not find service with ID {instance_id}",
        }
    expiry = util.get_expiry_time()
    backend.instances_table.update_instance(instance_id, expiry)
    backend.scheduler.update_service_schedule(instance_id, expiry)
    return {
        "id": instance_id,
        "expiry": expiry,
    }


@router.delete("/{instance_id}/")
async def delete_service(
        instance_id: str,
        response: Response
):
    instance = backend.instances_table.read_instance(instance_id)
    if instance is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {
            "message": f"Could not find service with ID {instance_id}",
        }

    try:
        container = backend.client.containers.get(instance_id)
        container.stop()
        backend.instances_table.delete_instance(instance_id)
        backend.scheduler.cancel_service_schedule(instance_id)
    except docker.errors.NotFound:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {
            "message": f"Could not find service with ID {instance_id}",
        }
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
