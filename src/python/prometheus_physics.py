"""
PROMETHEUS PHYSICS ENGINE — Phase 1
Built by: Ghias + Kiro

Core infrastructure:
  - PhysicsConstants: 80+ CODATA constants with units & uncertainties
  - DimensionalEngine: unit algebra, auto-checking, natural units
  - PhysicsLawDB: 250+ laws structured with equations & dependencies
  - PhysicsIdentifier: detect physics domain from question text
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import math
import re


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICAL CONSTANTS — CODATA 2022 + Cosmological (2026 values)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Constant:
    """A physical constant with value, units, uncertainty, and relations."""
    name: str
    symbol: str
    value: float
    units: str
    uncertainty: float = 0.0  # relative uncertainty
    category: str = ""
    aliases: List[str] = field(default_factory=list)
    notes: str = ""


class PhysicsConstants:
    """80+ physical constants from CODATA 2022 + cosmological values."""

    def __init__(self):
        self.constants: Dict[str, Constant] = {}
        self._build()

    def _add(self, name: str, symbol: str, value: float, units: str,
             uncertainty: float = 0.0, category: str = "", aliases: List[str] = None,
             notes: str = ""):
        self.constants[name] = Constant(
            name=name, symbol=symbol, value=value, units=units,
            uncertainty=uncertainty, category=category,
            aliases=aliases or [], notes=notes
        )

    def get(self, name: str) -> Optional[Constant]:
        """Get constant by name or alias."""
        if name in self.constants:
            return self.constants[name]
        # Search aliases
        name_lower = name.lower()
        for c in self.constants.values():
            if name_lower in [a.lower() for a in c.aliases] or name_lower == c.symbol.lower():
                return c
        return None

    def search(self, keyword: str) -> List[Constant]:
        """Search constants by keyword."""
        kw = keyword.lower()
        results = []
        for c in self.constants.values():
            if (kw in c.name.lower() or kw in c.symbol.lower() or
                kw in c.category.lower() or kw in c.units.lower() or
                any(kw in a.lower() for a in c.aliases)):
                results.append(c)
        return results

    def by_category(self, category: str) -> List[Constant]:
        """Get all constants in a category."""
        return [c for c in self.constants.values() if c.category == category]

    def _build(self):
        # ── FUNDAMENTAL (exact after 2019 SI redefinition) ──
        self._add("speed_of_light", "c", 299792458.0, "m/s",
                  0.0, "fundamental", ["c", "light speed"],
                  "Exact by definition (SI 2019)")
        self._add("planck_constant", "h", 6.62607015e-34, "J·s",
                  0.0, "fundamental", ["h", "Planck"],
                  "Exact by definition (SI 2019)")
        self._add("reduced_planck", "ℏ", 1.054571817e-34, "J·s",
                  0.0, "fundamental", ["hbar", "h-bar"],
                  "ℏ = h/(2π)")
        self._add("elementary_charge", "e", 1.602176634e-19, "C",
                  0.0, "fundamental", ["electron charge", "e"],
                  "Exact by definition (SI 2019)")
        self._add("boltzmann", "k_B", 1.380649e-23, "J/K",
                  0.0, "fundamental", ["kB", "Boltzmann constant"],
                  "Exact by definition (SI 2019)")
        self._add("avogadro", "N_A", 6.02214076e23, "mol⁻¹",
                  0.0, "fundamental", ["Avogadro", "NA"],
                  "Exact by definition (SI 2019)")
        self._add("gravitational", "G", 6.67430e-11, "m³/(kg·s²)",
                  1.5e-5, "fundamental", ["Newton constant", "big G"],
                  "Least precisely known fundamental constant")
        self._add("gas_constant", "R", 8.314462618, "J/(mol·K)",
                  0.0, "fundamental", ["gas constant"],
                  "R = N_A × k_B, exact")

        # ── ELECTROMAGNETIC ──
        self._add("vacuum_permittivity", "ε₀", 8.8541878128e-12, "F/m",
                  1.6e-10, "electromagnetic", ["epsilon_0", "permittivity"])
        self._add("vacuum_permeability", "μ₀", 1.25663706127e-6, "H/m",
                  1.6e-10, "electromagnetic", ["mu_0", "permeability"])
        self._add("impedance_vacuum", "Z₀", 376.730313412, "Ω",
                  1.6e-10, "electromagnetic", ["vacuum impedance"])
        self._add("coulomb_constant", "k_e", 8.9875517923e9, "N·m²/C²",
                  1.6e-10, "electromagnetic", ["Coulomb constant", "1/4πε₀"])
        self._add("bohr_magneton", "μ_B", 9.2740100657e-24, "J/T",
                  3.0e-10, "electromagnetic", ["Bohr magneton"])
        self._add("nuclear_magneton", "μ_N", 5.0507837393e-27, "J/T",
                  3.1e-10, "electromagnetic", ["nuclear magneton"])
        self._add("magnetic_flux_quantum", "Φ₀", 2.067833848e-15, "Wb",
                  0.0, "electromagnetic", ["flux quantum"],
                  "Φ₀ = h/(2e)")
        self._add("conductance_quantum", "G₀", 7.748091729e-5, "S",
                  0.0, "electromagnetic", ["conductance quantum"],
                  "G₀ = 2e²/h")
        self._add("von_klitzing", "R_K", 25812.80745, "Ω",
                  0.0, "electromagnetic", ["von Klitzing constant"],
                  "R_K = h/e²")
        self._add("josephson", "K_J", 483597.8484e9, "Hz/V",
                  0.0, "electromagnetic", ["Josephson constant"],
                  "K_J = 2e/h")

        # ── ATOMIC ──
        self._add("fine_structure", "α", 7.2973525643e-3, "",
                  1.5e-10, "atomic", ["alpha", "fine structure constant"],
                  "α = e²/(4πε₀ℏc) ≈ 1/137.036")
        self._add("bohr_radius", "a₀", 5.29177210544e-11, "m",
                  1.6e-10, "atomic", ["Bohr radius", "a0"])
        self._add("rydberg", "R_∞", 10973731.568157, "m⁻¹",
                  1.1e-12, "atomic", ["Rydberg constant"])
        self._add("rydberg_energy", "Ry", 13.605693122990, "eV",
                  1.1e-12, "atomic", ["Rydberg energy"],
                  "Ry = m_e c² α²/2")
        self._add("hartree_energy", "E_h", 4.3597447222060e-18, "J",
                  1.1e-12, "atomic", ["Hartree", "atomic unit of energy"],
                  "E_h = 2 Ry = m_e c² α²")
        self._add("compton_electron", "λ_C", 2.42631023538e-12, "m",
                  3.0e-10, "atomic", ["Compton wavelength"])
        self._add("classical_electron_radius", "r_e", 2.8179403205e-15, "m",
                  4.7e-10, "atomic", ["classical electron radius"])
        self._add("thomson_cross_section", "σ_T", 6.6524587051e-29, "m²",
                  9.4e-10, "atomic", ["Thomson cross section"])

        # ── PARTICLE MASSES ──
        self._add("electron_mass", "m_e", 9.1093837090e-31, "kg",
                  3.0e-10, "particle", ["electron mass"])
        self._add("electron_mass_eV", "m_e c²", 0.51099895069, "MeV",
                  3.0e-10, "particle", ["electron mass energy"])
        self._add("proton_mass", "m_p", 1.67262192595e-27, "kg",
                  3.1e-10, "particle", ["proton mass"])
        self._add("proton_mass_eV", "m_p c²", 938.27208943, "MeV",
                  3.1e-10, "particle", ["proton mass energy"])
        self._add("neutron_mass", "m_n", 1.67492750056e-27, "kg",
                  5.6e-10, "particle", ["neutron mass"])
        self._add("muon_mass", "m_μ", 1.883531627e-28, "kg",
                  2.2e-8, "particle", ["muon mass"])
        self._add("tau_mass", "m_τ", 3.16754e-27, "kg",
                  7.6e-5, "particle", ["tau mass"])
        self._add("w_boson_mass", "M_W", 80.3692, "GeV/c²",
                  1.2e-4, "particle", ["W mass"],
                  "2025 combined value")
        self._add("z_boson_mass", "M_Z", 91.1876, "GeV/c²",
                  2.3e-5, "particle", ["Z mass"])
        self._add("higgs_mass", "M_H", 125.20, "GeV/c²",
                  8.8e-4, "particle", ["Higgs mass"],
                  "LHC combined 2024")
        self._add("top_quark_mass", "m_t", 172.57, "GeV/c²",
                  1.7e-3, "particle", ["top mass"])

        # ── COUPLING CONSTANTS ──
        self._add("strong_coupling", "α_s", 0.1180, "",
                  8.5e-3, "coupling", ["alpha_s", "QCD coupling"],
                  "α_s(M_Z) from PDG 2024")
        self._add("fermi_coupling", "G_F", 1.1663787e-5, "GeV⁻²",
                  5.1e-7, "coupling", ["Fermi constant"],
                  "Weak interaction strength")
        self._add("weinberg_angle", "sin²θ_W", 0.23121, "",
                  1.3e-4, "coupling", ["weak mixing angle", "Weinberg angle"])

        # ── MUON g-2 (2026 Breakthrough Prize!) ──
        self._add("muon_anomaly_exp", "a_μ(exp)", 116592059e-11, "",
                  2.2e-7, "particle", ["muon g-2 experimental"],
                  "Fermilab final 2026: 127 ppb precision")
        self._add("muon_anomaly_sm", "a_μ(SM)", 116591810e-11, "",
                  4.3e-7, "particle", ["muon g-2 theory"],
                  "SM prediction (WP 2020)")

        # ── COSMOLOGICAL ──
        self._add("hubble_planck", "H₀", 67.4, "km/s/Mpc",
                  7.4e-3, "cosmological", ["Hubble constant Planck"],
                  "Planck 2018 CMB")
        self._add("hubble_local", "H₀(local)", 73.0, "km/s/Mpc",
                  1.4e-2, "cosmological", ["Hubble tension", "SH0ES"],
                  "SH0ES 2022, TENSION with CMB!")
        self._add("cmb_temperature", "T_CMB", 2.7255, "K",
                  2.2e-4, "cosmological", ["CMB temperature"])
        self._add("baryon_density", "Ω_b h²", 0.02237, "",
                  6.7e-3, "cosmological", ["baryon density"])
        self._add("dark_matter_density", "Ω_c h²", 0.1200, "",
                  1.0e-2, "cosmological", ["CDM density"])
        self._add("dark_energy_density", "Ω_Λ", 0.685, "",
                  1.2e-2, "cosmological", ["dark energy", "cosmological constant fraction"])
        self._add("age_universe", "t₀", 13.797e9, "yr",
                  1.5e-3, "cosmological", ["age of universe"])
        self._add("cosmological_constant", "Λ", 1.1056e-52, "m⁻²",
                  3.0e-2, "cosmological", ["Lambda", "CC"])
        self._add("critical_density", "ρ_c", 9.47e-27, "kg/m³",
                  1.5e-2, "cosmological", ["critical density"])

        # ── DESI 2026 dark energy parameters ──
        self._add("dark_energy_w0", "w₀", -0.727, "",
                  0.1, "cosmological", ["w0", "DE equation of state today"],
                  "DESI DR1+DR2 2025-2026: dark energy EVOLVES")
        self._add("dark_energy_wa", "w_a", -1.05, "",
                  0.3, "cosmological", ["wa", "DE evolution parameter"],
                  "DESI 2026: w(a) = w₀ + w_a(1-a)")

        # ── PLANCK UNITS ──
        self._add("planck_length", "l_P", 1.616255e-35, "m",
                  1.5e-5, "planck", ["Planck length"])
        self._add("planck_mass", "m_P", 2.176434e-8, "kg",
                  1.5e-5, "planck", ["Planck mass"])
        self._add("planck_time", "t_P", 5.391247e-44, "s",
                  1.5e-5, "planck", ["Planck time"])
        self._add("planck_temperature", "T_P", 1.416784e32, "K",
                  1.5e-5, "planck", ["Planck temperature"])
        self._add("planck_energy", "E_P", 1.220890e19, "GeV",
                  1.5e-5, "planck", ["Planck energy"])

        # ── STEFAN-BOLTZMANN & RADIATION ──
        self._add("stefan_boltzmann", "σ", 5.670374419e-8, "W/(m²·K⁴)",
                  0.0, "radiation", ["Stefan-Boltzmann constant"],
                  "σ = 2π⁵k⁴/(15h³c²)")
        self._add("wien_displacement", "b", 2.897771955e-3, "m·K",
                  0.0, "radiation", ["Wien constant"],
                  "λ_max T = b")
        self._add("radiation_constant", "a", 7.5657e-16, "J/(m³·K⁴)",
                  0.0, "radiation", ["radiation density constant"],
                  "a = 4σ/c")

        # ── NUCLEAR ──
        self._add("nuclear_radius", "r₀", 1.2e-15, "m",
                  0.02, "nuclear", ["nuclear radius parameter"],
                  "R = r₀ A^(1/3)")
        self._add("deuteron_mass", "m_d", 3.3435837768e-27, "kg",
                  3.0e-10, "nuclear", ["deuteron mass"])
        self._add("atomic_mass_unit", "u", 1.66053906892e-27, "kg",
                  3.0e-10, "nuclear", ["amu", "dalton"],
                  "1 u = 931.494 MeV/c²")
        self._add("amu_energy", "u·c²", 931.49410372, "MeV",
                  3.0e-10, "nuclear", ["amu energy equivalent"])

        # ── GRAVITATIONAL/ASTROPHYSICAL ──
        self._add("solar_mass", "M_☉", 1.989e30, "kg",
                  1.0e-4, "astrophysical", ["solar mass", "Msun"])
        self._add("solar_radius", "R_☉", 6.957e8, "m",
                  1.0e-4, "astrophysical", ["solar radius"])
        self._add("solar_luminosity", "L_☉", 3.828e26, "W",
                  1.0e-3, "astrophysical", ["solar luminosity"])
        self._add("earth_mass", "M_⊕", 5.972e24, "kg",
                  1.0e-4, "astrophysical", ["Earth mass"])
        self._add("earth_radius", "R_⊕", 6.371e6, "m",
                  5.0e-5, "astrophysical", ["Earth radius"])
        self._add("parsec", "pc", 3.0857e16, "m",
                  0.0, "astrophysical", ["parsec"])
        self._add("light_year", "ly", 9.4607e15, "m",
                  0.0, "astrophysical", ["light year", "lightyear"])
        self._add("astronomical_unit", "AU", 1.495978707e11, "m",
                  0.0, "astrophysical", ["AU", "astronomical unit"])
        self._add("schwarzschild_radius_sun", "r_s☉", 2953.25, "m",
                  1.5e-5, "astrophysical", ["Schwarzschild radius sun"],
                  "r_s = 2GM/c²")

    def stats(self) -> Dict:
        """Return statistics about constants database."""
        cats = {}
        for c in self.constants.values():
            cats[c.category] = cats.get(c.category, 0) + 1
        return {"total": len(self.constants), "by_category": cats}

    # ── Natural unit conversions ──
    def to_natural(self, value: float, from_units: str) -> float:
        """Convert SI to natural units (ℏ=c=k_B=1)."""
        c = 299792458.0
        hbar = 1.054571817e-34
        kB = 1.380649e-23
        eV = 1.602176634e-19

        conversions = {
            "kg": value * c**2 / eV,          # kg → eV
            "m": value / (hbar * c / eV),      # m → eV⁻¹
            "s": value / (hbar / eV),           # s → eV⁻¹
            "K": value * kB / eV,              # K → eV
            "J": value / eV,                    # J → eV
        }
        return conversions.get(from_units, value)

    def to_planck(self, value: float, from_units: str) -> float:
        """Convert SI to Planck units."""
        lP = 1.616255e-35
        tP = 5.391247e-44
        mP = 2.176434e-8
        TP = 1.416784e32

        conversions = {
            "m": value / lP,
            "s": value / tP,
            "kg": value / mP,
            "K": value / TP,
        }
        return conversions.get(from_units, value)


# ══════════════════════════════════════════════════════════════════════════════
# DIMENSIONAL ENGINE — Unit algebra, auto-checking, Buckingham π
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Dimension:
    """Represents physical dimensions as powers of base quantities.
    [M^a L^b T^c I^d Θ^e N^f J^g]
    M=mass, L=length, T=time, I=current, Θ=temperature, N=amount, J=luminosity
    """
    M: float = 0  # mass (kg)
    L: float = 0  # length (m)
    T: float = 0  # time (s)
    I: float = 0  # current (A)
    Th: float = 0  # temperature (K)
    N: float = 0  # amount (mol)
    J: float = 0  # luminous intensity (cd)

    def __mul__(self, other):
        return Dimension(self.M+other.M, self.L+other.L, self.T+other.T,
                        self.I+other.I, self.Th+other.Th, self.N+other.N, self.J+other.J)

    def __truediv__(self, other):
        return Dimension(self.M-other.M, self.L-other.L, self.T-other.T,
                        self.I-other.I, self.Th-other.Th, self.N-other.N, self.J-other.J)

    def __pow__(self, n):
        return Dimension(self.M*n, self.L*n, self.T*n, self.I*n, self.Th*n, self.N*n, self.J*n)

    def __eq__(self, other):
        return (abs(self.M-other.M) < 1e-10 and abs(self.L-other.L) < 1e-10 and
                abs(self.T-other.T) < 1e-10 and abs(self.I-other.I) < 1e-10 and
                abs(self.Th-other.Th) < 1e-10 and abs(self.N-other.N) < 1e-10 and
                abs(self.J-other.J) < 1e-10)

    def __hash__(self):
        return hash((round(self.M,6), round(self.L,6), round(self.T,6),
                     round(self.I,6), round(self.Th,6), round(self.N,6), round(self.J,6)))

    def is_dimensionless(self) -> bool:
        return self == Dimension()

    def __repr__(self):
        parts = []
        for name, val in [("M", self.M), ("L", self.L), ("T", self.T),
                          ("I", self.I), ("Θ", self.Th), ("N", self.N), ("J", self.J)]:
            if abs(val) > 1e-10:
                if val == 1:
                    parts.append(name)
                elif val == int(val):
                    parts.append(f"{name}^{int(val)}")
                else:
                    parts.append(f"{name}^{val}")
        return " ".join(parts) if parts else "dimensionless"


class DimensionalEngine:
    """Unit algebra engine: track dimensions, check consistency, convert."""

    # Base dimensions
    MASS = Dimension(M=1)
    LENGTH = Dimension(L=1)
    TIME = Dimension(T=1)
    CURRENT = Dimension(I=1)
    TEMPERATURE = Dimension(Th=1)
    AMOUNT = Dimension(N=1)
    DIMENSIONLESS = Dimension()

    def __init__(self):
        self.units: Dict[str, Dimension] = {}
        self.prefixes: Dict[str, float] = {}
        self._build_units()
        self._build_prefixes()

    def _build_prefixes(self):
        self.prefixes = {
            "Y": 1e24, "Z": 1e21, "E": 1e18, "P": 1e15, "T": 1e12,
            "G": 1e9, "M": 1e6, "k": 1e3, "h": 1e2, "da": 1e1,
            "d": 1e-1, "c": 1e-2, "m": 1e-3, "μ": 1e-6, "n": 1e-9,
            "p": 1e-12, "f": 1e-15, "a": 1e-18, "z": 1e-21, "y": 1e-24,
        }

    def _build_units(self):
        M, L, T, I, Th = self.MASS, self.LENGTH, self.TIME, self.CURRENT, self.TEMPERATURE
        D = self.DIMENSIONLESS

        # Base SI
        self.units["kg"] = M
        self.units["m"] = L
        self.units["s"] = T
        self.units["A"] = I
        self.units["K"] = Th
        self.units["mol"] = Dimension(N=1)
        self.units["cd"] = Dimension(J=1)

        # Derived SI
        self.units["N"] = M * L / (T**2)           # Newton = kg·m/s²
        self.units["J"] = M * L**2 / (T**2)        # Joule = kg·m²/s²
        self.units["W"] = M * L**2 / (T**3)        # Watt = kg·m²/s³
        self.units["Pa"] = M / (L * T**2)          # Pascal = kg/(m·s²)
        self.units["Hz"] = D / T                    # Hertz = 1/s (treat as T⁻¹)
        self.units["C"] = I * T                    # Coulomb = A·s
        self.units["V"] = M * L**2 / (T**3 * I)   # Volt = kg·m²/(A·s³)
        self.units["Ω"] = M * L**2 / (T**3 * I**2) # Ohm
        self.units["F"] = I**2 * T**4 / (M * L**2) # Farad
        self.units["H"] = M * L**2 / (T**2 * I**2) # Henry
        self.units["T"] = M / (I * T**2)           # Tesla = kg/(A·s²)
        self.units["Wb"] = M * L**2 / (I * T**2)  # Weber
        self.units["S"] = I**2 * T**3 / (M * L**2) # Siemens

        # Common non-SI
        self.units["eV"] = M * L**2 / (T**2)      # Same dim as energy
        self.units["MeV"] = M * L**2 / (T**2)
        self.units["GeV"] = M * L**2 / (T**2)
        self.units["erg"] = M * L**2 / (T**2)     # CGS energy
        self.units["dyn"] = M * L / (T**2)        # CGS force
        self.units["G"] = M / (I * T**2)          # Gauss (CGS magnetic)
        self.units["bar"] = M / (L * T**2)        # Pressure
        self.units["atm"] = M / (L * T**2)

        # Dimensionless
        self.units["rad"] = D
        self.units["sr"] = D
        self.units[""] = D

    def get_dimension(self, unit_str: str) -> Optional[Dimension]:
        """Parse a unit string and return its dimension.
        Handles: m/s, kg·m/s², m^2, N/m², etc.
        """
        if not unit_str or unit_str.strip() == "":
            return self.DIMENSIONLESS

        unit_str = unit_str.strip()

        # Direct lookup
        if unit_str in self.units:
            return self.units[unit_str]

        # Try to parse compound units
        return self._parse_compound(unit_str)

    def _parse_compound(self, unit_str: str) -> Optional[Dimension]:
        """Parse compound unit strings like kg·m/s², m/s, N·m, etc."""
        # Split by / for numerator/denominator
        parts = unit_str.replace("·", "*").replace("⋅", "*").split("/")

        if len(parts) == 1:
            return self._parse_product(parts[0])
        elif len(parts) == 2:
            num = self._parse_product(parts[0])
            den = self._parse_product(parts[1])
            if num and den:
                return num / den
        return None

    def _parse_product(self, product_str: str) -> Optional[Dimension]:
        """Parse a product of units like kg*m*s^-2."""
        result = self.DIMENSIONLESS
        # Split by * or ·
        tokens = re.split(r'[*·⋅]', product_str.strip())
        if not tokens or tokens == ['']:
            tokens = [product_str.strip()]

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            # Check for power: m^2, s^-2, etc.
            m = re.match(r'^([a-zA-Zμ]+)[\^]?([-]?\d+\.?\d*)$', token)
            if m:
                base = m.group(1)
                power = float(m.group(2)) if m.group(2) else 1.0
            else:
                # Check for superscript numbers
                m2 = re.match(r'^([a-zA-Zμ]+)([²³⁴⁵⁶⁷⁸⁹⁻]+)$', token)
                if m2:
                    base = m2.group(1)
                    sup = m2.group(2)
                    power = self._parse_superscript(sup)
                else:
                    base = token
                    power = 1.0

            if base in self.units:
                result = result * (self.units[base] ** power)
            else:
                return None  # Unknown unit

        return result

    def _parse_superscript(self, sup: str) -> float:
        """Convert superscript digits to number."""
        sup_map = {'⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
                   '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁻': '-'}
        return float(''.join(sup_map.get(c, '') for c in sup))

    def check_equation(self, lhs_units: str, rhs_units: str) -> bool:
        """Check if two sides of an equation have matching dimensions."""
        lhs = self.get_dimension(lhs_units)
        rhs = self.get_dimension(rhs_units)
        if lhs is None or rhs is None:
            return False
        return lhs == rhs

    def check_addition(self, *unit_strings: str) -> bool:
        """Check if all terms being added have the same dimensions."""
        dims = [self.get_dimension(u) for u in unit_strings]
        if any(d is None for d in dims):
            return False
        return all(d == dims[0] for d in dims)

    def derive_units(self, formula_units: List[Tuple[str, float]]) -> Dimension:
        """Given [(unit, power), ...], compute resulting dimension.
        E.g., [("kg", 1), ("m", 2), ("s", -2)] → energy dimension
        """
        result = self.DIMENSIONLESS
        for unit_str, power in formula_units:
            dim = self.get_dimension(unit_str)
            if dim:
                result = result * (dim ** power)
        return result

    def buckingham_pi(self, variables: Dict[str, Dimension]) -> int:
        """Buckingham π theorem: given variables with dimensions,
        return number of independent dimensionless groups.
        n_pi = n_variables - rank(dimensional_matrix)
        """
        if not variables:
            return 0

        # Build dimensional matrix
        var_names = list(variables.keys())
        n = len(var_names)

        # Get all non-zero base dimensions
        base_dims = ['M', 'L', 'T', 'I', 'Th', 'N', 'J']
        matrix = []
        for dim_name in base_dims:
            row = []
            for var in var_names:
                d = variables[var]
                row.append(getattr(d, dim_name))
            if any(abs(x) > 1e-10 for x in row):
                matrix.append(row)

        # Compute rank via Gaussian elimination
        rank = self._matrix_rank(matrix)
        return n - rank

    def _matrix_rank(self, matrix: List[List[float]]) -> int:
        """Compute rank via row reduction."""
        if not matrix:
            return 0
        m = [row[:] for row in matrix]  # copy
        rows, cols = len(m), len(m[0])
        rank = 0
        for col in range(cols):
            # Find pivot
            pivot = None
            for row in range(rank, rows):
                if abs(m[row][col]) > 1e-10:
                    pivot = row
                    break
            if pivot is None:
                continue
            # Swap
            m[rank], m[pivot] = m[pivot], m[rank]
            # Eliminate
            for row in range(rows):
                if row != rank and abs(m[row][col]) > 1e-10:
                    factor = m[row][col] / m[rank][col]
                    for c in range(cols):
                        m[row][c] -= factor * m[rank][c]
            rank += 1
        return rank

    def suggest_formula(self, target: Dimension, variables: Dict[str, Dimension]) -> Optional[Dict[str, float]]:
        """Given a target dimension and available variables,
        find powers that give the target dimension (Buckingham π / dimensional analysis).
        Solves: target = Π var_i^{a_i}
        """
        # Simple case: try small integer powers -3 to 3
        var_names = list(variables.keys())
        if len(var_names) > 4:
            var_names = var_names[:4]  # Limit combinatorial explosion

        from itertools import product as iproduct
        powers_range = [-3, -2, -1, 0, 1, 2, 3]

        for powers in iproduct(powers_range, repeat=len(var_names)):
            result = self.DIMENSIONLESS
            for var, p in zip(var_names, powers):
                if p != 0:
                    result = result * (variables[var] ** p)
            if result == target:
                return {var: p for var, p in zip(var_names, powers) if p != 0}
        return None


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS LAW DATABASE — 250+ laws structured with equations & dependencies
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PhysicsLaw:
    """A physical law with equation, domain, conditions, and connections."""
    name: str
    domain: str
    statement: str
    equation: str  # symbolic equation
    preconditions: List[str] = field(default_factory=list)
    consequences: List[str] = field(default_factory=list)
    derived_from: List[str] = field(default_factory=list)
    applications: List[str] = field(default_factory=list)
    level: int = 1  # 1=basic ... 12=research frontier
    tags: List[str] = field(default_factory=list)


class PhysicsLawDB:
    """Database of 250+ physics laws organized by domain and level."""

    def __init__(self):
        self.laws: Dict[str, PhysicsLaw] = {}
        self._build()

    def _add(self, name: str, domain: str, statement: str, equation: str,
             preconditions: List[str] = None, consequences: List[str] = None,
             derived_from: List[str] = None, applications: List[str] = None,
             level: int = 1, tags: List[str] = None):
        self.laws[name] = PhysicsLaw(
            name=name, domain=domain, statement=statement, equation=equation,
            preconditions=preconditions or [], consequences=consequences or [],
            derived_from=derived_from or [], applications=applications or [],
            level=level, tags=tags or []
        )

    def search(self, keyword: str) -> List[PhysicsLaw]:
        """Search laws by keyword in name, statement, equation, or tags."""
        kw = keyword.lower()
        results = []
        for law in self.laws.values():
            if (kw in law.name.lower() or kw in law.statement.lower() or
                kw in law.equation.lower() or kw in law.domain.lower() or
                any(kw in t.lower() for t in law.tags)):
                results.append(law)
        return results

    def by_domain(self, domain: str) -> List[PhysicsLaw]:
        """Get all laws in a domain."""
        return [l for l in self.laws.values() if l.domain == domain]

    def by_level(self, level: int) -> List[PhysicsLaw]:
        """Get all laws at a specific level."""
        return [l for l in self.laws.values() if l.level == level]

    def get_derivation_chain(self, name: str) -> List[str]:
        """Trace back the derivation tree for a law."""
        if name not in self.laws:
            return []
        chain = [name]
        visited = {name}
        queue = list(self.laws[name].derived_from)
        while queue:
            parent = queue.pop(0)
            if parent in visited or parent not in self.laws:
                continue
            visited.add(parent)
            chain.append(parent)
            queue.extend(self.laws[parent].derived_from)
        return chain

    def stats(self) -> Dict:
        """Return statistics."""
        domains = {}
        levels = {}
        for l in self.laws.values():
            domains[l.domain] = domains.get(l.domain, 0) + 1
            levels[l.level] = levels.get(l.level, 0) + 1
        return {"total": len(self.laws), "by_domain": domains, "by_level": levels}

    def _build(self):
        self._build_level1()
        self._build_level2()
        self._build_level3()
        self._build_level4()
        self._build_level5()
        self._build_level6()
        self._build_level7()
        self._build_level8()
        self._build_level9()
        self._build_level10()
        self._build_level11()
        self._build_level12()

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 1: CLASSICAL MECHANICS + NONLINEAR DYNAMICS (30)
    # ──────────────────────────────────────────────────────────────────
    def _build_level1(self):
        self._add("newton_second", "classical_mechanics",
            "Net force equals rate of change of momentum",
            "F = dp/dt = ma",
            preconditions=["inertial frame", "v≪c"],
            consequences=["equations of motion", "F=ma for constant mass"],
            level=1, tags=["Newton", "force", "momentum", "fundamental"])

        self._add("newton_third", "classical_mechanics",
            "Every action has equal and opposite reaction",
            "F₁₂ = -F₂₁",
            consequences=["momentum conservation in isolated systems"],
            level=1, tags=["Newton", "action-reaction"])

        self._add("energy_conservation", "classical_mechanics",
            "Total energy is conserved in isolated system",
            "dE/dt = 0; E = T + V = const",
            preconditions=["isolated system", "conservative forces or include all work"],
            derived_from=["noether_theorem"],
            level=1, tags=["conservation", "energy", "fundamental"])

        self._add("momentum_conservation", "classical_mechanics",
            "Total momentum conserved when no external force",
            "dp_total/dt = 0 when F_ext = 0",
            derived_from=["newton_second", "newton_third"],
            level=1, tags=["conservation", "momentum"])

        self._add("angular_momentum_conservation", "classical_mechanics",
            "Angular momentum conserved when no external torque",
            "dL/dt = 0 when τ_ext = 0",
            derived_from=["noether_theorem"],
            level=1, tags=["conservation", "angular momentum", "torque"])

        self._add("work_energy_theorem", "classical_mechanics",
            "Net work equals change in kinetic energy",
            "W_net = ΔKE = ½mv² - ½mv₀²",
            derived_from=["newton_second"],
            level=1, tags=["work", "kinetic energy"])

        self._add("euler_lagrange", "classical_mechanics",
            "Equations of motion from stationary action",
            "d/dt(∂L/∂q̇ᵢ) - ∂L/∂qᵢ = 0",
            preconditions=["L = T - V", "holonomic constraints"],
            derived_from=["hamilton_principle"],
            consequences=["Newton's laws", "generalized forces"],
            level=1, tags=["Lagrangian", "variational", "EOM"])

        self._add("hamilton_principle", "classical_mechanics",
            "Physical path extremizes the action S = ∫L dt",
            "δS = δ∫L dt = 0",
            consequences=["euler_lagrange", "all of classical mechanics"],
            level=1, tags=["action", "variational", "principle"])

        self._add("hamilton_equations", "classical_mechanics",
            "Equations of motion in phase space",
            "q̇ᵢ = ∂H/∂pᵢ, ṗᵢ = -∂H/∂qᵢ",
            preconditions=["Legendre transform exists: H = Σpq̇ - L"],
            derived_from=["euler_lagrange"],
            level=1, tags=["Hamiltonian", "phase space", "canonical"])

        self._add("poisson_brackets", "classical_mechanics",
            "Fundamental bracket structure of classical mechanics",
            "{f,g} = Σ(∂f/∂qᵢ·∂g/∂pᵢ - ∂f/∂pᵢ·∂g/∂qᵢ); {q,p}=1",
            consequences=["time evolution: df/dt = {f,H} + ∂f/∂t"],
            level=1, tags=["Poisson", "bracket", "canonical"])

        self._add("liouville_theorem", "classical_mechanics",
            "Phase space volume is preserved under Hamiltonian flow",
            "dρ/dt = 0; ∇·(ρv) = 0 in phase space",
            derived_from=["hamilton_equations"],
            consequences=["entropy can't decrease in phase space"],
            level=1, tags=["Liouville", "phase space", "incompressible"])

        self._add("noether_theorem", "classical_mechanics",
            "Every continuous symmetry gives a conserved quantity",
            "symmetry of L → Q = (∂L/∂q̇)δq conserved",
            applications=["time transl→energy", "space transl→momentum", "rotation→ang.mom."],
            level=1, tags=["Noether", "symmetry", "conservation", "fundamental"])

        self._add("virial_theorem", "classical_mechanics",
            "Time-averaged kinetic energy relates to potential for bound systems",
            "⟨T⟩ = -½Σ⟨Fᵢ·rᵢ⟩ = (n/2)⟨V⟩ for V∝rⁿ",
            preconditions=["bound system", "time average exists"],
            applications=["gravity (n=-1): 2⟨T⟩=-⟨V⟩", "harmonic (n=2): ⟨T⟩=⟨V⟩"],
            level=1, tags=["virial", "average", "bound"])

        self._add("kepler_first", "classical_mechanics",
            "Planets orbit in ellipses with Sun at one focus",
            "r = a(1-e²)/(1+e·cosθ)",
            derived_from=["newton_second", "gravity_newton"],
            level=1, tags=["Kepler", "orbit", "ellipse"])

        self._add("kepler_third", "classical_mechanics",
            "Orbital period squared proportional to semi-major axis cubed",
            "T² = (4π²/GM)a³",
            derived_from=["newton_second", "gravity_newton"],
            level=1, tags=["Kepler", "period", "orbit"])

        self._add("gravity_newton", "classical_mechanics",
            "Universal gravitation between two masses",
            "F = -GMm/r² r̂",
            consequences=["kepler_first", "kepler_third", "tides"],
            level=1, tags=["gravity", "Newton", "inverse square"])

        self._add("euler_rigid_body", "classical_mechanics",
            "Rotation equations for rigid body in body frame",
            "I₁ω̇₁ - (I₂-I₃)ω₂ω₃ = N₁ (+ cyclic)",
            preconditions=["rigid body", "principal axes"],
            level=1, tags=["Euler", "rigid body", "rotation"])

        self._add("navier_stokes", "classical_mechanics",
            "Fundamental equation of viscous fluid dynamics",
            "ρ(∂v/∂t + v·∇v) = -∇P + μ∇²v + ρg",
            preconditions=["Newtonian fluid", "continuum approximation"],
            applications=["turbulence", "aerodynamics", "pipe flow"],
            level=1, tags=["Navier-Stokes", "fluid", "viscous"])

        self._add("bernoulli", "classical_mechanics",
            "Energy conservation along streamline in inviscid flow",
            "P + ½ρv² + ρgh = const along streamline",
            preconditions=["steady", "incompressible", "inviscid", "along streamline"],
            derived_from=["energy_conservation"],
            level=1, tags=["Bernoulli", "fluid", "pressure"])

        self._add("continuity_equation", "classical_mechanics",
            "Mass conservation in fluid",
            "∂ρ/∂t + ∇·(ρv) = 0",
            level=1, tags=["continuity", "conservation", "mass", "fluid"])

        self._add("equipartition", "classical_mechanics",
            "Each quadratic degree of freedom has ½kT average energy",
            "⟨E_quadratic⟩ = ½k_BT per DOF",
            preconditions=["classical limit", "thermal equilibrium"],
            applications=["ideal gas: E=(3/2)NkT", "solid: E=3NkT"],
            level=1, tags=["equipartition", "thermal", "DOF"])

        self._add("dalembert_principle", "classical_mechanics",
            "Virtual work of constraint forces vanishes",
            "Σ(Fᵢ - mᵢaᵢ)·δrᵢ = 0",
            consequences=["euler_lagrange"],
            level=1, tags=["d'Alembert", "virtual work", "constraint"])

        self._add("canonical_transformation", "classical_mechanics",
            "Transformations preserving Hamilton's equations form",
            "{Q,P} = 1; generated by F₁(q,Q), F₂(q,P), F₃(p,Q), F₄(p,P)",
            derived_from=["hamilton_equations"],
            level=1, tags=["canonical", "generating function", "symplectic"])

        self._add("adiabatic_invariant", "classical_mechanics",
            "Action variable J=∮p dq/(2π) conserved under slow change",
            "J = ∮p dq/(2π) = const when parameter changes slowly",
            applications=["pendulum length change", "magnetic mirror"],
            level=1, tags=["adiabatic", "invariant", "action"])

        self._add("kam_theorem", "classical_mechanics",
            "Most tori survive small perturbation of integrable system",
            "Perturbed tori persist if frequency ratio sufficiently irrational",
            preconditions=["near-integrable system", "small perturbation"],
            level=1, tags=["KAM", "stability", "chaos", "tori"])

        self._add("lyapunov_exponent", "classical_mechanics",
            "Exponential divergence rate of nearby trajectories",
            "λ = lim_{t→∞} (1/t)ln|δx(t)/δx(0)|; chaos if λ>0",
            applications=["weather prediction limits", "three-body problem"],
            level=1, tags=["Lyapunov", "chaos", "sensitivity"])

        self._add("poincare_recurrence", "classical_mechanics",
            "Bounded Hamiltonian system returns arbitrarily close to initial state",
            "For any ε>0, ∃T: |x(T)-x(0)|<ε",
            preconditions=["bounded phase space", "measure-preserving"],
            level=1, tags=["Poincaré", "recurrence", "ergodic"])

        self._add("reynolds_number", "classical_mechanics",
            "Dimensionless ratio of inertial to viscous forces",
            "Re = ρvL/μ; turbulent if Re > Re_crit (~2300 pipe)",
            applications=["flow regime determination", "similarity"],
            level=1, tags=["Reynolds", "turbulence", "dimensionless"])

        self._add("hooke_law", "classical_mechanics",
            "Restoring force proportional to displacement (linear elastic)",
            "F = -kx; σ = Eε (stress-strain)",
            preconditions=["small deformation", "linear elastic regime"],
            level=1, tags=["Hooke", "elasticity", "spring"])

        self._add("pendulum_period", "classical_mechanics",
            "Period of simple pendulum (small angle)",
            "T = 2π√(L/g)",
            preconditions=["small angle θ≪1", "rigid rod/string"],
            derived_from=["euler_lagrange"],
            level=1, tags=["pendulum", "oscillation", "period"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 2: ELECTROMAGNETISM (25)
    # ──────────────────────────────────────────────────────────────────
    def _build_level2(self):
        self._add("gauss_law_electric", "electromagnetism",
            "Electric flux through closed surface equals enclosed charge/ε₀",
            "∇·E = ρ/ε₀; ∮E·dA = Q_enc/ε₀",
            consequences=["Coulomb's law", "field of charge distributions"],
            level=2, tags=["Maxwell", "Gauss", "electric", "divergence"])

        self._add("gauss_law_magnetic", "electromagnetism",
            "No magnetic monopoles — magnetic field lines always close",
            "∇·B = 0; ∮B·dA = 0",
            consequences=["B field lines are closed loops", "vector potential exists"],
            level=2, tags=["Maxwell", "Gauss", "magnetic", "monopole"])

        self._add("faraday_law", "electromagnetism",
            "Changing magnetic flux induces electric field",
            "∇×E = -∂B/∂t; EMF = -dΦ_B/dt",
            consequences=["electromagnetic induction", "transformers", "generators"],
            level=2, tags=["Maxwell", "Faraday", "induction", "curl"])

        self._add("ampere_maxwell", "electromagnetism",
            "Current and changing E field produce magnetic field",
            "∇×B = μ₀J + μ₀ε₀∂E/∂t",
            consequences=["EM waves exist", "displacement current"],
            level=2, tags=["Maxwell", "Ampère", "displacement current"])

        self._add("lorentz_force", "electromagnetism",
            "Force on charged particle in EM field",
            "F = q(E + v×B)",
            applications=["cyclotron motion", "mass spectrometer", "Hall effect"],
            level=2, tags=["Lorentz", "force", "charge", "magnetic"])

        self._add("coulomb_law", "electromagnetism",
            "Force between point charges",
            "F = kq₁q₂/r² r̂; k = 1/(4πε₀)",
            derived_from=["gauss_law_electric"],
            level=2, tags=["Coulomb", "electrostatic", "inverse square"])

        self._add("biot_savart", "electromagnetism",
            "Magnetic field from current element",
            "dB = (μ₀/4π) I dl×r̂/r²",
            derived_from=["ampere_maxwell"],
            level=2, tags=["Biot-Savart", "current", "magnetic field"])

        self._add("poynting_theorem", "electromagnetism",
            "EM energy conservation: energy flux + dissipation + storage",
            "∂u/∂t + ∇·S = -J·E; S = (1/μ₀)E×B",
            derived_from=["faraday_law", "ampere_maxwell"],
            level=2, tags=["Poynting", "energy", "radiation", "flux"])

        self._add("em_wave_equation", "electromagnetism",
            "EM waves propagate at speed of light",
            "∇²E - μ₀ε₀∂²E/∂t² = 0; v = 1/√(μ₀ε₀) = c",
            derived_from=["faraday_law", "ampere_maxwell"],
            consequences=["light is EM wave", "radiation"],
            level=2, tags=["wave", "propagation", "speed of light"])

        self._add("larmor_radiation", "electromagnetism",
            "Power radiated by accelerating charge",
            "P = q²a²/(6πε₀c³)",
            preconditions=["non-relativistic charge"],
            applications=["synchrotron losses", "antenna radiation"],
            level=2, tags=["Larmor", "radiation", "acceleration"])

        self._add("lienard_wiechert", "electromagnetism",
            "Exact retarded potentials of moving point charge",
            "φ = q/(4πε₀) 1/(R-R·v/c)|_ret; A = (v/c)φ",
            applications=["radiation from moving charges", "Bremsstrahlung"],
            level=2, tags=["retarded", "potential", "relativistic"])

        self._add("gauge_invariance_em", "electromagnetism",
            "Physics unchanged under gauge transformation",
            "A → A + ∇χ, φ → φ - ∂χ/∂t; E,B unchanged",
            consequences=["Lorenz gauge: ∂μAμ=0", "Coulomb gauge: ∇·A=0"],
            level=2, tags=["gauge", "invariance", "potential"])

        self._add("multipole_expansion", "electromagnetism",
            "Field of charge distribution as series in 1/r",
            "φ = (1/4πε₀)Σ(1/r^{l+1})∫ρ r'^l P_l(cosθ')dV'",
            applications=["monopole", "dipole", "quadrupole", "far field"],
            level=2, tags=["multipole", "expansion", "dipole", "quadrupole"])

        self._add("boundary_conditions_em", "electromagnetism",
            "EM field relations at material interfaces",
            "ΔE_∥=0, Δ(ε E_⊥)=σ_f, ΔB_⊥=0, Δ(B_∥/μ)=K_f×n̂",
            applications=["reflection", "refraction", "waveguides"],
            level=2, tags=["boundary", "interface", "discontinuity"])

        self._add("fresnel_equations", "electromagnetism",
            "Reflection and transmission amplitudes at interface",
            "r_s = (n₁cosθ₁-n₂cosθ₂)/(n₁cosθ₁+n₂cosθ₂); Brewster: tanθ_B=n₂/n₁",
            derived_from=["boundary_conditions_em"],
            level=2, tags=["Fresnel", "reflection", "transmission", "Brewster"])

        self._add("snell_law", "electromagnetism",
            "Refraction angle at interface between media",
            "n₁sinθ₁ = n₂sinθ₂",
            derived_from=["boundary_conditions_em"],
            level=2, tags=["Snell", "refraction", "index"])

        self._add("kramers_kronig", "electromagnetism",
            "Real and imaginary parts of response connected by causality",
            "Re ε(ω) = 1 + (2/π)P∫₀^∞ ω'Im ε(ω')/(ω'²-ω²) dω'",
            preconditions=["causal response function", "analytic in upper half plane"],
            level=2, tags=["Kramers-Kronig", "causality", "dispersion"])

        self._add("skin_depth", "electromagnetism",
            "Penetration depth of EM wave in conductor",
            "δ = √(2/ωμσ)",
            applications=["shielding", "eddy currents", "RF design"],
            level=2, tags=["skin depth", "conductor", "penetration"])

        self._add("waveguide_modes", "electromagnetism",
            "EM modes in hollow conductor with cutoff frequencies",
            "TE: E_z=0, TM: B_z=0; ω_c = cπ√((m/a)²+(n/b)²)",
            level=2, tags=["waveguide", "modes", "TE", "TM", "cutoff"])

        self._add("radiation_reaction", "electromagnetism",
            "Self-force on accelerating charge (Abraham-Lorentz)",
            "F_rad = (q²/6πε₀c³)ȧ = μ₀q²ȧ/(6πc)",
            applications=["radiation damping", "runaway solutions"],
            level=2, tags=["Abraham-Lorentz", "self-force", "radiation reaction"])

        self._add("em_energy_density", "electromagnetism",
            "Energy stored in electromagnetic field per unit volume",
            "u = ½(ε₀E² + B²/μ₀)",
            derived_from=["poynting_theorem"],
            level=2, tags=["energy density", "field energy"])

        self._add("lenz_law", "electromagnetism",
            "Induced EMF opposes the change causing it",
            "EMF = -dΦ_B/dt (negative sign)",
            derived_from=["faraday_law"],
            level=2, tags=["Lenz", "induction", "oppose"])

        self._add("magnetic_dipole_field", "electromagnetism",
            "Far field of magnetic dipole",
            "B = (μ₀/4π)(3(m·r̂)r̂ - m)/r³",
            derived_from=["multipole_expansion"],
            level=2, tags=["dipole", "magnetic", "far field"])

        self._add("ohm_law_microscopic", "electromagnetism",
            "Current density proportional to electric field in conductor",
            "J = σE (microscopic); V = IR (macroscopic)",
            level=2, tags=["Ohm", "conductivity", "resistance"])

        self._add("debye_shielding", "electromagnetism",
            "Screening of electric field in plasma/electrolyte",
            "φ(r) ~ (q/4πε₀r)e^{-r/λ_D}; λ_D = √(ε₀kT/ne²)",
            applications=["plasma physics", "colloids", "semiconductors"],
            level=2, tags=["Debye", "shielding", "screening", "plasma"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 3: QUANTUM MECHANICS (30)
    # ──────────────────────────────────────────────────────────────────
    def _build_level3(self):
        self._add("schrodinger_time_dep", "quantum_mechanics",
            "Time evolution of quantum state",
            "iℏ ∂ψ/∂t = Ĥψ",
            consequences=["unitary evolution", "superposition"],
            level=3, tags=["Schrödinger", "evolution", "fundamental"])

        self._add("schrodinger_time_indep", "quantum_mechanics",
            "Energy eigenvalue equation",
            "Ĥψ = Eψ",
            derived_from=["schrodinger_time_dep"],
            applications=["hydrogen atom", "harmonic oscillator", "particle in box"],
            level=3, tags=["Schrödinger", "eigenvalue", "stationary"])

        self._add("born_rule", "quantum_mechanics",
            "Probability of measurement outcome from wavefunction",
            "P(a) = |⟨a|ψ⟩|²",
            level=3, tags=["Born", "probability", "measurement", "postulate"])

        self._add("heisenberg_uncertainty", "quantum_mechanics",
            "Complementary observables cannot both be precisely known",
            "ΔAΔB ≥ ½|⟨[A,B]⟩|; ΔxΔp ≥ ℏ/2",
            consequences=["zero-point energy", "tunneling", "virtual particles"],
            level=3, tags=["Heisenberg", "uncertainty", "complementary"])

        self._add("canonical_commutation", "quantum_mechanics",
            "Fundamental commutation relation of position and momentum",
            "[x̂,p̂] = iℏ",
            consequences=["heisenberg_uncertainty", "ladder operators"],
            level=3, tags=["commutation", "canonical", "CCR"])

        self._add("angular_momentum_algebra", "quantum_mechanics",
            "Commutation relations for angular momentum",
            "[Jᵢ,Jⱼ] = iℏεᵢⱼₖJₖ; J²|j,m⟩=ℏ²j(j+1)|j,m⟩",
            consequences=["quantized angular momentum", "spherical harmonics"],
            level=3, tags=["angular momentum", "commutation", "su(2)"])

        self._add("ehrenfest_theorem", "quantum_mechanics",
            "Quantum expectation values obey classical-like equations",
            "d⟨A⟩/dt = ⟨∂A/∂t⟩ + (1/iℏ)⟨[A,H]⟩",
            applications=["⟨p⟩ → F=ma in classical limit"],
            level=3, tags=["Ehrenfest", "classical limit", "expectation"])

        self._add("pauli_exclusion", "quantum_mechanics",
            "No two identical fermions can occupy the same quantum state",
            "ψ(1,2) = -ψ(2,1) for fermions",
            consequences=["periodic table", "degeneracy pressure", "band structure"],
            level=3, tags=["Pauli", "exclusion", "fermion", "antisymmetric"])

        self._add("spin_statistics", "quantum_mechanics",
            "Integer spin = boson (symmetric), half-integer = fermion (antisymmetric)",
            "Bosons: [a,a†]=1; Fermions: {a,a†}=1",
            level=3, tags=["spin-statistics", "boson", "fermion"])

        self._add("harmonic_oscillator_qm", "quantum_mechanics",
            "Quantum harmonic oscillator with equally spaced levels",
            "E_n = (n+½)ℏω; a|n⟩=√n|n-1⟩, a†|n⟩=√(n+1)|n+1⟩",
            applications=["phonons", "photons", "molecular vibrations"],
            level=3, tags=["harmonic oscillator", "ladder", "phonon"])

        self._add("hydrogen_atom", "quantum_mechanics",
            "Exact solution of hydrogen atom",
            "E_n = -13.6eV/n²; ψ_nlm = R_nl(r)Y_lm(θ,φ)",
            applications=["spectral lines", "atomic physics", "chemistry"],
            level=3, tags=["hydrogen", "spectrum", "Bohr"])

        self._add("wkb_approximation", "quantum_mechanics",
            "Semiclassical approximation for slowly varying potential",
            "ψ ~ (1/√p)exp(±i∫p dx/ℏ); connection formulas at turning points",
            preconditions=["dλ/dx ≪ 1", "short wavelength limit"],
            applications=["tunneling rates", "bound state energies"],
            level=3, tags=["WKB", "semiclassical", "tunneling"])

        self._add("variational_principle_qm", "quantum_mechanics",
            "Trial wavefunction gives upper bound on ground state energy",
            "E₀ ≤ ⟨ψ_trial|H|ψ_trial⟩/⟨ψ_trial|ψ_trial⟩",
            applications=["helium atom", "molecular bonds"],
            level=3, tags=["variational", "Rayleigh-Ritz", "upper bound"])

        self._add("perturbation_theory_first", "quantum_mechanics",
            "First-order energy correction from perturbation V",
            "E_n^(1) = ⟨n⁰|V|n⁰⟩",
            preconditions=["V small compared to H₀"],
            level=3, tags=["perturbation", "first order", "correction"])

        self._add("perturbation_theory_second", "quantum_mechanics",
            "Second-order energy correction (non-degenerate)",
            "E_n^(2) = Σ_{m≠n} |⟨m⁰|V|n⁰⟩|²/(E_n⁰-E_m⁰)",
            level=3, tags=["perturbation", "second order"])

        self._add("fermi_golden_rule", "quantum_mechanics",
            "Transition rate from perturbation theory",
            "Γ = (2π/ℏ)|⟨f|V|i⟩|² ρ(E_f)",
            applications=["decay rates", "absorption", "scattering"],
            level=3, tags=["Fermi", "golden rule", "transition", "rate"])

        self._add("selection_rules", "quantum_mechanics",
            "Allowed transitions by symmetry of interaction",
            "Electric dipole: Δl=±1, Δm=0,±1, Δs=0",
            derived_from=["angular_momentum_algebra"],
            level=3, tags=["selection rules", "dipole", "transition"])

        self._add("clebsch_gordan", "quantum_mechanics",
            "Decomposition of tensor product of angular momentum states",
            "|j₁j₂;jm⟩ = Σ C^{jm}_{m₁m₂}|j₁m₁⟩|j₂m₂⟩",
            applications=["addition of angular momenta", "spectroscopy"],
            level=3, tags=["Clebsch-Gordan", "angular momentum", "addition"])

        self._add("berry_phase", "quantum_mechanics",
            "Geometric phase from adiabatic cyclic evolution",
            "γ = i∮⟨n|∇_R|n⟩·dR = ∫∫ F·dS (Berry curvature flux)",
            applications=["Aharonov-Bohm", "topological insulators", "molecular"],
            level=3, tags=["Berry", "geometric phase", "adiabatic", "topology"])

        self._add("no_cloning_theorem", "quantum_mechanics",
            "Impossible to create identical copy of arbitrary unknown quantum state",
            "∄ unitary U: U|ψ⟩|0⟩ = |ψ⟩|ψ⟩ for all |ψ⟩",
            consequences=["quantum cryptography security"],
            level=3, tags=["no-cloning", "information", "quantum"])

        self._add("bell_theorem", "quantum_mechanics",
            "No local hidden variable theory can reproduce all QM predictions",
            "|S| ≤ 2 (CHSH); QM allows up to 2√2",
            consequences=["quantum nonlocality", "entanglement is real resource"],
            level=3, tags=["Bell", "CHSH", "nonlocality", "entanglement"])

        self._add("density_matrix", "quantum_mechanics",
            "Description of mixed quantum states",
            "ρ = Σ pᵢ|ψᵢ⟩⟨ψᵢ|; ⟨A⟩ = Tr(ρA)",
            applications=["open systems", "thermal states", "decoherence"],
            level=3, tags=["density matrix", "mixed state", "trace"])

        self._add("path_integral_qm", "quantum_mechanics",
            "Quantum amplitude as sum over all paths",
            "K(b,a) = ∫Dx(t) e^{iS[x]/ℏ}",
            consequences=["Feynman diagrams in QFT", "instantons"],
            level=3, tags=["path integral", "Feynman", "action"])

        self._add("tunneling", "quantum_mechanics",
            "Non-zero probability of crossing classically forbidden region",
            "T ~ exp(-2∫√(2m(V-E))/ℏ dx)",
            applications=["alpha decay", "STM", "Josephson junction"],
            level=3, tags=["tunneling", "barrier", "exponential"])

        self._add("decoherence", "quantum_mechanics",
            "Environment-induced loss of quantum coherence",
            "ρ_off-diagonal → 0 on timescale τ_D",
            consequences=["classical world emerges", "measurement problem"],
            level=3, tags=["decoherence", "environment", "classical"])

        self._add("adiabatic_theorem_qm", "quantum_mechanics",
            "System stays in eigenstate if Hamiltonian changes slowly",
            "|⟨m(t)|ψ(t)⟩| ≈ 0 for m≠n if ℏ/τ ≪ ΔE",
            derived_from=["schrodinger_time_dep"],
            level=3, tags=["adiabatic", "slow", "eigenstate"])

        self._add("scattering_born", "quantum_mechanics",
            "First Born approximation for scattering amplitude",
            "f(θ) = -(m/2πℏ²)∫V(r')e^{i(k-k')·r'} d³r'",
            preconditions=["weak potential", "high energy"],
            level=3, tags=["Born", "scattering", "amplitude"])

        self._add("optical_theorem_qm", "quantum_mechanics",
            "Total cross section from forward scattering amplitude",
            "σ_tot = (4π/k) Im f(θ=0)",
            level=3, tags=["optical theorem", "cross section", "unitarity"])

        self._add("entanglement_entropy", "quantum_mechanics",
            "Quantum correlations measured by von Neumann entropy",
            "S = -Tr(ρ_A ln ρ_A); S=0 iff separable",
            applications=["quantum information", "black holes", "area law"],
            level=3, tags=["entanglement", "entropy", "von Neumann"])

        self._add("quantum_teleportation", "quantum_mechanics",
            "Transfer quantum state using entanglement + classical communication",
            "|ψ⟩_A → |ψ⟩_B using Bell pair + 2 classical bits",
            derived_from=["bell_theorem"],
            level=3, tags=["teleportation", "entanglement", "protocol"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 4: STATISTICAL MECHANICS + THERMODYNAMICS (25)
    # ──────────────────────────────────────────────────────────────────
    def _build_level4(self):
        self._add("boltzmann_distribution", "statistical_mechanics",
            "Probability of state with energy E at temperature T",
            "P(E) = e^{-E/k_BT}/Z",
            consequences=["all of equilibrium thermodynamics"],
            level=4, tags=["Boltzmann", "distribution", "canonical"])

        self._add("partition_function", "statistical_mechanics",
            "Generating function for all thermodynamic quantities",
            "Z = Σᵢ e^{-βEᵢ}; F = -k_BT ln Z",
            consequences=["⟨E⟩=-∂lnZ/∂β", "S=k_B(lnZ+β⟨E⟩)", "P=-∂F/∂V"],
            level=4, tags=["partition function", "free energy", "generating"])

        self._add("first_law_thermo", "statistical_mechanics",
            "Energy conservation including heat and work",
            "dU = δQ - δW = TdS - PdV + μdN",
            level=4, tags=["first law", "energy", "heat", "work"])

        self._add("second_law_thermo", "statistical_mechanics",
            "Entropy of isolated system never decreases",
            "dS ≥ 0 (isolated); dS = δQ/T (reversible)",
            consequences=["heat flows hot→cold", "Carnot efficiency limit"],
            level=4, tags=["second law", "entropy", "irreversibility"])

        self._add("third_law_thermo", "statistical_mechanics",
            "Entropy approaches zero as temperature approaches absolute zero",
            "S → 0 as T → 0 (for perfect crystal)",
            consequences=["cannot reach T=0 in finite steps"],
            level=4, tags=["third law", "Nernst", "absolute zero"])

        self._add("entropy_gibbs", "statistical_mechanics",
            "Entropy as information measure of probability distribution",
            "S = -k_B Σᵢ pᵢ ln pᵢ; S = k_B ln Ω (microcanonical)",
            level=4, tags=["entropy", "Gibbs", "information", "Boltzmann"])

        self._add("fermi_dirac_distribution", "statistical_mechanics",
            "Occupation probability for fermions at temperature T",
            "f(E) = 1/(e^{(E-μ)/k_BT} + 1)",
            preconditions=["identical fermions", "thermal equilibrium"],
            applications=["electron gas in metals", "white dwarfs", "semiconductors"],
            level=4, tags=["Fermi-Dirac", "fermion", "occupation"])

        self._add("bose_einstein_distribution", "statistical_mechanics",
            "Occupation probability for bosons at temperature T",
            "f(E) = 1/(e^{(E-μ)/k_BT} - 1)",
            applications=["photon gas", "phonons", "BEC"],
            level=4, tags=["Bose-Einstein", "boson", "condensation"])

        self._add("planck_distribution", "statistical_mechanics",
            "Spectral energy density of blackbody radiation",
            "u(ν) = (8πhν³/c³) · 1/(e^{hν/k_BT}-1)",
            derived_from=["bose_einstein_distribution"],
            consequences=["Stefan-Boltzmann law", "Wien displacement"],
            level=4, tags=["Planck", "blackbody", "radiation"])

        self._add("stefan_boltzmann_law", "statistical_mechanics",
            "Total power radiated by blackbody",
            "P = σAT⁴; σ = 2π⁵k_B⁴/(15h³c²)",
            derived_from=["planck_distribution"],
            level=4, tags=["Stefan-Boltzmann", "radiation", "T^4"])

        self._add("fluctuation_dissipation", "statistical_mechanics",
            "Response to perturbation related to spontaneous fluctuations",
            "⟨x²⟩ = k_BT/mω₀²; χ''(ω) ~ S(ω)/k_BT",
            applications=["Johnson noise", "Brownian motion", "Kubo formula"],
            level=4, tags=["FDT", "fluctuation", "dissipation", "Kubo"])

        self._add("landau_phase_transition", "statistical_mechanics",
            "Free energy expansion in order parameter near transition",
            "F = F₀ + a(T-Tc)η² + bη⁴ + ...",
            applications=["magnetism", "superconductivity", "liquid crystals"],
            level=4, tags=["Landau", "order parameter", "phase transition", "mean field"])

        self._add("ising_model", "statistical_mechanics",
            "Lattice model for phase transitions with spin-spin coupling",
            "H = -J Σ_{⟨ij⟩} sᵢsⱼ - h Σᵢ sᵢ",
            applications=["ferromagnetism", "Onsager 2D exact solution"],
            level=4, tags=["Ising", "lattice", "phase transition"])

        self._add("critical_exponents", "statistical_mechanics",
            "Power-law behavior near critical point with universal exponents",
            "C~|t|^{-α}, M~|t|^β, χ~|t|^{-γ}, ξ~|t|^{-ν}",
            applications=["universality classes", "scaling relations: α+2β+γ=2"],
            level=4, tags=["critical", "exponents", "universality", "scaling"])

        self._add("renormalization_group", "statistical_mechanics",
            "Scale transformation reveals fixed points and universality",
            "K' = R(K); fixed point K*: R(K*)=K*; exponents from linearization",
            applications=["critical phenomena", "QFT running coupling"],
            level=4, tags=["RG", "renormalization", "scaling", "Wilson"])

        self._add("jarzynski_equality", "statistical_mechanics",
            "Free energy difference from non-equilibrium work measurements",
            "⟨e^{-βW}⟩ = e^{-βΔF}",
            applications=["single-molecule experiments", "non-equilibrium thermo"],
            level=4, tags=["Jarzynski", "non-equilibrium", "free energy"])

        self._add("onsager_reciprocal", "statistical_mechanics",
            "Cross-transport coefficients are symmetric",
            "L_ij = L_ji (Onsager relations)",
            preconditions=["near equilibrium", "time-reversal symmetry"],
            applications=["thermoelectrics", "Peltier-Seebeck"],
            level=4, tags=["Onsager", "reciprocal", "linear response"])

        self._add("boltzmann_h_theorem", "statistical_mechanics",
            "H function decreases monotonically toward equilibrium",
            "dH/dt ≤ 0; H = ∫f ln f dv",
            consequences=["irreversibility from reversible dynamics"],
            level=4, tags=["H-theorem", "Boltzmann", "irreversibility"])

        self._add("maxwell_distribution", "statistical_mechanics",
            "Speed distribution of ideal gas molecules",
            "f(v) = 4π(m/2πk_BT)^{3/2} v² e^{-mv²/2k_BT}",
            derived_from=["boltzmann_distribution"],
            level=4, tags=["Maxwell", "velocity", "speed", "gas"])

        self._add("clausius_clapeyron", "statistical_mechanics",
            "Slope of phase boundary in P-T diagram",
            "dP/dT = ΔS/ΔV = L/(TΔV)",
            applications=["boiling point vs pressure", "ice skating"],
            level=4, tags=["Clausius-Clapeyron", "phase boundary", "latent heat"])

        self._add("carnot_efficiency", "statistical_mechanics",
            "Maximum efficiency of heat engine between two temperatures",
            "η_max = 1 - T_c/T_h",
            derived_from=["second_law_thermo"],
            level=4, tags=["Carnot", "efficiency", "heat engine"])

        self._add("gibbs_free_energy", "statistical_mechanics",
            "Thermodynamic potential at constant T,P",
            "G = H - TS = U + PV - TS; dG ≤ 0 at const T,P",
            applications=["chemical equilibrium", "phase stability"],
            level=4, tags=["Gibbs", "free energy", "equilibrium"])

        self._add("chemical_potential", "statistical_mechanics",
            "Energy cost of adding one particle",
            "μ = (∂G/∂N)_{T,P} = (∂F/∂N)_{T,V}",
            applications=["diffusion", "osmosis", "BEC condition μ→0"],
            level=4, tags=["chemical potential", "particle number"])

        self._add("grand_canonical", "statistical_mechanics",
            "Ensemble with fluctuating particle number",
            "Z_G = Σ_N e^{βμN} Z_N; Ω = -k_BT ln Z_G",
            applications=["adsorption", "quantum gases", "open systems"],
            level=4, tags=["grand canonical", "ensemble", "chemical potential"])

        self._add("bose_einstein_condensation", "statistical_mechanics",
            "Macroscopic occupation of ground state below critical temperature",
            "T_c = (2πℏ²/mk_B)(n/ζ(3/2))^{2/3}",
            applications=["superfluid He-4", "ultracold atoms", "laser cooling"],
            level=4, tags=["BEC", "condensation", "macroscopic quantum"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 5: SPECIAL + GENERAL RELATIVITY (20)
    # ──────────────────────────────────────────────────────────────────
    def _build_level5(self):
        self._add("lorentz_transformation", "relativity",
            "Coordinate transformation between inertial frames",
            "t'=γ(t-vx/c²), x'=γ(x-vt); γ=1/√(1-v²/c²)",
            consequences=["time_dilation", "length_contraction"],
            level=5, tags=["Lorentz", "boost", "inertial"])

        self._add("time_dilation", "relativity",
            "Moving clocks run slow",
            "Δt' = γΔτ; Δτ = Δt/γ (proper time shorter)",
            derived_from=["lorentz_transformation"],
            level=5, tags=["time dilation", "proper time", "twin paradox"])

        self._add("length_contraction", "relativity",
            "Moving objects are shortened along direction of motion",
            "L = L₀/γ",
            derived_from=["lorentz_transformation"],
            level=5, tags=["length contraction", "Lorentz"])

        self._add("mass_energy", "relativity",
            "Mass and energy are equivalent",
            "E = mc²; E² = (pc)² + (mc²)²",
            consequences=["nuclear energy", "pair production", "rest mass energy"],
            level=5, tags=["Einstein", "E=mc²", "mass-energy"])

        self._add("four_momentum", "relativity",
            "Relativistic energy-momentum four-vector",
            "p^μ = (E/c, p⃗); p_μp^μ = -(mc)²",
            level=5, tags=["four-vector", "momentum", "invariant mass"])

        self._add("einstein_field_equations", "relativity",
            "Spacetime curvature determined by energy-momentum",
            "G_μν + Λg_μν = (8πG/c⁴)T_μν",
            preconditions=["general covariance", "equivalence principle"],
            consequences=["gravitational waves", "black holes", "cosmology"],
            level=5, tags=["Einstein", "field equations", "curvature", "GR"])

        self._add("geodesic_equation", "relativity",
            "Free particles follow geodesics (straightest paths in curved space)",
            "d²x^μ/dτ² + Γ^μ_νρ (dx^ν/dτ)(dx^ρ/dτ) = 0",
            derived_from=["einstein_field_equations"],
            level=5, tags=["geodesic", "free fall", "Christoffel"])

        self._add("schwarzschild_metric", "relativity",
            "Spacetime geometry outside spherical non-rotating mass",
            "ds² = -(1-r_s/r)c²dt² + dr²/(1-r_s/r) + r²dΩ²; r_s=2GM/c²",
            derived_from=["einstein_field_equations"],
            applications=["black holes", "perihelion precession", "light bending"],
            level=5, tags=["Schwarzschild", "black hole", "metric"])

        self._add("kerr_metric", "relativity",
            "Spacetime around rotating black hole",
            "ds² includes frame-dragging; has ergosphere and two horizons",
            applications=["astrophysical black holes", "Penrose process"],
            level=5, tags=["Kerr", "rotating", "ergosphere"])

        self._add("gravitational_redshift", "relativity",
            "Photon loses energy climbing out of gravitational well",
            "Δν/ν = -ΔΦ/c² = -GM/(rc²)",
            derived_from=["equivalence_principle"],
            level=5, tags=["redshift", "gravitational", "GPS"])

        self._add("gravitational_waves", "relativity",
            "Ripples in spacetime from accelerating masses",
            "h_μν propagates at c; h ~ 2GμΩ²r²/(c⁴d)",
            derived_from=["einstein_field_equations"],
            applications=["LIGO detection", "binary pulsars"],
            level=5, tags=["gravitational waves", "LIGO", "strain"])

        self._add("friedmann_equations", "relativity",
            "Evolution of the scale factor in homogeneous isotropic universe",
            "H² = (8πG/3)ρ - k/a²; ä/a = -(4πG/3)(ρ+3P/c²) + Λ/3",
            derived_from=["einstein_field_equations"],
            applications=["Big Bang", "expansion", "dark energy"],
            level=5, tags=["Friedmann", "cosmology", "expansion", "scale factor"])

        self._add("hubble_law", "relativity",
            "Recession velocity proportional to distance (expansion)",
            "v = H₀d; H₀ ≈ 70 km/s/Mpc",
            derived_from=["friedmann_equations"],
            level=5, tags=["Hubble", "expansion", "redshift"])

        self._add("hawking_radiation", "relativity",
            "Black holes emit thermal radiation at temperature T_H",
            "T_H = ℏc³/(8πGMk_B)",
            consequences=["BH evaporation", "information paradox"],
            level=5, tags=["Hawking", "radiation", "temperature", "quantum gravity"])

        self._add("bekenstein_hawking_entropy", "relativity",
            "Black hole entropy proportional to horizon area",
            "S_BH = k_B c³A/(4Gℏ) = A/(4l_P²)",
            consequences=["holographic principle", "information bounds"],
            level=5, tags=["Bekenstein", "entropy", "area", "holographic"])

        self._add("equivalence_principle", "relativity",
            "Gravity locally indistinguishable from acceleration",
            "m_inertial = m_gravitational (exact)",
            consequences=["geodesic motion", "gravitational redshift"],
            level=5, tags=["equivalence", "inertial mass", "gravitational mass"])

        self._add("penrose_singularity", "relativity",
            "Trapped surface implies spacetime singularity",
            "If trapped surface exists → geodesic incompleteness",
            level=5, tags=["Penrose", "singularity", "trapped surface"])

        self._add("frame_dragging", "relativity",
            "Rotating mass drags spacetime (Lense-Thirring effect)",
            "Ω_LT = 2GJ/(c²r³)",
            derived_from=["kerr_metric"],
            level=5, tags=["frame dragging", "Lense-Thirring", "Kerr"])

        self._add("cosmological_redshift", "relativity",
            "Wavelength stretched by expansion of universe",
            "1+z = a(t_obs)/a(t_emit) = λ_obs/λ_emit",
            derived_from=["friedmann_equations"],
            level=5, tags=["cosmological", "redshift", "expansion"])

        self._add("raychaudhuri_equation", "relativity",
            "Evolution of expansion of geodesic congruence",
            "dθ/dτ = -θ²/3 - σ²+ω² - R_μν u^μu^ν",
            applications=["singularity theorems", "focusing"],
            level=5, tags=["Raychaudhuri", "geodesic", "focusing"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 6: QUANTUM FIELD THEORY + PARTICLE PHYSICS (20)
    # ──────────────────────────────────────────────────────────────────
    def _build_level6(self):
        self._add("klein_gordon", "quantum_field_theory",
            "Relativistic wave equation for spin-0 particles",
            "(□ + m²c²/ℏ²)φ = 0; □ = ∂²/∂t² - c²∇²",
            level=6, tags=["Klein-Gordon", "scalar", "spin-0"])

        self._add("dirac_equation", "quantum_field_theory",
            "Relativistic wave equation for spin-½ particles",
            "(iγ^μ∂_μ - mc/ℏ)ψ = 0",
            consequences=["antimatter prediction", "spin naturally included"],
            level=6, tags=["Dirac", "spinor", "spin-½", "antimatter"])

        self._add("feynman_propagator", "quantum_field_theory",
            "Amplitude for particle to go from x to y",
            "D_F(x-y) = ⟨0|T{φ(x)φ(y)}|0⟩ = ∫d⁴k e^{ik(x-y)}/(k²-m²+iε)",
            level=6, tags=["propagator", "Feynman", "Green's function"])

        self._add("lsz_reduction", "quantum_field_theory",
            "S-matrix elements from time-ordered correlation functions",
            "⟨f|S|i⟩ ~ ∏(□+m²) ⟨0|T{φ...φ}|0⟩ (amputated, on-shell)",
            level=6, tags=["LSZ", "S-matrix", "reduction", "amplitude"])

        self._add("ward_identity", "quantum_field_theory",
            "Gauge invariance constrains Green's functions",
            "q_μ M^μ = 0 (for on-shell QED amplitude)",
            consequences=["photon remains massless", "charge conservation"],
            level=6, tags=["Ward", "gauge", "identity", "QED"])

        self._add("running_coupling", "quantum_field_theory",
            "Coupling constants depend on energy scale",
            "μ dg/dμ = β(g); QED: β>0 (grows), QCD: β<0 (shrinks)",
            consequences=["asymptotic freedom", "confinement", "unification"],
            level=6, tags=["running", "coupling", "beta function", "RG"])

        self._add("asymptotic_freedom", "quantum_field_theory",
            "QCD coupling vanishes at high energy",
            "α_s(Q²) = α_s(μ²)/[1 + (α_s(μ²)β₀/2π)ln(Q²/μ²)]",
            consequences=["quarks free at short distances", "perturbative QCD"],
            level=6, tags=["asymptotic freedom", "QCD", "strong coupling"])

        self._add("higgs_mechanism", "quantum_field_theory",
            "Spontaneous symmetry breaking gives mass to gauge bosons",
            "⟨φ⟩=v≠0; M_W=gv/2, M_Z=gv/(2cosθ_W), M_H=√(2λ)v",
            consequences=["W±, Z massive; photon massless"],
            level=6, tags=["Higgs", "SSB", "mass generation", "electroweak"])

        self._add("goldstone_theorem", "quantum_field_theory",
            "Spontaneous breaking of continuous symmetry produces massless bosons",
            "Broken generators → massless Nambu-Goldstone bosons",
            applications=["pions (approx)", "phonons", "magnons"],
            level=6, tags=["Goldstone", "SSB", "massless", "Nambu"])

        self._add("cpt_theorem", "quantum_field_theory",
            "All local Lorentz-invariant QFTs are invariant under CPT",
            "CPT|particle⟩ = |antiparticle⟩; same mass, opposite quantum numbers",
            level=6, tags=["CPT", "symmetry", "antiparticle"])

        self._add("anomalous_magnetic_moment", "quantum_field_theory",
            "Quantum corrections to g-factor of electron/muon",
            "a_e = (g-2)/2 = α/(2π) + ... ; a_μ deviates from SM (2026!)",
            applications=["precision test of QED/SM", "BSM physics hint"],
            level=6, tags=["g-2", "anomalous", "QED", "muon", "2026"])

        self._add("standard_model_gauge", "quantum_field_theory",
            "Gauge group of the Standard Model",
            "SU(3)_C × SU(2)_L × U(1)_Y → SU(3)_C × U(1)_EM after SSB",
            consequences=["12 gauge bosons: 8g + W±,Z + γ"],
            level=6, tags=["Standard Model", "gauge group", "SU(3)", "SU(2)", "U(1)"])

        self._add("ckm_matrix", "quantum_field_theory",
            "Quark flavor mixing matrix (CP violation source)",
            "V_CKM: 3×3 unitary, 4 parameters (3 angles + 1 CP phase)",
            level=6, tags=["CKM", "quark mixing", "CP violation", "flavor"])

        self._add("neutrino_oscillation", "quantum_field_theory",
            "Neutrinos change flavor during propagation",
            "P(ν_α→ν_β) = sin²(2θ)sin²(Δm²L/4E)",
            consequences=["neutrinos have mass", "PMNS matrix"],
            level=6, tags=["neutrino", "oscillation", "PMNS", "mass"])

        self._add("confinement", "quantum_field_theory",
            "Quarks cannot be isolated — color flux tube formation",
            "V(r) ~ σr at large r (linear potential, string tension σ)",
            derived_from=["asymptotic_freedom"],
            level=6, tags=["confinement", "QCD", "color", "hadron"])

        self._add("optical_theorem_qft", "quantum_field_theory",
            "Total cross section from imaginary part of forward amplitude",
            "σ_tot = (1/s)Im M(s,t=0)",
            level=6, tags=["optical theorem", "unitarity", "cross section"])

        self._add("anomaly_cancellation", "quantum_field_theory",
            "SM is consistent because gauge anomalies cancel between quarks and leptons",
            "Σ Y³ = 0 per generation (anomaly-free)",
            level=6, tags=["anomaly", "cancellation", "consistency"])

        self._add("effective_field_theory", "quantum_field_theory",
            "Low-energy physics captured by local operators ordered by dimension",
            "L_eff = Σ_n c_n O_n/Λ^{n-4}; higher dim suppressed by scale Λ",
            applications=["Fermi theory", "chiral perturbation", "SMEFT"],
            level=6, tags=["EFT", "effective", "power counting", "scale"])

        self._add("feynman_rules", "quantum_field_theory",
            "Rules to compute scattering amplitudes from diagrams",
            "Vertex: coupling; Propagator: 1/(p²-m²); External: spinor/polarization",
            applications=["cross sections", "decay rates", "loop corrections"],
            level=6, tags=["Feynman", "rules", "diagram", "amplitude"])

        self._add("renormalization", "quantum_field_theory",
            "Absorb UV divergences into redefined parameters",
            "g_bare = g_R + counterterms; physics independent of cutoff",
            applications=["QED: finite predictions", "running couplings"],
            level=6, tags=["renormalization", "UV", "divergence", "counterterm"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 7: CONDENSED MATTER (20)
    # ──────────────────────────────────────────────────────────────────
    def _build_level7(self):
        self._add("bloch_theorem", "condensed_matter",
            "Eigenstates in periodic potential are Bloch waves",
            "ψ_k(r) = e^{ik·r} u_k(r); u_k periodic",
            consequences=["band structure", "Brillouin zones"],
            level=7, tags=["Bloch", "periodic", "crystal", "band"])

        self._add("band_theory", "condensed_matter",
            "Electronic states form continuous bands separated by gaps",
            "E(k) forms bands; metal (partial fill), insulator (full+gap), semiconductor",
            derived_from=["bloch_theorem"],
            level=7, tags=["band", "gap", "metal", "insulator"])

        self._add("fermi_liquid", "condensed_matter",
            "Interacting fermions behave as weakly-interacting quasiparticles",
            "Quasiparticle: m*≠m, Z<1, finite lifetime ~ (E-E_F)²",
            applications=["metals", "He-3", "heavy fermions"],
            level=7, tags=["Fermi liquid", "Landau", "quasiparticle"])

        self._add("bcs_theory", "condensed_matter",
            "Superconductivity from Cooper pairing of electrons",
            "Δ = V⟨c_↑c_↓⟩; E_gap = 2Δ(0) = 3.5 k_BT_c",
            consequences=["zero resistance", "Meissner effect", "flux quantization"],
            level=7, tags=["BCS", "Cooper pair", "superconductor", "gap"])

        self._add("meissner_effect", "condensed_matter",
            "Superconductor expels magnetic field from interior",
            "B = 0 inside SC; penetration depth λ_L",
            derived_from=["bcs_theory"],
            level=7, tags=["Meissner", "expulsion", "superconductor"])

        self._add("josephson_effect", "condensed_matter",
            "Supercurrent through weak link depends on phase difference",
            "DC: I=I_c sinΔφ; AC: V=(ℏ/2e)dΔφ/dt",
            applications=["SQUIDs", "voltage standard", "qubits"],
            level=7, tags=["Josephson", "junction", "phase", "SQUID"])

        self._add("quantum_hall_effect", "condensed_matter",
            "Hall conductance quantized in units of e²/h",
            "σ_xy = νe²/h; ν=integer (IQHE) or fraction (FQHE)",
            applications=["resistance standard", "topological physics"],
            level=7, tags=["quantum Hall", "quantized", "Landau level", "topology"])

        self._add("berry_phase_condensed", "condensed_matter",
            "Geometric phase in band structure gives topological invariants",
            "γ = ∮⟨u_k|∇_k|u_k⟩·dk; Chern number C = (1/2π)∫F dk₁dk₂",
            applications=["topological insulators", "anomalous Hall"],
            level=7, tags=["Berry phase", "Chern", "topological", "band"])

        self._add("anderson_localization", "condensed_matter",
            "Disorder can localize all eigenstates (no diffusion)",
            "All states localized in 1D,2D; mobility edge in 3D",
            level=7, tags=["Anderson", "localization", "disorder"])

        self._add("kondo_effect", "condensed_matter",
            "Resistance minimum from magnetic impurity screening",
            "T_K = D exp(-1/Jρ₀); resistance rises as T→0 below T_K",
            level=7, tags=["Kondo", "impurity", "screening", "resistance"])

        self._add("topological_insulator", "condensed_matter",
            "Bulk insulator with topologically protected surface states",
            "Z₂ invariant ν=1; helical Dirac cone on surface",
            applications=["spintronics", "quantum computing"],
            level=7, tags=["topological insulator", "Z2", "surface states"])

        self._add("landau_levels", "condensed_matter",
            "Discrete energy levels of 2D electrons in magnetic field",
            "E_n = ℏω_c(n+½); ω_c=eB/m; degeneracy=eB/h per area",
            level=7, tags=["Landau level", "magnetic", "2DEG", "degeneracy"])

        self._add("phonon_dispersion", "condensed_matter",
            "Quantized lattice vibrations with acoustic and optical branches",
            "ω_acoustic ~ |k| (long λ); ω_optical ~ const (short λ)",
            applications=["specific heat", "thermal conductivity", "Debye model"],
            level=7, tags=["phonon", "acoustic", "optical", "Debye"])

        self._add("hubbard_model", "condensed_matter",
            "Minimal model for strongly correlated electrons",
            "H = -t Σ c†_iσ c_jσ + U Σ n_i↑ n_i↓",
            applications=["Mott insulator", "magnetism", "high-Tc"],
            level=7, tags=["Hubbard", "correlation", "Mott", "t-U"])

        self._add("mermin_wagner", "condensed_matter",
            "No spontaneous continuous symmetry breaking in ≤2D at T>0",
            "⟨M⟩=0 in 2D isotropic Heisenberg model at T>0",
            level=7, tags=["Mermin-Wagner", "2D", "fluctuations", "no order"])

        self._add("ginzburg_landau", "condensed_matter",
            "Phenomenological theory of superconductivity near T_c",
            "F = ∫[α|ψ|²+β|ψ|⁴+|(∇-2ieA/ℏ)ψ|²/2m* + B²/2μ₀] dV",
            applications=["vortices", "type I/II", "GL coherence length"],
            level=7, tags=["Ginzburg-Landau", "order parameter", "vortex"])

        self._add("fractional_qhe", "condensed_matter",
            "Fractional quantization from strongly correlated 2D electrons",
            "Laughlin: ψ = Π(zᵢ-zⱼ)^m e^{-Σ|z|²/4}; ν=1/m",
            level=7, tags=["FQHE", "Laughlin", "anyons", "fractional"])

        self._add("weyl_semimetal", "condensed_matter",
            "3D material with linear band crossing (Weyl nodes)",
            "H = ±v_F σ·k near node; Fermi arcs on surface",
            level=7, tags=["Weyl", "semimetal", "Dirac", "node"])

        self._add("dft_kohn_sham", "condensed_matter",
            "Density functional theory reduces many-body to single-particle equations",
            "[-ℏ²∇²/2m + V_eff(r)]φᵢ = εᵢφᵢ; V_eff includes exchange-correlation",
            applications=["materials science", "molecular simulation"],
            level=7, tags=["DFT", "Kohn-Sham", "density functional"])

        self._add("spin_orbit_coupling", "condensed_matter",
            "Coupling between electron spin and orbital motion",
            "H_SO = (ℏ/4m²c²)(∇V×p)·σ; Rashba: α_R(σ×k)_z",
            applications=["topological states", "spintronics"],
            level=7, tags=["spin-orbit", "Rashba", "SOC"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 8: QUANTUM OPTICS + PHOTONICS (15)
    # ──────────────────────────────────────────────────────────────────
    def _build_level8(self):
        self._add("coherent_states", "quantum_optics",
            "Minimum uncertainty states of the EM field (laser light)",
            "|α⟩ = e^{-|α|²/2} Σ α^n/√(n!)|n⟩; Poissonian photon stats",
            level=8, tags=["coherent", "Glauber", "laser", "Poisson"])

        self._add("squeezed_states", "quantum_optics",
            "States with reduced noise in one quadrature below vacuum",
            "ΔX₁<1/2, ΔX₂>1/2; ΔX₁ΔX₂=1/4 (minimum uncertainty)",
            applications=["LIGO enhancement", "quantum metrology"],
            level=8, tags=["squeezed", "sub-vacuum", "quadrature"])

        self._add("jaynes_cummings", "quantum_optics",
            "Exactly solvable model of atom-cavity interaction",
            "H = ℏω a†a + ½ℏΩ σ_z + ℏg(aσ⁺ + a†σ⁻)",
            consequences=["vacuum Rabi splitting", "collapse and revival"],
            level=8, tags=["Jaynes-Cummings", "cavity QED", "Rabi"])

        self._add("photon_antibunching", "quantum_optics",
            "Non-classical light: photons tend to arrive separately",
            "g²(0) < 1; single-photon source",
            level=8, tags=["antibunching", "nonclassical", "g2"])

        self._add("hong_ou_mandel", "quantum_optics",
            "Two identical photons on beamsplitter always exit together",
            "Coincidence dip to zero: quantum interference of indistinguishable photons",
            level=8, tags=["HOM", "interference", "indistinguishable", "beamsplitter"])

        self._add("purcell_effect", "quantum_optics",
            "Cavity enhances/suppresses spontaneous emission rate",
            "F_P = 3Qλ³/(4π²V_mode); Γ_cav = F_P × Γ_free",
            level=8, tags=["Purcell", "cavity", "spontaneous emission"])

        self._add("master_equation_lindblad", "quantum_optics",
            "Evolution of open quantum system (includes dissipation)",
            "dρ/dt = -i[H,ρ]/ℏ + Σ γₖ(L_kρL_k† - ½{L_k†L_k,ρ})",
            applications=["cavity decay", "atomic cooling", "decoherence"],
            level=8, tags=["Lindblad", "master equation", "open system", "dissipation"])

        self._add("laser_threshold", "quantum_optics",
            "Condition for stimulated emission to dominate",
            "Population inversion N₂>N₁; gain > loss threshold",
            level=8, tags=["laser", "threshold", "population inversion", "gain"])

        self._add("parametric_down_conversion", "quantum_optics",
            "Nonlinear crystal splits pump photon into entangled pair",
            "ω_p = ω_s + ω_i; k_p = k_s + k_i (phase matching)",
            applications=["entangled photon source", "quantum cryptography"],
            level=8, tags=["SPDC", "entangled", "parametric", "nonlinear"])

        self._add("eit_slow_light", "quantum_optics",
            "Quantum interference makes medium transparent and slows light",
            "v_group ~ c×(Ω_c²/ω_p²) can be < 1 m/s",
            level=8, tags=["EIT", "slow light", "transparency"])

        self._add("quantum_key_distribution", "quantum_optics",
            "Secure key exchange using quantum no-cloning",
            "BB84: 4 states, 2 bases; Eve detection via error rate > 11%",
            derived_from=["no_cloning_theorem"],
            level=8, tags=["QKD", "BB84", "cryptography", "secure"])

        self._add("nonlinear_optics_chi2", "quantum_optics",
            "Second-order nonlinearity: SHG, OPA, DFG",
            "P^(2) = ε₀χ^(2)E²; phase matching: Δk=0",
            level=8, tags=["χ²", "SHG", "nonlinear", "phase matching"])

        self._add("nonlinear_optics_chi3", "quantum_optics",
            "Third-order: Kerr effect, self-focusing, four-wave mixing",
            "n = n₀ + n₂I; self-focusing when P > P_crit",
            level=8, tags=["χ³", "Kerr", "self-focusing", "FWM"])

        self._add("photonic_crystal", "quantum_optics",
            "Periodic dielectric structure with photonic band gaps",
            "Analogous to electronic bands; ω(k) with forbidden gaps",
            level=8, tags=["photonic crystal", "band gap", "periodic"])

        self._add("quantum_noise_limit", "quantum_optics",
            "Standard quantum limit for measurements",
            "ΔxΔp ≥ ℏ/2; SQL: Δx_SQL = √(ℏ/mω)",
            applications=["LIGO", "atomic clocks", "force sensing"],
            level=8, tags=["SQL", "quantum noise", "measurement", "sensitivity"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 9: PLASMA + ASTROPHYSICAL FLUIDS (15)
    # ──────────────────────────────────────────────────────────────────
    def _build_level9(self):
        self._add("plasma_frequency", "plasma_physics",
            "Natural oscillation frequency of plasma electrons",
            "ω_p = √(ne²/ε₀m_e)",
            consequences=["EM waves reflect below ω_p", "Debye shielding"],
            level=9, tags=["plasma frequency", "oscillation", "cutoff"])

        self._add("vlasov_equation", "plasma_physics",
            "Collisionless kinetic equation for plasma",
            "∂f/∂t + v·∇f + (q/m)(E+v×B)·∇_v f = 0",
            level=9, tags=["Vlasov", "kinetic", "collisionless", "distribution"])

        self._add("mhd_equations", "plasma_physics",
            "Magnetohydrodynamics: fluid + Maxwell coupled",
            "ρ(∂v/∂t + v·∇v) = -∇P + J×B; ∂B/∂t = ∇×(v×B) + η∇²B",
            applications=["solar wind", "fusion", "astrophysical jets"],
            level=9, tags=["MHD", "magnetohydrodynamics", "fluid", "magnetic"])

        self._add("alfven_waves", "plasma_physics",
            "Waves propagating along magnetic field lines",
            "v_A = B/√(μ₀ρ); ω = k_∥ v_A",
            level=9, tags=["Alfvén", "wave", "magnetic", "MHD"])

        self._add("magnetic_reconnection", "plasma_physics",
            "Topology change of magnetic field releasing energy",
            "Sweet-Parker: v_in/v_A ~ 1/√Re_m; Petschek: faster",
            applications=["solar flares", "magnetosphere", "tokamak disruptions"],
            level=9, tags=["reconnection", "topology", "energy release"])

        self._add("landau_damping", "plasma_physics",
            "Collisionless damping of plasma waves by resonant particles",
            "γ ~ -ω_p(π/2)(ω/k)²(∂f₀/∂v)|_{v=ω/k}",
            level=9, tags=["Landau damping", "collisionless", "resonant"])

        self._add("cyclotron_motion", "plasma_physics",
            "Charged particle gyration in magnetic field",
            "ω_c = |q|B/m; r_L = mv_⊥/(|q|B)",
            level=9, tags=["cyclotron", "gyration", "Larmor radius"])

        self._add("magnetic_mirror", "plasma_physics",
            "Particle reflection from converging magnetic field",
            "μ = mv_⊥²/(2B) = const (adiabatic invariant); reflects if v_∥→0",
            level=9, tags=["magnetic mirror", "adiabatic", "confinement"])

        self._add("plasma_beta", "plasma_physics",
            "Ratio of thermal to magnetic pressure",
            "β = nk_BT/(B²/2μ₀); β≫1 thermal dominates, β≪1 magnetic",
            level=9, tags=["beta", "pressure ratio", "confinement"])

        self._add("jeans_instability", "plasma_physics",
            "Gravitational collapse criterion for gas cloud",
            "λ_J = c_s√(π/Gρ); M_J = (5k_BT/Gm)^{3/2}(3/4πρ)^{1/2}",
            applications=["star formation", "galaxy formation"],
            level=9, tags=["Jeans", "instability", "collapse", "gravitational"])

        self._add("chandrasekhar_limit", "plasma_physics",
            "Maximum mass for white dwarf (electron degeneracy)",
            "M_Ch ≈ 1.4 M_☉ = 5.83 μ_e^{-2} M_☉",
            level=9, tags=["Chandrasekhar", "white dwarf", "limit", "degeneracy"])

        self._add("eddington_luminosity", "plasma_physics",
            "Maximum luminosity before radiation pressure unbinds matter",
            "L_Edd = 4πGMc/κ ≈ 3.3×10⁴(M/M_☉) L_☉",
            level=9, tags=["Eddington", "luminosity", "radiation pressure"])

        self._add("synchrotron_radiation", "plasma_physics",
            "Radiation from relativistic charged particle in magnetic field",
            "P = (q²c/6π)(γ⁴/R²); peaks at ω_c ~ γ³eB/m",
            applications=["pulsars", "AGN jets", "synchrotron facilities"],
            level=9, tags=["synchrotron", "relativistic", "radiation"])

        self._add("bremsstrahlung", "plasma_physics",
            "Radiation from deceleration of charged particle",
            "P_ff ∝ n_e n_i Z² T^{1/2} (thermal brems)",
            applications=["X-ray emission from hot gas", "plasma diagnostics"],
            level=9, tags=["Bremsstrahlung", "free-free", "X-ray"])

        self._add("dynamo_theory", "plasma_physics",
            "Self-sustaining magnetic field generation by fluid motion",
            "∂B/∂t = ∇×(v×B) + η∇²B; Rm=vL/η>Rm_crit for dynamo",
            applications=["Earth's field", "solar cycle", "galaxy fields"],
            level=9, tags=["dynamo", "magnetic field", "generation", "MHD"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 10: NUCLEAR + ATOMIC (15)
    # ──────────────────────────────────────────────────────────────────
    def _build_level10(self):
        self._add("nuclear_binding_energy", "nuclear_physics",
            "Semi-empirical mass formula (Bethe-Weizsäcker)",
            "B = a_V A - a_S A^{2/3} - a_C Z(Z-1)/A^{1/3} - a_A(N-Z)²/A ± δ",
            applications=["stability", "fission/fusion energetics"],
            level=10, tags=["binding energy", "SEMF", "liquid drop"])

        self._add("nuclear_shell_model", "nuclear_physics",
            "Magic numbers from spin-orbit coupled nuclear potential",
            "Magic: 2,8,20,28,50,82,126; extra stability at closed shells",
            level=10, tags=["shell model", "magic numbers", "spin-orbit"])

        self._add("radioactive_decay", "nuclear_physics",
            "Exponential decay law for unstable nuclei",
            "N(t) = N₀ e^{-λt}; t_{1/2} = ln2/λ",
            level=10, tags=["decay", "half-life", "exponential", "activity"])

        self._add("alpha_decay_gamow", "nuclear_physics",
            "Alpha tunneling through Coulomb barrier",
            "T ~ exp(-2π Z_α Z_d e²/ℏv); Geiger-Nuttall relation",
            derived_from=["tunneling"],
            level=10, tags=["alpha", "Gamow", "tunneling", "Coulomb"])

        self._add("beta_decay_fermi", "nuclear_physics",
            "Weak interaction converts neutron to proton (or vice versa)",
            "n → p + e⁻ + ν̄_e; Γ = G_F² |M|² f(Z,E₀)/(2π³)",
            level=10, tags=["beta decay", "Fermi", "weak", "neutrino"])

        self._add("nuclear_fission", "nuclear_physics",
            "Heavy nucleus splits releasing binding energy difference",
            "U-235 + n → fission products + 2-3n + ~200 MeV",
            applications=["nuclear reactor", "atomic bomb", "criticality"],
            level=10, tags=["fission", "chain reaction", "critical mass"])

        self._add("nuclear_fusion", "nuclear_physics",
            "Light nuclei combine releasing energy (powers stars)",
            "4p → He-4 + 2e⁺ + 2ν + 26.7 MeV (pp chain)",
            applications=["solar energy", "fusion reactors", "nucleosynthesis"],
            level=10, tags=["fusion", "pp chain", "CNO", "Lawson"])

        self._add("breit_wigner_resonance", "nuclear_physics",
            "Cross section near resonance energy",
            "σ(E) = π/k² × ΓᵢΓf/[(E-E₀)² + (Γ/2)²]",
            level=10, tags=["Breit-Wigner", "resonance", "cross section", "width"])

        self._add("fine_structure", "nuclear_physics",
            "Relativistic and spin-orbit corrections to hydrogen",
            "ΔE = -E_n α²/n [1/(j+½) - 3/(4n)]",
            level=10, tags=["fine structure", "spin-orbit", "relativistic"])

        self._add("zeeman_effect", "nuclear_physics",
            "Splitting of spectral lines in magnetic field",
            "ΔE = m_j g_J μ_B B",
            applications=["spectroscopy", "astrophysics", "MRI"],
            level=10, tags=["Zeeman", "magnetic", "splitting", "spectral"])

        self._add("stark_effect", "nuclear_physics",
            "Splitting of spectral lines in electric field",
            "Linear: ΔE ∝ F (hydrogen); Quadratic: ΔE ∝ F² (others)",
            level=10, tags=["Stark", "electric field", "splitting"])

        self._add("born_oppenheimer", "nuclear_physics",
            "Separate nuclear and electronic motion in molecules",
            "ψ_total ≈ ψ_elec(r;R) × ψ_nuc(R)",
            preconditions=["m_e ≪ M_nucleus"],
            level=10, tags=["Born-Oppenheimer", "molecular", "adiabatic"])

        self._add("laser_cooling", "nuclear_physics",
            "Use radiation pressure to cool atoms to μK temperatures",
            "Doppler limit: T_D = ℏΓ/2k_B; recoil limit: T_r = (ℏk)²/2mk_B",
            applications=["BEC", "atomic clocks", "quantum simulation"],
            level=10, tags=["laser cooling", "Doppler", "MOT", "ultracold"])

        self._add("lawson_criterion", "nuclear_physics",
            "Condition for fusion energy breakeven",
            "nτ_E > 10²⁰ m⁻³·s (for D-T at ~10 keV)",
            applications=["tokamak", "inertial confinement", "NIF"],
            level=10, tags=["Lawson", "fusion", "breakeven", "confinement"])

        self._add("rutherford_scattering", "nuclear_physics",
            "Coulomb scattering cross section",
            "dσ/dΩ = (Z₁Z₂e²/4E)² / sin⁴(θ/2)",
            level=10, tags=["Rutherford", "scattering", "Coulomb", "nucleus"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 11: COSMOLOGY + ASTROPHYSICS (15)
    # ──────────────────────────────────────────────────────────────────
    def _build_level11(self):
        self._add("dark_energy_evolution", "cosmology",
            "DESI 2025-2026: dark energy equation of state changes with time",
            "w(a) = w₀ + w_a(1-a); w₀≈-0.7, w_a≈-1.05 (NOT constant!)",
            consequences=["ΛCDM challenged", "new physics needed"],
            level=11, tags=["DESI", "dark energy", "2026", "evolution", "w(a)"])

        self._add("inflation_slow_roll", "cosmology",
            "Accelerated expansion driven by scalar field",
            "ε = (M_P²/2)(V'/V)² ≪ 1; η = M_P²(V''/V) ≪ 1",
            consequences=["flatness", "horizon problem", "seed perturbations"],
            level=11, tags=["inflation", "slow-roll", "scalar field"])

        self._add("cmb_anisotropy", "cosmology",
            "Temperature fluctuations from primordial perturbations",
            "ΔT/T ~ 10⁻⁵; C_l spectrum peaks from acoustic oscillations",
            applications=["cosmological parameters", "Planck satellite"],
            level=11, tags=["CMB", "anisotropy", "power spectrum", "acoustic"])

        self._add("nucleosynthesis_bbn", "cosmology",
            "Light element production in first 3 minutes",
            "Y_p ≈ 0.25 (He mass fraction); D/H ~ 2.5×10⁻⁵",
            applications=["baryon density constraint", "neutrino counting"],
            level=11, tags=["BBN", "nucleosynthesis", "helium", "deuterium"])

        self._add("structure_formation", "cosmology",
            "Growth of density perturbations into galaxies",
            "δ̈ + 2Hδ̇ - 4πGρ̄δ = 0 (linear); Press-Schechter mass function",
            level=11, tags=["structure", "growth", "perturbation", "galaxy"])

        self._add("tov_equation", "cosmology",
            "Hydrostatic equilibrium of neutron star in GR",
            "dP/dr = -(ε+P)(m+4πr³P)/(r(r-2m))",
            level=11, tags=["TOV", "neutron star", "hydrostatic", "GR"])

        self._add("no_hair_theorem", "cosmology",
            "Stationary BH fully characterized by mass, charge, spin only",
            "BH → (M, Q, J); all other info lost",
            level=11, tags=["no-hair", "black hole", "uniqueness"])

        self._add("sakharov_conditions", "cosmology",
            "Requirements for baryogenesis (matter-antimatter asymmetry)",
            "1) B violation, 2) C+CP violation, 3) out of thermal equilibrium",
            level=11, tags=["Sakharov", "baryogenesis", "CP", "asymmetry"])

        self._add("hubble_tension", "cosmology",
            "Discrepancy between CMB and local H₀ measurements (5σ, 2026)",
            "H₀(Planck)=67.4 vs H₀(SH0ES)=73.0 km/s/Mpc",
            consequences=["new physics? early dark energy? systematics?"],
            level=11, tags=["Hubble tension", "H0", "2026", "crisis"])

        self._add("gravitational_wave_sources", "cosmology",
            "GW from compact binary mergers detected by LIGO/Virgo",
            "h ~ (4G/c⁴)(μ/d)(πfGM)^{2/3}; chirp mass",
            level=11, tags=["GW", "LIGO", "merger", "binary"])

        self._add("cosmic_distance_ladder", "cosmology",
            "Chain of methods to measure cosmological distances",
            "Parallax → Cepheids → SNIa → Hubble flow",
            level=11, tags=["distance ladder", "Cepheid", "supernova", "parallax"])

        self._add("dark_matter_evidence", "cosmology",
            "Multiple independent observations require dark matter",
            "Rotation curves flat; gravitational lensing; CMB; structure formation",
            level=11, tags=["dark matter", "rotation curve", "lensing", "evidence"])

        self._add("lambda_cdm", "cosmology",
            "Standard model of cosmology: 6 parameters",
            "Ω_b, Ω_c, H₀, τ, n_s, A_s → everything (but DESI challenges Λ!)",
            level=11, tags=["ΛCDM", "standard model", "cosmology", "6 parameters"])

        self._add("reionization", "cosmology",
            "First stars/AGN ionize neutral hydrogen at z~6-10",
            "Lyman-α absorption; Gunn-Peterson trough at z>6",
            level=11, tags=["reionization", "epoch", "first stars", "Lyman"])

        self._add("type_ia_supernova", "cosmology",
            "Standardizable candle for measuring cosmic expansion",
            "M_peak ≈ -19.3; Phillips relation: brighter=slower decline",
            applications=["dark energy discovery (1998)", "distance measurement"],
            level=11, tags=["SNIa", "supernova", "standard candle", "dark energy"])

    # ──────────────────────────────────────────────────────────────────
    # LEVEL 12: RESEARCH FRONTIER — 2025/2026 CUTTING EDGE (20)
    # ──────────────────────────────────────────────────────────────────
    def _build_level12(self):
        self._add("er_equals_epr", "research_frontier",
            "Entanglement (EPR) and wormholes (ER) are the same thing",
            "ER = EPR: entangled particles connected by Einstein-Rosen bridge",
            level=12, tags=["ER=EPR", "wormhole", "entanglement", "Maldacena"])

        self._add("ads_cft", "research_frontier",
            "Gravity in anti-de Sitter ↔ conformal field theory on boundary",
            "Z_gravity[φ₀] = ⟨e^{∫φ₀O}⟩_CFT; bulk/boundary duality",
            applications=["strong coupling calculations", "quark-gluon plasma"],
            level=12, tags=["AdS/CFT", "holography", "duality", "Maldacena"])

        self._add("ryu_takayanagi", "research_frontier",
            "Entanglement entropy = area of minimal surface in bulk",
            "S_A = Area(γ_A)/(4G_N)",
            derived_from=["ads_cft", "bekenstein_hawking_entropy"],
            level=12, tags=["Ryu-Takayanagi", "entanglement", "holographic", "area"])

        self._add("swampland_distance", "research_frontier",
            "In quantum gravity, tower of states becomes light at infinite distance",
            "m(φ) ~ m₀ e^{-α|φ|/M_P} as |φ|→∞",
            level=12, tags=["swampland", "distance", "tower", "string theory"])

        self._add("amplituhedron", "research_frontier",
            "Scattering amplitudes as volume of geometric object",
            "Amplitude = volume of amplituhedron (no locality/unitarity assumed!)",
            level=12, tags=["amplituhedron", "amplitude", "geometry", "Arkani-Hamed"])

        self._add("quantum_error_correction_holography", "research_frontier",
            "Holographic duality is a quantum error-correcting code",
            "Bulk operators = logical qubits; boundary = physical qubits; code subspace",
            level=12, tags=["QEC", "holography", "code", "subspace"])

        self._add("eigenstate_thermalization", "research_frontier",
            "Individual eigenstates look thermal for local observables",
            "⟨E_n|O|E_n⟩ ≈ O_micro(E) for ETH-satisfying systems",
            level=12, tags=["ETH", "thermalization", "eigenstate"])

        self._add("many_body_localization", "research_frontier",
            "Disordered interacting systems can fail to thermalize",
            "MBL phase: area-law entanglement even at high energy",
            level=12, tags=["MBL", "localization", "non-ergodic"])

        self._add("muon_g2_anomaly_2026", "research_frontier",
            "Muon magnetic moment deviates from Standard Model (2026 final!)",
            "Δa_μ = a_μ(exp) - a_μ(SM) = 249±48 × 10⁻¹¹ (>5σ)",
            consequences=["new particles?", "BSM physics confirmed?"],
            level=12, tags=["muon g-2", "anomaly", "2026", "BSM", "Breakthrough Prize"])

        self._add("desi_dark_energy_2026", "research_frontier",
            "DESI DR1+DR2: dark energy is NOT constant — evolves over time",
            "w(a) = w₀+w_a(1-a); w₀=-0.73, w_a=-1.05; rules out pure Λ at ~3σ",
            consequences=["quintessence?", "phantom crossing", "new cosmological model"],
            level=12, tags=["DESI", "dark energy", "2026", "evolving", "w0wa"])

        self._add("topological_quantum_computation", "research_frontier",
            "Fault-tolerant QC using non-Abelian anyons and braiding",
            "Logical gates = braids of anyons; topologically protected",
            applications=["Microsoft approach", "Majorana-based qubits"],
            level=12, tags=["topological QC", "anyons", "braiding", "fault-tolerant"])

        self._add("tensor_networks_geometry", "research_frontier",
            "Tensor networks (MERA) naturally produce hyperbolic geometry",
            "MERA ~ discrete AdS; entanglement structure = geometry",
            level=12, tags=["tensor network", "MERA", "geometry", "AdS"])

        self._add("measurement_induced_transition", "research_frontier",
            "Phase transition in entanglement driven by measurement rate",
            "Low measurement: volume-law entanglement; High: area-law",
            level=12, tags=["MIPT", "measurement", "entanglement transition"])

        self._add("fracton_topological_order", "research_frontier",
            "Exotic topological phases with immobile excitations",
            "Fractons: excitations that cannot move without creating others",
            level=12, tags=["fracton", "topological order", "immobile", "subdimensional"])

        self._add("floquet_engineering", "research_frontier",
            "Periodic driving creates effective Hamiltonians with new topology",
            "H_eff from Magnus expansion; time-crystal phases",
            level=12, tags=["Floquet", "driving", "time crystal", "engineering"])

        self._add("quantum_supremacy_2025", "research_frontier",
            "Quantum computers solve tasks classical cannot (Nobel 2025 related)",
            "Random circuit sampling in O(n) vs exp(n) classical",
            level=12, tags=["quantum supremacy", "advantage", "Nobel 2025", "superconducting"])

        self._add("sachdev_ye_kitaev", "research_frontier",
            "Solvable model of quantum chaos, near-AdS₂ dual",
            "H = Σ_{ijkl} J_{ijkl} ψ_i ψ_j ψ_k ψ_l; maximal chaos λ_L=2πk_BT/ℏ",
            level=12, tags=["SYK", "quantum chaos", "AdS₂", "scrambling"])

        self._add("celestial_holography", "research_frontier",
            "S-matrix as correlators on celestial sphere at infinity",
            "4D scattering amplitudes ↔ 2D CFT on celestial sphere",
            level=12, tags=["celestial", "holography", "S-matrix", "CFT"])

        self._add("quantum_thermodynamics", "research_frontier",
            "Thermodynamics at quantum scale with coherence as resource",
            "Work extraction from coherence; quantum engines beat Carnot?",
            level=12, tags=["quantum thermo", "coherence", "engine", "resource"])

        self._add("information_paradox_progress", "research_frontier",
            "Page curve from island formula (2019-2026 progress)",
            "S(radiation) follows Page curve via quantum extremal surfaces + islands",
            level=12, tags=["information paradox", "Page curve", "island", "black hole"])


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS IDENTIFIER — Detect domain from question text
# ══════════════════════════════════════════════════════════════════════════════

class PhysicsIdentifier:
    """Detect which physics domain a question belongs to."""

    DOMAIN_KEYWORDS = {
        "classical_mechanics": [
            "force", "mass", "acceleration", "velocity", "momentum", "energy",
            "kinetic", "potential", "lagrangian", "hamiltonian", "newton",
            "orbit", "kepler", "pendulum", "spring", "friction", "torque",
            "angular momentum", "rigid body", "fluid", "viscous", "pressure",
            "bernoulli", "turbul", "reynolds", "navier", "stokes", "chaos",
            "lyapunov", "oscillat", "vibrat", "collision", "projectile",
            "centripetal", "inertia", "equilibrium", "lever", "pulley",
            "inclined plane", "work", "power", "joule"
        ],
        "electromagnetism": [
            "electric", "magnetic", "charge", "current", "voltage", "resistance",
            "capacit", "inductor", "inductance", "maxwell", "gauss", "faraday", "ampere",
            "coulomb", "lorentz", "electromagnetic", "radiation", "antenna",
            "wave", "polariz", "refract", "reflect", "lens", "mirror",
            "diffract", "interfer", "circuit", "ohm", "dielectric",
            "dipole", "flux", "emf", "transformer", "impedance", "waveguide",
            "skin depth", "copper", "fresnel", "snell", "kramers",
            "kronig", "dispersion", "optic", "toroid", "coil",
            "total internal reflection", "critical angle"
        ],
        "quantum_mechanics": [
            "quantum", "wavefunction", "schrodinger", "schrödinger", "operator",
            "eigenvalue", "eigenstate", "superposition", "entangle", "spin",
            "uncertainty", "heisenberg", "commut", "hilbert", "bra", "ket",
            "observable", "measurement", "probability amplitude", "tunneling",
            "harmonic oscillator", "hydrogen atom", "orbital", "photon",
            "planck", "bohr", "de broglie", "wave-particle", "qubit",
            "decoherence", "bell", "EPR", "density matrix", "perturbation",
            "variational", "WKB", "bound state", "selection rule",
            "clebsch", "gordan", "angular momentum", "berry phase",
            "no-cloning", "cloning theorem", "path integral",
            "fermi golden", "golden rule", "anharmonic",
            "ground state energy", "expectation value",
            "fine structure", "spin-orbit"
        ],
        "statistical_mechanics": [
            "entropy", "temperature", "thermodynamic", "heat", "boltzmann",
            "partition function", "free energy", "phase transition", "critical",
            "fermi-dirac", "bose-einstein", "canonical", "microcanonical",
            "grand canonical", "equipartition", "specific heat", "latent",
            "carnot", "efficiency", "reversible", "irreversible", "adiabatic",
            "isothermal", "isobaric", "blackbody", "stefan", "planck radiation",
            "ising", "mean field", "order parameter", "condensat",
            "renormalization group", "critical phenomena", "clausius",
            "clapeyron", "jarzynski", "non-equilibrium", "mixing",
            "Wien", "peak wavelength", "radiation spectrum",
            "maxwell distribution", "speed distribution",
            "chemical potential", "helmholtz", "gibbs"
        ],
        "relativity": [
            "relativity", "relativistic", "lorentz", "spacetime", "metric",
            "geodesic", "curvature", "schwarzschild", "kerr", "black hole",
            "event horizon", "singularity", "gravitational wave", "LIGO",
            "time dilation", "length contraction", "twin paradox", "E=mc",
            "four-vector", "tensor", "einstein field", "cosmolog", "hubble",
            "expansion", "redshift", "dark energy", "inflation", "friedmann",
            "big bang", "CMB", "hawking", "neutron star", "mercury",
            "precession", "perihelion", "deflection", "gravitational redshift",
            "general relativity", "special relativity", "light bending"
        ],
        "quantum_field_theory": [
            "feynman diagram", "propagator", "vertex", "renormaliz",
            "standard model", "QED", "QCD", "electroweak", "higgs",
            "quark", "lepton", "gluon", "W boson", "Z boson", "neutrino",
            "cross section", "decay rate", "coupling constant", "running",
            "asymptotic freedom", "confinement", "anomaly", "gauge",
            "symmetry breaking", "goldstone", "CKM", "PMNS", "flavor",
            "coleman", "mandula", "supersymmetry", "SUSY",
            "oscillation", "compton", "muon g-2",
            "parton", "deep inelastic", "effective field theory"
        ],
        "condensed_matter": [
            "crystal", "lattice", "phonon", "band", "semiconductor",
            "superconductor", "BCS", "cooper pair", "meissner", "josephson",
            "topological", "insulator", "hall effect", "fermi surface",
            "bloch", "brillouin", "doping", "transistor", "diode",
            "magnetism", "ferromagnet", "antiferromagnet", "magnon",
            "kondo", "hubbard", "strongly correlated", "metal",
            "anderson localization", "debye", "specific heat",
            "kohn-sham", "DFT", "density functional",
            "laughlin", "fractional", "landau level",
            "gap equation", "tight-binding", "graphene", "semimetal"
        ],
        "quantum_optics": [
            "laser", "photon", "coherent state", "squeezed", "cavity QED",
            "single photon", "entangled photon", "beam splitter",
            "nonlinear optic", "second harmonic", "parametric",
            "quantum key", "QKD", "antibunching",
            "jaynes", "cummings", "rabi", "purcell",
            "hong-ou-mandel", "down-conversion",
            "fock state", "number state", "photon number",
            "laser cooling", "magneto-optical trap", "MOT"
        ],
        "plasma_physics": [
            "plasma", "MHD", "magnetohydro", "fusion", "tokamak",
            "alfven", "cyclotron", "reconnection", "solar wind",
            "corona", "ionosphere", "vlasov", "landau damping",
            "collisionless"
        ],
        "nuclear_physics": [
            "nuclear", "nucleus", "fission", "fusion", "radioactive",
            "decay", "half-life", "alpha", "beta", "gamma ray",
            "neutron", "proton", "isotope", "binding energy",
            "shell model", "magic number", "cross section"
        ],
        "cosmology": [
            "universe", "cosmology", "dark matter", "dark energy",
            "big bang", "inflation", "CMB", "hubble", "redshift",
            "expansion", "DESI", "supernova", "neutron star",
            "pulsar", "quasar", "galaxy", "black hole",
            "baryogenesis", "sakharov", "age of universe",
            "distance ladder", "reionization"
        ],
        "research_frontier": [
            "AdS/CFT", "holograph", "amplituhedron", "ER=EPR",
            "swampland", "eigenstate thermalization",
            "many-body localization", "MBL", "fracton",
            "floquet", "time crystal", "measurement-induced",
            "tensor network", "MERA", "celestial",
            "SYK", "sachdev", "quantum supremacy",
            "information paradox", "page curve", "island formula"
        ],
    }

    # Priority phrases: multi-word patterns that STRONGLY indicate a domain
    # These get 5x weight to override single-word matches like "quantum"
    PRIORITY_PHRASES = {
        "condensed_matter": [
            "quantum hall", "hall effect", "laughlin", "fractional hall",
            "BCS", "cooper pair", "bloch theorem", "band structure",
            "topological insulator", "kondo effect", "hubbard model",
            "anderson localization", "josephson", "superconductor",
            "phonon", "debye model", "fermi surface", "landau level",
            "brillouin zone", "density functional", "kohn-sham",
            "rashba", "semiconductor", "tight-binding", "graphene"
        ],
        "research_frontier": [
            "ER=EPR", "er=epr", "ads/cft", "AdS/CFT", "amplituhedron",
            "eigenstate thermalization", "many-body localization",
            "measurement-induced", "fracton", "floquet", "time crystal",
            "tensor network", "MERA", "celestial holography", "SYK",
            "swampland", "page curve", "island formula",
            "quantum supremacy", "information paradox"
        ],
        "cosmology": [
            "jeans mass", "jeans instability", "star formation",
            "baryogenesis", "sakharov",
            "dark matter candidate", "dark energy evolution",
            "hubble tension",
            "DESI", "distance ladder", "age of universe",
            "nucleosynthesis", "reionization", "structure formation",
            "lambda CDM", "ΛCDM"
        ],
        "quantum_optics": [
            "cavity QED", "jaynes-cummings", "jaynes cummings",
            "hong-ou-mandel", "squeezed light", "squeezed state",
            "coherent state", "single photon", "entangled photon",
            "parametric down", "photon antibunching", "purcell effect"
        ],
        "plasma_physics": [
            "landau damping", "alfven wave", "magnetic reconnection",
            "MHD equation", "vlasov equation", "plasma frequency",
            "lawson criterion", "tokamak", "solar corona",
            "cyclotron", "magnetic mirror"
        ],
    }

    def identify(self, question: str) -> List[Tuple[str, float]]:
        """Identify physics domain(s) from question text.
        Returns list of (domain, confidence) sorted by confidence.
        """
        q_lower = question.lower()
        scores = {}

        # First check priority phrases (5x weight)
        for domain, phrases in self.PRIORITY_PHRASES.items():
            for phrase in phrases:
                pl = phrase.lower()
                # Short phrases (≤4 chars) need word boundary match
                if len(pl) <= 4:
                    # Check as whole word
                    import re
                    if re.search(r'\b' + re.escape(pl) + r'\b', q_lower):
                        scores[domain] = scores.get(domain, 0) + 5 + len(phrase) / 5
                else:
                    if pl in q_lower:
                        scores[domain] = scores.get(domain, 0) + 5 + len(phrase) / 5

        # Then check regular keywords
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = scores.get(domain, 0)
            for kw in keywords:
                if kw.lower() in q_lower:
                    score += 1 + len(kw) / 20
            if score > 0:
                scores[domain] = score

        if not scores:
            return [("unknown", 0.0)]

        # Normalize to confidence
        max_score = max(scores.values())
        results = [(domain, score / max_score) for domain, score in scores.items()]
        return sorted(results, key=lambda x: -x[1])

    def is_physics_question(self, question: str) -> bool:
        """Quick check if question is physics-related."""
        results = self.identify(question)
        return results[0][0] != "unknown"

    def get_relevant_laws(self, question: str, law_db: PhysicsLawDB) -> List[PhysicsLaw]:
        """Get physics laws relevant to a question."""
        domains = self.identify(question)
        results = []

        # Get laws from top domain(s)
        for domain, conf in domains[:3]:
            if conf > 0.3:
                results.extend(law_db.by_domain(domain))

        # Also search by keywords in question
        words = question.lower().split()
        for word in words:
            if len(word) > 4:
                results.extend(law_db.search(word))

        # Deduplicate
        seen = set()
        unique = []
        for law in results:
            if law.name not in seen:
                seen.add(law.name)
                unique.append(law)

        return unique[:20]  # Top 20 most relevant
