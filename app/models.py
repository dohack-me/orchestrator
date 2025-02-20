from pydantic import BaseModel


class ImageModel(BaseModel):
    image: str
    tag: str = "latest"