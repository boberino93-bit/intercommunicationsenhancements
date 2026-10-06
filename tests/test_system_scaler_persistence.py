import unittest
from org_agent_mesh.system_scaler import DEFAULT_PROJECTS, ProjectScaleSignal, ScalerMemory, decide
RUN="run"; NOW="2026-10-05T22:42:00Z"; MEASURED="2026-10-05T22:41:30Z"
def signals(**over):
    out=[]
    for p in DEFAULT_PROJECTS:
        d=dict(project_id=p,run_id=RUN,measured_at_utc=MEASURED,active_research=0,standby_research=8,queued_eligible_work=1,manager_queue_depth=0,capacity_state="GREEN"); d.update(over); out.append(ProjectScaleSignal(**d))
    return out
def run(items): return decide(stage_population=30,run_id=RUN,now_utc=NOW,signals=items,memory=ScalerMemory(healthy_windows={p:4 for p in DEFAULT_PROJECTS}))
class PersistenceGateTests(unittest.TestCase):
    def test_unconfirmed_persistence_globally_holds(self): self.assertIn("DUAL_PERSISTENCE_UNCONFIRMED",run(signals(persistence_state="ARTIFACTORY_ONLY"))["decisions"][0]["reason"])
    def test_zero_loss_false_globally_holds(self): self.assertIn("PERSISTENCE_DEGRADED",run(signals(persistence_zero_loss=False))["decisions"][0]["reason"])
    def test_digest_mismatch_globally_holds(self): self.assertIn("PERSISTENCE_DIGEST_MISMATCH",run(signals(persistence_digest_mismatch_count=1))["decisions"][0]["reason"])
    def test_conflict_globally_holds(self): self.assertIn("PERSISTENCE_CONFLICT",run(signals(persistence_conflict_count=1))["decisions"][0]["reason"])
    def test_persistence_changes_input_digest(self):
        a=run(signals()); b=run(signals(persistence_state="ARTIFACTORY_ONLY")); self.assertNotEqual(a["input_digest"],b["input_digest"])
if __name__=="__main__": unittest.main()
