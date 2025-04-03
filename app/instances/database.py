import datetime

from app import util
from app.main import client, pool


def sync_database():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            docker_instance_ids = set(
                [container.name for container in client.containers.list() if util.is_uuid(container.name)])
            database_instance_ids = set([x[0] for x in cur.execute('SELECT "id" FROM service_instance').fetchall()])

            docker_extras = docker_instance_ids - database_instance_ids
            database_extras = database_instance_ids - docker_instance_ids

            for instance_id in docker_extras:
                container = client.containers.get(instance_id)
                container.stop()
            for instance_id in database_extras:
                cur.execute('DELETE FROM service_instance WHERE "id" = %s', (instance_id,))
                pass


def update_instance(instance_id: str, endpoint: str, expiry: datetime.datetime):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE service_instance SET "endpoint" = %s, "expiry" = %s WHERE "id" = %s',
                        (endpoint, expiry, instance_id,))
            conn.commit()


def get_instance_ids():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            return [instance_id[0] for instance_id in cur.execute('SELECT "id" FROM service_instance').fetchall()]


def get_instance_expiry(instance_id: str):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            expiry = cur.execute('SELECT "expiry" FROM service_instance WHERE "id" = %s', (instance_id,)).fetchone()
            return datetime.datetime.fromisoformat(expiry[0]) if expiry else None


def delete_instance(instance_id: str):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM service_instance WHERE "id" = %s', (instance_id,))
            conn.commit()
