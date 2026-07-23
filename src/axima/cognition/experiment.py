"""Experiment Engine — preregistered hypothesis testing.

Experiments have preregistered success criteria defined BEFORE running.
Simulated results cannot be promoted to real-world facts.
The simulation/observation boundary is enforced structurally.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ExperimentStatus(Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ResultDomain(Enum):
    """Distinguishes simulated from observed results."""

    SIMULATED = "SIMULATED"
    OBSERVED = "OBSERVED"


@dataclass
class ExperimentResult:
    """Result from an experiment run."""

    data: Dict[str, Any]
    domain: ResultDomain
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meets_criteria: Optional[bool] = None


@dataclass
class Experiment:
    """A preregistered experiment with defined success criteria."""

    id: str
    hypothesis: str
    design: Dict[str, Any]  # Experimental design spec
    preregistered_criteria: List[str]  # Success criteria defined before running
    variables: Dict[str, Any]  # Independent/dependent variables
    controls: List[str]  # Control conditions
    results: Optional[ExperimentResult] = None
    conclusion: Optional[str] = None
    status: ExperimentStatus = ExperimentStatus.PLANNED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    preregistered_at: Optional[datetime] = None


class ExperimentEngine:
    """Manages the experiment lifecycle with governance integration.

    Key invariants:
    1. Success criteria must be preregistered before running
    2. Simulated results are structurally distinct from observed results
    3. Simulated results CANNOT be promoted to real-world facts
    4. Discoveries require governance approval to be published
    """

    def __init__(self, governance_gate: Any = None) -> None:
        self._experiments: Dict[str, Experiment] = {}
        self._discoveries: List[Dict[str, Any]] = []
        self._governance = governance_gate

    @property
    def experiments(self) -> Dict[str, Experiment]:
        return dict(self._experiments)

    @property
    def discoveries(self) -> List[Dict[str, Any]]:
        return list(self._discoveries)

    def design(
        self,
        hypothesis: str,
        variables: Dict[str, Any],
        controls: List[str],
        design_spec: Optional[Dict[str, Any]] = None,
    ) -> Experiment:
        """Design an experiment.  Does NOT run it yet.

        The experiment starts in PLANNED status with no preregistered criteria.
        """
        experiment = Experiment(
            id=str(uuid.uuid4()),
            hypothesis=hypothesis,
            design=design_spec or {"type": "observational"},
            preregistered_criteria=[],
            variables=variables,
            controls=controls,
            status=ExperimentStatus.PLANNED,
        )
        self._experiments[experiment.id] = experiment
        return experiment

    def preregister(self, experiment_id: str, criteria: List[str]) -> Experiment:
        """Preregister success criteria BEFORE running the experiment.

        Once preregistered, criteria are immutable.
        """
        if experiment_id not in self._experiments:
            raise KeyError(f"Experiment {experiment_id} not found")

        experiment = self._experiments[experiment_id]

        if experiment.status != ExperimentStatus.PLANNED:
            raise ValueError("Cannot preregister criteria after experiment has started")

        if experiment.preregistered_criteria:
            raise ValueError("Criteria already preregistered — no post-hoc changes")

        if not criteria:
            raise ValueError("Must provide at least one success criterion")

        experiment.preregistered_criteria = list(criteria)
        experiment.preregistered_at = datetime.now(timezone.utc)
        return experiment

    def run(
        self,
        experiment_id: str,
        runner: Callable[[Experiment], Dict[str, Any]],
        domain: ResultDomain = ResultDomain.SIMULATED,
    ) -> Experiment:
        """Run an experiment.  Requires preregistered criteria.

        The runner function receives the experiment and returns result data.
        Domain tag (SIMULATED vs OBSERVED) is attached structurally.
        """
        if experiment_id not in self._experiments:
            raise KeyError(f"Experiment {experiment_id} not found")

        experiment = self._experiments[experiment_id]

        # Must have preregistered criteria
        if not experiment.preregistered_criteria:
            raise ValueError("Cannot run experiment without preregistered success criteria")

        if experiment.status not in (ExperimentStatus.PLANNED,):
            raise ValueError(f"Experiment cannot be run from status {experiment.status.value}")

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now(timezone.utc)

        try:
            data = runner(experiment)
            result = ExperimentResult(data=data, domain=domain)
            experiment.results = result
            experiment.status = ExperimentStatus.COMPLETE
            experiment.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            experiment.status = ExperimentStatus.FAILED
            experiment.conclusion = f"Experiment failed: {str(e)}"
            experiment.completed_at = datetime.now(timezone.utc)

        return experiment

    def analyze(
        self,
        experiment_id: str,
        evaluator: Optional[Callable[[Experiment], bool]] = None,
    ) -> Dict[str, Any]:
        """Analyze experiment results against preregistered criteria.

        Returns analysis dict with per-criterion results.
        """
        if experiment_id not in self._experiments:
            raise KeyError(f"Experiment {experiment_id} not found")

        experiment = self._experiments[experiment_id]

        if experiment.status != ExperimentStatus.COMPLETE:
            raise ValueError("Cannot analyze experiment that is not complete")

        if experiment.results is None:
            raise ValueError("No results to analyze")

        # Evaluate criteria
        if evaluator:
            meets_criteria = evaluator(experiment)
        else:
            # Default: check if result data has a 'success' key
            meets_criteria = experiment.results.data.get("success", False)

        experiment.results.meets_criteria = meets_criteria

        analysis = {
            "experiment_id": experiment.id,
            "hypothesis": experiment.hypothesis,
            "criteria": experiment.preregistered_criteria,
            "meets_criteria": meets_criteria,
            "result_domain": experiment.results.domain.value,
            "is_simulated": experiment.results.domain == ResultDomain.SIMULATED,
            "data": experiment.results.data,
        }

        # Set conclusion
        domain_tag = "[SIMULATED] " if experiment.results.domain == ResultDomain.SIMULATED else ""
        if meets_criteria:
            experiment.conclusion = f"{domain_tag}Hypothesis supported — criteria met"
        else:
            experiment.conclusion = f"{domain_tag}Hypothesis not supported — criteria not met"

        return analysis

    def submit_discovery(
        self,
        experiment_id: str,
        summary: str,
    ) -> Dict[str, Any]:
        """Submit an experiment's conclusion as a discovery.

        CANNOT promote simulated results to real-world facts.
        Requires governance approval.
        """
        if experiment_id not in self._experiments:
            raise KeyError(f"Experiment {experiment_id} not found")

        experiment = self._experiments[experiment_id]

        if experiment.status != ExperimentStatus.COMPLETE:
            raise ValueError("Cannot submit discovery from incomplete experiment")

        if experiment.results is None:
            raise ValueError("No results to base discovery on")

        # Enforce simulation boundary
        if experiment.results.domain == ResultDomain.SIMULATED:
            discovery = {
                "experiment_id": experiment.id,
                "hypothesis": experiment.hypothesis,
                "summary": summary,
                "domain": "SIMULATED",
                "is_fact": False,  # CANNOT be promoted to fact
                "caveat": "Result is from simulation — not a real-world observation",
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            discovery = {
                "experiment_id": experiment.id,
                "hypothesis": experiment.hypothesis,
                "summary": summary,
                "domain": "OBSERVED",
                "is_fact": experiment.results.meets_criteria is True,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            }

        # Governance check
        if self._governance is not None:
            permission = self._governance.check_permission("submit_discovery")
            if not permission.allowed:
                discovery["status"] = "blocked_by_governance"
                return discovery

        discovery["status"] = "accepted"
        self._discoveries.append(discovery)
        return discovery
