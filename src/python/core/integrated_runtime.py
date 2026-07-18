"""
AXIMA Integration Architecture — Wires Phase 0 + Ω + Ψ + Λ together.

Coordinates all subsystems without duplicating responsibilities:
  Observer, Reality Graph, Goal System, Attention, Prediction, Planner,
  Executor, Reflection, Cognitive Physics, Meta Reasoning, Autonomous Supervisor.

The integrated runtime is the final form of AXIMA's cognitive loop.
"""

import time
from typing import Optional, Dict, Any

from core.reality_graph import get_reality_graph, RealityGraph
from core.cognitive_runtime import CognitiveRuntime
from core.autonomous_supervisor import AutonomousSupervisor, get_supervisor
from core.autonomous_goals import get_goal_generator
from core.discovery_pipeline import get_discovery_pipeline
from core.knowledge_maintenance import get_maintenance
from core.cognitive_physics import get_physics
from core.activation_spreading import get_spreading
from core.memory_consolidation import get_consolidation
from core.knowledge_decay import get_decay
from core.principle_evolution import get_principle_evolution
from core.self_assessment import get_self_assessment
from core.autonomy_governance import get_governance
from core.cognitive_scheduler import get_scheduler


class IntegratedRuntime:
    """The fully integrated AXIMA cognitive system.
    
    Coordinates:
    - Phase 0: Router, Tracer, Errors, Contracts, Reality Graph, Goals, Understanding
    - Phase Ω: Observer, Sync, Attention, Prediction, Planner, Executor, Reflection, 
               Evolution, Contradiction, Curiosity, Cognitive Runtime
    - Phase Ψ: Cognitive State, Laws, Physics, Spreading, Consolidation, Decay,
               Principle Evolution, Self Metrics, Meta Reasoning, Scheduler
    - Phase Λ: Supervisor, Goals, Hypotheses, Experiments, Discovery, Maintenance,
               Self-Assessment, Governance
    """

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()

        # Phase Ω: Cognitive Runtime (orchestrates per-interaction loop)
        self._runtime = CognitiveRuntime(self._graph)

        # Phase Ψ: Cognitive Physics (governs state changes)
        self._physics = get_physics(self._graph)
        self._spreading = get_spreading(self._graph)
        self._consolidation = get_consolidation(self._graph)
        self._decay = get_decay(self._graph)
        self._principle_evo = get_principle_evolution(self._graph)

        # Phase Λ: Autonomous Cognition
        self._supervisor = get_supervisor(self._graph)
        self._goal_gen = get_goal_generator(self._graph)
        self._discovery = get_discovery_pipeline(self._graph)
        self._maintenance = get_maintenance(self._graph)
        self._assessment = get_self_assessment(self._graph)
        self._governance = get_governance(self._graph)
        self._scheduler = get_scheduler(self._graph)

    def process_interaction(self, text: str, execute_fn=None) -> Dict[str, Any]:
        """Process a user interaction through the full cognitive loop.
        
        1. Signal user active
        2. Run cognitive runtime (Observe → Attend → Predict → Plan → Execute → Reflect)
        3. Apply cognitive physics
        4. Spread activation
        """
        # User is active
        self._supervisor.on_user_active()

        # Full cognitive cycle (Phase Ω)
        state = self._runtime.think(text, execute_fn=execute_fn)

        # Apply physics to recently touched nodes (Phase Ψ)
        self._physics.tick(active_only=True, limit=20)
        self._spreading.spread_all(threshold=0.3)

        return state.summary()

    def autonomous_cycle(self) -> Dict[str, Any]:
        """One cycle of autonomous background cognition.
        
        Called when user is idle. Supervised by governance.
        
        1. Check if allowed (governance)
        2. Schedule what runs (scheduler)
        3. Generate goals
        4. Run discovery pipeline
        5. Maintain knowledge
        6. Apply physics
        7. Self-assess
        """
        # Governance check
        if self._governance._policy.human_override_active:
            return {"status": "paused_by_human_override"}

        # Supervisor tick
        supervisor_result = self._supervisor.tick()
        if supervisor_result.get("skipped_reason"):
            return {"status": "skipped", "reason": supervisor_result["skipped_reason"]}

        result = {"status": "completed", "actions": []}

        # What should run this cycle (scheduler)
        to_run = self._scheduler.what_runs_now()

        for task in to_run:
            start = time.time()
            action_result = self._run_autonomous_task(task)
            elapsed = (time.time() - start) * 1000
            self._scheduler.mark_completed(task, actual_ms=elapsed)
            result["actions"].append({"task": task, "result": action_result, "ms": round(elapsed, 1)})

        return result

    def idle_start(self):
        """Signal that user has gone idle."""
        self._supervisor.on_user_idle()

    def idle_end(self):
        """Signal that user is back."""
        self._supervisor.on_user_active()

    def assess(self) -> Dict[str, Any]:
        """Full system self-assessment."""
        return self._assessment.assess()

    def governance_status(self) -> Dict[str, Any]:
        """Current governance state."""
        return self._governance.policy_summary()

    def rollback_last(self) -> Optional[Dict]:
        """Rollback most recent autonomous action."""
        return self._governance.rollback_last()

    def stats(self) -> Dict[str, Any]:
        """Full system statistics."""
        return {
            "runtime": self._runtime.current_state(),
            "physics": self._physics.stats(),
            "supervisor": self._supervisor.stats(),
            "governance": self._governance.stats(),
            "assessment": self._assessment.assess() if self._assessment._assessments else {},
            "graph": self._graph.stats(),
        }

    # ─── Internal ───

    def _run_autonomous_task(self, task_type: str) -> Dict[str, Any]:
        """Execute a single autonomous task within governance bounds."""
        if task_type == "physics_tick":
            self._physics.tick(active_only=True, limit=30)
            return {"nodes_processed": "≤30"}

        elif task_type == "activation_spreading":
            self._spreading.spread_all(threshold=0.2)
            self._spreading.decay_all(rate=0.02)
            return {"spread": True}

        elif task_type == "memory_consolidation":
            return self._consolidation.consolidate_step(max_work=3)

        elif task_type == "knowledge_decay":
            self._decay.decay_tick(max_nodes=50)
            return {"decayed": True}

        elif task_type == "principle_evolution":
            self._principle_evo.evolve_tick()
            return {"evolved": True}

        elif task_type == "self_metrics":
            return self._assessment.assess()

        elif task_type == "curiosity":
            # Autonomous goal generation + discovery
            goals = self._goal_gen.generate(max_goals=2)
            discoveries = self._discovery.discover_step(max_hypotheses=2)
            maintenance = self._maintenance.maintain_step(max_work=3)

            # Commit goals if governance allows
            committed = 0
            for goal in goals:
                if self._governance.can_commit(goal.confidence, len(goal.related_nodes)):
                    self._goal_gen.commit_goal(goal)
                    self._governance.record_action("create", description=f"Auto-goal: {goal.objective[:50]}")
                    committed += 1

            return {
                "goals_generated": len(goals),
                "goals_committed": committed,
                "discoveries": discoveries,
                "maintenance": maintenance,
            }

        return {"unknown_task": task_type}


_integrated: Optional[IntegratedRuntime] = None
def get_integrated_runtime(graph: Optional[RealityGraph] = None) -> IntegratedRuntime:
    global _integrated
    if _integrated is None:
        _integrated = IntegratedRuntime(graph=graph)
    return _integrated
