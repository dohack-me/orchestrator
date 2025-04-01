import sqlite3

from app import util
from app.main import client
from app.environment import database_path

class DatabaseConnection:
    def __init__(self):
        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()



def init_database():
    with DatabaseConnection() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS containers (service_id TEXT PRIMARY KEY NOT NULL, expiry DATETIME NOT NULL)")

        docker_service_ids = set(
            [container.name for container in client.containers.list() if util.is_uuid(container.name)])
        database_service_ids = set([x[0] for x in cur.execute("SELECT service_id FROM containers").fetchall()])

        docker_extras = docker_service_ids - database_service_ids
        database_extras = database_service_ids - docker_service_ids

        for service_id in docker_extras:
            cur.execute("INSERT INTO containers (service_id, expiry) VALUES (?, ?)",
                              (service_id, util.get_expiry_time()))
        for service_id in database_extras:
            cur.execute("DELETE FROM containers WHERE service_id = ?", (service_id,))

def create_service(service_id: str):
    with DatabaseConnection() as cur:
        expiry_time = util.get_expiry_time()
        cur.execute("INSERT INTO containers (service_id, expiry) VALUES (?, ?)", (service_id, expiry_time))

def extend_service(service_id: str):
    with DatabaseConnection() as cur:
        expiry_time = util.get_expiry_time()
        cur.execute("UPDATE containers SET expiry = ? WHERE service_id = ?", (expiry_time, service_id))

    return expiry_time

def delete_service(service_id: str):
    with DatabaseConnection() as cur:
        cur.execute("DELETE FROM containers WHERE service_id = ?", (service_id,))

def get_expiry_time(service_id: str):
    with DatabaseConnection() as cur:
        expiry_time = cur.execute("SELECT expiry FROM containers WHERE service_id = ?", (service_id,)).fetchone()
    return expiry_time[0] if expiry_time else None

def get_services():
    with DatabaseConnection() as cur:
        return [service_id[0] for service_id in cur.execute("SELECT service_id FROM containers").fetchall()]

def is_service(service_id: str):
    with DatabaseConnection() as cur:
        return cur.execute("SELECT service_id FROM containers WHERE service_id = ?", (service_id, )).fetchone() is not None