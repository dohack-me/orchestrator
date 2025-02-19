import uuid
import warnings

import docker.errors
from fastapi import APIRouter
from fastapi import Response, Depends, status
from pydantic import BaseModel

from app import dependencies, util
from app.main import client
from app.environment import base_url, network_name
from app.models import ImageModel

router = APIRouter(
    prefix="/api/v1/image",
    dependencies=[Depends(dependencies.get_key)]
)

@router.put("/")
async def pull_image(
        body: ImageModel,
):
    client.images.pull(
        repository=body.repository,
        tag=body.tag,
    )

@router.delete("/")
async def delete_image(
        body: ImageModel,
        response: Response,
):
    try:
        client.images.remove(
            image=f"{body.repository}:{body.tag}",
        )
    except docker.errors.APIError: # why is there no errors documented for this method lol, im assuming it throws this error
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
