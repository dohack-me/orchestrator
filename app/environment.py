import os

def assert_env(name):
    env = os.getenv(name)
    if env is None:
        raise RuntimeError(f"Environment variable {name} is not set")
    return env

base_url = assert_env("BASE_URL")
secret_key = assert_env("SECRET_KEY")
network_name = assert_env('NETWORK_NAME')
skip_proxy = assert_env("SKIP_PROXY")

if base_url.count("*") > 1:
    raise RuntimeError('Base URL has more than 1 asterisk')
