from app import util
from app.main import client
from app.environment import email, network_name

def create_proxy():
    print("Could not find proxy container. Creating it now...")
    if not util.image_exists("traefik:latest"):
        client.images.pull("traefik", "latest")
    client.containers.run(
        image="traefik",
        name="proxy",
        restart_policy={"Name": "always"},
        detach=True,
        network="proxy",
        command=[
            "--providers.docker=true",
            "--entrypoints.http.address=:80",
            "--entrypoints.https.address=:443",
            "--certificatesresolvers.letsencrypt.acme.httpchallenge=true",
            "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=http",
            "--certificatesresolvers.letsencrypt.acme.storage=/traefik/acme.json",
            f"--certificatesresolvers.letsencrypt.acme.email={email}",
            f"--certificatesresolvers.letsencrypt.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory"
        ],
        ports={'80/tcp': 80},
        volumes=[
            "/var/run/docker.sock:/var/run/docker.sock",
            "traefik-data:/traefik"
        ],
    )
    print("Created proxy container.")

def create_network():
    print("Could not find proxy network. Creating it now...")
    client.networks.create(
        name=network_name,
        driver="bridge",
    )
    print("Created proxy network.")