from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time


class TotpVerificationError(ValueError):
    pass


def _counter_code(secret_b32: str, counter: int, digits: int) -> str:
    try:
        key = base64.b32decode(secret_b32.upper(), casefold=True)
    except Exception as exc:
        raise TotpVerificationError("INVALID_TOTP_SECRET_ENCODING") from exc
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10 ** digits)).zfill(digits)


def verify_totp(secret_b32: str, code: str, *, unix_time: int | None = None, step_seconds: int = 30, digits: int = 6, window: int = 1) -> bool:
    """Verify a standards-compatible TOTP code.

    Caller must obtain the shared secret from the designated credential subsystem.
    This module does not persist, log, or export enrollment material.
    """
    if not isinstance(code, str) or not code.isdigit() or len(code) != digits:
        return False
    now = int(time.time() if unix_time is None else unix_time)
    counter = now // step_seconds
    for delta in range(-window, window + 1):
        candidate = _counter_code(secret_b32, counter + delta, digits)
        if hmac.compare_digest(candidate, code):
            return True
    return False
