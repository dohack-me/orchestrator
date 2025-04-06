import logging

import docker

from src import util
from src.backend.database import ServiceInstanceTable
from src.environment import authenticate, registry, registry_username, registry_password


class OrchestratorBackendSingleton:
    def __init__(self):
        # lazy importing to prevent circular import, thanks python
        from src.backend.deployer import OrchestratorDeployerSingleton
        from src.backend.scheduler import OrchestratorSchedulerSingleton

        logging.basicConfig(level=logging.INFO)

        self.client = docker.from_env()

        if authenticate:
            logging.info("Authenticating to Docker registry")
            self.client.login(username=registry_username, password=registry_password, registry=registry)

        logging.info("Initializing database tables")
        self.instances_table = ServiceInstanceTable()
        self.instances_table.initialize_table()
        logging.info("Syncing database with existing docker containers")
        self.sync_database()

        logging.info("Registering deployer singleton")
        self.deployer = OrchestratorDeployerSingleton(self)
        logging.info("Starting scheduler thread")
        self.scheduler = OrchestratorSchedulerSingleton(self)

        logging.info("Syncing events with database")
        self.sync_events()

    def sync_database(self) -> None:
        docker_instance_ids = set(
            [container.name for container in self.client.containers.list() if util.is_uuid(container.name)])
        database_instance_ids = set([instance.instance_id for instance in self.instances_table.read_instances()])

        docker_extras = docker_instance_ids - database_instance_ids
        database_extras = database_instance_ids - docker_instance_ids

        for instance_id in docker_extras:
            logging.info(f"Removing orphan docker container instance {instance_id}")
            self.client.containers.get(instance_id).stop()
        for instance_id in database_extras:
            logging.info(f"Removing orphan database row instance {instance_id}")
            self.instances_table.delete_instance(instance_id)

    def sync_events(self) -> None:
        for instance in self.instances_table.read_instances():
            self.scheduler.start_instance_event(instance.instance_id, instance.expiry)
