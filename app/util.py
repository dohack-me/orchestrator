import docker.errors
from app.main import client

def image_exists(image: str) -> bool:
    try:
        client.images.get(image)
    except docker.errors.ImageNotFound:
        return False
    return True

def container_exists(name: str) -> bool:
    try:
        client.containers.get(name)
    except docker.errors.NotFound:
        return False
    return True

def network_exists(name: str) -> bool:
    try:
        client.networks.get(name)
    except docker.errors.NotFound:
        return False
    return True