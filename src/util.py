import datetime
import uuid

from src.environment import instance_lifetime


def is_uuid(target: str):
    try:
        uuid_object = uuid.UUID(target)
    except ValueError:
        return False
    return str(uuid_object) == target


def get_expiry_time():
    return datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=int(instance_lifetime))
