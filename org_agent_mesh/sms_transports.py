from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Protocol
from urllib.parse import urlsplit


class SmsTransportError(RuntimeError):
    """Fail-closed transport error with retry classification."""

    def __init__(self, code: str, *, retryable: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class ResolvedSmsDestination:
    """Runtime-only routing result returned by a protected destination resolver."""

    e164: str
    sip_uri: str


@dataclass(frozen=True)
class SipMessageResult:
    status_code: int
    reason: str = ""
    transaction_id: str | None = None


class ProtectedDestinationResolver(Protocol):
    def resolve(self, destination_ref: str) -> ResolvedSmsDestination: ...


class SipMessageClient(Protocol):
    def send_message(
        self,
        *,
        request_uri: str,
        body: str,
        content_type: str,
        idempotency_key: str,
        timeout_seconds: float,
    ) -> SipMessageResult: ...


def _sip_host(uri: str) -> tuple[str, str]:
    # urlsplit does not understand bare SIP URIs reliably, so normalize only
    # for parsing. Userinfo is allowed; route parameters are stripped from host.
    if not isinstance(uri, str) or ":" not in uri:
        raise SmsTransportError("invalid_sip_uri")
    scheme, rest = uri.split(":", 1)
    scheme = scheme.lower()
    if scheme not in {"sip", "sips"}:
        raise SmsTransportError("invalid_sip_uri_scheme")
    authority = rest.split("?", 1)[0]
    if "@" in authority:
        authority = authority.rsplit("@", 1)[1]
    authority = authority.split(";", 1)[0]
    if authority.startswith("["):
        end = authority.find("]")
        if end == -1:
            raise SmsTransportError("invalid_sip_uri_host")
        host = authority[1:end]
    else:
        host = authority.split(":", 1)[0]
    host = host.strip().rstrip(".").lower()
    if not host:
        raise SmsTransportError("invalid_sip_uri_host")
    return scheme, host


def _valid_e164(value: str) -> bool:
    return bool(re.fullmatch(r"\+[1-9][0-9]{7,14}", value or ""))


class SipMessageSmsTransport:
    """RFC 3428 MESSAGE transport for providers that explicitly bridge SIP to SMS.

    This adapter intentionally does not contain SIP credentials or destination
    numbers. Authentication belongs in the concrete SipMessageClient and
    destination resolution belongs in ProtectedDestinationResolver.
    """

    def __init__(
        self,
        *,
        resolver: ProtectedDestinationResolver,
        client: SipMessageClient,
        allowed_gateway_hosts: Iterable[str],
        require_tls: bool = True,
        timeout_seconds: float = 5.0,
        max_body_bytes: int = 1024,
    ) -> None:
        hosts = frozenset(str(v).strip().rstrip(".").lower() for v in allowed_gateway_hosts if str(v).strip())
        if not hosts:
            raise SmsTransportError("sip_gateway_allowlist_required")
        if not (0.5 <= float(timeout_seconds) <= 30.0):
            raise SmsTransportError("unsafe_sip_timeout")
        if not (64 <= int(max_body_bytes) <= 4096):
            raise SmsTransportError("unsafe_sip_message_size_limit")
        self.resolver = resolver
        self.client = client
        self.allowed_gateway_hosts = hosts
        self.require_tls = bool(require_tls)
        self.timeout_seconds = float(timeout_seconds)
        self.max_body_bytes = int(max_body_bytes)

    def send(self, destination_ref: str, message: str, *, idempotency_key: str) -> str | None:
        if not isinstance(destination_ref, str) or not destination_ref.startswith(
            ("vault://", "secret://", "principal://")
        ):
            raise SmsTransportError("sms_destination_must_be_protected_reference")
        if not isinstance(message, str) or not message.strip():
            raise SmsTransportError("sms_message_required")
        if len(message.encode("utf-8")) > self.max_body_bytes:
            raise SmsTransportError("sms_message_too_large")
        if not isinstance(idempotency_key, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{8,160}", idempotency_key):
            raise SmsTransportError("invalid_idempotency_key")

        destination = self.resolver.resolve(destination_ref)
        if not isinstance(destination, ResolvedSmsDestination):
            raise SmsTransportError("destination_resolution_failed")
        if not _valid_e164(destination.e164):
            raise SmsTransportError("resolved_destination_not_e164")

        scheme, host = _sip_host(destination.sip_uri)
        if self.require_tls and scheme != "sips":
            raise SmsTransportError("sip_tls_required")
        if host not in self.allowed_gateway_hosts:
            raise SmsTransportError("sip_gateway_not_allowlisted")

        try:
            result = self.client.send_message(
                request_uri=destination.sip_uri,
                body=message,
                content_type="text/plain; charset=utf-8",
                idempotency_key=idempotency_key,
                timeout_seconds=self.timeout_seconds,
            )
        except TimeoutError as exc:
            raise SmsTransportError("sip_gateway_timeout", retryable=True) from exc
        except SmsTransportError:
            raise
        except Exception as exc:
            raise SmsTransportError("sip_gateway_transport_failure", retryable=True) from exc

        if not isinstance(result, SipMessageResult):
            raise SmsTransportError("invalid_sip_gateway_response")

        status = int(result.status_code)
        # RFC 3428: 200 means accepted at final destination; 202 means accepted
        # by a gateway/store-and-forward service and does not guarantee final delivery.
        if status == 200:
            return result.transaction_id or f"sip-200:{idempotency_key}"
        if status == 202:
            return result.transaction_id or f"sip-202:{idempotency_key}"
        if status in {408, 425, 429} or 500 <= status <= 599:
            raise SmsTransportError(f"sip_gateway_retryable_{status}", retryable=True)
        raise SmsTransportError(f"sip_gateway_rejected_{status}", retryable=False)


class FailoverSmsTransport:
    """Bounded failover between preconfigured transports.

    The same idempotency key is forwarded to every attempted transport so
    concrete providers can suppress duplicates. Failover is only performed
    for explicitly retryable failures.
    """

    def __init__(self, transports: Iterable[object]) -> None:
        self.transports = tuple(transports)
        if len(self.transports) < 2:
            raise SmsTransportError("failover_requires_multiple_transports")

    def send(self, destination_ref: str, message: str, *, idempotency_key: str) -> str | None:
        last: SmsTransportError | None = None
        for transport in self.transports:
            try:
                return transport.send(destination_ref, message, idempotency_key=idempotency_key)
            except SmsTransportError as exc:
                last = exc
                if not exc.retryable:
                    raise
        if last is not None:
            raise last
        raise SmsTransportError("sms_transport_unavailable")
