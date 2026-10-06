import json
from pathlib import Path
import unittest

from org_agent_mesh.project_context_binding import (
    ProjectContextBindingError,
    bind_host_project_context,
    parse_project_launch_context,
    render_project_launch_context,
    require_project_context_ready,
    resolve_host_project_id,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "governance" / "PROJECT_CONTEXT_BINDING_REGISTRY.json").read_text())


class ProjectContextBindingTests(unittest.TestCase):
    def test_display_name_resolves(self):
        self.assertEqual(resolve_host_project_id(REGISTRY, "Duo Screen"), "duo-open")

    def test_xrp_mapping_exists_and_uses_internal_forum(self):
        binding = bind_host_project_context(REGISTRY, host_project_context="Xrp analysis")
        self.assertEqual(binding.project_id, "xrp-thesis")
        self.assertEqual(binding.forum_authority, "INTERNAL_ARTIFACTORY")
        self.assertEqual(binding.forum_namespace, "/XRPTHESIS-AgentBus/messages")

    def test_conflicting_explicit_project_is_denied(self):
        with self.assertRaises(ProjectContextBindingError):
            bind_host_project_context(REGISTRY, host_project_context="Duo Screen", explicit_project_id="benefitflow")

    def test_launch_context_round_trip(self):
        binding = bind_host_project_context(REGISTRY, host_project_context="Duo Screen")
        rendered = render_project_launch_context(binding)
        parsed = parse_project_launch_context("Start work\n" + rendered + "\nThen continue", REGISTRY)
        self.assertEqual(parsed, binding)

    def test_tampered_launch_context_is_denied(self):
        binding = bind_host_project_context(REGISTRY, host_project_context="Duo Screen")
        rendered = render_project_launch_context(binding).replace("boberino93-bit/duo-open", "boberino93-bit/benefitflow")
        with self.assertRaises(ProjectContextBindingError):
            parse_project_launch_context(rendered, REGISTRY)

    def test_ready_barrier_requires_local_context(self):
        binding = bind_host_project_context(REGISTRY, host_project_context="Duo Screen")
        with self.assertRaises(ProjectContextBindingError):
            require_project_context_ready(binding=binding, local_bootstrap_loaded=True, context_reference_loaded=False, identity_lock_checked=True, handoff_loaded=True, coordination_route_loaded=True)
        self.assertTrue(require_project_context_ready(binding=binding, local_bootstrap_loaded=True, context_reference_loaded=True, identity_lock_checked=True, handoff_loaded=True, coordination_route_loaded=True))


if __name__ == "__main__":
    unittest.main()
