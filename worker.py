
import os

from workers import asgi, env


def binding_value(name, default):
    try:
        if isinstance(env, dict):
            value = env.get(name, default)
        else:
            value = getattr(env, name, default)
    except Exception:
        value = default

    return str(value if value is not None else default)


def truthy(value):
    return str(value).lower() in ("1", "true", "yes", "on")


os.environ["DEMO_MODE"] = (
    "true"
    if truthy(binding_value("DEMO_MODE", "true"))
    else "false"
)

for flag in ("ENABLE_DEMO_API", "ENABLE_D1_INBOX"):
    os.environ[flag] = (
        "1" if truthy(binding_value(flag, "0")) else "0"
    )

# Import only after configuring the environment.
from main import app

Default = asgi.entrypoint(app)
