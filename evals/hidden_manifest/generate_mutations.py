#!/usr/bin/env python3
"""Generate semantic mutations from existing public benchmark cases.

Takes existing eval cases and produces mutations:
- Negate: Flip the expected answer or add negation
- Change numbers: Modify numeric values in inputs
- Swap entities: Replace entities with related alternatives

These mutations create novel cases that the system cannot have
memorized from the public manifest.

Usage:
    python evals/hidden_manifest/generate_mutations.py \
        --source evals/public/manifest.json \
        --output evals/hidden_manifest/hidden_cases.json \
        --mutations-per-case 3

    python evals/hidden_manifest/generate_mutations.py \
        --validate evals/hidden_manifest/hidden_cases.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MutationResult:
    """A single mutation of a benchmark case."""

    input: str
    expected_output: str
    mutation_type: str
    parent_id: str
    difficulty: str


class NumberMutator:
    """Mutates numeric values in math problems."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def mutate(self, input_text: str, expected: str) -> Optional[MutationResult]:
        """Change numbers in a math input and recompute expected."""
        # Find numbers in the input
        numbers = re.findall(r"\b(\d+)\b", input_text)
        if not numbers:
            return None

        # Pick a number to mutate
        target = self._rng.choice(numbers)
        target_val = int(target)

        # Generate a new value (different but reasonable)
        if target_val == 0:
            new_val = self._rng.randint(1, 10)
        elif target_val < 10:
            new_val = self._rng.randint(1, 20)
            while new_val == target_val:
                new_val = self._rng.randint(1, 20)
        else:
            # Scale by a random factor
            factor = self._rng.choice([0.5, 2, 3, 0.25])
            new_val = int(target_val * factor)
            if new_val == target_val:
                new_val = target_val + self._rng.randint(1, 10)

        new_input = input_text.replace(target, str(new_val), 1)

        # Attempt to recompute expected output for simple arithmetic
        new_expected = self._recompute_expected(new_input, expected, target_val, new_val)

        return MutationResult(
            input=new_input,
            expected_output=new_expected,
            mutation_type="change_numbers",
            parent_id="",  # Will be set by caller
            difficulty="medium",
        )

    def _recompute_expected(
        self, new_input: str, old_expected: str, old_num: int, new_num: int
    ) -> str:
        """Try to recompute the expected answer for simple operations."""
        lower_input = new_input.lower()

        # Simple arithmetic: "what is X * Y"
        mult_match = re.search(r"what is (\d+)\s*\*\s*(\d+)", lower_input)
        if mult_match:
            return str(int(mult_match.group(1)) * int(mult_match.group(2)))

        add_match = re.search(r"what is (\d+)\s*\+\s*(\d+)", lower_input)
        if add_match:
            return str(int(add_match.group(1)) + int(add_match.group(2)))

        div_match = re.search(r"what is (\d+)\s*/\s*(\d+)", lower_input)
        if div_match:
            divisor = int(div_match.group(2))
            if divisor != 0:
                return str(int(div_match.group(1)) // divisor)

        mod_match = re.search(r"what is (\d+)\s*mod\s*(\d+)", lower_input)
        if mod_match:
            divisor = int(mod_match.group(2))
            if divisor != 0:
                return str(int(mod_match.group(1)) % divisor)

        # Power: "what is X^Y"
        pow_match = re.search(r"what is (\d+)\^(\d+)", lower_input)
        if pow_match:
            base = int(pow_match.group(1))
            exp = int(pow_match.group(2))
            if exp <= 20:
                return str(base ** exp)

        # Factorial: "what is the factorial of X"
        fact_match = re.search(r"factorial of (\d+)", lower_input)
        if fact_match:
            n = int(fact_match.group(1))
            if n <= 12:
                result = 1
                for i in range(2, n + 1):
                    result *= i
                return str(result)

        # sqrt: "what is sqrt(X)"
        sqrt_match = re.search(r"sqrt\((\d+)\)", lower_input)
        if sqrt_match:
            n = int(sqrt_match.group(1))
            import math
            result = math.sqrt(n)
            if result == int(result):
                return str(int(result))
            return f"{result:.4f}"

        # Linear solve: "solve Ax + B = 0" → x = -B/A
        linear_match = re.search(r"solve\s+(\d+)x\s*([+-])\s*(\d+)\s*=\s*0", lower_input)
        if linear_match:
            a = int(linear_match.group(1))
            sign = linear_match.group(2)
            b = int(linear_match.group(3))
            if sign == "+":
                x = -b / a
            else:
                x = b / a
            if x == int(x):
                return str(int(x))
            return f"{x:.4f}"

        # If we can't recompute, mark as needing manual review
        return f"[NEEDS_REVIEW: mutation of '{old_expected}']"


class NegationMutator:
    """Negates or inverts the expected behavior."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def mutate(self, input_text: str, expected: str) -> Optional[MutationResult]:
        """Negate a case — make the expected output different."""
        lower = input_text.lower()

        # For equations: change the sign
        if "solve" in lower:
            return self._negate_equation(input_text, expected)

        # For numeric answers: negate the value
        try:
            val = float(expected)
            new_expected = str(-val) if val != 0 else "1"
            # Modify input to produce negated result
            new_input = self._modify_for_negation(input_text, val)
            if new_input:
                return MutationResult(
                    input=new_input,
                    expected_output=new_expected,
                    mutation_type="negate",
                    parent_id="",
                    difficulty="medium",
                )
        except (ValueError, TypeError):
            pass

        return None

    def _negate_equation(self, input_text: str, expected: str) -> Optional[MutationResult]:
        """Negate an equation by flipping signs."""
        # e.g., "solve x^2 - 4 = 0" → "solve x^2 + 4 = 0" (no real roots)
        # or change coefficients
        new_input = input_text
        if " - " in new_input:
            new_input = new_input.replace(" - ", " + ", 1)
        elif " + " in new_input:
            new_input = new_input.replace(" + ", " - ", 1)
        else:
            return None

        return MutationResult(
            input=new_input,
            expected_output=f"[NEEDS_REVIEW: negation of '{expected}']",
            mutation_type="negate",
            parent_id="",
            difficulty="hard",
        )

    def _modify_for_negation(self, input_text: str, original_val: float) -> Optional[str]:
        """Modify input text to produce a negated result."""
        # For "what is X + Y", change to "what is X - Y" to potentially negate
        if "+" in input_text:
            return input_text.replace("+", "-", 1)
        if "*" in input_text:
            # Multiply by -1 effectively
            return input_text.replace("*", "* -", 1)
        return None


class EntityMutator:
    """Swaps entities with related alternatives."""

    ENTITY_SWAPS = {
        # Math functions
        "sin": ("cos", {"0": "1"}),
        "cos": ("sin", {"0": "0"}),
        "derivative": ("integral", {}),
        "integrate": ("differentiate", {}),
        "GCD": ("LCM", {}),
        # Languages
        "gravity": ("energy", {}),
        "DNA": ("RNA", {}),
        "photosynthesis": ("respiration", {}),
        # Sort algorithms
        "binary search": ("linear search", {}),
        "quicksort": ("mergesort", {}),
        "bubble sort": ("insertion sort", {}),
        "merge sort": ("heap sort", {}),
        "linked list": ("doubly linked list", {}),
        "stack": ("queue", {}),
        "binary tree": ("AVL tree", {}),
        "hash map": ("linked hash map", {}),
        "dijkstra": ("bellman ford", {}),
    }

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def mutate(self, input_text: str, expected: str, category: str) -> Optional[MutationResult]:
        """Swap an entity in the input with a related alternative."""
        for entity, (replacement, answer_map) in self.ENTITY_SWAPS.items():
            if entity.lower() in input_text.lower():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(entity), re.IGNORECASE)
                new_input = pattern.sub(replacement, input_text, count=1)

                # If we have a known answer mapping, use it
                if expected in answer_map:
                    new_expected = answer_map[expected]
                else:
                    new_expected = f"[NEEDS_REVIEW: entity swap '{entity}'→'{replacement}']"

                # For codegen, compilation judge doesn't need exact expected
                if category == "codegen":
                    new_expected = f"def {replacement.replace(' ', '_')}"

                return MutationResult(
                    input=new_input,
                    expected_output=new_expected,
                    mutation_type="swap_entities",
                    parent_id="",
                    difficulty="medium",
                )

        return None


def generate_mutations(
    manifest_data: Dict[str, Any],
    mutations_per_case: int = 3,
    seed: int = 42,
) -> Dict[str, Any]:
    """Generate hidden mutations from a public manifest.

    Args:
        manifest_data: Loaded public manifest dictionary.
        mutations_per_case: Max mutations to generate per source case.
        seed: Random seed for reproducibility.

    Returns:
        Hidden manifest dictionary ready to save.
    """
    rng = random.Random(seed)
    cases = manifest_data.get("cases", [])

    number_mutator = NumberMutator(rng)
    negation_mutator = NegationMutator(rng)
    entity_mutator = EntityMutator(rng)

    hidden_cases: List[Dict[str, Any]] = []
    case_counter = 0

    for case in cases:
        parent_id = case["id"]
        input_text = case["input"]
        expected = case["expected_output"]
        category = case["category"]
        judge_type = case["judge_type"]

        mutators = [
            ("change_numbers", lambda: number_mutator.mutate(input_text, expected)),
            ("negate", lambda: negation_mutator.mutate(input_text, expected)),
            ("swap_entities", lambda: entity_mutator.mutate(input_text, expected, category)),
        ]

        rng.shuffle(mutators)
        generated = 0

        for mutation_name, mutator_fn in mutators:
            if generated >= mutations_per_case:
                break

            result = mutator_fn()
            if result is None:
                continue

            # Skip cases that need manual review in automated generation
            if "[NEEDS_REVIEW" in result.expected_output:
                continue

            case_counter += 1
            hidden_cases.append({
                "id": f"hidden_{category}_{case_counter:03d}",
                "category": category,
                "input": result.input,
                "expected_output": result.expected_output,
                "judge_type": judge_type,
                "difficulty": result.difficulty,
                "hidden": True,
                "source": f"mutation_{mutation_name}",
                "parent_id": parent_id,
                "mutation_type": mutation_name,
            })
            generated += 1

    # Compute integrity hash
    content = json.dumps(hidden_cases, sort_keys=True, ensure_ascii=True)
    manifest_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    return {
        "version": "1.0.0",
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hash": manifest_hash,
        "mutation_source": manifest_data.get("version", "unknown"),
        "contamination_disclosures": [
            "Derived from public manifest via automated mutations",
            "Number mutations may have rounding errors",
            "Entity swaps may produce semantically invalid questions",
        ],
        "cases": hidden_cases,
    }


def validate_manifest(manifest_path: Path) -> bool:
    """Validate a hidden manifest against the schema.

    Args:
        manifest_path: Path to the hidden manifest JSON.

    Returns:
        True if valid, False otherwise.
    """
    schema_path = Path(__file__).parent / "schema.json"

    with open(manifest_path) as f:
        manifest = json.load(f)

    with open(schema_path) as f:
        schema = json.load(f)

    # Basic structural validation (no jsonschema dependency)
    errors: List[str] = []

    if "version" not in manifest:
        errors.append("Missing required field: version")
    if "cases" not in manifest:
        errors.append("Missing required field: cases")
    if "frozen_at" not in manifest:
        errors.append("Missing required field: frozen_at")
    if "hash" not in manifest:
        errors.append("Missing required field: hash")

    if "cases" in manifest:
        valid_categories = {"math", "physics", "codegen", "multilingual", "knowledge", "web", "creative"}
        valid_judge_types = {"exact", "tolerance", "ast", "proof", "compilation", "test", "semantic", "human"}
        valid_difficulties = {"trivial", "easy", "medium", "hard", "frontier"}

        for i, case in enumerate(manifest["cases"]):
            if "id" not in case:
                errors.append(f"Case {i}: missing 'id'")
            if "category" not in case:
                errors.append(f"Case {i}: missing 'category'")
            elif case["category"] not in valid_categories:
                errors.append(f"Case {i}: invalid category '{case['category']}'")
            if "input" not in case:
                errors.append(f"Case {i}: missing 'input'")
            if "expected_output" not in case:
                errors.append(f"Case {i}: missing 'expected_output'")
            if "judge_type" not in case:
                errors.append(f"Case {i}: missing 'judge_type'")
            elif case["judge_type"] not in valid_judge_types:
                errors.append(f"Case {i}: invalid judge_type '{case['judge_type']}'")
            if "difficulty" not in case:
                errors.append(f"Case {i}: missing 'difficulty'")
            elif case["difficulty"] not in valid_difficulties:
                errors.append(f"Case {i}: invalid difficulty '{case['difficulty']}'")

        # Verify hash integrity
        content = json.dumps(manifest["cases"], sort_keys=True, ensure_ascii=True)
        computed_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if manifest.get("hash") and manifest["hash"] != computed_hash:
            errors.append(f"Integrity check failed: hash mismatch")

    if errors:
        print(f"Validation FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return False

    print(f"Validation PASSED: {len(manifest.get('cases', []))} cases, integrity verified.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate semantic mutations from public benchmark cases"
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Path to public manifest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for hidden cases",
    )
    parser.add_argument(
        "--mutations-per-case",
        type=int,
        default=3,
        help="Maximum mutations per source case (default: 3)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--validate",
        type=Path,
        help="Validate an existing hidden manifest",
    )

    args = parser.parse_args()

    if args.validate:
        success = validate_manifest(args.validate)
        return 0 if success else 1

    if not args.source:
        print("Error: --source is required for generation mode")
        parser.print_help()
        return 1

    if not args.output:
        print("Error: --output is required for generation mode")
        parser.print_help()
        return 1

    # Load source manifest
    if not args.source.exists():
        print(f"Error: Source manifest not found: {args.source}")
        return 1

    with open(args.source) as f:
        manifest_data = json.load(f)

    print(f"Source manifest: {args.source}")
    print(f"Source cases: {len(manifest_data.get('cases', []))}")
    print(f"Mutations per case: {args.mutations_per_case}")
    print(f"Seed: {args.seed}")
    print()

    # Generate mutations
    hidden_manifest = generate_mutations(
        manifest_data,
        mutations_per_case=args.mutations_per_case,
        seed=args.seed,
    )

    print(f"Generated {len(hidden_manifest['cases'])} hidden cases")
    print(f"Hash: {hidden_manifest['hash'][:16]}...")

    # Save output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(hidden_manifest, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {args.output}")

    # Validate what we just generated
    print()
    validate_manifest(args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
