import os

def assert_env(name):
    if (env := os.getenv(name)) is None:
        raise RuntimeError(f"Environment variable {name} is not set")
    return env

base_url = assert_env("BASE_URL")
secret_key = assert_env("SECRET_KEY")
network_name = assert_env('NETWORK_NAME')

if base_url.count("*") > 1:
    raise RuntimeError('Base URL has more than 1 asterisk')
