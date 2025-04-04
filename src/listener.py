"""
This class is responsible for listening for Postgres events, and then calling appropriate methods to handle the call.
"""
import asyncio
import logging
import threading

from psycopg import Connection

from src import deployment, scheduler
from src import util
from src.environment import database_url
from src.main import conn


def initialize_listener():
    thread = threading.Thread(target=_listener_thread)
    thread.start()

def _listener_thread():
    with Connection.connect(database_url, autocommit=True) as listener_conn:
        with listener_conn.cursor() as cur:
            cur.execute("LISTEN create_instance")
            events = listener_conn.notifies()
            for event in events:
                logging.info(f"Received new event")
                instance_id = event.payload
                if len(instance_id) <= 0:
                    continue
                asyncio.create_task(on_create_instance(instance_id))


async def on_create_instance(instance_id: str):
    logging.info(f"Received request to launch instance for id {instance_id}")
    with conn.cursor() as cur:
        service_id = service_id[0] if (
            service_id := cur.execute('SELECT "serviceId" from service_instance WHERE "id" = %s',
                                      (instance_id,)).fetchone()) else None
        if service_id is None:
            return
        image, tag, service_type = cur.execute('SELECT "image", "tag", "type" FROM service WHERE "id" = %s',
                                               (service_id,)).fetchone()
        match service_type:
            case "WEBSITE":
                endpoint = deployment.deploy_website(image, tag, instance_id)
            case "SOCKET":
                endpoint = deployment.deploy_socket(image, tag, instance_id)
            case _:
                return
        expiry = util.get_expiry_time()
        cur.execute('UPDATE service_instance SET "endpoint" = %s, "expiry" = %s WHERE "id" = %s',
                    (endpoint, expiry,
                     instance_id,))  # TODO: Migrate to acur as scheduler doesnt need updated row for some time
        conn.commit()
        scheduler.start_instance_event(instance_id, expiry)