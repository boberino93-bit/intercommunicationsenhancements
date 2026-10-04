from datetime import datetime,timedelta,timezone
import pytest
from swarm_kernel.kernel import *
CFG=ProjectConfig("example","owner/example","main","Example-AgentBus/")
def test_binding():
    with pytest.raises(PermissionError): validate_binding(CFG,"other","owner/example")
def test_paths_and_gate():
    assert record_path("leases","run_1","task_1")==".swarm/leases/run_1/task_1.json"
    with pytest.raises(ValueError): record_path("leases","../run","task")
    assert not can_open_start_gate(["a","b"],["a"])[0]
def test_lease_and_gates():
    now=datetime(2026,1,1,tzinfo=timezone.utc); l=new_lease(CFG,"run_1","task","a",0,now); assert l["version"]==1; assert lease_transition_allowed(l,1,"b",now)[1]=="LEASE_HELD"; assert lease_transition_allowed(l,1,"b",now+timedelta(seconds=1801))[1]=="EXPIRED_RECLAIM"; assert circuit_state(CFG,3)=="DEGRADED_READ_ONLY"; assert backpressure_state(CFG,15)=="HARD_STOP_SECONDARY_WORK"
def test_preflight_convergence():
    c={"identity_binding":True,"run_epoch":True,"role_binding":True,"package_parity":True,"recovery_state":True,"manager_presence":True,"foreign_write_policy":True,"tests":False}; assert not preflight(CFG,c)["ready"]; assert not convergence_gate(research_accounted=True,manager_dispositions_complete=True,primary_decisions_persisted=True,package_parity_restored=True,unresolved_leases=1,recovery_checkpoint_valid=True)["complete"]
