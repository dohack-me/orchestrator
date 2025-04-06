"""
This file is responsible for deploying Docker containers on the host machine,
then returning appropriate endpoints for clients to connect to.
"""
from src.backend.main import OrchestratorBackendSingleton
from src.environment import base_url, network_name, public_host


class OrchestratorDeployerSingleton:
    def __init__(self, app: OrchestratorBackendSingleton):
        self.app = app

    def deploy_website(self, image: str, tag: str, instance_id: str) -> str:
        url = base_url.replace("*", instance_id[:8])
        self.app.client.containers.run(
            image=f"{image}:{tag}",
            name=instance_id,
            auto_remove=True,
            detach=True,
            network=network_name,
            labels={
                "traefik.enable": "true",
                f"traefik.http.routers.http-{instance_id}.entrypoints": "http",
                f"traefik.http.routers.http-{instance_id}.rule": f"Host(`{url}`)",
                f"traefik.http.routers.https-{instance_id}.entrypoints": "https",
                f"traefik.http.routers.https-{instance_id}.rule": f"Host(`{url}`)",
                f"traefik.http.routers.https-{instance_id}.tls": "true",
                f"traefik.http.routers.https-{instance_id}.tls.certresolver": "letsencrypt",
                f"traefik.http.routers.https-{instance_id}.tls.domains[0].main": base_url,
            }
        )
        return f"https://{url}"

    def deploy_socket(self, image: str, tag: str, instance_id: str) -> str:
        container = self.app.client.containers.run(
            image=f"{image}:{tag}",
            name=instance_id,
            auto_remove=True,
            detach=True,
            publish_all_ports=True,
            privileged=True,
            network=network_name,
        )
        container.reload()
        port = int(list(container.ports.values())[0][0]["HostPort"])
        return f"nc {public_host} {port}"
