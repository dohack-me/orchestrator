from enum import Enum

from pydantic import BaseModel


class ServiceTypes(Enum):
    WEBSITE = "WEBSITE"
    SOCKET = "SOCKET"


class ImageModel(BaseModel):
    image: str
    tag: str = "latest"
