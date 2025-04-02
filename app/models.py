from pydantic import BaseModel
from enum import Enum

class ServiceTypes(Enum):
    WEBSITE = "WEBSITE"
    SOCKET = "SOCKET"

class ImageModel(BaseModel):
    image: str
    tag: str = "latest"

class ImageWithTypeModel(BaseModel):
    image: str
    tag: str = "latest"
    type: ServiceTypes