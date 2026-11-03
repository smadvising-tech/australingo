import os

from workers import asgi, env

# Read Cloudflare Worker binding.
# Default to demo mode for safety.
demo_setting = getattr(env, "DEMO_MODE", "true")

os.environ["DEMO_MODE"] = (
    "true"
    if str(demo_setting).lower() in ("true", "1", "yes", "on")
    else "false"
)

# Import FastAPI only after configuring demo mode.
from main import app

Default = asgi.entrypoint(app)
