import os


def assert_env(name: str):
    if (env := os.getenv(name)) is None:
        raise RuntimeError(f"Environment variable {name} is not set")
    return env


base_url = assert_env("BASE_URL")
secret_key = assert_env("SECRET_KEY")
network_name = assert_env('NETWORK_NAME')
database_path = assert_env('DATABASE_PATH')
instance_lifetime = assert_env('INSTANCE_LIFETIME')
public_host = assert_env('PUBLIC_HOST')

authenticate = assert_env('AUTHENTICATE') == "true"
registry = (assert_env('REGISTRY') if authenticate else None)
registry_username = (assert_env('REGISTRY_USERNAME') if authenticate else None)
registry_password = (assert_env('REGISTRY_PASSWORD') if authenticate else None)

if base_url.count("*") > 1:
    raise RuntimeError('Base URL has more than 1 asterisk')
