from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioEvidence:
    scenario_id: str
    mission_completed: bool
    coordination_changed_behavior: bool
    user_interventions: int
    duplicate_work_avoided: int = 0
    recoveries_completed: int = 0
    raw_messages: int = 0
    raw_agent_steps: int = 0

    def __post_init__(self):
        if not self.scenario_id:
            raise ValueError("scenario_id is required")
        for field in ("user_interventions", "duplicate_work_avoided", "recoveries_completed", "raw_messages", "raw_agent_steps"):
            if getattr(self, field) < 0:
                raise ValueError(f"{field} cannot be negative")


def passive_intelligence_baseline(evidence):
    rows = list(evidence)
    if not rows:
        raise ValueError("at least one scenario is required")
    completed = sum(1 for row in rows if row.mission_completed)
    coordination_effects = sum(1 for row in rows if row.coordination_changed_behavior)
    interventions = sum(row.user_interventions for row in rows)
    useful = sum(row.duplicate_work_avoided + row.recoveries_completed for row in rows)
    return {
        "scenario_count": len(rows),
        "mission_completion_rate": completed / len(rows),
        "coordination_effect_rate": coordination_effects / len(rows),
        "user_intervention_index": interventions / len(rows),
        "useful_coordination_events": useful,
        "activity_metrics_are_authority": False,
        "raw_activity": {
            "messages": sum(row.raw_messages for row in rows),
            "agent_steps": sum(row.raw_agent_steps for row in rows),
        },
    }


def assert_anti_goodhart(baseline):
    if baseline.get("activity_metrics_are_authority") is not False:
        raise ValueError("activity metrics must not be authoritative success criteria")
    if baseline.get("mission_completion_rate", 0) <= 0 and baseline.get("useful_coordination_events", 0) <= 0:
        raise ValueError("baseline has activity but no mission/useful-outcome evidence")
    return True
