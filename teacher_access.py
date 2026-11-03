
import base64
import binascii
import hmac
import os

from fastapi import HTTPException, Request


def setting(request, name, default=""):
    env = request.scope.get("env")
    value = None

    if isinstance(env, dict):
        value = env.get(name)
    elif env is not None:
        try:
            value = getattr(env, name, None)
        except Exception:
            pass

    if value is None:
        value = os.environ.get(name, default)

    return str(value if value is not None else default)


def enabled(value):
    return str(value).lower() in ("1", "true", "yes", "on")


def require_teacher(request: Request):
    demo = enabled(setting(request, "DEMO_MODE", "false"))

    inbox_enabled = (
        enabled(setting(request, "ENABLE_DEMO_API", "0"))
        or enabled(setting(request, "ENABLE_D1_INBOX", "0"))
    )

    # Only the synthetic preview without an active inbox is public.
    if demo and not inbox_enabled:
        return

    # Read Worker secrets from request scope.
    # Local development can still use environment variables.
    username = setting(request, "TEACHER_USERNAME")
    password = setting(request, "TEACHER_PASSWORD")

    if not username or not password:
        raise HTTPException(
            503,
            "Teacher login not configured"
        )

    header = request.headers.get("authorization", "")
    valid = False

    if header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(
                header[6:].strip(),
                validate=True
            ).decode("utf-8")

            name, separator, supplied_password = decoded.partition(":")

            valid = bool(separator) and (
                hmac.compare_digest(
                    name.encode(),
                    username.encode()
                )
                and hmac.compare_digest(
                    supplied_password.encode(),
                    password.encode()
                )
            )

        except (ValueError, UnicodeDecodeError, binascii.Error):
            pass

    if not valid:
        raise HTTPException(
            401,
            "Teacher login required",
            headers={
                "WWW-Authenticate": 'Basic realm="Australigo"'
            }
        )
