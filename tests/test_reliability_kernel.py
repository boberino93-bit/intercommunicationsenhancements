from datetime import datetime, timedelta, timezone
import unittest

from org_agent_mesh.project_scope import ProjectBinding
from org_agent_mesh.reliability_kernel import (
    AdmissionDenied,
    CertificateVerificationError,
    CertificateVerifier,
    EffectivePolicySlice,
    HandoffVerificationError,
    HysteresisGate,
    InvariantViolation,
    KernelMode,
    KernelState,
    PolicyCompilationError,
    PolicyCompiler,
    ReasonCode,
    ResourceGovernor,
    ResourcePolicy,
    SchemaEvolutionRegistry,
    SchemaProtocolVersion,
    CompatibilityError,
    issue_handoff,
    verify_handoff,
)

KEY = b"0123456789abcdef0123456789abcdef"
NOW = datetime(2026, 10, 5, 6, 30, tzinfo=timezone.utc)


def binding(capabilities=("READ_SOURCE", "WRITE_SOURCE", "WRITE_ACCEPTED_STATE")):
    return ProjectBinding(
        project_id="intercommunicationsenhancements",
        repository_identity="boberino93-bit/intercommunicationsenhancements",
        project_root="/Intercommunication enhancements",
        agent_id="primary-v18",
        agent_instance_id="primary-v18-instance",
        protocol_version="2.4.0-alpha.1",
        capabilities=capabilities,
    )


class ReliabilityKernelTests(unittest.TestCase):
    def test_policy_compiler_cannot_escalate(self):
        compiler = PolicyCompiler()
        with self.assertRaises(PolicyCompilationError):
            compiler.compile_slice(
                binding(),
                work_instance_id="work-1",
                requested_capabilities=("READ_SOURCE", "DELETE_DATA"),
                requested_effect_classes=("READ_SOURCE",),
                execution_profile="READ_ONLY",
                ownership_epoch=1,
            )

    def test_production_deployment_is_not_created_by_compiler(self):
        compiler = PolicyCompiler()
        with self.assertRaises(PolicyCompilationError):
            compiler.compile_slice(
                binding(),
                work_instance_id="work-1",
                requested_capabilities=("READ_SOURCE",),
                requested_effect_classes=("PRODUCTION_DEPLOYMENT",),
                execution_profile="IMPLEMENTATION_WORKSPACE",
                ownership_epoch=1,
            )

    def test_certificate_verifies_and_binds_project_repo_epoch(self):
        compiler = PolicyCompiler()
        ps = compiler.compile_slice(
            binding(),
            work_instance_id="work-1",
            requested_capabilities=("READ_SOURCE", "WRITE_SOURCE"),
            requested_effect_classes=("READ_SOURCE", "WRITE_SOURCE"),
            execution_profile="IMPLEMENTATION_WORKSPACE",
            ownership_epoch=4,
            schema_versions={"event": "1.0"},
        )
        cert = compiler.issue_certificate(
            ps,
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=10),
            nonce="nonce-1",
            signing_key=KEY,
        )
        self.assertTrue(CertificateVerifier().verify(
            cert,
            verification_key=KEY,
            now=NOW + timedelta(minutes=1),
            binding=binding(),
            work_instance_id="work-1",
            ownership_epoch=4,
            required_effect="WRITE_SOURCE",
        ))

    def test_stale_ownership_epoch_rejected(self):
        compiler = PolicyCompiler()
        ps = compiler.compile_slice(
            binding(),
            work_instance_id="work-1",
            requested_capabilities=("READ_SOURCE",),
            requested_effect_classes=("READ_SOURCE",),
            execution_profile="READ_ONLY",
            ownership_epoch=3,
        )
        cert = compiler.issue_certificate(ps, issued_at=NOW, expires_at=NOW + timedelta(minutes=10), nonce="nonce-2", signing_key=KEY)
        with self.assertRaises(CertificateVerificationError) as ctx:
            CertificateVerifier().verify(cert, verification_key=KEY, now=NOW, binding=binding(), work_instance_id="work-1", ownership_epoch=4)
        self.assertIn(ReasonCode.OWNERSHIP_STALE.value, str(ctx.exception))

    def test_certificate_replay_can_be_consumed_once(self):
        compiler = PolicyCompiler()
        ps = compiler.compile_slice(
            binding(), work_instance_id="work-1", requested_capabilities=("READ_SOURCE",),
            requested_effect_classes=("READ_SOURCE",), execution_profile="READ_ONLY", ownership_epoch=1,
        )
        cert = compiler.issue_certificate(ps, issued_at=NOW, expires_at=NOW + timedelta(minutes=10), nonce="nonce-3", signing_key=KEY)
        verifier = CertificateVerifier()
        verifier.verify(cert, verification_key=KEY, now=NOW, binding=binding(), work_instance_id="work-1", ownership_epoch=1, consume=True)
        with self.assertRaises(CertificateVerificationError):
            verifier.verify(cert, verification_key=KEY, now=NOW, binding=binding(), work_instance_id="work-1", ownership_epoch=1, consume=True)

    def test_resource_governor_bounds_concurrency_and_weight(self):
        gov = ResourceGovernor(ResourcePolicy(max_concurrent=2, max_weight=3))
        gov.reserve(reservation_id="r1", work_instance_id="w1", weight=2)
        gov.reserve(reservation_id="r2", work_instance_id="w2", weight=1)
        with self.assertRaises(AdmissionDenied):
            gov.reserve(reservation_id="r3", work_instance_id="w3", weight=1)
        self.assertTrue(gov.release("r1"))
        self.assertIsNotNone(gov.reserve(reservation_id="r3", work_instance_id="w3", weight=1))

    def test_safe_minimal_mode_fails_closed(self):
        state = KernelState()
        state.enter_safe_minimal("test")
        self.assertEqual(state.mode, KernelMode.SAFE_MINIMAL)
        self.assertTrue(state.assert_effect_allowed("DIAGNOSTIC"))
        with self.assertRaises(InvariantViolation):
            state.assert_effect_allowed("WRITE_SOURCE")

    def test_handoff_cannot_expand_capability(self):
        with self.assertRaises(HandoffVerificationError):
            issue_handoff(
                project_id="intercommunicationsenhancements",
                repository_identity="boberino93-bit/intercommunicationsenhancements",
                work_instance_id="work-1",
                sender_agent_instance_id="a1",
                receiver_agent_instance_id="a2",
                sender_capabilities=("READ_SOURCE",),
                receiver_capabilities=("READ_SOURCE", "WRITE_SOURCE"),
                ownership_epoch=2,
                checkpoint_digest="abc",
                policy_certificate_id="pc-1",
                issued_at=NOW,
                expires_at=NOW + timedelta(minutes=10),
                nonce="h1",
                signing_key=KEY,
            )

    def test_handoff_verifies_against_epoch(self):
        handoff = issue_handoff(
            project_id="intercommunicationsenhancements",
            repository_identity="boberino93-bit/intercommunicationsenhancements",
            work_instance_id="work-1",
            sender_agent_instance_id="a1",
            receiver_agent_instance_id="a2",
            sender_capabilities=("READ_SOURCE", "WRITE_SOURCE"),
            receiver_capabilities=("READ_SOURCE",),
            ownership_epoch=2,
            checkpoint_digest="abc",
            policy_certificate_id="pc-1",
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=10),
            nonce="h2",
            signing_key=KEY,
        )
        self.assertTrue(verify_handoff(
            handoff,
            verification_key=KEY,
            now=NOW + timedelta(minutes=1),
            project_id="intercommunicationsenhancements",
            repository_identity="boberino93-bit/intercommunicationsenhancements",
            current_ownership_epoch=2,
        ))
        with self.assertRaises(HandoffVerificationError):
            verify_handoff(
                handoff,
                verification_key=KEY,
                now=NOW + timedelta(minutes=1),
                project_id="intercommunicationsenhancements",
                repository_identity="boberino93-bit/intercommunicationsenhancements",
                current_ownership_epoch=3,
            )

    def test_schema_registry_blocks_incompatible_writer_or_reader(self):
        registry = SchemaEvolutionRegistry()
        registry.register(SchemaProtocolVersion("events", "2.0", "1.5", "2.0"))
        self.assertTrue(registry.require_writer_compatible("events", "2.0", "2.1", ["1.5", "2.0"]))
        with self.assertRaises(CompatibilityError):
            registry.require_writer_compatible("events", "2.0", "1.9", ["1.5"])
        with self.assertRaises(CompatibilityError):
            registry.require_writer_compatible("events", "2.0", "2.1", ["1.4"])

    def test_hysteresis_prevents_thrashing(self):
        gate = HysteresisGate(enter_threshold=0.8, exit_threshold=0.4, cooldown_seconds=60)
        self.assertTrue(gate.update(0.9, NOW))
        self.assertTrue(gate.update(0.1, NOW + timedelta(seconds=30)))
        self.assertFalse(gate.update(0.1, NOW + timedelta(seconds=61)))


if __name__ == "__main__":
    unittest.main()
