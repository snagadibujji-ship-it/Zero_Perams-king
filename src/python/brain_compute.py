"""
AXIMA BRAIN — Module 6: Computation Layer
Built by: Ghias + Kiro

THE KILLER FEATURE NotebookLM lacks.

When user's documents contain formulas:
  1. EXTRACT formulas from text
  2. When user asks with numbers → SUBSTITUTE and COMPUTE
  3. Show step-by-step with citation to their own source

NotebookLM: "According to your textbook, F=ma"
AXIMA: "From your textbook (Ch1 p3): F = ma = 5 × 3 = 15 N" + full explanation
"""

import re
import math
from typing import Dict, List, Optional, Tuple
from brain_ingest import DocumentBrain, Chunk


class BrainCompute:
    """Extract formulas from user's documents and compute with them."""

    def __init__(self, brain: DocumentBrain):
        self.brain = brain
        self.formula_bank: Dict[str, dict] = {}  # lhs → {formula, source, section, variables}
        self._build_formula_bank()

    def _build_formula_bank(self):
        """Extract all formulas from brain and parse them."""
        for chunk in self.brain.chunks.values():
            for formula in chunk.formulas:
                parsed = self._parse_formula(formula)
                if parsed:
                    self.formula_bank[parsed["lhs"]] = {
                        "full": formula,
                        "lhs": parsed["lhs"],
                        "rhs": parsed["rhs"],
                        "variables": parsed["variables"],
                        "source": chunk.source,
                        "section": chunk.section,
                    }

    def _parse_formula(self, formula: str) -> Optional[Dict]:
        """Parse 'X = expression' into components."""
        m = re.match(r'([A-Za-z_]\w*)\s*=\s*(.+)', formula)
        if not m:
            return None
        lhs = m.group(1).strip()
        rhs = m.group(2).strip()
        # Clean RHS: remove trailing descriptions like "where m is mass..."
        rhs = re.split(r'\s+(?:where|for|with|in which|measured|given)\s+', rhs)[0].strip()
        # Remove trailing period or comma
        rhs = rhs.rstrip('.,;')
        # Extract variable names from RHS
        variables = set(re.findall(r'\b([A-Za-z_]\w*)\b', rhs))
        # Remove known constants/functions
        constants = {'sin', 'cos', 'tan', 'sqrt', 'log', 'ln', 'pi', 'e', 'exp'}
        variables -= constants
        variables -= {lhs}  # remove the LHS variable
        return {"lhs": lhs, "rhs": rhs, "variables": list(variables)}

    def find_formula(self, target: str) -> Optional[Dict]:
        """Find a formula that computes the target variable."""
        target_lower = target.lower().strip()
        # Direct match
        if target_lower in self.formula_bank:
            return self.formula_bank[target_lower]
        # Case-insensitive
        for key, data in self.formula_bank.items():
            if key.lower() == target_lower:
                return data
        # Search in full formula text
        for key, data in self.formula_bank.items():
            if target_lower in data["full"].lower():
                return data
        return None

    def compute(self, question: str, values: Dict[str, float] = None) -> Optional[Dict]:
        """Given a question with numbers, find formula and compute.
        
        Returns: {answer, formula, steps, source, section}
        """
        # Extract numbers and variable assignments from question
        if values is None:
            values = self._extract_values(question)

        # Figure out what we're solving for
        target = self._extract_target(question)

        # Find applicable formula
        formula_data = None
        if target:
            formula_data = self.find_formula(target)

        # If no direct target, try to find formula that uses the given variables
        if not formula_data:
            formula_data = self._find_by_variables(values.keys())

        if not formula_data:
            return None

        # Compute
        try:
            result = self._evaluate(formula_data["rhs"], values)
            if result is None:
                return None

            # Build step-by-step
            steps = []
            steps.append(f"From your source: {formula_data['source']} ({formula_data['section']})")
            steps.append(f"Formula: {formula_data['lhs']} = {formula_data['rhs']}")
            steps.append(f"Given: {', '.join(f'{k}={v}' for k,v in values.items())}")

            # Show substitution
            substituted = formula_data['rhs']
            for var, val in values.items():
                substituted = re.sub(r'\b' + re.escape(var) + r'\b', str(val), substituted)
            steps.append(f"Substitute: {formula_data['lhs']} = {substituted}")
            steps.append(f"Result: {formula_data['lhs']} = {result}")

            return {
                "answer": result,
                "formula": formula_data["full"],
                "target": formula_data["lhs"],
                "steps": steps,
                "source": formula_data["source"],
                "section": formula_data["section"],
            }
        except:
            return None

    def _extract_values(self, question: str) -> Dict[str, float]:
        """Extract variable=value pairs from question text."""
        values = {}

        # Pattern: "m = 5" or "m=5" or "mass = 5 kg"
        for m in re.finditer(r'([a-zA-Z_]\w*)\s*=\s*([-\d.]+(?:[eE][-+]?\d+)?)', question):
            var = m.group(1)
            val = float(m.group(2))
            values[var] = val

        # Pattern: "5 kg" → m=5, "10 m/s" → v=10
        unit_map = {
            'kg': 'm', 'm/s': 'v', 'm/s²': 'a', 'N': 'F',
            'J': 'E', 'W': 'P', 'm': 'h', 's': 't',
        }
        for m in re.finditer(r'([-\d.]+)\s*(kg|m/s²|m/s|N|J|W|m|s)\b', question):
            val = float(m.group(1))
            unit = m.group(2)
            if unit in unit_map:
                var = unit_map[unit]
                if var not in values:
                    values[var] = val

        return values

    def _extract_target(self, question: str) -> Optional[str]:
        """Figure out what variable the user wants to find."""
        q = question.lower()
        # "find F" / "calculate E" / "what is v"
        m = re.search(r'(?:find|calculate|compute|what is|determine)\s+(?:the\s+)?([A-Za-z_]\w*)', question, re.IGNORECASE)
        if m:
            return m.group(1)
        # "force" → F, "energy" → E, "velocity" → v
        name_map = {
            'force': 'F', 'energy': 'E', 'velocity': 'v', 'speed': 'v',
            'acceleration': 'a', 'momentum': 'p', 'power': 'P',
            'mass': 'm', 'height': 'h', 'time': 't',
            'kinetic energy': 'KE', 'potential energy': 'PE',
        }
        for name, var in name_map.items():
            if name in q:
                return var
        return None

    def _find_by_variables(self, given_vars) -> Optional[Dict]:
        """Find formula that uses the given variables."""
        given = set(v.lower() for v in given_vars)
        best = None
        best_overlap = 0
        for key, data in self.formula_bank.items():
            formula_vars = set(v.lower() for v in data["variables"])
            overlap = len(given & formula_vars)
            if overlap > best_overlap:
                best_overlap = overlap
                best = data
        return best if best_overlap >= 2 else None

    def _evaluate(self, expression: str, values: Dict[str, float]) -> Optional[float]:
        """Safely evaluate a mathematical expression with given values."""
        try:
            # Prepare expression for eval
            expr = expression
            # Replace variable names with values
            for var, val in sorted(values.items(), key=lambda x: -len(x[0])):
                expr = re.sub(r'\b' + re.escape(var) + r'\b', str(val), expr)

            # Replace common math notation
            expr = expr.replace('^', '**')
            expr = expr.replace('²', '**2')
            expr = expr.replace('³', '**3')

            # Handle implicit multiplication: "2m" → "2*m", but only digits followed by letters
            expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)

            # Safe eval with math functions
            allowed = {"__builtins__": {}, "sqrt": math.sqrt, "pi": math.pi,
                       "sin": math.sin, "cos": math.cos, "tan": math.tan,
                       "log": math.log, "exp": math.exp, "abs": abs}

            # Check if all variables are substituted (no letters remaining)
            remaining_vars = re.findall(r'\b[a-zA-Z_]\w*\b', expr)
            remaining_vars = [v for v in remaining_vars if v not in ('sqrt','pi','sin','cos','tan','log','exp','abs')]
            if remaining_vars:
                return None  # Can't compute — missing variables

            result = eval(expr, allowed)
            if isinstance(result, (int, float)) and not math.isnan(result) and not math.isinf(result):
                return round(result, 6)
        except:
            pass
        return None

    def list_available_formulas(self) -> List[str]:
        """List all formulas extracted from user's sources."""
        return [f"{data['lhs']} = {data['rhs']} [{data['source']}]"
                for data in self.formula_bank.values()]

    def stats(self) -> Dict:
        return {"formulas_extracted": len(self.formula_bank)}
