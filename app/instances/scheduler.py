"""
This class is responsible for scheduling the deletion of instances and their containers.
"""

import datetime
import sched
import threading
import time

from app.instances import database
from app.main import client

events: dict[str, sched.Event] = {}
scheduler = sched.scheduler(time.time, time.sleep)


def _shutdown_service(instance_id: str):
    container = client.containers.get(instance_id)
    container.stop()
    database.delete_instance(instance_id)
    events.pop(instance_id)


def init_schedulers():
    for instance_id in database.get_instance_ids():
        start_service_schedule(instance_id, database.get_instance_expiry(instance_id))

    def run_scheduler():
        while True:
            scheduler.run(blocking=True)

    threading.Thread(target=run_scheduler, daemon=True).start()


def start_service_schedule(instance_id: str, expiry_time: datetime.datetime):
    event = scheduler.enterabs(expiry_time.timestamp(), 1, _shutdown_service, (instance_id,))
    events.update({instance_id: event})


def update_service_schedule(instance_id: str, expiry_time: datetime.datetime):
    scheduler.cancel(events.get(instance_id))
    start_service_schedule(instance_id, expiry_time)


def cancel_service_schedule(instance_id: str):
    scheduler.cancel(events.pop(instance_id))
