import asyncio
import datetime
import logging
from asyncio import WindowsSelectorEventLoopPolicy

import docker
from psycopg import Connection, AsyncConnection

from src.environment import authenticate, registry, registry_username, registry_password, database_url

logging.basicConfig(level=logging.INFO)
asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

client = docker.from_env()
conn = Connection.connect(database_url)
apool = asyncio.run(AsyncConnection.connect(database_url))

from src import util, scheduler, listener

def sync_database():
    with conn.cursor() as cur:
        docker_instance_ids = set(
            [container.name for container in client.containers.list() if util.is_uuid(container.name)])
        database_instance_ids = set(
            [x[0] for x in cur.execute('SELECT "id" FROM service_instance').fetchall()])

        docker_extras = docker_instance_ids - database_instance_ids
        database_extras = database_instance_ids - docker_instance_ids

        for instance_id in docker_extras:
            async def stop_container(container_name: str):
                client.containers.get(container_name).stop()

            asyncio.create_task(stop_container(instance_id))
        for instance_id in database_extras:
            cur.execute('DELETE FROM service_instance WHERE "id" = %(instance_id)s', {"instance_id": instance_id})


def sync_events():
    with conn.cursor() as cur:
        for instance_id in [instance_id[0] for instance_id in
                            cur.execute('SELECT "id" FROM service_instance').fetchall()]:
            async def initialize_event():
                expiry = datetime.datetime.fromisoformat(expiry[0]) if (
                    expiry := cur.execute('SELECT "expiry" FROM service_instance WHERE "id" = %s',
                                          (instance_id,)).fetchone()) else None
                scheduler.start_instance_event(instance_id, expiry)

            asyncio.create_task(initialize_event())



def initialize():
    if authenticate:
        logging.info("Authenticating to Docker registry")
        client.login(username=registry_username, password=registry_password, registry=registry)

    logging.info("Syncing with database")
    sync_database()
    logging.info("Syncing events with database")
    sync_events()

    logging.info("Starting listener thread")
    listener.initialize_listener()
    logging.info("Starting scheduler thread")
    scheduler.initialize_scheduler()


if __name__ == '__main__':
    initialize()
