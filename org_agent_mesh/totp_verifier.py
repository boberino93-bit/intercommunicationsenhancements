from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time


class TotpVerificationError(ValueError):
    pass


def _counter_code(secret_b32: str, counter: int, digits: int) -> str:
    if counter < 0:
        raise TotpVerificationError("INVALID_TOTP_COUNTER")
    try:
        key = base64.b32decode(secret_b32.upper(), casefold=True)
    except Exception as exc:
        raise TotpVerificationError("INVALID_TOTP_SECRET_ENCODING") from exc
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10 ** digits)).zfill(digits)


def match_totp_counter(
    secret_b32: str,
    code: str,
    *,
    unix_time: int | None = None,
    step_seconds: int = 30,
    digits: int = 6,
    window: int = 1,
) -> int | None:
    """Return the exact RFC-6238 counter matched by *code*, else ``None``.

    Returning the matched counter, rather than a Boolean only, is security-relevant:
    replay protection must consume the counter that actually produced the accepted code,
    including codes accepted from an adjacent drift window.
    """
    if step_seconds <= 0 or digits <= 0 or window < 0:
        raise TotpVerificationError("INVALID_TOTP_PARAMETERS")
    if not isinstance(code, str) or not code.isdigit() or len(code) != digits:
        return None
    now = int(time.time() if unix_time is None else unix_time)
    counter = now // step_seconds
    for delta in range(-window, window + 1):
        candidate_counter = counter + delta
        if candidate_counter < 0:
            continue
        candidate = _counter_code(secret_b32, candidate_counter, digits)
        if hmac.compare_digest(candidate, code):
            return candidate_counter
    return None


def verify_totp(
    secret_b32: str,
    code: str,
    *,
    unix_time: int | None = None,
    step_seconds: int = 30,
    digits: int = 6,
    window: int = 1,
) -> bool:
    """Verify a standards-compatible TOTP code.

    Caller must obtain the shared secret from the designated credential subsystem.
    This module does not persist, log, or export enrollment material.
    """
    return match_totp_counter(
        secret_b32,
        code,
        unix_time=unix_time,
        step_seconds=step_seconds,
        digits=digits,
        window=window,
    ) is not None
