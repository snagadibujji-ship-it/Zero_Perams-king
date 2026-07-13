# PROMETHEUS PHYSICS ENGINE — PhD COSMIC LEVEL PLAN
## Built by: Ghias + Kiro

---

## CURRENT STATE
- ✅ FormulaBook: 60+ basic formulas (mechanics, electrical, control, signals)
- ✅ EngineeringSolver: chains formulas to solve word problems
- ✅ Math theorems: 254 verified (algebra, topology, analysis, geometry, number theory)
- ❌ NO advanced physics (QM, GR, QFT, stat mech, condensed matter, cosmology)
- ❌ NO physics derivation engine (can't derive from principles)
- ❌ NO physics theorems/laws database
- ❌ NO dimensional analysis engine
- ❌ NO Lagrangian/Hamiltonian mechanics

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROMETHEUS PHYSICS ENGINE                      │
│                    (prometheus_physics.py)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   LAWS DB    │  │  CONSTANTS   │  │  DIMENSIONAL ANALYSIS │  │
│  │  150+ laws   │  │  50+ consts  │  │  unit tracking/check  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                  │                      │               │
│  ┌──────▼──────────────────▼──────────────────────▼───────────┐  │
│  │              PHYSICS REASONING ENGINE                        │  │
│  │  • Identify domain → select relevant laws                   │  │
│  │  • Derive from first principles (not lookup)                │  │
│  │  • Chain derivations: law₁ + law₂ → result                 │  │
│  │  • Approximation engine (Taylor, limits, regimes)           │  │
│  │  • Symmetry analysis → conservation laws                    │  │
│  └────────────────────────────┬───────────────────────────────┘  │
│                               │                                   │
│  ┌────────────────────────────▼───────────────────────────────┐  │
│  │              DOMAIN SOLVERS                                  │  │
│  │                                                              │  │
│  │  Level 1: Classical Mechanics                                │  │
│  │    • Newtonian (F=ma, energy, momentum)                     │  │
│  │    • Lagrangian (L=T-V, Euler-Lagrange, constraints)        │  │
│  │    • Hamiltonian (H, canonical transformations, Poisson)     │  │
│  │    • Rigid body (inertia tensor, Euler angles, rotation)    │  │
│  │    • Continuum mechanics (stress, strain, elasticity)        │  │
│  │                                                              │  │
│  │  Level 2: Electromagnetism                                   │  │
│  │    • Maxwell's equations (differential + integral)           │  │
│  │    • EM waves (propagation, polarization, radiation)         │  │
│  │    • Relativistic electrodynamics (4-potential, tensors)     │  │
│  │    • Gauge theory (U(1), gauge invariance)                  │  │
│  │                                                              │  │
│  │  Level 3: Quantum Mechanics                                  │  │
│  │    • Schrödinger equation (time-dep + time-indep)           │  │
│  │    • Operators, commutators, uncertainty                     │  │
│  │    • Angular momentum (addition, Clebsch-Gordan)            │  │
│  │    • Perturbation theory (time-indep + time-dep)            │  │
│  │    • Path integrals (Feynman formulation)                   │  │
│  │    • Scattering (Born approx, partial waves, S-matrix)      │  │
│  │    • Density matrix, decoherence, entanglement              │  │
│  │                                                              │  │
│  │  Level 4: Statistical Mechanics & Thermodynamics             │  │
│  │    • Ensembles (micro, canonical, grand canonical)          │  │
│  │    • Partition functions → all thermodynamics                │  │
│  │    • Phase transitions (Ising, mean field, Landau)          │  │
│  │    • Fluctuation-dissipation, linear response               │  │
│  │    • Boltzmann equation, transport                           │  │
│  │                                                              │  │
│  │  Level 5: Special & General Relativity                       │  │
│  │    • Lorentz transformations, 4-vectors, invariants         │  │
│  │    • Geodesics, Einstein field equations                     │  │
│  │    • Schwarzschild, Kerr, FRW metrics                       │  │
│  │    • Gravitational waves, linearized gravity                │  │
│  │    • Cosmology (Friedmann, dark energy, inflation)          │  │
│  │                                                              │  │
│  │  Level 6: Quantum Field Theory                               │  │
│  │    • Canonical quantization (scalar, spinor, vector)        │  │
│  │    • Feynman diagrams, propagators, vertices                │  │
│  │    • Renormalization (UV divergences, running coupling)      │  │
│  │    • Standard Model (QED, QCD, electroweak)                 │  │
│  │    • Symmetry breaking (Higgs mechanism, SSB)               │  │
│  │                                                              │  │
│  │  Level 7: Condensed Matter                                   │  │
│  │    • Band theory, Bloch waves, Fermi surfaces               │  │
│  │    • Superconductivity (BCS, Ginzburg-Landau)               │  │
│  │    • Topological phases (Berry phase, Chern number)         │  │
│  │    • Many-body (Hartree-Fock, DFT, Green's functions)       │  │
│  │                                                              │  │
│  │  Level 8: Advanced & Research                                │  │
│  │    • String theory basics (Nambu-Goto, Polyakov)            │  │
│  │    • AdS/CFT correspondence                                  │  │
│  │    • Quantum information (qubits, gates, entanglement)      │  │
│  │    • Non-equilibrium stat mech                               │  │
│  │    • Quantum gravity approaches                              │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              PHYSICS PROOF ENGINE                             │  │
│  │  • Derive results from axioms (Newton's laws → orbit eq.)   │  │
│  │  • Variational methods (minimize action → EOM)              │  │
│  │  • Symmetry → Conservation (Noether for each symmetry)      │  │
│  │  • Limiting cases (ℏ→0 gives classical, c→∞ gives NR)      │  │
│  │  • Dimensional analysis (when in doubt, check units!)       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              PHYSICS THEOREM AUTO-LEARN                       │  │
│  │  • Uses web search for unknown laws/results                  │  │
│  │  • Validates dimensional consistency                         │  │
│  │  • Saves to learned_physics.json                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PHYSICS LAWS DATABASE (150+ entries, organized by domain)

### Level 1: Classical Mechanics (25 laws)
1. Newton's 1st (inertia)
2. Newton's 2nd (F=ma, vector form F=dp/dt)
3. Newton's 3rd (action-reaction)
4. Conservation of energy
5. Conservation of momentum
6. Conservation of angular momentum
7. Work-energy theorem
8. Euler-Lagrange equation: d/dt(∂L/∂q̇) - ∂L/∂q = 0
9. Hamilton's equations: q̇=∂H/∂p, ṗ=-∂H/∂q
10. Noether's theorem (symmetry → conservation)
11. Virial theorem: ⟨T⟩ = -½⟨Σ F·r⟩
12. D'Alembert's principle
13. Hamilton's principle (δS=0, least action)
14. Liouville's theorem (phase space volume preserved)
15. Kepler's laws (orbits)
16. Navier-Stokes equations
17. Euler equations (inviscid fluid)
18. Bernoulli's principle
19. Hooke's law (elasticity tensor form)
20. Poisson bracket relations
21. Canonical transformations
22. Action-angle variables
23. Adiabatic invariants
24. KAM theorem (stability of integrable systems)
25. Equipartition theorem

### Level 2: Electromagnetism (20 laws)
1. Gauss's law: ∇·E = ρ/ε₀
2. Gauss's law (magnetic): ∇·B = 0
3. Faraday's law: ∇×E = -∂B/∂t
4. Ampère-Maxwell: ∇×B = μ₀J + μ₀ε₀∂E/∂t
5. Lorentz force: F = q(E + v×B)
6. Coulomb's law
7. Biot-Savart law
8. Poynting vector: S = (1/μ₀)E×B
9. Energy density: u = ½(ε₀E² + B²/μ₀)
10. Wave equation: ∇²E = μ₀ε₀ ∂²E/∂t²
11. Lienard-Wiechert potentials (retarded)
12. Radiation formula (Larmor): P = q²a²/(6πε₀c³)
13. Gauge transformations (Lorenz, Coulomb)
14. Multipole expansion
15. Image charges method
16. Boundary conditions (E,B at interfaces)
17. Fresnel equations (reflection/transmission)
18. Dispersion relations
19. Kramers-Kronig relations
20. Jefimenko's equations (retarded fields)

### Level 3: Quantum Mechanics (25 laws)
1. Schrödinger equation: iℏ∂ψ/∂t = Ĥψ
2. Time-independent: Ĥψ = Eψ
3. Born rule: P = |⟨φ|ψ⟩|²
4. Heisenberg uncertainty: ΔxΔp ≥ ℏ/2
5. Ehrenfest theorem: d⟨A⟩/dt = ⟨[A,H]⟩/iℏ
6. Commutation: [x̂,p̂] = iℏ
7. Angular momentum: [Jᵢ,Jⱼ] = iℏεᵢⱼₖJₖ
8. Pauli exclusion principle
9. Spin-statistics theorem
10. Hydrogen atom (exact solution, quantum numbers n,l,m)
11. Harmonic oscillator (ladder operators, E=(n+½)ℏω)
12. WKB approximation
13. Variational principle (E₀ ≤ ⟨ψ|H|ψ⟩)
14. Perturbation theory (non-degenerate + degenerate)
15. Fermi's golden rule: Γ = (2π/ℏ)|⟨f|V|i⟩|² ρ(E)
16. Selection rules (dipole: Δl=±1, Δm=0,±1)
17. Adiabatic theorem + Berry phase
18. No-cloning theorem
19. Bell's theorem (no local hidden variables)
20. Density matrix: ρ = Σ pᵢ|ψᵢ⟩⟨ψᵢ|
21. Decoherence and measurement
22. Wigner-Eckart theorem
23. Clebsch-Gordan decomposition
24. Path integral: K = ∫Dx e^{iS[x]/ℏ}
25. Feynman-Kac formula

### Level 4: Statistical Mechanics (20 laws)
1. Boltzmann distribution: P(E) ∝ e^{-E/kT}
2. Partition function: Z = Σ e^{-βEᵢ}
3. Free energy: F = -kT ln Z
4. Entropy: S = -kΣ pᵢ ln pᵢ (Gibbs)
5. Second law: dS ≥ 0 (isolated system)
6. Third law: S→0 as T→0
7. Fluctuation-dissipation theorem
8. Equipartition: ½kT per quadratic DOF
9. Fermi-Dirac distribution: f(E) = 1/(e^{(E-μ)/kT}+1)
10. Bose-Einstein distribution: f(E) = 1/(e^{(E-μ)/kT}-1)
11. Planck radiation: u(ν) = 8πhν³/c³ · 1/(e^{hν/kT}-1)
12. Stefan-Boltzmann: P = σT⁴
13. Phase transitions (Ehrenfest classification)
14. Landau theory (order parameter expansion)
15. Critical exponents and universality
16. Ising model (exact 2D solution)
17. Renormalization group (block spin, fixed points)
18. Onsager reciprocal relations
19. Kramers escape rate
20. Jarzynski equality: ⟨e^{-βW}⟩ = e^{-βΔF}

### Level 5: Relativity (20 laws)
1. Lorentz transformation: t'=γ(t-vx/c²), x'=γ(x-vt)
2. Time dilation: Δt' = γΔt
3. Length contraction: L' = L/γ
4. E=mc² (mass-energy)
5. Four-momentum: p^μ = (E/c, p)
6. Invariant mass: m²c² = E²/c² - p²
7. Einstein field equations: G_μν + Λg_μν = 8πG/c⁴ T_μν
8. Geodesic equation: d²x^μ/dτ² + Γ^μ_νρ dx^ν/dτ dx^ρ/dτ = 0
9. Schwarzschild metric (non-rotating BH)
10. Kerr metric (rotating BH)
11. Gravitational redshift: Δν/ν = -ΔΦ/c²
12. Gravitational lensing (deflection angle)
13. Gravitational waves: h_μν propagates at c
14. Friedmann equations (cosmology)
15. Hubble's law: v = H₀d
16. Cosmological redshift: 1+z = a(t₀)/a(t)
17. Penrose singularity theorem
18. Hawking radiation: T = ℏc³/(8πGMk)
19. Bekenstein-Hawking entropy: S = A/(4l_P²)
20. ADM formalism (3+1 decomposition)

### Level 6: Quantum Field Theory (20 laws)
1. Klein-Gordon equation: (□+m²)φ = 0
2. Dirac equation: (iγ^μ∂_μ - m)ψ = 0
3. Feynman propagator: ⟨0|T{φ(x)φ(y)}|0⟩
4. LSZ reduction formula
5. Dyson series (S-matrix expansion)
6. Wick's theorem
7. Ward identity (gauge invariance → relations)
8. QED vertex: ieγ^μ
9. QED running coupling: α(q²) = α/(1-(α/3π)ln(q²/m²))
10. Anomalous magnetic moment: g-2
11. Lamb shift
12. Asymptotic freedom (QCD): β<0
13. Confinement (qualitative)
14. Higgs mechanism: φ→v+h, gives mass W^±=gv/2
15. Goldstone theorem (SSB → massless bosons)
16. Coleman-Mandula theorem
17. CPT theorem
18. Spin-statistics connection
19. Optical theorem: σ_tot = (4π/k)Im f(0)
20. Anomaly cancellation (Standard Model)

### Level 7: Condensed Matter (15 laws)
1. Bloch's theorem: ψ_k(r) = e^{ik·r} u_k(r)
2. Band structure (tight-binding, nearly-free electron)
3. Fermi liquid theory (Landau quasiparticles)
4. BCS theory: Δ = V⟨c↑c↓⟩ (Cooper pairs)
5. Meissner effect (B=0 inside superconductor)
6. London equations: ∇²B = B/λ²
7. Josephson effect: I = I_c sin(Δφ)
8. Berry phase: γ = ∮⟨n|∇_k|n⟩·dk
9. Chern number (topological invariant)
10. Quantum Hall effect: σ_xy = ne²/h
11. Anderson localization
12. Kondo effect
13. Hubbard model
14. Mermin-Wagner theorem (no 2D long-range order for continuous symmetry)
15. TKNN invariant (topological band theory)

### Level 8: Modern/Research (10 laws)
1. Holographic principle (entropy ∝ area)
2. AdS/CFT: gravity in AdS ↔ CFT on boundary
3. Maldacena conjecture
4. Area law for entanglement entropy
5. Ryu-Takayanagi formula
6. Sachdev-Ye-Kitaev model
7. No-hair theorem (BH characterized by M,Q,J only)
8. Cosmic censorship (singularities hidden by horizons)
9. Inflation (slow-roll: ε = (V'/V)²/(16πG))
10. Dark energy equation of state: w = P/ρ

---

## PHYSICAL CONSTANTS (50+)

| Constant | Symbol | Value |
|----------|--------|-------|
| Speed of light | c | 2.998×10⁸ m/s |
| Planck's constant | h | 6.626×10⁻³⁴ J·s |
| Reduced Planck | ℏ | 1.055×10⁻³⁴ J·s |
| Boltzmann | k_B | 1.381×10⁻²³ J/K |
| Gravitational | G | 6.674×10⁻¹¹ N·m²/kg² |
| Elementary charge | e | 1.602×10⁻¹⁹ C |
| Electron mass | m_e | 9.109×10⁻³¹ kg |
| Proton mass | m_p | 1.673×10⁻²⁷ kg |
| Avogadro | N_A | 6.022×10²³ mol⁻¹ |
| Gas constant | R | 8.314 J/(mol·K) |
| Permittivity | ε₀ | 8.854×10⁻¹² F/m |
| Permeability | μ₀ | 4π×10⁻⁷ H/m |
| Fine structure | α | 1/137.036 |
| Stefan-Boltzmann | σ | 5.670×10⁻⁸ W/(m²·K⁴) |
| Hubble constant | H₀ | ~70 km/s/Mpc |
| Planck length | l_P | 1.616×10⁻³⁵ m |
| Planck mass | m_P | 2.176×10⁻⁸ kg |
| Planck time | t_P | 5.391×10⁻⁴⁴ s |
| Bohr radius | a₀ | 5.292×10⁻¹¹ m |
| Rydberg | R_∞ | 1.097×10⁷ m⁻¹ |
| Compton wavelength (e) | λ_C | 2.426×10⁻¹² m |
| Magnetic flux quantum | Φ₀ | 2.068×10⁻¹⁵ Wb |
| von Klitzing constant | R_K | 25812.807 Ω |
| Conductance quantum | G₀ | 7.748×10⁻⁵ S |

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation (prometheus_physics.py)
- PhysicsLawDB: 155 laws (structured like TheoremDB)
- PhysicsConstants: 50+ constants with units
- DimensionalAnalyzer: automatic unit checking
- PhysicsIdentifier: detect which domain a question belongs to

### Phase 2: Classical Solvers
- NewtonianSolver: force diagrams, energy methods
- LagrangianSolver: generalized coords, constraints, EOM derivation
- HamiltonianSolver: canonical transformations, phase space
- FluidSolver: Navier-Stokes, Bernoulli applications

### Phase 3: Quantum & EM
- QuantumSolver: solve SE for standard potentials, perturbation theory
- EMSolver: Maxwell applications, radiation, waveguides
- AngularMomentumEngine: CG coefficients, selection rules

### Phase 4: Advanced
- StatMechSolver: partition functions → thermodynamics, phase transitions
- RelativitySolver: metric calculations, geodesics, cosmology
- QFTSolver: Feynman rules, cross sections, renormalization (symbolic)

### Phase 5: Research Level
- PhysicsDerivationEngine: derive any result from first principles
- PhysicsProofEngine: verify physics arguments step-by-step
- CrossDomain: connect math theorems to physics applications
- AutoLearn: search web for unknown physics results

---

## REUSE FROM MATH ENGINE
- Calculus engine (derivatives, integrals) → physics derivations
- Matrix/linear algebra → quantum mechanics, tensors
- ODE solver → equations of motion
- Probability → quantum measurement, statistical mechanics
- Differential geometry → general relativity
- Group theory → symmetries, particle physics

---

## SUCCESS CRITERIA
- Can solve Jackson EM problems
- Can solve Griffiths QM problems
- Can solve Landau & Lifshitz level problems
- Can derive standard results from first principles
- Handles dimensional analysis automatically
- PhD qualifying exam physics: >80% correct
- All answers with step-by-step derivation + units check

---

## FILE: `src/python/prometheus_physics.py`
Target: ~4000 lines
Dependencies: prometheus.py (calculus, algebra), prometheus_advanced.py (theorems, matrices)
