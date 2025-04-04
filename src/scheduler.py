"""
This class is responsible for scheduling the deletion of instances and their containers.
"""
import datetime
import sched
import threading
import time

from src.main import conn, client

scheduler = sched.scheduler(time.time, time.sleep)
events: dict[str, sched.Event] = {}


def initialize_scheduler():
    thread = threading.Thread(target=_scheduler_thread)
    thread.start()

def _scheduler_thread():
    while True:
        scheduler.run(blocking=True)

def start_instance_event(instance_id: str, expiry_time: datetime.datetime):
    event = scheduler.enterabs(expiry_time.timestamp(), 1, shutdown_instance, (instance_id,))
    events.update({instance_id: event})

def cancel_service_schedule(instance_id: str):
    scheduler.cancel(events.pop(instance_id))

def update_service_schedule(instance_id: str, expiry_time: datetime.datetime):
    scheduler.cancel(events.get(instance_id))
    start_instance_event(instance_id, expiry_time)

def shutdown_instance(instance_id: str):
    with conn.cursor() as cur:
        cur.execute('DELETE FROM service_instance WHERE "id" = %s', (instance_id,))
        conn.commit()

    container = client.containers.get(instance_id)
    container.stop()
    events.pop(instance_id)