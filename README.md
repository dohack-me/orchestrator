# orchestrator

A Python FastAPI server to automatically deploy containers.

Website containers are proxied via a Traefik instance. Socket containers are directly exposed.

## Environment Variables

- `BASE_URL` - The FQDN which website instances can be accessed from. 
  - Up to 1 `*` can be included, which will be replaced by the first segment of the instance's UUID.
- `SECRET_KEY` - Clients will need to have the header `Authorization: <SECRET_KEY>` to interact with the app.
- `NETWORK_NAME` - The docker network name website instance containers will be a part of.
- `AUTHENTICATE` - If set to `true`, the app will authenticate to a docker registry on startup.
  - `REGISTRY` - The FQDN of the registry to connect to.
  - `REGISTRY_USERNAME` - The username to use to connect to the registry.
  - `REGISTRY_PASSWORD` - The password to use to connect to the registry.
- `DATABASE_PATH` - The relative path to the app's SQLite database.
- `INSTANCE_LIFETIME` - The amount of seconds each instance will last for.
- `PUBLIC_HOST` - The hostname to use when returning the netcat command endpoint for socket instances.
