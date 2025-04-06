import datetime
import sqlite3
from contextlib import contextmanager
from typing import List, Optional


class ServiceInstance:
    def __init__(self, instance_id: str, expiry: datetime.datetime):
        self.instance_id = instance_id
        self.expiry = expiry


class ServiceInstanceTable:
    def __init__(self, override_database_path: Optional[str] = None):
        if override_database_path is None:
            from src.environment import database_path
            self.database_path = database_path
        else:
            self.database_path = override_database_path

    @contextmanager
    def get_cursor(self):
        conn = sqlite3.connect(self.database_path)
        cur = conn.cursor()
        yield cur
        conn.commit()
        cur.close()
        conn.close()

    def initialize_table(self) -> None:
        with self.get_cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS service_instances (id TEXT PRIMARY KEY NOT NULL, expiry INT NOT NULL)")

    def create_instance(self, instance_id: str, expiry: datetime.datetime) -> ServiceInstance:
        with self.get_cursor() as cur:
            cur.execute("INSERT INTO service_instances (id, expiry) VALUES (?, ?)", (instance_id, expiry.timestamp()))
        return ServiceInstance(instance_id, expiry)

    def read_instance(self, instance_id: str) -> Optional[ServiceInstance]:
        with self.get_cursor() as cur:
            result = cur.execute("SELECT expiry FROM service_instances WHERE id = ?", (instance_id,)).fetchone()
        if result is None:
            return None
        return ServiceInstance(instance_id, datetime.datetime.fromtimestamp(result[0], datetime.timezone.utc))

    def read_instances(self) -> List[ServiceInstance]:
        with self.get_cursor() as cur:
            results = cur.execute("SELECT id, expiry FROM service_instances").fetchall()
        return [ServiceInstance(row[0], datetime.datetime.fromtimestamp(row[1], datetime.timezone.utc)) for row in
                results]

    def update_instance(self, instance_id: str, expiry: datetime.datetime) -> None:
        with self.get_cursor() as cur:
            cur.execute("UPDATE service_instances SET expiry = ? WHERE id = ?", (expiry.timestamp(), instance_id))

    def delete_instance(self, instance_id: str) -> bool:
        with self.get_cursor() as cur:
            results = cur.execute("DELETE FROM service_instances WHERE id = ?", (instance_id,)).fetchone()
        return results is None
