import uuid
import datetime

import docker.errors

from app import database
from app.main import client
from app.environment import container_lifetime

def image_exists(image: str):
    try:
        client.images.get(image)
    except docker.errors.ImageNotFound:
        return False
    return True

def container_exists(name: str):
    try:
        client.containers.get(name)
    except docker.errors.NotFound:
        return False
    return True

def network_exists(name: str):
    try:
        client.networks.get(name)
    except docker.errors.NotFound:
        return False
    return True

def is_uuid(target: str):
    try:
        uuid_object = uuid.UUID(target)
    except ValueError:
        return False
    return str(uuid_object) == target

def get_expiry_time():
    return datetime.datetime.now() + datetime.timedelta(seconds=int(container_lifetime))