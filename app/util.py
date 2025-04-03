import datetime
import uuid
from zoneinfo import ZoneInfo

from app.environment import container_lifetime


def is_uuid(target: str):
    try:
        uuid_object = uuid.UUID(target)
    except ValueError:
        return False
    return str(uuid_object) == target

def get_expiry_time():
    return datetime.datetime.now(tz=ZoneInfo("Etc/UTC")) + datetime.timedelta(seconds=int(container_lifetime))