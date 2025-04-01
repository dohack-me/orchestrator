import sqlite3
import warnings

from app import util
from app.main import client
from app.environment import database_path

conn = sqlite3.connect(database_path)

def init_database():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS containers (service_id TEXT PRIMARY KEY NOT NULL, expiry DATETIME NOT NULL)")

    docker_service_ids = set([container.name for container in client.containers.list() if util.is_uuid(container.name)])
    database_service_ids = set([x[0] for x in cur.execute("SELECT service_id FROM containers").fetchall()])

    docker_extras = docker_service_ids - database_service_ids
    database_extras = database_service_ids - docker_service_ids

    for service_id in docker_extras:
        cur.execute("INSERT INTO containers (service_id, expiry) VALUES (?, ?)",
                    (service_id, util.get_expiry_time()))
    for service_id in database_extras:
        cur.execute("DELETE FROM containers WHERE service_id = ?", (service_id,))
    conn.commit()
    cur.close()


def create_row(container_name: str):
    cur = conn.cursor()
    cur.execute("INSERT INTO containers (service_id, expiry) VALUES (?, ?)", (container_name, util.get_expiry_time()))
    conn.commit()
    cur.close()

def delete_row(container_name: str):
    cur = conn.cursor()
    cur.execute("DELETE FROM containers WHERE service_id = ?", (container_name,))
    conn.commit()
    cur.close()
