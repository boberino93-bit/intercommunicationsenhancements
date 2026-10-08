import unittest

from org_agent_mesh.sms_transports import (
    FailoverSmsTransport,
    ResolvedSmsDestination,
    SipMessageResult,
    SipMessageSmsTransport,
    SmsTransportError,
)


class Resolver:
    def __init__(self, result):
        self.result = result
        self.refs = []
    def resolve(self, ref):
        self.refs.append(ref)
        return self.result


class Client:
    def __init__(self, result=None, exc=None):
        self.result = result or SipMessageResult(200, "OK", "tx-1")
        self.exc = exc
        self.calls = []
    def send_message(self, **kwargs):
        self.calls.append(kwargs)
        if self.exc:
            raise self.exc
        return self.result


class StubTransport:
    def __init__(self, result="ok", error=None):
        self.result=result; self.error=error; self.calls=[]
    def send(self, destination_ref, message, *, idempotency_key):
        self.calls.append((destination_ref,message,idempotency_key))
        if self.error: raise self.error
        return self.result


class SipSmsTests(unittest.TestCase):
    def transport(self, *, uri="sips:+12505550123@sms.example.net", status=200, require_tls=True):
        resolver=Resolver(ResolvedSmsDestination("+12505550123", uri))
        client=Client(SipMessageResult(status, "x", f"tx-{status}"))
        return SipMessageSmsTransport(
            resolver=resolver, client=client,
            allowed_gateway_hosts={"sms.example.net"},
            require_tls=require_tls,
        ), resolver, client

    def test_sends_rfc3428_plaintext_over_allowlisted_sips_gateway(self):
        t, resolver, client = self.transport()
        ref=t.send("vault://principals/robert/mobile", "Authentication code: 12345678.", idempotency_key="AUTHN-12345678")
        self.assertEqual(ref, "tx-200")
        call=client.calls[0]
        self.assertEqual(call["request_uri"], "sips:+12505550123@sms.example.net")
        self.assertEqual(call["content_type"], "text/plain; charset=utf-8")
        self.assertEqual(call["idempotency_key"], "AUTHN-12345678")

    def test_accepts_202_gateway_ack_without_claiming_delivery(self):
        t,_,_=self.transport(status=202)
        self.assertEqual(t.send("principal://robert/mobile","x",idempotency_key="AUTHN-12345678"),"tx-202")

    def test_rejects_raw_phone_destination(self):
        t,_,_=self.transport()
        with self.assertRaisesRegex(SmsTransportError,"protected_reference"):
            t.send("+12505550123","x",idempotency_key="AUTHN-12345678")

    def test_rejects_non_e164_resolution(self):
        resolver=Resolver(ResolvedSmsDestination("2505550123","sips:2505550123@sms.example.net"))
        t=SipMessageSmsTransport(resolver=resolver,client=Client(),allowed_gateway_hosts={"sms.example.net"})
        with self.assertRaisesRegex(SmsTransportError,"not_e164"):
            t.send("vault://x","x",idempotency_key="AUTHN-12345678")

    def test_requires_tls_by_default(self):
        t,_,_=self.transport(uri="sip:+12505550123@sms.example.net")
        with self.assertRaisesRegex(SmsTransportError,"tls_required"):
            t.send("vault://x","x",idempotency_key="AUTHN-12345678")

    def test_rejects_unallowlisted_gateway(self):
        resolver=Resolver(ResolvedSmsDestination("+12505550123","sips:+12505550123@evil.example"))
        t=SipMessageSmsTransport(resolver=resolver,client=Client(),allowed_gateway_hosts={"sms.example.net"})
        with self.assertRaisesRegex(SmsTransportError,"not_allowlisted"):
            t.send("vault://x","x",idempotency_key="AUTHN-12345678")

    def test_rejects_403_without_failover(self):
        t,_,_=self.transport(status=403)
        with self.assertRaises(SmsTransportError) as cm:
            t.send("vault://x","x",idempotency_key="AUTHN-12345678")
        self.assertFalse(cm.exception.retryable)

    def test_marks_503_retryable(self):
        t,_,_=self.transport(status=503)
        with self.assertRaises(SmsTransportError) as cm:
            t.send("vault://x","x",idempotency_key="AUTHN-12345678")
        self.assertTrue(cm.exception.retryable)

    def test_timeout_is_retryable(self):
        resolver=Resolver(ResolvedSmsDestination("+12505550123","sips:+12505550123@sms.example.net"))
        t=SipMessageSmsTransport(resolver=resolver,client=Client(exc=TimeoutError()),allowed_gateway_hosts={"sms.example.net"})
        with self.assertRaises(SmsTransportError) as cm:
            t.send("vault://x","x",idempotency_key="AUTHN-12345678")
        self.assertTrue(cm.exception.retryable)

    def test_message_size_bounded(self):
        t,_,_=self.transport()
        with self.assertRaisesRegex(SmsTransportError,"too_large"):
            t.send("vault://x","x"*2000,idempotency_key="AUTHN-12345678")

    def test_failover_only_on_retryable_failure(self):
        a=StubTransport(error=SmsTransportError("temp",retryable=True))
        b=StubTransport(result="backup")
        f=FailoverSmsTransport([a,b])
        out=f.send("vault://x","m",idempotency_key="AUTHN-12345678")
        self.assertEqual(out,"backup")
        self.assertEqual(len(b.calls),1)

    def test_failover_stops_on_permanent_failure(self):
        a=StubTransport(error=SmsTransportError("bad",retryable=False))
        b=StubTransport(result="backup")
        f=FailoverSmsTransport([a,b])
        with self.assertRaisesRegex(SmsTransportError,"bad"):
            f.send("vault://x","m",idempotency_key="AUTHN-12345678")
        self.assertEqual(len(b.calls),0)

    def test_failover_preserves_idempotency_key(self):
        a=StubTransport(error=SmsTransportError("temp",retryable=True))
        b=StubTransport(result="backup")
        f=FailoverSmsTransport([a,b])
        f.send("vault://x","m",idempotency_key="AUTHN-ABCDEFGH")
        self.assertEqual(a.calls[0][2],"AUTHN-ABCDEFGH")
        self.assertEqual(b.calls[0][2],"AUTHN-ABCDEFGH")


if __name__ == "__main__":
    unittest.main()
