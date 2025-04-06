"""
This class is responsible for scheduling the deletion of instances and their containers.
"""
import datetime
import logging
import sched
import threading
import time

from src.backend.main import OrchestratorBackendSingleton


class OrchestratorSchedulerSingleton:
    def __init__(self, app: OrchestratorBackendSingleton):
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.events: dict[str, sched.Event] = {}
        self.app = app

        self.thread = threading.Thread(target=self._scheduler_thread)
        self.thread.start()

    def _scheduler_thread(self):
        while True:
            self.scheduler.run(blocking=True)

    def start_instance_event(self, instance_id: str, expiry_time: datetime.datetime) -> None:
        event = self.scheduler.enterabs(expiry_time.timestamp(), 1, self.shutdown_instance, (instance_id,))
        self.events.update({instance_id: event})

    def cancel_service_schedule(self, instance_id: str) -> None:
        self.scheduler.cancel(self.events.pop(instance_id))

    def update_service_schedule(self, instance_id: str, expiry_time: datetime.datetime) -> None:
        self.scheduler.cancel(self.events.get(instance_id))
        self.start_instance_event(instance_id, expiry_time)

    def shutdown_instance(self, instance_id: str) -> None:
        logging.info(f"Removing expired instance {instance_id}")

        self.app.instances_table.delete_instance(instance_id)

        container = self.app.client.containers.get(instance_id)
        container.stop()

        self.events.pop(instance_id)
