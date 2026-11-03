import base64
import binascii
import hmac
import os

from fastapi import HTTPException, Request


def require_teacher(request: Request):
    demo = os.environ.get("DEMO_MODE", "false").lower() == "true"
    api_enabled = os.environ.get("ENABLE_DEMO_API") == "1"

    # Public synthetic preview only. Real inbox requires login.
    if demo and not api_enabled:
        return

    username = os.environ.get("TEACHER_USERNAME", "")
    password = os.environ.get("TEACHER_PASSWORD", "")

    if not username or not password:
        raise HTTPException(503, "Teacher login not configured")

    valid = False
    header = request.headers.get("authorization", "")

    if header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(
                header[6:].strip(), validate=True
            ).decode("utf-8")
            name, separator, supplied_password = decoded.partition(":")
            valid = bool(separator) and (
                hmac.compare_digest(name.encode(), username.encode())
                and hmac.compare_digest(
                    supplied_password.encode(), password.encode()
                )
            )
        except (ValueError, UnicodeDecodeError, binascii.Error):
            pass

    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Teacher login required",
            headers={"WWW-Authenticate": 'Basic realm="Australigo"'}
        )
