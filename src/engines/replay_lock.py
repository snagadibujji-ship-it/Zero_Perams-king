import hashlib
import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tooling.causal_counterfactual_runner import CausalCounterfactualRunner
from tooling.civilization_production_benchmark import (
    CivilizationProductionBenchmark,
    BenchmarkConfig,
)
from tooling.phase4_certification import Phase4Certification
from tooling.phase5_calibration_report import Phase5CalibrationReport
from tooling.phaseC_world_report import PhaseCWorldReport


def _digest(obj: Dict[str, object]) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ReplayLockVerifier:
    """Hard determinism verifier for repeated seeded runs."""

    def run(self, seed: int = 17, repeats: int = 5) -> Dict[str, object]:
        run_hashes: List[Dict[str, str]] = []
        for _ in range(repeats):
            cf = CausalCounterfactualRunner().run(seed=seed)
            bench = CivilizationProductionBenchmark().run(
                BenchmarkConfig(seed=seed, counterfactual_report=cf)
            )
            p4 = Phase4Certification().run(seed=seed)
            p5 = Phase5CalibrationReport().run(seed=seed)
            pC = PhaseCWorldReport().run(seed=seed)
            run_hashes.append(
                {
                    "counterfactual": _digest(cf),
                    "benchmark_gates": _digest(bench.get("quality_gates", {})),
                    "phase4": _digest(p4),
                    "phase5": _digest(p5),
                    "phaseC": _digest(pC),
                }
            )

        unique = {
            key: len(set(r[key] for r in run_hashes)) for key in run_hashes[0].keys()
        }
        return {
            "seed": seed,
            "repeats": repeats,
            "hash_uniqueness": unique,
            "deterministic": all(v == 1 for v in unique.values()),
            "sample_hashes": run_hashes[0],
        }


if __name__ == "__main__":
    print(json.dumps(ReplayLockVerifier().run(), indent=2, ensure_ascii=False))
