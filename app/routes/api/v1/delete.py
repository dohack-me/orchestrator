from fastapi import APIRouter, Response, Depends, status
from pydantic import BaseModel
import docker.errors
from app import dependencies
from app.main import client

router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(dependencies.get_key)]
)

class DeleteServiceModel(BaseModel):
    id: str

@router.delete("/service")
async def delete(
        body: DeleteServiceModel,
        response: Response
):
    try:
        container = client.containers.get(body.id)
        container.stop()
    except docker.errors.NotFound:
        response.status_code = status.HTTP_404_NOT_FOUND
    except docker.errors.APIError:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR