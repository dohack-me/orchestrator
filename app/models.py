from pydantic import BaseModel


class ImageModel(BaseModel):
    repository: str
    tag: str = "latest"