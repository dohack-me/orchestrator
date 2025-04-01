import datetime
import sched
import time
import threading

from app import database
from app.main import client

events: dict[str, sched.Event] = {}
scheduler = sched.scheduler(time.time, time.sleep)

def _shutdown_service(service_id: str):
    container = client.containers.get(service_id)
    container.stop()
    database.delete_service(service_id)
    events.pop(service_id)

def init_schedulers():
    for service_id in database.get_services():
        start_service_schedule(service_id)

    def run_scheduler():
        while True:
            scheduler.run(blocking=True)

    threading.Thread(target=run_scheduler, daemon=True).start()

def start_service_schedule(service_id: str):
    expiry_time = datetime.datetime.fromisoformat(database.get_expiry_time(service_id))
    event = scheduler.enterabs(expiry_time.timestamp(), 1, _shutdown_service, (service_id,))
    events.update({service_id: event})

def update_service_schedule(service_id: str):
    scheduler.cancel(events.get(service_id))
    start_service_schedule(service_id)

def cancel_service_schedule(service_id: str):
    scheduler.cancel(events.pop(service_id))
