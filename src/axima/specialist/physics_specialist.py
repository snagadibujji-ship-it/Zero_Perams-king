"""Physics Specialist — equation solving with units, dimensional analysis, and derivations.

Every computation enforces dimensional consistency. Uncertainty propagation is mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Units and Dimensions
# ---------------------------------------------------------------------------

class BaseDimension(Enum):
    LENGTH = auto()
    MASS = auto()
    TIME = auto()
    CURRENT = auto()
    TEMPERATURE = auto()
    AMOUNT = auto()
    LUMINOSITY = auto()


@dataclass(frozen=True)
class Dimension:
    """Dimensional signature as exponents of base dimensions."""
    length: float = 0.0
    mass: float = 0.0
    time: float = 0.0
    current: float = 0.0
    temperature: float = 0.0
    amount: float = 0.0
    luminosity: float = 0.0

    def __mul__(self, other: "Dimension") -> "Dimension":
        return Dimension(
            length=self.length + other.length,
            mass=self.mass + other.mass,
            time=self.time + other.time,
            current=self.current + other.current,
            temperature=self.temperature + other.temperature,
            amount=self.amount + other.amount,
            luminosity=self.luminosity + other.luminosity,
        )

    def __truediv__(self, other: "Dimension") -> "Dimension":
        return Dimension(
            length=self.length - other.length,
            mass=self.mass - other.mass,
            time=self.time - other.time,
            current=self.current - other.current,
            temperature=self.temperature - other.temperature,
            amount=self.amount - other.amount,
            luminosity=self.luminosity - other.luminosity,
        )

    def __pow__(self, exp: float) -> "Dimension":
        return Dimension(
            length=self.length * exp,
            mass=self.mass * exp,
            time=self.time * exp,
            current=self.current * exp,
            temperature=self.temperature * exp,
            amount=self.amount * exp,
            luminosity=self.luminosity * exp,
        )

    @property
    def is_dimensionless(self) -> bool:
        return (self.length == 0 and self.mass == 0 and self.time == 0
                and self.current == 0 and self.temperature == 0
                and self.amount == 0 and self.luminosity == 0)


# Common dimension signatures
DIMENSIONLESS = Dimension()
METER = Dimension(length=1)
KILOGRAM = Dimension(mass=1)
SECOND = Dimension(time=1)
VELOCITY = Dimension(length=1, time=-1)
ACCELERATION = Dimension(length=1, time=-2)
FORCE = Dimension(mass=1, length=1, time=-2)
ENERGY = Dimension(mass=1, length=2, time=-2)
POWER = Dimension(mass=1, length=2, time=-3)
PRESSURE = Dimension(mass=1, length=-1, time=-2)
CHARGE = Dimension(current=1, time=1)


@dataclass
class PhysicalQuantity:
    """A value with units and optional uncertainty."""
    value: float
    dimension: Dimension
    unit_label: str = ""
    uncertainty: Optional[float] = None

    def __post_init__(self) -> None:
        if self.uncertainty is not None and self.uncertainty < 0:
            raise ValueError("Uncertainty must be non-negative")

    def __repr__(self) -> str:
        unc_str = f" +/- {self.uncertainty}" if self.uncertainty else ""
        return f"{self.value}{unc_str} [{self.unit_label}]"


@dataclass
class DimensionalError:
    """Records a dimensional inconsistency."""
    expected: Dimension
    got: Dimension
    context: str


@dataclass
class DerivationAssumption:
    """An assumption required for a physics derivation."""
    statement: str
    domain: str = "classical_mechanics"
    verified: bool = False


@dataclass
class DerivationStep:
    """One step in a physics derivation."""
    law: str
    equation: str
    substitution: Optional[Dict[str, str]] = None
    justification: str = ""


@dataclass
class Derivation:
    """Full derivation chain for a physics result."""
    steps: List[DerivationStep] = field(default_factory=list)
    assumptions: List[DerivationAssumption] = field(default_factory=list)
    result: Optional[PhysicalQuantity] = None
    valid: bool = True
    error: Optional[str] = None


@dataclass
class PhysicsEquation:
    """A known physics equation with metadata."""
    name: str
    formula: str
    variables: Dict[str, Dimension]
    result_dimension: Dimension
    domain: str = "classical_mechanics"


# Core equation library
_EQUATIONS: Dict[str, PhysicsEquation] = {
    "kinetic_energy": PhysicsEquation(
        name="Kinetic Energy",
        formula="0.5 * m * v**2",
        variables={"m": KILOGRAM, "v": VELOCITY},
        result_dimension=ENERGY,
    ),
    "newton_second": PhysicsEquation(
        name="Newton's Second Law",
        formula="F = m * a",
        variables={"m": KILOGRAM, "a": ACCELERATION},
        result_dimension=FORCE,
    ),
    "uniform_motion": PhysicsEquation(
        name="Uniform Motion",
        formula="d = v * t",
        variables={"v": VELOCITY, "t": SECOND},
        result_dimension=METER,
    ),
    "gravitational_pe": PhysicsEquation(
        name="Gravitational Potential Energy",
        formula="m * g * h",
        variables={"m": KILOGRAM, "g": ACCELERATION, "h": METER},
        result_dimension=ENERGY,
    ),
    "ohms_law": PhysicsEquation(
        name="Ohm's Law",
        formula="V = I * R",
        variables={"I": Dimension(current=1), "R": Dimension(mass=1, length=2, time=-3, current=-2)},
        result_dimension=Dimension(mass=1, length=2, time=-3, current=-1),
    ),
}

_CONSTANTS: Dict[str, PhysicalQuantity] = {
    "G": PhysicalQuantity(6.674e-11, Dimension(length=3, mass=-1, time=-2), "m^3/(kg*s^2)"),
    "c": PhysicalQuantity(2.998e8, VELOCITY, "m/s"),
    "g": PhysicalQuantity(9.81, ACCELERATION, "m/s^2"),
    "k_B": PhysicalQuantity(1.381e-23, Dimension(mass=1, length=2, time=-2, temperature=-1), "J/K"),
    "h": PhysicalQuantity(6.626e-34, Dimension(mass=1, length=2, time=-1), "J*s"),
    "e": PhysicalQuantity(1.602e-19, CHARGE, "C"),
}


class PhysicsSpecialist:
    """Domain specialist for physics with mandatory unit checking."""

    def __init__(self) -> None:
        self._equations = dict(_EQUATIONS)
        self._constants = dict(_CONSTANTS)

    @property
    def available_equations(self) -> List[str]:
        return list(self._equations.keys())

    def solve_with_units(
        self,
        equation_name: str,
        known_values: Dict[str, PhysicalQuantity],
        solve_for: Optional[str] = None,
    ) -> Derivation:
        """Solve a known equation given values with units."""
        if equation_name not in self._equations:
            return Derivation(
                valid=False,
                error=f"Unknown equation: {equation_name}. Available: {list(self._equations.keys())}",
            )

        eq = self._equations[equation_name]
        steps: List[DerivationStep] = []
        assumptions: List[DerivationAssumption] = [
            DerivationAssumption(
                statement=f"Using {eq.name}: {eq.formula}",
                domain=eq.domain,
                verified=True,
            ),
        ]

        # Dimensional check
        errors = self._check_dimensions(eq, known_values)
        if errors:
            error_msgs = [f"{e.context}: expected {e.expected}, got {e.got}" for e in errors]
            return Derivation(
                steps=steps, assumptions=assumptions, valid=False,
                error=f"Dimensional inconsistency: {'; '.join(error_msgs)}",
            )

        steps.append(DerivationStep(
            law=eq.name, equation=eq.formula,
            justification="Dimensional check passed for all inputs",
        ))

        result = self._evaluate_equation(equation_name, known_values)
        if result is None:
            return Derivation(
                steps=steps, assumptions=assumptions, valid=False,
                error="Could not evaluate equation with given values",
            )

        steps.append(DerivationStep(
            law="substitution",
            equation=f"result = {result.value} {result.unit_label}",
            substitution={k: str(v.value) for k, v in known_values.items()},
            justification="Direct substitution of known values",
        ))

        return Derivation(steps=steps, assumptions=assumptions, result=result, valid=True)

    def dimensional_analysis(
        self,
        quantities: List[PhysicalQuantity],
        operation: str = "multiply",
    ) -> Tuple[Dimension, Optional[DimensionalError]]:
        """Check or compute resulting dimension from operations on quantities."""
        if not quantities:
            return DIMENSIONLESS, None

        if operation == "multiply":
            result = DIMENSIONLESS
            for q in quantities:
                result = result * q.dimension
            return result, None
        elif operation == "divide":
            if len(quantities) < 2:
                return quantities[0].dimension, None
            result = quantities[0].dimension
            for q in quantities[1:]:
                result = result / q.dimension
            return result, None
        elif operation == "add":
            base = quantities[0].dimension
            for i, q in enumerate(quantities[1:], 1):
                if q.dimension != base:
                    return base, DimensionalError(
                        expected=base, got=q.dimension,
                        context=f"Cannot add quantity[{i}] to quantity[0]: dimensions differ",
                    )
            return base, None
        else:
            return DIMENSIONLESS, DimensionalError(
                expected=DIMENSIONLESS, got=DIMENSIONLESS,
                context=f"Unknown operation: {operation}",
            )

    def derive(
        self,
        target: str,
        given: Dict[str, PhysicalQuantity],
        assumptions: Optional[List[str]] = None,
    ) -> Derivation:
        """Multi-step derivation to compute a target quantity from given values."""
        user_assumptions = [
            DerivationAssumption(statement=a, verified=False)
            for a in (assumptions or [])
        ]
        steps: List[DerivationStep] = []

        # Find an equation that can be solved with given values
        matching_eq: Optional[str] = None
        for eq_name, eq in self._equations.items():
            needed = set(eq.variables.keys())
            available = set(given.keys()) | set(self._constants.keys())
            if needed.issubset(available):
                matching_eq = eq_name
                break

        if matching_eq is None:
            return Derivation(
                steps=steps, assumptions=user_assumptions, valid=False,
                error=f"No known equation produces '{target}' from given: {list(given.keys())}",
            )

        full_known = dict(given)
        eq = self._equations[matching_eq]
        for var_name in eq.variables:
            if var_name not in full_known and var_name in self._constants:
                full_known[var_name] = self._constants[var_name]

        sub = self.solve_with_units(matching_eq, full_known)
        return Derivation(
            steps=sub.steps + steps,
            assumptions=user_assumptions + sub.assumptions,
            result=sub.result, valid=sub.valid, error=sub.error,
        )

    def _check_dimensions(
        self, eq: PhysicsEquation, values: Dict[str, PhysicalQuantity],
    ) -> List[DimensionalError]:
        errors: List[DimensionalError] = []
        for var_name, expected_dim in eq.variables.items():
            if var_name in values:
                actual_dim = values[var_name].dimension
                if actual_dim != expected_dim:
                    errors.append(DimensionalError(
                        expected=expected_dim, got=actual_dim,
                        context=f"Variable '{var_name}'",
                    ))
        return errors

    def _evaluate_equation(
        self, eq_name: str, values: Dict[str, PhysicalQuantity],
    ) -> Optional[PhysicalQuantity]:
        """Evaluate a known equation numerically with uncertainty propagation."""
        if eq_name == "kinetic_energy":
            m, v = values.get("m"), values.get("v")
            if m and v:
                result_val = 0.5 * m.value * v.value ** 2
                unc = self._propagate_product(
                    [m.value, v.value ** 2], [m.uncertainty, self._power_unc(v.value, 2, v.uncertainty)], 0.5)
                return PhysicalQuantity(result_val, ENERGY, "J", unc)
        elif eq_name == "newton_second":
            m, a = values.get("m"), values.get("a")
            if m and a:
                result_val = m.value * a.value
                unc = self._propagate_product([m.value, a.value], [m.uncertainty, a.uncertainty])
                return PhysicalQuantity(result_val, FORCE, "N", unc)
        elif eq_name == "uniform_motion":
            v, t = values.get("v"), values.get("t")
            if v and t:
                result_val = v.value * t.value
                unc = self._propagate_product([v.value, t.value], [v.uncertainty, t.uncertainty])
                return PhysicalQuantity(result_val, METER, "m", unc)
        elif eq_name == "gravitational_pe":
            m, g, h = values.get("m"), values.get("g"), values.get("h")
            if m and g and h:
                result_val = m.value * g.value * h.value
                unc = self._propagate_product(
                    [m.value, g.value, h.value], [m.uncertainty, g.uncertainty, h.uncertainty])
                return PhysicalQuantity(result_val, ENERGY, "J", unc)
        elif eq_name == "ohms_law":
            I, R = values.get("I"), values.get("R")
            if I and R:
                result_val = I.value * R.value
                unc = self._propagate_product([I.value, R.value], [I.uncertainty, R.uncertainty])
                return PhysicalQuantity(result_val, Dimension(mass=1, length=2, time=-3, current=-1), "V", unc)
        return None

    @staticmethod
    def _propagate_product(
        values: List[float], uncertainties: List[Optional[float]], coefficient: float = 1.0,
    ) -> Optional[float]:
        """Propagate uncertainty for product using relative uncertainty in quadrature."""
        has_any = False
        rel_unc_sq = 0.0
        for val, unc in zip(values, uncertainties):
            if unc is not None and val != 0:
                has_any = True
                rel_unc_sq += (unc / val) ** 2
        if not has_any:
            return None
        product = coefficient
        for v in values:
            product *= v
        return abs(product) * (rel_unc_sq ** 0.5)

    @staticmethod
    def _power_unc(value: float, power: float, uncertainty: Optional[float]) -> Optional[float]:
        """Uncertainty of x^n."""
        if uncertainty is None or value == 0:
            return None
        return abs(power) * abs(value) ** (power - 1) * uncertainty
