"""
PROMETHEUS PHYSICS ENGINE — Phase 3: Classical + EM Solvers
Built by: Ghias + Kiro

Solvers that compute numerical answers from first principles:
  - NewtonianSolver: F=ma, projectiles, orbits, energy, collisions
  - LagrangianSolver: generalized coords, EOM, normal modes
  - EMSolver: Coulomb, Gauss, circuits, EM waves, radiation
  - WaveSolver: interference, diffraction, Doppler, optics
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


# ══════════════════════════════════════════════════════════════════════════════
# NEWTONIAN SOLVER — F=ma, projectiles, orbits, energy, collisions
# ══════════════════════════════════════════════════════════════════════════════

class NewtonianSolver:
    """Solve classical mechanics problems using Newton's laws + energy/momentum."""

    G = 6.674e-11  # gravitational constant
    g = 9.81       # surface gravity

    # ── Projectile motion ──

    def projectile(self, v0: float, angle_deg: float, h0: float = 0.0,
                   g: float = 9.81) -> Dict[str, float]:
        """Solve projectile motion. Returns range, max height, time of flight."""
        theta = math.radians(angle_deg)
        vx = v0 * math.cos(theta)
        vy = v0 * math.sin(theta)

        # Time of flight (landing at same height or h=0)
        # h0 + vy*t - 0.5*g*t^2 = 0
        disc = vy**2 + 2*g*h0
        if disc < 0:
            return {"error": "no real solution"}
        t_flight = (vy + math.sqrt(disc)) / g

        R = vx * t_flight
        h_max = h0 + vy**2 / (2*g)
        t_max_h = vy / g

        return {
            "range": R,
            "max_height": h_max,
            "time_of_flight": t_flight,
            "time_to_max_height": t_max_h,
            "vx": vx, "vy0": vy,
            "impact_speed": math.sqrt(vx**2 + (vy - g*t_flight)**2),
            "formula": f"R = v₀²sin(2θ)/g = {v0**2*math.sin(2*theta)/g:.4f} m (for h0=0)"
        }

    # ── Circular / orbital motion ──

    def circular_orbit(self, M: float, r: float) -> Dict[str, float]:
        """Orbital parameters for circular orbit around mass M at radius r."""
        v = math.sqrt(self.G * M / r)
        T = 2 * math.pi * r / v
        a_cent = v**2 / r
        E = -self.G * M / (2*r)  # total energy (virial theorem)
        L = M * v * r  # angular momentum (per unit mass: v*r)

        return {
            "orbital_speed": v,
            "period": T,
            "centripetal_acceleration": a_cent,
            "total_energy_per_mass": -self.G*M/(2*r),
            "angular_momentum_per_mass": v*r,
            "escape_speed": math.sqrt(2*self.G*M/r),
            "formula": "v = √(GM/r), T = 2πr/v, E = -GMm/2r"
        }

    def kepler_third(self, M: float, a: float) -> float:
        """Period from Kepler's 3rd law: T² = 4π²a³/GM."""
        return 2*math.pi*math.sqrt(a**3 / (self.G*M))

    def escape_velocity(self, M: float, r: float) -> float:
        """Escape velocity from surface of mass M at radius r."""
        return math.sqrt(2*self.G*M/r)

    # ── Energy methods ──

    def energy_conservation(self, m: float, v1: float, h1: float,
                           h2: float, friction_work: float = 0.0) -> float:
        """Find v2 using energy conservation: ½mv1²+mgh1 = ½mv2²+mgh2+W_friction."""
        KE1 = 0.5*m*v1**2
        PE1 = m*self.g*h1
        PE2 = m*self.g*h2
        KE2 = KE1 + PE1 - PE2 - friction_work
        if KE2 < 0:
            return 0.0  # stops
        return math.sqrt(2*KE2/m)

    def work_energy(self, F: float, d: float, angle_deg: float = 0.0) -> float:
        """Work done by force F over distance d at angle to displacement."""
        return F * d * math.cos(math.radians(angle_deg))

    # ── Collisions ──

    def elastic_collision_1d(self, m1: float, v1: float,
                             m2: float, v2: float) -> Tuple[float, float]:
        """1D elastic collision: returns (v1_final, v2_final)."""
        v1f = ((m1-m2)*v1 + 2*m2*v2) / (m1+m2)
        v2f = ((m2-m1)*v2 + 2*m1*v1) / (m1+m2)
        return v1f, v2f

    def inelastic_collision(self, m1: float, v1: float,
                            m2: float, v2: float) -> Tuple[float, float]:
        """Perfectly inelastic (stick together). Returns (v_final, KE_lost)."""
        vf = (m1*v1 + m2*v2) / (m1+m2)
        KE_before = 0.5*m1*v1**2 + 0.5*m2*v2**2
        KE_after = 0.5*(m1+m2)*vf**2
        return vf, KE_before - KE_after

    # ── Simple harmonic motion ──

    def shm(self, m: float = None, k: float = None, L: float = None,
            g: float = 9.81) -> Dict[str, float]:
        """Simple harmonic motion parameters.
        Provide (m, k) for spring or (L) for pendulum."""
        if k is not None and m is not None:
            omega = math.sqrt(k/m)
            T = 2*math.pi/omega
            f = 1/T
            return {"omega": omega, "period": T, "frequency": f,
                    "formula": "ω=√(k/m), T=2π√(m/k)"}
        elif L is not None:
            omega = math.sqrt(g/L)
            T = 2*math.pi/omega
            f = 1/T
            return {"omega": omega, "period": T, "frequency": f,
                    "formula": "ω=√(g/L), T=2π√(L/g)"}
        return {"error": "provide (m,k) or L"}

    # ── Forces ──

    def gravitational_force(self, m1: float, m2: float, r: float) -> float:
        """Newton's law of gravitation: F = GMm/r²."""
        return self.G * m1 * m2 / r**2

    def spring_force(self, k: float, x: float) -> float:
        """Hooke's law: F = -kx."""
        return -k * x

    def centripetal(self, m: float, v: float, r: float) -> float:
        """Centripetal force: F = mv²/r."""
        return m * v**2 / r

    def friction(self, mu: float, N: float) -> float:
        """Friction force: f = μN."""
        return mu * N

    # ── Inclined plane ──

    def inclined_plane(self, m: float, angle_deg: float, mu: float = 0.0) -> Dict[str, float]:
        """Forces and acceleration on inclined plane."""
        theta = math.radians(angle_deg)
        N = m * self.g * math.cos(theta)
        F_gravity_parallel = m * self.g * math.sin(theta)
        F_friction = mu * N
        F_net = F_gravity_parallel - F_friction
        a = F_net / m if F_net > 0 else 0.0

        return {
            "normal_force": N,
            "gravity_parallel": F_gravity_parallel,
            "friction_force": F_friction,
            "net_force": F_net,
            "acceleration": a,
            "formula": "a = g(sinθ - μcosθ)"
        }

    # ── Moment of inertia ──

    def moment_of_inertia(self, shape: str, M: float, R: float = 0,
                          L: float = 0) -> float:
        """Moment of inertia for standard shapes."""
        shapes = {
            "solid_sphere": (2/5)*M*R**2,
            "hollow_sphere": (2/3)*M*R**2,
            "solid_cylinder": (1/2)*M*R**2,
            "hollow_cylinder": M*R**2,
            "thin_rod_center": (1/12)*M*L**2,
            "thin_rod_end": (1/3)*M*L**2,
            "disk": (1/2)*M*R**2,
            "ring": M*R**2,
            "solid_cone": (3/10)*M*R**2,
        }
        return shapes.get(shape, 0.0)

    # ── Torque and rotation ──

    def torque(self, F: float, r: float, angle_deg: float = 90.0) -> float:
        """Torque τ = r × F = rF sinθ."""
        return r * F * math.sin(math.radians(angle_deg))

    def angular_acceleration(self, torque: float, I: float) -> float:
        """α = τ/I."""
        return torque / I if I > 0 else 0.0


# ══════════════════════════════════════════════════════════════════════════════
# LAGRANGIAN SOLVER — Generalized coords, EOM, normal modes, Hamiltonian
# ══════════════════════════════════════════════════════════════════════════════

class LagrangianSolver:
    """Analytical mechanics: Lagrangian/Hamiltonian formulation."""

    # ── Standard Lagrangians (symbolic) ──

    @staticmethod
    def standard_lagrangians() -> Dict[str, Dict]:
        """Standard Lagrangians for common systems."""
        return {
            "free_particle": {
                "L": "½m(ẋ²+ẏ²+ż²)",
                "coords": "x, y, z",
                "EOM": "mẍ=0, mÿ=0, mz̈=0 (straight line)",
                "conserved": "p_x, p_y, p_z, E",
            },
            "harmonic_oscillator": {
                "L": "½mẋ² - ½kx²",
                "coords": "x",
                "EOM": "mẍ + kx = 0 → x(t) = A cos(ωt+φ), ω=√(k/m)",
                "conserved": "E = ½mẋ² + ½kx²",
                "hamiltonian": "H = p²/2m + ½kx²",
            },
            "simple_pendulum": {
                "L": "½mL²θ̇² + mgLcosθ",
                "coords": "θ",
                "EOM": "θ̈ + (g/L)sinθ = 0 → θ̈ + (g/L)θ = 0 (small angle)",
                "conserved": "E = ½mL²θ̇² - mgLcosθ",
                "period_small": "T = 2π√(L/g)",
            },
            "double_pendulum": {
                "L": "½(m₁+m₂)L₁²θ̇₁² + ½m₂L₂²θ̇₂² + m₂L₁L₂θ̇₁θ̇₂cos(θ₁-θ₂) + (m₁+m₂)gL₁cosθ₁ + m₂gL₂cosθ₂",
                "coords": "θ₁, θ₂",
                "EOM": "Coupled nonlinear ODEs (chaotic for large angles)",
                "conserved": "E (total energy only)",
                "notes": "Exhibits chaos; Lyapunov exponent > 0 for most ICs",
            },
            "central_force": {
                "L": "½m(ṙ² + r²θ̇²) - V(r)",
                "coords": "r, θ (polar)",
                "EOM": "m(r̈-rθ̇²) = -dV/dr; d(mr²θ̇)/dt = 0",
                "conserved": "E, L=mr²θ̇ (angular momentum)",
                "effective_potential": "V_eff(r) = V(r) + L²/(2mr²)",
            },
            "charged_particle_em": {
                "L": "½mv² - qφ + qv·A",
                "coords": "x, y, z",
                "EOM": "m𝐚 = q(E + v×B) (Lorentz force from Lagrangian)",
                "canonical_momentum": "p = mv + qA",
                "hamiltonian": "H = (p-qA)²/2m + qφ",
            },
            "coupled_oscillators": {
                "L": "½m(ẋ₁²+ẋ₂²) - ½k(x₁²+x₂²) - ½κ(x₁-x₂)²",
                "coords": "x₁, x₂",
                "EOM": "mẍ₁ = -(k+κ)x₁ + κx₂; mẍ₂ = κx₁ - (k+κ)x₂",
                "normal_modes": "ω₁=√(k/m) (in-phase), ω₂=√((k+2κ)/m) (out-of-phase)",
                "modal_coords": "q₁=(x₁+x₂)/√2, q₂=(x₁-x₂)/√2",
            },
            "rotating_frame": {
                "L": "½m|v_rot + Ω×r|² - V(r)",
                "coords": "rotating frame coords",
                "EOM": "ma_rot = F - 2m(Ω×v_rot) - m(Ω×(Ω×r))",
                "pseudo_forces": "Coriolis: -2m(Ω×v), Centrifugal: -mΩ×(Ω×r)",
            },
        }

    # ── Normal mode finder ──

    @staticmethod
    def normal_modes_2dof(m1: float, m2: float, k1: float, k2: float,
                          k_coupling: float) -> Dict[str, float]:
        """Find normal mode frequencies for 2-DOF coupled system.
        m1 ẍ₁ = -k1 x₁ - k_c(x₁-x₂)
        m2 ẍ₂ = -k2 x₂ - k_c(x₂-x₁)"""
        # For equal masses (most common case in physics):
        # ω² solutions of det(K-ω²M)=0
        a11 = (k1 + k_coupling) / m1
        a22 = (k2 + k_coupling) / m2
        a12 = -k_coupling / m1
        a21 = -k_coupling / m2

        # Eigenvalues of the matrix [[a11,a12],[a21,a22]]
        trace = a11 + a22
        det = a11*a22 - a12*a21
        disc = trace**2 - 4*det
        if disc < 0:
            return {"error": "complex frequencies (damped)"}

        omega1_sq = (trace - math.sqrt(disc)) / 2
        omega2_sq = (trace + math.sqrt(disc)) / 2

        omega1 = math.sqrt(max(omega1_sq, 0))
        omega2 = math.sqrt(max(omega2_sq, 0))

        return {
            "omega1": omega1,
            "omega2": omega2,
            "f1": omega1/(2*math.pi),
            "f2": omega2/(2*math.pi),
            "T1": 2*math.pi/omega1 if omega1 > 0 else float('inf'),
            "T2": 2*math.pi/omega2 if omega2 > 0 else float('inf'),
            "formula": "ω² from det(K-ω²M)=0"
        }

    # ── Hamiltonian from Lagrangian ──

    @staticmethod
    def legendre_transform_info() -> Dict[str, str]:
        """How to go from L to H."""
        return {
            "definition": "H(q,p) = Σ pᵢq̇ᵢ - L(q,q̇)",
            "canonical_momentum": "pᵢ = ∂L/∂q̇ᵢ",
            "hamilton_equations": "q̇ᵢ = ∂H/∂pᵢ, ṗᵢ = -∂H/∂qᵢ",
            "energy": "H = E if L has no explicit time dependence",
            "poisson_bracket": "{f,g} = Σ(∂f/∂qᵢ ∂g/∂pᵢ - ∂f/∂pᵢ ∂g/∂qᵢ)",
            "time_evolution": "df/dt = {f,H} + ∂f/∂t",
        }

    # ── Effective potential ──

    @staticmethod
    def effective_potential(r: float, L: float, m: float, V_func=None,
                           M_central: float = 0) -> float:
        """V_eff(r) = V(r) + L²/(2mr²) for central force problem.
        If M_central given, uses V = -GMm/r (gravity)."""
        centrifugal = L**2 / (2*m*r**2) if r > 0 else float('inf')
        if V_func:
            return V_func(r) + centrifugal
        elif M_central > 0:
            G = 6.674e-11
            return -G*M_central*m/r + centrifugal
        return centrifugal

    # ── Euler-Lagrange solver (numerical for 1D) ──

    @staticmethod
    def solve_eom_1d(F_func, x0: float, v0: float, dt: float = 0.01,
                     t_max: float = 10.0, m: float = 1.0) -> List[Tuple[float, float, float]]:
        """Solve mẍ = F(x, v, t) numerically using RK4.
        Returns list of (t, x, v)."""
        results = [(0.0, x0, v0)]
        x, v, t = x0, v0, 0.0

        while t < t_max:
            # RK4 for second-order ODE
            a1 = F_func(x, v, t) / m
            k1x = v
            k1v = a1

            a2 = F_func(x + 0.5*dt*k1x, v + 0.5*dt*k1v, t + 0.5*dt) / m
            k2x = v + 0.5*dt*k1v
            k2v = a2

            a3 = F_func(x + 0.5*dt*k2x, v + 0.5*dt*k2v, t + 0.5*dt) / m
            k3x = v + 0.5*dt*k2v
            k3v = a3

            a4 = F_func(x + dt*k3x, v + dt*k3v, t + dt) / m
            k4x = v + dt*k3v
            k4v = a4

            x += (dt/6)*(k1x + 2*k2x + 2*k3x + k4x)
            v += (dt/6)*(k1v + 2*k2v + 2*k3v + k4v)
            t += dt
            results.append((t, x, v))

        return results


# ══════════════════════════════════════════════════════════════════════════════
# EM SOLVER — Coulomb, Gauss, circuits, EM waves, radiation
# ══════════════════════════════════════════════════════════════════════════════

class EMSolver:
    """Solve electromagnetism problems from Maxwell's equations."""

    # Constants
    epsilon_0 = 8.854e-12   # F/m
    mu_0 = 1.2566e-6        # H/m
    c = 2.998e8             # m/s
    k_e = 8.988e9           # N·m²/C²
    e = 1.602e-19           # C

    # ── Electrostatics ──

    def coulomb_force(self, q1: float, q2: float, r: float) -> float:
        """F = kq₁q₂/r²."""
        return self.k_e * q1 * q2 / r**2

    def electric_field_point(self, q: float, r: float) -> float:
        """E = kq/r² (magnitude)."""
        return self.k_e * abs(q) / r**2

    def electric_field_line_charge(self, lam: float, r: float) -> float:
        """E from infinite line charge: E = λ/(2πε₀r)."""
        return lam / (2 * math.pi * self.epsilon_0 * r)

    def electric_field_plane(self, sigma: float) -> float:
        """E from infinite plane: E = σ/(2ε₀)."""
        return abs(sigma) / (2 * self.epsilon_0)

    def electric_field_sphere(self, Q: float, r: float, R: float) -> float:
        """E from uniformly charged sphere (radius R) at distance r.
        Inside: E = Qr/(4πε₀R³), Outside: E = Q/(4πε₀r²)."""
        if r >= R:
            return self.k_e * abs(Q) / r**2
        else:
            return self.k_e * abs(Q) * r / R**3

    def potential_point(self, q: float, r: float) -> float:
        """V = kq/r."""
        return self.k_e * q / r

    def capacitance_parallel_plate(self, A: float, d: float,
                                    epsilon_r: float = 1.0) -> float:
        """C = ε₀εᵣA/d for parallel plate capacitor."""
        return self.epsilon_0 * epsilon_r * A / d

    def capacitor_energy(self, C: float, V: float) -> float:
        """E = ½CV²."""
        return 0.5 * C * V**2

    # ── Magnetostatics ──

    def magnetic_field_wire(self, I: float, r: float) -> float:
        """B from infinite straight wire: B = μ₀I/(2πr)."""
        return self.mu_0 * abs(I) / (2 * math.pi * r)

    def magnetic_field_solenoid(self, n: float, I: float) -> float:
        """B inside solenoid: B = μ₀nI (n = turns per meter)."""
        return self.mu_0 * n * I

    def magnetic_field_loop(self, I: float, R: float, z: float = 0) -> float:
        """B on axis of circular loop at distance z from center.
        B = μ₀IR²/[2(R²+z²)^{3/2}]."""
        return self.mu_0 * I * R**2 / (2 * (R**2 + z**2)**1.5)

    def lorentz_force(self, q: float, v: float, B: float, angle_deg: float = 90) -> float:
        """F = qvBsinθ (magnetic part)."""
        return abs(q) * v * B * math.sin(math.radians(angle_deg))

    def cyclotron_frequency(self, q: float, B: float, m: float) -> float:
        """ω_c = |q|B/m."""
        return abs(q) * B / m

    def cyclotron_radius(self, m: float, v: float, q: float, B: float) -> float:
        """r_L = mv/(|q|B) (Larmor radius)."""
        return m * v / (abs(q) * B)

    # ── Circuits ──

    def ohm(self, V: float = None, I: float = None, R: float = None) -> float:
        """Ohm's law V=IR. Provide any two to get the third."""
        if V is None:
            return I * R
        elif I is None:
            return V / R
        else:
            return V / I

    def series_resistance(self, *resistors: float) -> float:
        """R_total = R1 + R2 + ..."""
        return sum(resistors)

    def parallel_resistance(self, *resistors: float) -> float:
        """1/R_total = 1/R1 + 1/R2 + ..."""
        return 1 / sum(1/r for r in resistors if r > 0)

    def rc_time_constant(self, R: float, C: float) -> float:
        """τ = RC."""
        return R * C

    def rl_time_constant(self, R: float, L: float) -> float:
        """τ = L/R."""
        return L / R

    def resonant_frequency(self, L: float, C: float) -> float:
        """f₀ = 1/(2π√(LC))."""
        return 1 / (2 * math.pi * math.sqrt(L * C))

    def impedance_rlc_series(self, R: float, L: float, C: float, f: float) -> complex:
        """Z = R + j(ωL - 1/ωC) for series RLC."""
        omega = 2 * math.pi * f
        XL = omega * L
        XC = 1 / (omega * C) if omega * C > 0 else float('inf')
        return complex(R, XL - XC)

    def power_ac(self, V_rms: float, I_rms: float, phi: float = 0) -> Dict[str, float]:
        """AC power: P=VIcosφ, Q=VIsinφ, S=VI."""
        return {
            "real_power": V_rms * I_rms * math.cos(phi),
            "reactive_power": V_rms * I_rms * math.sin(phi),
            "apparent_power": V_rms * I_rms,
            "power_factor": math.cos(phi),
        }

    # ── EM Waves ──

    def em_wave_speed(self, epsilon_r: float = 1.0, mu_r: float = 1.0) -> float:
        """v = c/√(εᵣμᵣ)."""
        return self.c / math.sqrt(epsilon_r * mu_r)

    def wavelength(self, f: float, v: float = None) -> float:
        """λ = v/f (default v=c)."""
        if v is None:
            v = self.c
        return v / f

    def poynting_magnitude(self, E: float, B: float = None) -> float:
        """S = E×B/μ₀ = E²/(μ₀c) for plane wave."""
        if B is not None:
            return E * B / self.mu_0
        return E**2 / (self.mu_0 * self.c)

    def radiation_pressure(self, I: float, absorbed: bool = True) -> float:
        """P_rad = I/c (absorbed) or 2I/c (reflected)."""
        return I / self.c if absorbed else 2*I / self.c

    # ── Radiation ──

    def larmor_power(self, q: float, a: float) -> float:
        """P = q²a²/(6πε₀c³) — power radiated by accelerating charge."""
        return q**2 * a**2 / (6 * math.pi * self.epsilon_0 * self.c**3)

    def dipole_radiation_power(self, p0: float, omega: float) -> float:
        """P = p₀²ω⁴/(12πε₀c³) — oscillating electric dipole."""
        return p0**2 * omega**4 / (12 * math.pi * self.epsilon_0 * self.c**3)

    def skin_depth(self, f: float, sigma: float, mu_r: float = 1.0) -> float:
        """δ = √(2/(ωμσ)) — skin depth in conductor."""
        omega = 2 * math.pi * f
        mu = self.mu_0 * mu_r
        return math.sqrt(2 / (omega * mu * sigma))

    # ── Optics shortcuts ──

    def snell(self, n1: float, theta1_deg: float, n2: float) -> float:
        """Snell's law: returns θ₂ in degrees. Returns -1 for total internal reflection."""
        sin_theta2 = n1 * math.sin(math.radians(theta1_deg)) / n2
        if abs(sin_theta2) > 1:
            return -1  # total internal reflection
        return math.degrees(math.asin(sin_theta2))

    def brewster_angle(self, n1: float, n2: float) -> float:
        """Brewster angle: tan(θ_B) = n2/n1."""
        return math.degrees(math.atan(n2 / n1))

    def critical_angle(self, n1: float, n2: float) -> float:
        """Critical angle for total internal reflection (n1 > n2)."""
        if n1 <= n2:
            return 90.0  # no TIR
        return math.degrees(math.asin(n2 / n1))


# ══════════════════════════════════════════════════════════════════════════════
# WAVE SOLVER — Interference, diffraction, Doppler, standing waves, optics
# ══════════════════════════════════════════════════════════════════════════════

class WaveSolver:
    """Solve wave physics problems: interference, diffraction, Doppler, optics."""

    c = 2.998e8  # speed of light

    # ── Basic wave properties ──

    def wave_equation(self, f: float, wavelength: float = None, v: float = None) -> Dict[str, float]:
        """v = fλ. Provide two to get the third."""
        if wavelength is not None and v is None:
            v = f * wavelength
        elif v is not None and wavelength is None:
            wavelength = v / f
        elif wavelength is not None and v is not None:
            f = v / wavelength
        return {"frequency": f, "wavelength": wavelength, "speed": v,
                "period": 1/f, "wave_number": 2*math.pi/wavelength if wavelength else 0,
                "angular_frequency": 2*math.pi*f}

    # ── Interference ──

    def double_slit(self, d: float, wavelength: float, L: float,
                    m: int = None) -> Dict[str, float]:
        """Young's double slit: d sinθ = mλ (bright), (m+½)λ (dark).
        d=slit separation, L=screen distance."""
        if m is not None:
            sin_theta = m * wavelength / d
            if abs(sin_theta) > 1:
                return {"error": "order too high"}
            theta = math.asin(sin_theta)
            y = L * math.tan(theta)
            return {"angle_rad": theta, "angle_deg": math.degrees(theta),
                    "position_y": y, "order": m, "type": "bright"}

        # Return fringe spacing
        dy = wavelength * L / d
        return {"fringe_spacing": dy, "formula": "Δy = λL/d",
                "central_max_width": 2*dy}

    def thin_film(self, n_film: float, thickness: float, wavelength: float,
                  n_above: float = 1.0, n_below: float = 1.5) -> Dict[str, str]:
        """Thin film interference condition.
        Phase change on reflection if going from low-n to high-n."""
        lambda_film = wavelength / n_film
        path_diff = 2 * thickness

        # Phase changes
        phase_top = math.pi if n_above < n_film else 0  # reflection at top
        phase_bot = math.pi if n_film < n_below else 0  # reflection at bottom

        net_phase = 2 * math.pi * path_diff / lambda_film + phase_top - phase_bot
        # Constructive if net_phase = 2mπ
        is_constructive = abs(net_phase % (2*math.pi)) < 0.3 or abs(net_phase % (2*math.pi) - 2*math.pi) < 0.3

        return {
            "optical_path_diff": 2 * n_film * thickness,
            "phase_shift_reflections": phase_top - phase_bot,
            "constructive_condition": f"2nt = (m+½)λ" if phase_top != phase_bot else "2nt = mλ",
            "minimum_thickness_constructive": wavelength / (4*n_film) if phase_top != phase_bot else wavelength / (2*n_film),
        }

    # ── Diffraction ──

    def single_slit(self, a: float, wavelength: float, L: float = None,
                    m: int = 1) -> Dict[str, float]:
        """Single slit diffraction: a sinθ = mλ gives dark fringes."""
        sin_theta = m * wavelength / a
        if abs(sin_theta) > 1:
            return {"error": "order too high"}
        theta = math.asin(sin_theta)
        result = {"angle_rad": theta, "angle_deg": math.degrees(theta),
                  "order": m, "type": "dark_fringe"}
        if L:
            result["position_y"] = L * math.tan(theta)
        # Central maximum half-width
        result["central_max_half_angle"] = math.degrees(math.asin(wavelength/a))
        return result

    def diffraction_grating(self, d: float, wavelength: float, m: int = 1) -> Dict[str, float]:
        """Grating equation: d sinθ = mλ. d = grating spacing."""
        sin_theta = m * wavelength / d
        if abs(sin_theta) > 1:
            return {"error": f"order {m} not possible", "max_order": int(d/wavelength)}
        theta = math.asin(sin_theta)
        return {"angle_rad": theta, "angle_deg": math.degrees(theta),
                "order": m, "max_order": int(d/wavelength),
                "resolving_power": m * (1/d) if d > 0 else 0}

    def rayleigh_criterion(self, wavelength: float, D: float) -> float:
        """Angular resolution: θ_min = 1.22 λ/D (circular aperture)."""
        return 1.22 * wavelength / D

    # ── Doppler effect ──

    def doppler_sound(self, f_source: float, v_sound: float,
                      v_observer: float = 0, v_source: float = 0) -> float:
        """Doppler for sound: f_obs = f_src × (v + v_obs)/(v + v_src).
        v_obs positive toward source, v_src positive away from observer."""
        return f_source * (v_sound + v_observer) / (v_sound + v_source)

    def doppler_light(self, f_source: float, v_relative: float) -> float:
        """Relativistic Doppler: f_obs = f_src × √((1-β)/(1+β)).
        v_relative positive = receding (redshift)."""
        beta = v_relative / self.c
        if abs(beta) >= 1:
            return 0.0
        return f_source * math.sqrt((1 - beta) / (1 + beta))

    def doppler_redshift(self, z: float, f_emit: float = None,
                         lambda_emit: float = None) -> Dict[str, float]:
        """Given redshift z: λ_obs = λ_emit(1+z), f_obs = f_emit/(1+z)."""
        result = {"redshift": z}
        if lambda_emit:
            result["lambda_observed"] = lambda_emit * (1 + z)
        if f_emit:
            result["f_observed"] = f_emit / (1 + z)
        result["velocity_approx"] = z * self.c if z < 0.3 else None
        return result

    # ── Standing waves ──

    def standing_wave_string(self, L: float, n: int, v: float = None,
                             T: float = None, mu: float = None) -> Dict[str, float]:
        """Standing waves on string fixed at both ends.
        f_n = nv/(2L), λ_n = 2L/n."""
        if v is None and T is not None and mu is not None:
            v = math.sqrt(T / mu)
        elif v is None:
            return {"error": "provide v or (T, mu)"}

        f_n = n * v / (2 * L)
        lambda_n = 2 * L / n

        return {"harmonic": n, "frequency": f_n, "wavelength": lambda_n,
                "speed": v, "nodes": n + 1, "antinodes": n,
                "formula": f"f_n = nv/(2L) = {n}×{v:.1f}/(2×{L}) = {f_n:.2f} Hz"}

    def standing_wave_pipe(self, L: float, n: int, v: float = 343.0,
                           open_both: bool = True) -> Dict[str, float]:
        """Standing waves in pipe.
        Open both ends: f_n = nv/(2L) (all harmonics)
        Closed one end: f_n = nv/(4L) (odd harmonics only, n=1,3,5,...)"""
        if open_both:
            f_n = n * v / (2*L)
            lambda_n = 2*L/n
        else:
            # Only odd harmonics
            n_odd = 2*n - 1
            f_n = n_odd * v / (4*L)
            lambda_n = 4*L/n_odd

        return {"harmonic": n, "frequency": f_n, "wavelength": lambda_n,
                "open_both": open_both}

    # ── Lens / Mirror optics ──

    def thin_lens(self, f: float = None, u: float = None, v: float = None) -> Dict[str, float]:
        """Thin lens equation: 1/f = 1/v - 1/u (sign convention: u<0 real object)."""
        # Using 1/f = 1/v + 1/u with real-is-positive convention
        if f is not None and u is not None:
            v = 1 / (1/f - 1/u) if abs(1/f - 1/u) > 1e-15 else float('inf')
        elif f is not None and v is not None:
            u = 1 / (1/f - 1/v) if abs(1/f - 1/v) > 1e-15 else float('inf')
        elif u is not None and v is not None:
            f = 1 / (1/u + 1/v) if abs(1/u + 1/v) > 1e-15 else float('inf')
        else:
            return {"error": "provide two of f, u, v"}

        magnification = -v/u if u != 0 else 0
        return {"focal_length": f, "object_distance": u, "image_distance": v,
                "magnification": magnification,
                "image_type": "real" if v > 0 else "virtual",
                "image_orientation": "inverted" if magnification < 0 else "upright"}

    def mirror(self, f: float = None, u: float = None, v: float = None,
               R: float = None) -> Dict[str, float]:
        """Mirror equation: 1/f = 1/v + 1/u, f = R/2."""
        if R is not None and f is None:
            f = R / 2
        return self.thin_lens(f=f, u=u, v=v)

    # ── Wave intensity ──

    def intensity_inverse_square(self, P: float, r: float) -> float:
        """I = P/(4πr²) for isotropic point source."""
        return P / (4 * math.pi * r**2)

    def decibel(self, I: float, I_ref: float = 1e-12) -> float:
        """Sound level in dB: L = 10 log₁₀(I/I₀)."""
        if I <= 0:
            return float('-inf')
        return 10 * math.log10(I / I_ref)

    def beat_frequency(self, f1: float, f2: float) -> float:
        """Beat frequency = |f₁ - f₂|."""
        return abs(f1 - f2)


# ══════════════════════════════════════════════════════════════════════════════
# QUANTUM SOLVER — Schrödinger, perturbation, angular momentum, scattering
# ══════════════════════════════════════════════════════════════════════════════

class QuantumSolver:
    """Solve quantum mechanics problems: energy levels, wavefunctions, transitions."""

    hbar = 1.0546e-34  # J·s
    m_e = 9.109e-31    # kg
    eV = 1.602e-19     # J
    a0 = 5.292e-11     # Bohr radius (m)

    # ── Infinite square well ──

    def infinite_well(self, n: int, L: float, m: float = None) -> Dict[str, float]:
        """Particle in infinite square well: E_n = n²π²ℏ²/(2mL²)."""
        if m is None:
            m = self.m_e
        E_n = (n**2 * math.pi**2 * self.hbar**2) / (2 * m * L**2)
        k_n = n * math.pi / L
        return {
            "energy_J": E_n, "energy_eV": E_n / self.eV,
            "quantum_number": n, "wavelength": 2*L/n,
            "wave_vector": k_n,
            "formula": f"E_n = n²π²ℏ²/(2mL²) = {E_n/self.eV:.6f} eV",
            "normalization": f"A = √(2/L) = {math.sqrt(2/L):.6f}",
        }

    # ── Harmonic oscillator ──

    def harmonic_oscillator(self, n: int, omega: float, m: float = None) -> Dict[str, float]:
        """QM harmonic oscillator: E_n = (n+½)ℏω."""
        if m is None:
            m = self.m_e
        E_n = (n + 0.5) * self.hbar * omega
        x_rms = math.sqrt((2*n+1) * self.hbar / (2*m*omega))
        return {
            "energy_J": E_n, "energy_eV": E_n / self.eV,
            "quantum_number": n, "zero_point_energy": 0.5*self.hbar*omega,
            "x_rms": x_rms,
            "formula": f"E_n = (n+½)ℏω = {E_n/self.eV:.6e} eV",
        }

    # ── Hydrogen atom ──

    def hydrogen(self, n: int, Z: int = 1) -> Dict[str, float]:
        """Hydrogen-like atom: E_n = -Z²×13.6eV/n²."""
        E_n_eV = -Z**2 * 13.6 / n**2
        r_n = n**2 * self.a0 / Z
        v_n = Z * 2.188e6 / n  # m/s (Bohr velocity)
        return {
            "energy_eV": E_n_eV, "energy_J": E_n_eV * self.eV,
            "n": n, "Z": Z,
            "radius_m": r_n, "radius_a0": n**2 / Z,
            "velocity": v_n,
            "degeneracy": 2 * n**2,
            "formula": f"E_n = -Z²×13.6/n² = {E_n_eV:.4f} eV",
            "ionization_energy_eV": abs(E_n_eV),
        }

    def hydrogen_transition(self, n_i: int, n_f: int, Z: int = 1) -> Dict[str, float]:
        """Transition energy and wavelength between hydrogen levels."""
        E_i = -Z**2 * 13.6 / n_i**2
        E_f = -Z**2 * 13.6 / n_f**2
        dE = E_f - E_i  # negative = emission
        wavelength = abs(1240e-9 / dE) if dE != 0 else float('inf')  # λ = hc/E in nm→m
        return {
            "delta_E_eV": dE, "photon_energy_eV": abs(dE),
            "wavelength_m": wavelength, "wavelength_nm": wavelength * 1e9,
            "frequency_Hz": abs(dE) * self.eV / (6.626e-34),
            "emission": dE < 0, "absorption": dE > 0,
            "series": "Lyman" if n_f==1 else "Balmer" if n_f==2 else "Paschen" if n_f==3 else "Brackett",
        }

    # ── Angular momentum ──

    def angular_momentum(self, l: int, m_l: int = None) -> Dict[str, float]:
        """Orbital angular momentum eigenvalues."""
        L_mag = self.hbar * math.sqrt(l*(l+1))
        result = {
            "l": l, "L_magnitude": L_mag,
            "L_squared": self.hbar**2 * l*(l+1),
            "m_l_range": list(range(-l, l+1)),
            "num_states": 2*l+1,
        }
        if m_l is not None:
            result["L_z"] = m_l * self.hbar
        return result

    def spin(self, s: float) -> Dict[str, float]:
        """Spin angular momentum."""
        S_mag = self.hbar * math.sqrt(s*(s+1))
        return {
            "s": s, "S_magnitude": S_mag,
            "S_squared": self.hbar**2 * s*(s+1),
            "m_s_range": [s - i for i in range(int(2*s+1))],
            "num_states": int(2*s+1),
        }

    def add_angular_momentum(self, j1: float, j2: float) -> Dict[str, list]:
        """Add two angular momenta: j ranges from |j1-j2| to j1+j2."""
        j_min = abs(j1 - j2)
        j_max = j1 + j2
        j_values = []
        j = j_min
        while j <= j_max + 0.01:
            j_values.append(j)
            j += 1
        total_states = int((2*j1+1)*(2*j2+1))
        return {"j_values": j_values, "j_min": j_min, "j_max": j_max,
                "total_states": total_states}

    # ── Uncertainty principle ──

    def uncertainty(self, dx: float = None, dp: float = None) -> Dict[str, float]:
        """Heisenberg: ΔxΔp ≥ ℏ/2. Given one, find minimum of other."""
        result = {"minimum_product": self.hbar/2}
        if dx is not None:
            result["min_dp"] = self.hbar / (2*dx)
            result["min_dv"] = self.hbar / (2*self.m_e*dx)
        if dp is not None:
            result["min_dx"] = self.hbar / (2*dp)
        return result

    # ── Tunneling ──

    def tunneling_rectangular(self, E: float, V0: float, L: float,
                              m: float = None) -> float:
        """Transmission through rectangular barrier of height V0, width L.
        T ≈ exp(-2κL) where κ = √(2m(V0-E))/ℏ for E < V0."""
        if m is None:
            m = self.m_e
        if E >= V0:
            return 1.0
        kappa = math.sqrt(2*m*(V0-E)) / self.hbar
        return math.exp(-2*kappa*L)

    # ── Expectation values ──

    def expectation_ho_x2(self, n: int, m: float, omega: float) -> float:
        """⟨x²⟩ for harmonic oscillator state n: ⟨x²⟩ = (n+½)ℏ/(mω)."""
        return (n + 0.5) * self.hbar / (m * omega)

    def expectation_ho_p2(self, n: int, m: float, omega: float) -> float:
        """⟨p²⟩ for harmonic oscillator state n: ⟨p²⟩ = (n+½)mℏω."""
        return (n + 0.5) * m * self.hbar * omega

    def expectation_hydrogen_r(self, n: int, l: int) -> float:
        """⟨r⟩ for hydrogen: ⟨r⟩ = a₀[3n²-l(l+1)]/(2)."""
        return self.a0 * (3*n**2 - l*(l+1)) / 2


# ══════════════════════════════════════════════════════════════════════════════
# STATISTICAL MECHANICS SOLVER — Partition functions, thermodynamics
# ══════════════════════════════════════════════════════════════════════════════

class StatMechSolver:
    """Solve statistical mechanics: partition functions, ensembles, phase transitions."""

    kB = 1.381e-23  # J/K
    h = 6.626e-34   # J·s
    NA = 6.022e23   # mol⁻¹

    # ── Partition functions ──

    def partition_ideal_gas(self, T: float, V: float, N: int, m: float) -> Dict[str, float]:
        """Partition function for ideal gas (classical).
        Z = (V/λ³)^N / N! where λ = h/√(2πmkT)."""
        lam = self.h / math.sqrt(2*math.pi*m*self.kB*T)  # thermal wavelength
        z1 = V / lam**3  # single-particle Z
        # ln(Z_N) = N ln(z1) - N ln(N) + N (Stirling)
        ln_Z = N * math.log(z1) - N*math.log(N) + N
        F = -self.kB * T * ln_Z
        S = -F/T + N*self.kB*(5/2 + math.log(z1/N))  # Sackur-Tetrode
        P = N * self.kB * T / V
        E = 1.5 * N * self.kB * T

        return {
            "thermal_wavelength": lam,
            "ln_Z": ln_Z,
            "free_energy": F,
            "entropy": S,
            "pressure": P,
            "energy": E,
            "heat_capacity_V": 1.5*N*self.kB,
            "formula": "PV=NkT, E=(3/2)NkT, S=Nk[5/2+ln(V/Nλ³)]"
        }

    def partition_harmonic(self, T: float, omega: float) -> Dict[str, float]:
        """Partition function for quantum harmonic oscillator.
        Z = 1/(2sinh(βℏω/2)) = e^{-βℏω/2}/(1-e^{-βℏω})."""
        hbar = 1.0546e-34
        beta = 1/(self.kB*T)
        x = beta * hbar * omega / 2
        if x > 500:
            Z = math.exp(-x)
        else:
            Z = 1/(2*math.sinh(x))
        E = hbar*omega*(0.5 + 1/(math.exp(2*x)-1))
        Cv = self.kB * (2*x/math.sinh(2*x))**2 if x < 500 else 0

        return {"Z": Z, "energy": E, "heat_capacity": Cv,
                "formula": "Z=1/[2sinh(ℏω/2kT)], E=ℏω[½+1/(e^{ℏω/kT}-1)]"}

    def partition_two_level(self, T: float, epsilon: float) -> Dict[str, float]:
        """Two-level system with energies 0, ε."""
        beta = 1/(self.kB*T)
        Z = 1 + math.exp(-beta*epsilon)
        E = epsilon / (math.exp(beta*epsilon) + 1)
        # Schottky heat capacity
        x = beta*epsilon
        Cv = self.kB * x**2 * math.exp(x) / (1+math.exp(x))**2

        return {"Z": Z, "energy": E, "heat_capacity": Cv,
                "probability_excited": 1/(1+math.exp(beta*epsilon)),
                "formula": "Schottky anomaly: peak Cv at kT≈0.42ε"}

    # ── Thermodynamic relations ──

    def ideal_gas(self, n: float = None, P: float = None, V: float = None,
                  T: float = None) -> Dict[str, float]:
        """PV = nRT. Provide 3 to get the 4th."""
        R = 8.314
        if T is None and n and P and V:
            T = P*V/(n*R)
        elif P is None and n and V and T:
            P = n*R*T/V
        elif V is None and n and P and T:
            V = n*R*T/P
        elif n is None and P and V and T:
            n = P*V/(R*T)
        else:
            return {"error": "provide exactly 3 of n, P, V, T"}
        return {"n": n, "P": P, "V": V, "T": T, "R": R}

    def carnot(self, T_hot: float, T_cold: float) -> Dict[str, float]:
        """Carnot cycle efficiency and COP."""
        eta = 1 - T_cold/T_hot
        COP_heat = T_hot/(T_hot-T_cold)
        COP_cool = T_cold/(T_hot-T_cold)
        return {"efficiency": eta, "COP_heat_pump": COP_heat,
                "COP_refrigerator": COP_cool,
                "formula": "η = 1-Tc/Th"}

    def stefan_boltzmann(self, T: float, A: float = 1.0,
                         emissivity: float = 1.0) -> float:
        """Power radiated: P = εσAT⁴."""
        sigma = 5.670e-8
        return emissivity * sigma * A * T**4

    def wien_peak(self, T: float) -> float:
        """Wien's law: λ_max = b/T."""
        b = 2.898e-3
        return b / T

    # ── Quantum statistics ──

    def fermi_energy(self, n: float, m: float = None) -> float:
        """Fermi energy for free electron gas: E_F = (ℏ²/2m)(3π²n)^{2/3}."""
        if m is None:
            m = 9.109e-31
        hbar = 1.0546e-34
        return (hbar**2 / (2*m)) * (3*math.pi**2*n)**(2/3)

    def fermi_dirac(self, E: float, mu: float, T: float) -> float:
        """Fermi-Dirac distribution: f(E) = 1/(e^{(E-μ)/kT}+1)."""
        x = (E - mu)/(self.kB*T)
        if x > 500:
            return 0.0
        if x < -500:
            return 1.0
        return 1/(math.exp(x)+1)

    def bose_einstein(self, E: float, mu: float, T: float) -> float:
        """Bose-Einstein distribution: f(E) = 1/(e^{(E-μ)/kT}-1)."""
        x = (E - mu)/(self.kB*T)
        if x > 500:
            return 0.0
        if x < 0.01:
            return self.kB*T/(E-mu) if E > mu else float('inf')
        return 1/(math.exp(x)-1)

    def bec_temperature(self, n: float, m: float) -> float:
        """BEC critical temperature: T_c = (2πℏ²/mkB)(n/ζ(3/2))^{2/3}."""
        hbar = 1.0546e-34
        zeta_32 = 2.612  # ζ(3/2)
        return (2*math.pi*hbar**2/(m*self.kB)) * (n/zeta_32)**(2/3)

    # ── Phase transitions ──

    def ising_2d_tc(self, J: float) -> float:
        """Onsager's exact T_c for 2D square Ising: kT_c/J = 2/ln(1+√2)."""
        return 2*J / (self.kB * math.log(1+math.sqrt(2)))

    def landau_free_energy(self, T: float, Tc: float, eta: float,
                           a0: float = 1.0, b: float = 1.0) -> float:
        """Landau free energy: F = a₀(T-Tc)η² + bη⁴."""
        return a0*(T-Tc)*eta**2 + b*eta**4

    def landau_order_parameter(self, T: float, Tc: float,
                                a0: float = 1.0, b: float = 1.0) -> float:
        """Equilibrium order parameter from Landau theory.
        η = 0 for T>Tc, η = √(a₀(Tc-T)/2b) for T<Tc."""
        if T >= Tc:
            return 0.0
        return math.sqrt(a0*(Tc-T)/(2*b))

    def clausius_clapeyron(self, dP_dT: float = None, L: float = None,
                           T: float = None, dV: float = None) -> Dict[str, float]:
        """Clausius-Clapeyron: dP/dT = L/(TΔV). Provide 3 to get 4th."""
        if dP_dT is None and L and T and dV:
            dP_dT = L/(T*dV)
        elif L is None and dP_dT and T and dV:
            L = dP_dT*T*dV
        elif T is None and dP_dT and L and dV:
            T = L/(dP_dT*dV)
        elif dV is None and dP_dT and L and T:
            dV = L/(dP_dT*T)
        return {"dP_dT": dP_dT, "latent_heat": L, "T": T, "delta_V": dV}


# ══════════════════════════════════════════════════════════════════════════════
# RELATIVITY SOLVER — SR/GR calculations
# ══════════════════════════════════════════════════════════════════════════════

class RelativitySolver:
    """Solve special and general relativity problems."""

    c = 2.998e8
    G = 6.674e-11
    hbar = 1.0546e-34
    kB = 1.381e-23

    def gamma(self, v: float) -> float:
        """Lorentz factor γ = 1/√(1-v²/c²)."""
        beta = v/self.c
        return 1/math.sqrt(1 - beta**2)

    def time_dilation(self, dt_proper: float, v: float) -> float:
        """Δt = γΔτ — dilated time in lab frame."""
        return self.gamma(v) * dt_proper

    def length_contraction(self, L_proper: float, v: float) -> float:
        """L = L₀/γ — contracted length."""
        return L_proper / self.gamma(v)

    def relativistic_energy(self, m: float, v: float) -> Dict[str, float]:
        """E = γmc², KE = (γ-1)mc², p = γmv."""
        g = self.gamma(v)
        E = g * m * self.c**2
        KE = (g-1) * m * self.c**2
        p = g * m * v
        return {"total_energy": E, "kinetic_energy": KE, "momentum": p,
                "rest_energy": m*self.c**2, "gamma": g}

    def energy_momentum(self, E: float = None, p: float = None,
                        m: float = None) -> Dict[str, float]:
        """E² = (pc)² + (mc²)². Provide 2 to get 3rd."""
        if m is not None and p is not None:
            E = math.sqrt((p*self.c)**2 + (m*self.c**2)**2)
        elif E is not None and p is not None:
            mc2_sq = E**2 - (p*self.c)**2
            m = math.sqrt(max(mc2_sq, 0)) / self.c**2
        elif E is not None and m is not None:
            p = math.sqrt(max(E**2 - (m*self.c**2)**2, 0)) / self.c
        return {"E": E, "p": p, "m": m}

    def schwarzschild_radius(self, M: float) -> float:
        """r_s = 2GM/c²."""
        return 2*self.G*M/self.c**2

    def hawking_temperature(self, M: float) -> float:
        """T_H = ℏc³/(8πGMk_B)."""
        return self.hbar*self.c**3 / (8*math.pi*self.G*M*self.kB)

    def gravitational_redshift(self, M: float, r_emit: float, r_obs: float = None) -> float:
        """z = 1/√(1-r_s/r) - 1 for emission at r near mass M."""
        rs = self.schwarzschild_radius(M)
        if r_obs is None:  # observer at infinity
            return 1/math.sqrt(1 - rs/r_emit) - 1
        return math.sqrt((1-rs/r_obs)/(1-rs/r_emit)) - 1

    def orbital_precession(self, M: float, a: float, e: float) -> float:
        """GR perihelion precession per orbit: Δφ = 6πGM/(c²a(1-e²))."""
        return 6*math.pi*self.G*M / (self.c**2 * a * (1-e**2))

    def light_deflection(self, M: float, b: float) -> float:
        """Deflection angle: Δθ = 4GM/(c²b) for light passing at impact parameter b."""
        return 4*self.G*M / (self.c**2 * b)

    def cosmological_redshift_to_distance(self, z: float, H0: float = 70.0) -> Dict[str, float]:
        """Approximate distance from redshift (for z << 1: d ≈ cz/H0)."""
        H0_si = H0 * 1000 / (3.086e22)  # km/s/Mpc → 1/s
        d_proper = self.c * z / H0_si if z < 0.3 else None
        d_Mpc = self.c * z / (H0 * 1000) * 1e-6 if z < 0.3 else None
        return {"redshift": z, "distance_m": d_proper,
                "distance_Mpc": d_Mpc,
                "lookback_time_approx": z / H0_si if z < 0.3 else None,
                "note": "valid for z<<1" if z < 0.3 else "need full cosmology for z>0.3"}

    def friedmann_critical_density(self, H0: float = 70.0) -> float:
        """ρ_c = 3H²/(8πG)."""
        H0_si = H0 * 1000 / (3.086e22)
        return 3*H0_si**2 / (8*math.pi*self.G)


# ══════════════════════════════════════════════════════════════════════════════
# NUCLEAR SOLVER — Binding energy, decay, reactions
# ══════════════════════════════════════════════════════════════════════════════

class NuclearSolver:
    """Solve nuclear physics problems: binding energy, decay, reactions."""

    # Semi-empirical mass formula coefficients (MeV)
    a_V = 15.56   # volume
    a_S = 17.23   # surface
    a_C = 0.697   # Coulomb
    a_A = 23.285  # asymmetry
    a_P = 12.0    # pairing

    u_MeV = 931.494  # 1 amu in MeV/c²
    m_p = 938.272    # proton mass MeV
    m_n = 939.565    # neutron mass MeV

    def binding_energy(self, Z: int, A: int) -> Dict[str, float]:
        """Semi-empirical mass formula B(Z,A)."""
        N = A - Z
        # Pairing term
        if A % 2 == 1:
            delta = 0
        elif Z % 2 == 0:
            delta = self.a_P / A**0.5
        else:
            delta = -self.a_P / A**0.5

        B = (self.a_V*A - self.a_S*A**(2/3) - self.a_C*Z*(Z-1)/A**(1/3)
             - self.a_A*(N-Z)**2/A + delta)

        return {
            "binding_energy_MeV": B,
            "binding_per_nucleon": B/A,
            "Z": Z, "N": N, "A": A,
            "volume": self.a_V*A,
            "surface": -self.a_S*A**(2/3),
            "coulomb": -self.a_C*Z*(Z-1)/A**(1/3),
            "asymmetry": -self.a_A*(N-Z)**2/A,
            "pairing": delta,
        }

    def q_value(self, reactant_masses: List[float], product_masses: List[float]) -> float:
        """Q = (Σm_reactants - Σm_products)c² in MeV (masses in MeV/c²)."""
        return sum(reactant_masses) - sum(product_masses)

    def half_life_to_decay_constant(self, t_half: float) -> float:
        """λ = ln(2)/t_half."""
        return math.log(2) / t_half

    def decay_remaining(self, N0: float, t: float, t_half: float) -> float:
        """N(t) = N₀ × 2^{-t/t_half}."""
        return N0 * 2**(-t/t_half)

    def activity(self, N: float, t_half: float) -> float:
        """A = λN = N ln(2)/t_half."""
        return N * math.log(2) / t_half

    def dt_fusion_energy(self) -> Dict[str, float]:
        """D-T fusion: D + T → He-4 + n + 17.6 MeV."""
        return {"Q_MeV": 17.6, "reaction": "²H + ³H → ⁴He + n",
                "deuterium_mass": 2.0141, "tritium_mass": 3.0160,
                "helium4_mass": 4.0026, "neutron_energy_MeV": 14.1,
                "alpha_energy_MeV": 3.5}


# ══════════════════════════════════════════════════════════════════════════════
# ASTROPHYSICS SOLVER — Stellar, cosmological calculations
# ══════════════════════════════════════════════════════════════════════════════

class AstroSolver:
    """Solve astrophysics and cosmology problems."""

    G = 6.674e-11; c = 2.998e8; kB = 1.381e-23
    sigma = 5.670e-8  # Stefan-Boltzmann
    M_sun = 1.989e30; R_sun = 6.957e8; L_sun = 3.828e26
    pc = 3.086e16     # parsec in meters

    def luminosity(self, R: float, T: float) -> float:
        """L = 4πR²σT⁴ (Stefan-Boltzmann for star)."""
        return 4*math.pi*R**2*self.sigma*T**4

    def absolute_magnitude(self, L: float) -> float:
        """M = M_sun - 2.5 log₁₀(L/L_sun)."""
        return 4.83 - 2.5*math.log10(L/self.L_sun)

    def distance_modulus(self, d_pc: float) -> float:
        """m - M = 5 log₁₀(d/10pc)."""
        return 5*math.log10(d_pc/10)

    def main_sequence_lifetime(self, M: float, L: float = None) -> float:
        """t ~ M/L × t_sun. If L not given, use L∝M^3.5."""
        if L is None:
            L = self.L_sun * (M/self.M_sun)**3.5
        t_sun = 1e10 * 365.25*86400  # 10 Gyr in seconds
        return t_sun * (M/self.M_sun) / (L/self.L_sun)

    def chandrasekhar_mass(self) -> float:
        """M_Ch ≈ 1.4 M_sun."""
        return 1.44 * self.M_sun

    def eddington_luminosity(self, M: float) -> float:
        """L_Edd = 4πGMc/κ ≈ 3.3×10⁴(M/M_sun)L_sun."""
        return 3.3e4 * (M/self.M_sun) * self.L_sun

    def schwarzschild_radius(self, M: float) -> float:
        """r_s = 2GM/c²."""
        return 2*self.G*M/self.c**2

    def hubble_time(self, H0: float = 70.0) -> float:
        """t_H = 1/H₀ (age estimate for matter-dominated)."""
        H0_si = H0 * 1000 / (3.086e22)
        return 1/H0_si

    def lookback_time(self, z: float, H0: float = 70.0) -> float:
        """Approximate lookback time for flat matter-dominated: t ~ (2/3H₀)[1-1/(1+z)^{3/2}]."""
        H0_si = H0 * 1000 / (3.086e22)
        return (2/(3*H0_si))*(1 - 1/(1+z)**1.5)

    def virial_temperature(self, M: float, R: float, mu: float = 0.6) -> float:
        """T_vir = GMμm_p/(2kR) — virial temperature of gas cloud."""
        m_p = 1.673e-27
        return self.G*M*mu*m_p/(2*self.kB*R)

    def jeans_mass(self, T: float, n: float, mu: float = 2.3) -> float:
        """Jeans mass: M_J = (5kT/Gμm_p)^{3/2}(3/4πρ)^{1/2}."""
        m_p = 1.673e-27
        rho = n * mu * m_p
        cs = math.sqrt(self.kB*T/(mu*m_p))
        lambda_J = cs * math.sqrt(math.pi/(self.G*rho))
        return (math.pi/6) * rho * lambda_J**3


# ══════════════════════════════════════════════════════════════════════════════
# DERIVATION ENGINE — Derive results from first principles
# ══════════════════════════════════════════════════════════════════════════════

class DerivationEngine:
    """Derive physics results step-by-step from fundamental laws."""

    @staticmethod
    def derive(target: str) -> Optional[Dict[str, str]]:
        """Return step-by-step derivation for common physics results."""
        derivations = {
            "E=mc2": {
                "result": "E = mc²",
                "from": "Special relativity + work-energy theorem",
                "steps": [
                    "1. Relativistic momentum: p = γmv",
                    "2. Force: F = dp/dt",
                    "3. Work: dE = F·dx = v·dp",
                    "4. dE = v d(γmv) = mc² dγ",
                    "5. Integrate: E = γmc² (total energy)",
                    "6. At rest (v=0, γ=1): E₀ = mc²",
                ],
            },
            "hawking_temperature": {
                "result": "T_H = ℏc³/(8πGMk_B)",
                "from": "Unruh effect + equivalence principle",
                "steps": [
                    "1. Unruh: accelerated observer sees T = ℏa/(2πck_B)",
                    "2. Surface gravity of Schwarzschild BH: κ = c⁴/(4GM)",
                    "3. Equivalence principle: near-horizon observer has a = κ",
                    "4. Accounting for redshift to infinity: T_H = ℏκ/(2πck_B)",
                    "5. T_H = ℏc³/(8πGMk_B)",
                ],
            },
            "schwarzschild_radius": {
                "result": "r_s = 2GM/c²",
                "from": "Escape velocity = c",
                "steps": [
                    "1. Escape velocity: v_esc = √(2GM/r)",
                    "2. Set v_esc = c (nothing can escape)",
                    "3. c = √(2GM/r_s)",
                    "4. r_s = 2GM/c²",
                    "Note: This Newtonian argument gives correct GR result!",
                ],
            },
            "kepler_third_law": {
                "result": "T² = 4π²a³/(GM)",
                "from": "Newton's second law + gravity",
                "steps": [
                    "1. Circular orbit: F_grav = F_centripetal",
                    "2. GMm/r² = mv²/r",
                    "3. v = 2πr/T (circular orbit)",
                    "4. GM/r = (2πr/T)²",
                    "5. T² = 4π²r³/(GM)",
                    "6. For ellipse: replace r → a (semi-major axis)",
                ],
            },
            "uncertainty_principle": {
                "result": "ΔxΔp ≥ ℏ/2",
                "from": "Wave mechanics + Fourier analysis",
                "steps": [
                    "1. Position space: ψ(x) with width Δx",
                    "2. Momentum space: φ(p) = FT[ψ(x)] with width Δp",
                    "3. Fourier uncertainty: ΔxΔk ≥ ½",
                    "4. de Broglie: p = ℏk",
                    "5. Therefore: ΔxΔp ≥ ℏ/2",
                    "General: ΔAΔB ≥ ½|⟨[A,B]⟩| from Cauchy-Schwarz",
                ],
            },
            "planck_radiation": {
                "result": "u(ν) = 8πhν³/c³ × 1/(e^{hν/kT}-1)",
                "from": "Quantum statistics of photons",
                "steps": [
                    "1. Mode density in cavity: g(ν) = 8πν²/c³",
                    "2. Each mode is quantum HO: E_n = nhν",
                    "3. Average photon number: ⟨n⟩ = 1/(e^{hν/kT}-1) (Bose-Einstein)",
                    "4. Average energy per mode: ⟨E⟩ = hν/(e^{hν/kT}-1)",
                    "5. u(ν) = g(ν)×⟨E⟩ = 8πhν³/c³ × 1/(e^{hν/kT}-1)",
                ],
            },
            "dirac_equation": {
                "result": "(iγ^μ∂_μ - m)ψ = 0",
                "from": "Linearize Klein-Gordon to get first-order in time",
                "steps": [
                    "1. Klein-Gordon: (□+m²)φ=0 is second-order → negative probabilities",
                    "2. Want first-order: iℏ∂ψ/∂t = (α·p + βm)ψ",
                    "3. Require E²=p²+m² → α,β must satisfy Clifford algebra",
                    "4. {αᵢ,αⱼ}=2δᵢⱼ, {αᵢ,β}=0, β²=1",
                    "5. Minimum dimension: 4×4 matrices (γ matrices)",
                    "6. Covariant form: (iγ^μ∂_μ - m)ψ = 0",
                    "7. Predicts: antimatter, spin-½, g=2",
                ],
            },
            "noether_energy": {
                "result": "Time translation symmetry → Energy conservation",
                "from": "Noether's theorem applied to time translation",
                "steps": [
                    "1. Action S = ∫L dt is invariant under t→t+ε",
                    "2. δL = ε dL/dt = ε d/dt(Σpᵢq̇ᵢ - H) (total derivative)",
                    "3. Noether current: Q = Σ(∂L/∂q̇ᵢ)δqᵢ - εL",
                    "4. For time translation: δqᵢ = εq̇ᵢ",
                    "5. Q = Σpᵢq̇ᵢ - L = H (Hamiltonian)",
                    "6. dQ/dt = 0 → dH/dt = 0 (energy conserved)",
                ],
            },
        }
        return derivations.get(target)

    @staticmethod
    def available_derivations() -> List[str]:
        """List all available derivation targets."""
        return ["E=mc2", "hawking_temperature", "schwarzschild_radius",
                "kepler_third_law", "uncertainty_principle", "planck_radiation",
                "dirac_equation", "noether_energy"]


# ══════════════════════════════════════════════════════════════════════════════
# FERMI ESTIMATOR — Order-of-magnitude estimates
# ══════════════════════════════════════════════════════════════════════════════

class FermiEstimator:
    """Make order-of-magnitude estimates from first principles."""

    @staticmethod
    def estimate(question: str) -> Optional[Dict[str, str]]:
        """Fermi estimates for classic problems."""
        estimates = {
            "piano_tuners_chicago": {
                "answer": "~200 piano tuners",
                "reasoning": [
                    "Chicago population: ~3 million",
                    "People per household: ~3 → 1M households",
                    "Fraction with pianos: ~5% → 50,000 pianos",
                    "Tunings per year: ~1-2 → 75,000 tunings/year",
                    "Tunings per tuner per day: ~4",
                    "Working days: ~250 → 1000 tunings/tuner/year",
                    "Tuners needed: 75,000/1000 ≈ 75-200",
                ],
            },
            "atoms_in_human": {
                "answer": "~7×10²⁷ atoms",
                "reasoning": [
                    "Human mass: ~70 kg",
                    "Mostly water (H₂O): avg atomic mass ~7 amu",
                    "N = 70/(7×1.66×10⁻²⁷) ≈ 6×10²⁷",
                ],
            },
            "power_of_sun": {
                "answer": "~4×10²⁶ W",
                "reasoning": [
                    "Solar constant at Earth: ~1400 W/m²",
                    "Earth-Sun distance: 1.5×10¹¹ m",
                    "Sphere area: 4π(1.5×10¹¹)² ≈ 2.8×10²³ m²",
                    "L = 1400 × 2.8×10²³ ≈ 4×10²⁶ W",
                ],
            },
            "energy_to_heat_ocean": {
                "answer": "~5×10²⁶ J per degree",
                "reasoning": [
                    "Ocean mass: ~1.4×10²¹ kg",
                    "Specific heat of water: 4200 J/(kg·K)",
                    "E = mcΔT = 1.4×10²¹ × 4200 × 1 ≈ 6×10²⁴ J per °C",
                ],
            },
            "age_of_universe": {
                "answer": "~14 billion years",
                "reasoning": [
                    "Hubble constant: H₀ ≈ 70 km/s/Mpc",
                    "Hubble time: 1/H₀ = 1/(70×10³/3.086×10²²) s",
                    "= 3.086×10²²/(70×10³) ≈ 4.4×10¹⁷ s",
                    "≈ 14×10⁹ years",
                ],
            },
            "neutrinos_through_body": {
                "answer": "~10¹⁴ per second",
                "reasoning": [
                    "Solar neutrino flux at Earth: ~6×10¹⁰/cm²/s",
                    "Human cross-sectional area: ~1 m² = 10⁴ cm²",
                    "Neutrinos through body: 6×10¹⁰ × 10⁴ ≈ 6×10¹⁴/s",
                    "(But almost none interact! σ ~ 10⁻⁴⁴ cm²)",
                ],
            },
        }
        # Try to match
        q_lower = question.lower()
        for key, est in estimates.items():
            if any(w in q_lower for w in key.split("_")):
                return est
        return None

    @staticmethod
    def dimensional_estimate(target_units: str, known_scales: Dict[str, float]) -> str:
        """Use dimensional analysis to estimate unknown quantity."""
        return f"Combine {known_scales} to get [{target_units}] using Buckingham π"


# ══════════════════════════════════════════════════════════════════════════════
# CROSS-DOMAIN CONNECTOR — Link math theorems to physics applications
# ══════════════════════════════════════════════════════════════════════════════

class CrossDomainPhysics:
    """Connect mathematical theorems to physics applications."""

    @staticmethod
    def math_to_physics_map() -> Dict[str, List[str]]:
        """Map mathematical structures to their physics applications."""
        return {
            "differential_geometry": [
                "General Relativity (spacetime = manifold, gravity = curvature)",
                "Gauge theory (connections on fiber bundles)",
                "Berry phase (connection on parameter space)",
                "Topological defects (classification by homotopy)",
            ],
            "group_theory": [
                "Particle physics (SU(3)×SU(2)×U(1) = Standard Model)",
                "Crystal symmetry (32 point groups, 230 space groups)",
                "Selection rules (forbidden transitions by symmetry)",
                "Conservation laws (Noether: symmetry → conserved quantity)",
            ],
            "hilbert_space": [
                "Quantum mechanics (states = vectors, observables = operators)",
                "Quantum field theory (Fock space)",
                "Signal processing (L² function space)",
            ],
            "topology": [
                "Topological insulators (Z₂ invariant, Chern number)",
                "Magnetic monopoles (Dirac quantization from topology)",
                "Cosmic strings, domain walls (topological defects)",
                "TQFT (Chern-Simons, Jones polynomial → anyons)",
            ],
            "representation_theory": [
                "Angular momentum addition (Clebsch-Gordan)",
                "Particle multiplets (quarks in SU(3) reps)",
                "Selection rules (matrix elements vanish by symmetry)",
                "Crystal field theory (splitting by reduced symmetry)",
            ],
            "complex_analysis": [
                "Scattering amplitudes (analyticity, dispersion relations)",
                "Kramers-Kronig relations (causality → analyticity)",
                "Conformal field theory (2D physics from complex maps)",
                "Instanton calculus (saddle points in complex plane)",
            ],
            "functional_analysis": [
                "Quantum mechanics (operators on Hilbert space)",
                "Spectral theorem → quantum measurement",
                "Distribution theory → Dirac delta, Green's functions",
                "Variational methods → ground state energy bounds",
            ],
            "probability_statistics": [
                "Statistical mechanics (all of thermodynamics)",
                "Quantum measurement (Born rule)",
                "Random matrix theory → nuclear spectra, quantum chaos",
                "Stochastic processes → Brownian motion, Langevin",
            ],
            "number_theory": [
                "String theory (modular forms, moonshine)",
                "Quantum Hall effect (rational filling fractions)",
                "Riemann zeta → Casimir effect regularization",
                "p-adic numbers in holography",
            ],
            "category_theory": [
                "TQFT (functors from cobordism to Hilbert spaces)",
                "Duality (electric-magnetic, AdS/CFT as functor)",
                "Quantum protocols (monoidal categories)",
            ],
        }

    @staticmethod
    def physics_analogies() -> Dict[str, Dict[str, str]]:
        """Physical systems that share the same mathematical structure."""
        return {
            "harmonic_oscillator_universality": {
                "math": "x'' + ω²x = 0",
                "instances": "mass-spring, LC circuit, pendulum (small), molecular vibration, photon mode",
            },
            "diffusion_schrodinger": {
                "math": "∂u/∂t = D∇²u (diffusion) vs iℏ∂ψ/∂t = -(ℏ²/2m)∇²ψ",
                "connection": "Wick rotation t→iτ turns Schrödinger into diffusion",
            },
            "em_fluid": {
                "math": "Maxwell equations ↔ linearized Euler equations",
                "connection": "Vorticity↔magnetic field, velocity↔vector potential",
            },
            "bh_thermodynamics": {
                "math": "Laws of BH mechanics = Laws of thermodynamics",
                "connection": "κ↔T, A↔S, M↔E (Bekenstein-Hawking)",
            },
            "ads_cft_dictionary": {
                "math": "Bulk fields ↔ boundary operators",
                "connection": "Mass→dimension, gauge→global symmetry, BH→thermal state",
            },
        }


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS AUTO-LEARN — Search web for unknown physics
# ══════════════════════════════════════════════════════════════════════════════

class PhysicsAutoLearn:
    """Auto-learn physics laws and constants from web search."""

    def __init__(self):
        self.learned_file = "src/data/learned_physics.json"

    def search_law(self, query: str) -> Optional[Dict]:
        """Search for a physics law/result not in the database.
        Returns structured result if found."""
        # This integrates with online_search when available
        try:
            import json, os
            if os.path.exists(self.learned_file):
                with open(self.learned_file) as f:
                    learned = json.load(f)
                for item in learned:
                    if query.lower() in item.get("name", "").lower():
                        return item
        except:
            pass
        return None

    def save_learned(self, name: str, statement: str, equation: str,
                     domain: str, source: str):
        """Save a learned physics result to disk."""
        import json, os
        os.makedirs(os.path.dirname(self.learned_file), exist_ok=True)
        learned = []
        if os.path.exists(self.learned_file):
            try:
                with open(self.learned_file) as f:
                    learned = json.load(f)
            except:
                pass
        learned.append({
            "name": name, "statement": statement, "equation": equation,
            "domain": domain, "source": source
        })
        with open(self.learned_file, 'w') as f:
            json.dump(learned, f, indent=2)
