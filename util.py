import docker.errors
from docker import DockerClient

def image_exists(client: DockerClient, image: str) -> bool:
    try:
        client.images.get(image)
    except docker.errors.ImageNotFound:
        return False
    return True

def container_exists(client: DockerClient, name: str) -> bool:
    try:
        client.containers.get(name)
    except docker.errors.NotFound:
        return False
    return True