import docker.errors
from fastapi import APIRouter
from fastapi import Response, Depends, status

from src.frontend import dependencies
from src.frontend.models import ImageModel
from src.main import backend

router = APIRouter(
    prefix="/api/v1/image",
    dependencies=[Depends(dependencies.get_key)]
)


@router.get("/")
async def get_images():
    return [(image.id, image.tags) for image in backend.client.images.list()]


@router.put("/")
async def pull_image(
        body: ImageModel,
):
    backend.client.images.pull(
        repository=body.image,
        tag=body.tag,
    )


@router.delete("/")
async def delete_image(
        body: ImageModel,
        response: Response,
):
    try:
        backend.client.images.remove(
            image=f"{body.image}:{body.tag}",
        )
    except docker.errors.APIError:  # why is there no errors documented for this method lol, im assuming it throws this error
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
