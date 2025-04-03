"""
This class is responsible for listening for Postgres events, and then calling appropriate methods to handle the call.
"""
import threading

from app import util
from app.instances import deployment, scheduler, database
from app.main import pool


def init_listener():
    threading.Thread(target=listener_thread, daemon=True).start()


def listener_thread():
    with pool.connection() as conn:
        conn.set_autocommit(True)
        with conn.cursor() as cur:
            cur.execute("LISTEN create_instance")
            events = conn.notifies()
            for event in events:
                service_id = event.payload
                if len(service_id) <= 0:
                    continue
                on_create_instance(service_id)


def on_create_instance(instance_id: str):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            service_id = cur.execute('SELECT "serviceId" from service_instance WHERE "id" = %s',
                                     (instance_id,)).fetchone()
            service_id = service_id[0] if service_id else None
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
            database.update_instance(instance_id, endpoint, expiry)
            scheduler.start_service_schedule(instance_id, expiry)
