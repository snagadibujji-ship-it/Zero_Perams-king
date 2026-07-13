"""
PROMETHEUS PHYSICS ENGINE — Phase 2: Mathematical Physics Layer
Built by: Ghias + Kiro

Components:
  - SpecialFunctions: Bessel, Legendre, spherical harmonics, Hermite, Laguerre, Gamma, etc.
  - TensorEngine: index notation, contraction, Christoffel, metric operations
  - GreensFunctionDB: Green's functions for standard PDEs
  - SymmetryEngine: Lie groups, representations, Casimirs
  - ApproximationEngine: Taylor, WKB, perturbation, Padé, asymptotic
"""

from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import math

# ══════════════════════════════════════════════════════════════════════════════
# SPECIAL FUNCTIONS — Numerical + symbolic properties
# ══════════════════════════════════════════════════════════════════════════════

class SpecialFunctions:
    """Compute and describe special functions of mathematical physics."""

    # ── Gamma function and relatives ──

    @staticmethod
    def gamma(x: float) -> float:
        """Gamma function Γ(x) = ∫₀^∞ t^{x-1} e^{-t} dt."""
        if x <= 0 and x == int(x):
            return float('inf')  # poles at 0, -1, -2, ...
        # Use Stirling + recursion for positive
        if x < 0.5:
            # Reflection formula: Γ(x)Γ(1-x) = π/sin(πx)
            return math.pi / (math.sin(math.pi * x) * SpecialFunctions.gamma(1 - x))
        # Lanczos approximation
        g = 7
        c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
             771.32342877765313, -176.61502916214059, 12.507343278686905,
             -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7]
        x -= 1
        t = c[0]
        for i in range(1, g + 2):
            t += c[i] / (x + i)
        w = x + g + 0.5
        return math.sqrt(2 * math.pi) * (w ** (x + 0.5)) * math.exp(-w) * t

    @staticmethod
    def beta(a: float, b: float) -> float:
        """Beta function B(a,b) = Γ(a)Γ(b)/Γ(a+b)."""
        return SpecialFunctions.gamma(a) * SpecialFunctions.gamma(b) / SpecialFunctions.gamma(a + b)

    @staticmethod
    def factorial(n: int) -> int:
        """n! for non-negative integer."""
        if n < 0:
            return 0
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    @staticmethod
    def double_factorial(n: int) -> int:
        """n!! = n(n-2)(n-4)..."""
        if n <= 0:
            return 1
        result = 1
        while n > 0:
            result *= n
            n -= 2
        return result

    # ── Bessel functions ──

    @staticmethod
    def bessel_j(n: int, x: float, terms: int = 30) -> float:
        """Bessel function of the first kind J_n(x) via series."""
        result = 0.0
        for m in range(terms):
            sign = (-1) ** m
            num = (x / 2) ** (2 * m + n)
            den = SpecialFunctions.factorial(m) * SpecialFunctions.factorial(m + n)
            if den == 0:
                continue
            result += sign * num / den
        return result

    @staticmethod
    def bessel_y(n: int, x: float) -> float:
        """Bessel function of the second kind Y_n(x) (Neumann function).
        Y_n(x) = [J_n(x)cos(nπ) - J_{-n}(x)] / sin(nπ) for non-integer n.
        For integer n, use limit form."""
        if x <= 0:
            return float('-inf')
        if n == 0:
            # Y_0 approximation for small x
            euler = 0.5772156649
            return (2 / math.pi) * (math.log(x / 2) + euler) * SpecialFunctions.bessel_j(0, x) \
                   - (2 / math.pi) * SpecialFunctions._y0_series(x)
        # For integer n, use recurrence
        # Y_{n+1} = (2n/x)Y_n - Y_{n-1}
        y0 = SpecialFunctions.bessel_y(0, x)
        y1 = SpecialFunctions._bessel_y1(x)
        if n == 1:
            return y1
        ym1, y_cur = y0, y1
        for k in range(1, n):
            y_next = (2 * k / x) * y_cur - ym1
            ym1 = y_cur
            y_cur = y_next
        return y_cur

    @staticmethod
    def _y0_series(x: float, terms: int = 20) -> float:
        """Series part of Y_0."""
        result = 0.0
        for m in range(1, terms):
            sign = (-1) ** (m + 1)
            hm = sum(1.0 / k for k in range(1, m + 1))
            num = (x / 2) ** (2 * m)
            den = SpecialFunctions.factorial(m) ** 2
            result += sign * hm * num / den
        return result

    @staticmethod
    def _bessel_y1(x: float, terms: int = 20) -> float:
        """Y_1(x) via series."""
        euler = 0.5772156649
        j1 = SpecialFunctions.bessel_j(1, x)
        # Y_1 = (2/π)[J_1(x)(ln(x/2)+γ) - 1/x - series]
        s = 0.0
        for m in range(terms):
            sign = (-1) ** m
            hm = sum(1.0 / k for k in range(1, m + 1)) if m > 0 else 0
            hm1 = sum(1.0 / k for k in range(1, m + 2))
            num = (x / 2) ** (2 * m + 1)
            den = SpecialFunctions.factorial(m) * SpecialFunctions.factorial(m + 1)
            if den > 0:
                s += sign * (hm + hm1) * num / den
        return (2 / math.pi) * (j1 * (math.log(x / 2) + euler) - 1 / x - s / 2)

    @staticmethod
    def spherical_bessel_j(n: int, x: float) -> float:
        """Spherical Bessel function j_n(x) = √(π/2x) J_{n+1/2}(x)."""
        if abs(x) < 1e-15:
            return 1.0 if n == 0 else 0.0
        if n == 0:
            return math.sin(x) / x
        elif n == 1:
            return math.sin(x) / x**2 - math.cos(x) / x
        # Recurrence: j_{n+1} = (2n+1)/x * j_n - j_{n-1}
        j0 = math.sin(x) / x
        j1 = math.sin(x) / x**2 - math.cos(x) / x
        for k in range(1, n):
            j_next = (2 * k + 1) / x * j1 - j0
            j0 = j1
            j1 = j_next
        return j1

    # ── Legendre polynomials and associated ──

    @staticmethod
    def legendre_p(l: int, x: float) -> float:
        """Legendre polynomial P_l(x) via recurrence."""
        if l == 0:
            return 1.0
        if l == 1:
            return x
        p_prev, p_curr = 1.0, x
        for k in range(1, l):
            p_next = ((2 * k + 1) * x * p_curr - k * p_prev) / (k + 1)
            p_prev = p_curr
            p_curr = p_next
        return p_curr

    @staticmethod
    def assoc_legendre(l: int, m: int, x: float) -> float:
        """Associated Legendre polynomial P_l^m(x)."""
        if abs(m) > l:
            return 0.0
        if m < 0:
            m_abs = -m
            sign = (-1)**m_abs * SpecialFunctions.factorial(l-m_abs) / SpecialFunctions.factorial(l+m_abs)
            return sign * SpecialFunctions.assoc_legendre(l, m_abs, x)

        # Start with P_m^m
        pmm = 1.0
        if m > 0:
            somx2 = math.sqrt(1 - x*x)
            fact = 1.0
            for i in range(1, m+1):
                pmm *= -fact * somx2
                fact += 2.0

        if l == m:
            return pmm

        # P_{m+1}^m
        pmm1 = x * (2*m + 1) * pmm
        if l == m + 1:
            return pmm1

        # Recurrence
        for k in range(m+1, l):
            p_next = ((2*k+1)*x*pmm1 - (k+m)*pmm) / (k-m+1)
            pmm = pmm1
            pmm1 = p_next
        return pmm1

    @staticmethod
    def spherical_harmonic(l: int, m: int, theta: float, phi: float) -> complex:
        """Spherical harmonic Y_l^m(θ,φ) — complex valued."""
        # Normalization
        norm = math.sqrt((2*l+1)/(4*math.pi) *
                        SpecialFunctions.factorial(l-abs(m)) /
                        SpecialFunctions.factorial(l+abs(m)))
        plm = SpecialFunctions.assoc_legendre(l, abs(m), math.cos(theta))

        if m >= 0:
            return norm * plm * complex(math.cos(m*phi), math.sin(m*phi))
        else:
            return ((-1)**m) * norm * plm * complex(math.cos(abs(m)*phi), -math.sin(abs(m)*phi))

    # ── Hermite polynomials (physicist's convention) ──

    @staticmethod
    def hermite(n: int, x: float) -> float:
        """Hermite polynomial H_n(x) — physicist's convention.
        H_0=1, H_1=2x, H_{n+1}=2xH_n - 2nH_{n-1}"""
        if n == 0:
            return 1.0
        if n == 1:
            return 2 * x
        h_prev, h_curr = 1.0, 2 * x
        for k in range(1, n):
            h_next = 2 * x * h_curr - 2 * k * h_prev
            h_prev = h_curr
            h_curr = h_next
        return h_curr

    # ── Laguerre polynomials ──

    @staticmethod
    def laguerre(n: int, x: float) -> float:
        """Laguerre polynomial L_n(x).
        L_0=1, L_1=1-x, (n+1)L_{n+1}=(2n+1-x)L_n - nL_{n-1}"""
        if n == 0:
            return 1.0
        if n == 1:
            return 1.0 - x
        l_prev, l_curr = 1.0, 1.0 - x
        for k in range(1, n):
            l_next = ((2*k + 1 - x) * l_curr - k * l_prev) / (k + 1)
            l_prev = l_curr
            l_curr = l_next
        return l_curr

    @staticmethod
    def assoc_laguerre(n: int, k: int, x: float) -> float:
        """Associated (generalized) Laguerre polynomial L_n^k(x).
        Used in hydrogen wavefunctions."""
        if n == 0:
            return 1.0
        if n == 1:
            return 1 + k - x
        l_prev, l_curr = 1.0, 1 + k - x
        for j in range(1, n):
            l_next = ((2*j + 1 + k - x) * l_curr - (j + k) * l_prev) / (j + 1)
            l_prev = l_curr
            l_curr = l_next
        return l_curr

    # ── Chebyshev polynomials ──

    @staticmethod
    def chebyshev_t(n: int, x: float) -> float:
        """Chebyshev polynomial of first kind T_n(x).
        T_0=1, T_1=x, T_{n+1}=2xT_n - T_{n-1}"""
        if n == 0:
            return 1.0
        if n == 1:
            return x
        t_prev, t_curr = 1.0, x
        for _ in range(1, n):
            t_next = 2 * x * t_curr - t_prev
            t_prev = t_curr
            t_curr = t_next
        return t_curr

    @staticmethod
    def chebyshev_u(n: int, x: float) -> float:
        """Chebyshev polynomial of second kind U_n(x).
        U_0=1, U_1=2x, U_{n+1}=2xU_n - U_{n-1}"""
        if n == 0:
            return 1.0
        if n == 1:
            return 2 * x
        u_prev, u_curr = 1.0, 2 * x
        for _ in range(1, n):
            u_next = 2 * x * u_curr - u_prev
            u_prev = u_curr
            u_curr = u_next
        return u_curr

    # ── Airy functions ──

    @staticmethod
    def airy_ai(x: float, terms: int = 40) -> float:
        """Airy function Ai(x) — series for moderate x."""
        # Ai(x) = c1 f(x) - c2 g(x) where
        # c1 = 1/(3^{2/3} Γ(2/3)), c2 = 1/(3^{1/3} Γ(1/3))
        c1 = 1.0 / (3**(2/3) * SpecialFunctions.gamma(2/3))
        c2 = 1.0 / (3**(1/3) * SpecialFunctions.gamma(1/3))
        f, g = 0.0, 0.0
        for k in range(terms):
            f += SpecialFunctions._airy_coeff_f(k) * x**(3*k) / SpecialFunctions.factorial(3*k)
            g += SpecialFunctions._airy_coeff_g(k) * x**(3*k+1) / SpecialFunctions.factorial(3*k+1)
        return c1 * f - c2 * g

    @staticmethod
    def _airy_coeff_f(k: int) -> float:
        result = 1.0
        for i in range(k):
            result *= (3*i + 2)
        return result if k > 0 else 1.0

    @staticmethod
    def _airy_coeff_g(k: int) -> float:
        result = 1.0
        for i in range(k):
            result *= (3*i + 4)
        return result if k > 0 else 1.0

    # ── Error function ──

    @staticmethod
    def erf(x: float) -> float:
        """Error function erf(x) = (2/√π) ∫₀^x e^{-t²} dt."""
        if abs(x) < 1e-15:
            return 0.0
        # Horner approximation (Abramowitz & Stegun)
        sign = 1 if x >= 0 else -1
        x = abs(x)
        a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
        p = 0.3275911
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1) * t * math.exp(-x*x)
        return sign * y

    @staticmethod
    def erfc(x: float) -> float:
        """Complementary error function erfc(x) = 1 - erf(x)."""
        return 1.0 - SpecialFunctions.erf(x)

    # ── Hypergeometric (2F1) ──

    @staticmethod
    def hyper_2f1(a: float, b: float, c: float, z: float, terms: int = 100) -> float:
        """Gauss hypergeometric function ₂F₁(a,b;c;z) — series for |z|<1."""
        if abs(z) >= 1:
            return float('nan')  # Need analytic continuation
        result = 1.0
        term = 1.0
        for n in range(1, terms):
            term *= (a + n - 1) * (b + n - 1) / ((c + n - 1) * n) * z
            result += term
            if abs(term) < 1e-15:
                break
        return result

    # ── Riemann Zeta ──

    @staticmethod
    def zeta(s: float, terms: int = 100) -> float:
        """Riemann zeta function ζ(s) for s > 1 via direct sum + Euler-Maclaurin."""
        if s <= 1:
            return float('inf')
        result = 0.0
        for n in range(1, terms + 1):
            result += 1.0 / n**s
        # Euler-Maclaurin correction
        result += 1.0 / ((s - 1) * terms**(s-1))
        return result

    # ── Elliptic integrals ──

    @staticmethod
    def elliptic_k(k: float) -> float:
        """Complete elliptic integral of first kind K(k) via AGM."""
        if abs(k) >= 1:
            return float('inf')
        a, b = 1.0, math.sqrt(1 - k*k)
        for _ in range(50):
            a_new = (a + b) / 2
            b = math.sqrt(a * b)
            a = a_new
            if abs(a - b) < 1e-15:
                break
        return math.pi / (2 * a)

    @staticmethod
    def elliptic_e(k: float) -> float:
        """Complete elliptic integral of second kind E(k) via AGM variant."""
        if abs(k) >= 1:
            return 1.0
        a, b = 1.0, math.sqrt(1 - k*k)
        c_sum = k*k
        power = 1
        for _ in range(50):
            a_new = (a + b) / 2
            b_new = math.sqrt(a * b)
            c = (a - b) / 2
            power *= 2
            c_sum += power * c*c
            a, b = a_new, b_new
            if abs(c) < 1e-15:
                break
        return (math.pi / (2 * a)) * (1 - c_sum / 2)

    # ── Dirac delta properties ──

    @staticmethod
    def delta_properties() -> Dict[str, str]:
        """Properties of the Dirac delta function."""
        return {
            "definition": "∫f(x)δ(x-a)dx = f(a)",
            "normalization": "∫δ(x)dx = 1",
            "scaling": "δ(ax) = δ(x)/|a|",
            "derivative": "∫f(x)δ'(x)dx = -f'(0)",
            "composition": "δ(g(x)) = Σ δ(x-xᵢ)/|g'(xᵢ)| at zeros xᵢ",
            "fourier": "δ(x) = (1/2π)∫e^{ikx}dk",
            "3d": "δ³(r) = δ(x)δ(y)δ(z) = δ(r)/(4πr²) in spherical",
        }

    # ── Describe function (symbolic info) ──

    @staticmethod
    def describe(name: str) -> Optional[Dict]:
        """Get properties, recurrence, generating function, orthogonality for a special function."""
        catalog = {
            "bessel_j": {
                "name": "Bessel function of first kind J_n(x)",
                "ode": "x²y'' + xy' + (x²-n²)y = 0",
                "generating": "e^{(x/2)(t-1/t)} = Σ J_n(x) t^n",
                "orthogonality": "∫₀^a J_n(α_{nm}r/a) J_n(α_{nk}r/a) r dr = (a²/2)[J_{n+1}(α_{nm})]² δ_{mk}",
                "recurrence": "J_{n-1}(x) + J_{n+1}(x) = (2n/x)J_n(x)",
                "asymptotic": "J_n(x) ~ √(2/πx) cos(x - nπ/2 - π/4) for x→∞",
            },
            "legendre": {
                "name": "Legendre polynomial P_l(x)",
                "ode": "(1-x²)y'' - 2xy' + l(l+1)y = 0",
                "generating": "1/√(1-2xt+t²) = Σ P_l(x) t^l",
                "orthogonality": "∫₋₁¹ P_l(x) P_m(x) dx = 2δ_{lm}/(2l+1)",
                "recurrence": "(l+1)P_{l+1} = (2l+1)xP_l - lP_{l-1}",
                "rodrigues": "P_l(x) = (1/2^l l!) d^l/dx^l (x²-1)^l",
            },
            "hermite": {
                "name": "Hermite polynomial H_n(x) (physicist's)",
                "ode": "y'' - 2xy' + 2ny = 0",
                "generating": "e^{2xt-t²} = Σ H_n(x) t^n/n!",
                "orthogonality": "∫₋∞^∞ H_m(x) H_n(x) e^{-x²} dx = √π 2^n n! δ_{mn}",
                "recurrence": "H_{n+1}(x) = 2xH_n(x) - 2nH_{n-1}(x)",
                "physics": "QM harmonic oscillator: ψ_n(x) = c_n H_n(αx) e^{-α²x²/2}",
            },
            "laguerre": {
                "name": "Laguerre polynomial L_n(x)",
                "ode": "xy'' + (1-x)y' + ny = 0",
                "generating": "e^{-xt/(1-t)}/(1-t) = Σ L_n(x) t^n",
                "orthogonality": "∫₀^∞ L_m(x) L_n(x) e^{-x} dx = δ_{mn}",
                "recurrence": "(n+1)L_{n+1} = (2n+1-x)L_n - nL_{n-1}",
                "physics": "Hydrogen radial: R_nl(r) ~ r^l L_{n-l-1}^{2l+1}(2r/na₀) e^{-r/na₀}",
            },
            "spherical_harmonic": {
                "name": "Spherical harmonic Y_l^m(θ,φ)",
                "equation": "Y_l^m = N_lm P_l^m(cosθ) e^{imφ}",
                "orthogonality": "∫Y_l^m* Y_l'^m' dΩ = δ_{ll'}δ_{mm'}",
                "addition_theorem": "P_l(cosγ) = (4π/2l+1) Σ Y_l^m*(θ',φ') Y_l^m(θ,φ)",
                "physics": "Angular part of Laplacian eigenfunctions; ∇²Y=-l(l+1)Y/r²",
                "parity": "Y_l^m(-r̂) = (-1)^l Y_l^m(r̂)",
            },
            "gamma": {
                "name": "Gamma function Γ(x)",
                "definition": "Γ(x) = ∫₀^∞ t^{x-1} e^{-t} dt for Re(x)>0",
                "factorial": "Γ(n+1) = n! for non-negative integers",
                "reflection": "Γ(x)Γ(1-x) = π/sin(πx)",
                "duplication": "Γ(x)Γ(x+1/2) = √π/2^{2x-1} Γ(2x)",
                "stirling": "Γ(x) ~ √(2π/x)(x/e)^x for x→∞",
                "residues": "Res(Γ,-n) = (-1)^n/n!",
            },
            "hypergeometric": {
                "name": "Gauss hypergeometric ₂F₁(a,b;c;z)",
                "definition": "₂F₁ = Σ (a)_n(b)_n/(c)_n · z^n/n!",
                "ode": "z(1-z)y'' + [c-(a+b+1)z]y' - ab y = 0",
                "special_cases": "Many functions are special cases: P_l, T_n, K(k), arcsin, log, ...",
                "euler_integral": "₂F₁ = Γ(c)/[Γ(b)Γ(c-b)] ∫₀¹ t^{b-1}(1-t)^{c-b-1}(1-zt)^{-a} dt",
            },
            "airy": {
                "name": "Airy functions Ai(x), Bi(x)",
                "ode": "y'' - xy = 0",
                "physics": "WKB connection formulas; linear potential in QM",
                "asymptotic_neg": "Ai(-x) ~ cos(2x^{3/2}/3 - π/4)/(√π x^{1/4})",
                "asymptotic_pos": "Ai(x) ~ e^{-2x^{3/2}/3}/(2√π x^{1/4})",
            },
            "bessel_spherical": {
                "name": "Spherical Bessel function j_l(x)",
                "relation": "j_l(x) = √(π/2x) J_{l+1/2}(x)",
                "explicit": "j_0=sin(x)/x, j_1=sin(x)/x²-cos(x)/x",
                "ode": "x²y''+2xy'+[x²-l(l+1)]y=0",
                "physics": "Free-particle radial wavefunction in QM",
                "orthogonality": "∫₀^∞ j_l(kr) j_l(k'r) r² dr = (π/2k²)δ(k-k')",
            },
        }
        return catalog.get(name)


# ══════════════════════════════════════════════════════════════════════════════
# TENSOR ENGINE — Index notation, metric operations, curvature
# ══════════════════════════════════════════════════════════════════════════════

class TensorEngine:
    """Tensor calculus engine for general relativity and differential geometry.
    Works with symbolic metric components as callables or numerical arrays."""

    def __init__(self, dim: int = 4):
        self.dim = dim
        self.metric = None  # g_μν as 2D list
        self.inverse_metric = None  # g^μν

    def set_metric(self, g: List[List[float]]):
        """Set the metric tensor g_μν."""
        self.metric = g
        self.inverse_metric = self._invert_matrix(g)

    def _invert_matrix(self, m: List[List[float]]) -> List[List[float]]:
        """Invert a matrix (Gauss-Jordan)."""
        n = len(m)
        # Augmented matrix
        aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
        for col in range(n):
            # Find pivot
            max_row = col
            for row in range(col+1, n):
                if abs(aug[row][col]) > abs(aug[max_row][col]):
                    max_row = row
            aug[col], aug[max_row] = aug[max_row], aug[col]
            pivot = aug[col][col]
            if abs(pivot) < 1e-15:
                continue
            for j in range(2*n):
                aug[col][j] /= pivot
            for row in range(n):
                if row != col:
                    factor = aug[row][col]
                    for j in range(2*n):
                        aug[row][j] -= factor * aug[col][j]
        return [row[n:] for row in aug]

    def christoffel(self, mu: int, nu: int, rho: int) -> float:
        """Christoffel symbol Γ^mu_{nu rho} from metric.
        Γ^σ_{μν} = ½g^{σρ}(∂_μ g_{νρ} + ∂_ν g_{μρ} - ∂_ρ g_{μν})
        Note: For numerical metrics, derivatives must be provided separately.
        This returns the formula structure."""
        if self.inverse_metric is None:
            return 0.0
        # For constant metrics, Christoffel = 0
        return 0.0

    def christoffel_from_derivatives(self, g: List[List[float]],
                                      dg: List[List[List[float]]],
                                      ginv: List[List[float]]) -> List[List[List[float]]]:
        """Compute Christoffel symbols given metric, its derivatives, and inverse.
        dg[alpha][mu][nu] = ∂_alpha g_{mu nu}
        Returns Gamma[sigma][mu][nu] = Γ^σ_{μν}
        """
        n = self.dim
        gamma = [[[0.0]*n for _ in range(n)] for _ in range(n)]
        for sigma in range(n):
            for mu in range(n):
                for nu in range(n):
                    val = 0.0
                    for rho in range(n):
                        val += 0.5 * ginv[sigma][rho] * (
                            dg[mu][nu][rho] + dg[nu][mu][rho] - dg[rho][mu][nu]
                        )
                    gamma[sigma][mu][nu] = val
        return gamma

    def riemann_from_christoffel(self, gamma: List[List[List[float]]],
                                  dgamma: List[List[List[List[float]]]]) -> List[List[List[List[float]]]]:
        """Riemann tensor R^rho_{sigma mu nu} from Christoffel symbols and their derivatives.
        R^ρ_{σμν} = ∂_μΓ^ρ_{νσ} - ∂_νΓ^ρ_{μσ} + Γ^ρ_{μλ}Γ^λ_{νσ} - Γ^ρ_{νλ}Γ^λ_{μσ}
        """
        n = self.dim
        R = [[[[0.0]*n for _ in range(n)] for _ in range(n)] for _ in range(n)]
        for rho in range(n):
            for sigma in range(n):
                for mu in range(n):
                    for nu in range(n):
                        val = dgamma[mu][rho][nu][sigma] - dgamma[nu][rho][mu][sigma]
                        for lam in range(n):
                            val += gamma[rho][mu][lam] * gamma[lam][nu][sigma]
                            val -= gamma[rho][nu][lam] * gamma[lam][mu][sigma]
                        R[rho][sigma][mu][nu] = val
        return R

    def ricci_tensor(self, riemann: List[List[List[List[float]]]]) -> List[List[float]]:
        """Ricci tensor R_{μν} = R^ρ_{μρν} (contraction of Riemann)."""
        n = self.dim
        ricci = [[0.0]*n for _ in range(n)]
        for mu in range(n):
            for nu in range(n):
                for rho in range(n):
                    ricci[mu][nu] += riemann[rho][mu][rho][nu]
        return ricci

    def ricci_scalar(self, ricci: List[List[float]], ginv: List[List[float]]) -> float:
        """Ricci scalar R = g^{μν} R_{μν}."""
        n = self.dim
        R = 0.0
        for mu in range(n):
            for nu in range(n):
                R += ginv[mu][nu] * ricci[mu][nu]
        return R

    def einstein_tensor(self, ricci: List[List[float]], R_scalar: float,
                        g: List[List[float]]) -> List[List[float]]:
        """Einstein tensor G_{μν} = R_{μν} - ½Rg_{μν}."""
        n = self.dim
        G = [[0.0]*n for _ in range(n)]
        for mu in range(n):
            for nu in range(n):
                G[mu][nu] = ricci[mu][nu] - 0.5 * R_scalar * g[mu][nu]
        return G

    def contract(self, tensor: list, index1: int, index2: int, rank: int) -> list:
        """Contract two indices of a tensor (trace over those indices with metric)."""
        # Simplified: for rank-2, contraction gives scalar (trace)
        if rank == 2:
            n = len(tensor)
            return sum(tensor[i][i] for i in range(n))
        return tensor  # Higher ranks need more complex handling

    def raise_index(self, vector_lower: List[float], ginv: List[List[float]]) -> List[float]:
        """Raise index: v^μ = g^{μν} v_ν."""
        n = len(vector_lower)
        return [sum(ginv[mu][nu] * vector_lower[nu] for nu in range(n)) for mu in range(n)]

    def lower_index(self, vector_upper: List[float], g: List[List[float]]) -> List[float]:
        """Lower index: v_μ = g_{μν} v^ν."""
        n = len(vector_upper)
        return [sum(g[mu][nu] * vector_upper[nu] for nu in range(n)) for mu in range(n)]

    def determinant(self, matrix: List[List[float]]) -> float:
        """Compute determinant of matrix."""
        n = len(matrix)
        if n == 1:
            return matrix[0][0]
        if n == 2:
            return matrix[0][0]*matrix[1][1] - matrix[0][1]*matrix[1][0]
        if n == 3:
            return (matrix[0][0]*(matrix[1][1]*matrix[2][2]-matrix[1][2]*matrix[2][1])
                   -matrix[0][1]*(matrix[1][0]*matrix[2][2]-matrix[1][2]*matrix[2][0])
                   +matrix[0][2]*(matrix[1][0]*matrix[2][1]-matrix[1][1]*matrix[2][0]))
        # General: LU decomposition
        m = [row[:] for row in matrix]
        det = 1.0
        for i in range(n):
            max_row = max(range(i, n), key=lambda r: abs(m[r][i]))
            if max_row != i:
                m[i], m[max_row] = m[max_row], m[i]
                det *= -1
            if abs(m[i][i]) < 1e-15:
                return 0.0
            det *= m[i][i]
            for j in range(i+1, n):
                factor = m[j][i] / m[i][i]
                for k in range(i, n):
                    m[j][k] -= factor * m[i][k]
        return det

    # ── Standard metrics ──

    @staticmethod
    def minkowski() -> List[List[float]]:
        """Minkowski metric η_{μν} = diag(-1,1,1,1)."""
        return [[-1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

    @staticmethod
    def schwarzschild(r: float, M: float, G: float = 6.674e-11, c: float = 3e8) -> List[List[float]]:
        """Schwarzschild metric at radius r for mass M.
        ds² = -(1-r_s/r)c²dt² + dr²/(1-r_s/r) + r²dΩ²"""
        rs = 2*G*M/c**2
        f = 1 - rs/r if r > rs else 0.01  # avoid singularity
        return [
            [-f*c**2, 0, 0, 0],
            [0, 1/f, 0, 0],
            [0, 0, r**2, 0],
            [0, 0, 0, r**2]  # simplified (should be r²sin²θ)
        ]

    @staticmethod
    def frw(a: float, k: int = 0) -> List[List[float]]:
        """FRW (Friedmann-Robertson-Walker) metric for scale factor a(t).
        k=0 (flat), k=1 (closed), k=-1 (open). Simplified spatial part."""
        return [
            [-1, 0, 0, 0],
            [0, a**2, 0, 0],
            [0, 0, a**2, 0],
            [0, 0, 0, a**2],
        ]

    @staticmethod
    def metric_info(name: str) -> Optional[Dict]:
        """Get information about standard metrics."""
        metrics = {
            "minkowski": {
                "name": "Minkowski (flat spacetime)",
                "line_element": "ds² = -c²dt² + dx² + dy² + dz²",
                "signature": "(-,+,+,+)",
                "christoffel": "All zero",
                "riemann": "All zero (flat)",
                "physics": "Special relativity, no gravity",
            },
            "schwarzschild": {
                "name": "Schwarzschild (non-rotating black hole)",
                "line_element": "ds² = -(1-r_s/r)c²dt² + dr²/(1-r_s/r) + r²dΩ²",
                "parameters": "r_s = 2GM/c² (Schwarzschild radius)",
                "singularities": "r=0 (true), r=r_s (coordinate, event horizon)",
                "physics": "Static spherically symmetric vacuum solution",
            },
            "kerr": {
                "name": "Kerr (rotating black hole)",
                "line_element": "ds² involves Δ=r²-2Mr+a², Σ=r²+a²cos²θ",
                "parameters": "M (mass), a=J/M (spin parameter)",
                "features": "Ergosphere, two horizons r±=M±√(M²-a²)",
                "physics": "Stationary axisymmetric vacuum solution",
            },
            "frw": {
                "name": "Friedmann-Robertson-Walker (cosmology)",
                "line_element": "ds² = -c²dt² + a(t)²[dr²/(1-kr²) + r²dΩ²]",
                "parameters": "a(t) scale factor, k=0,±1 curvature",
                "physics": "Homogeneous isotropic expanding universe",
            },
            "de_sitter": {
                "name": "de Sitter (exponentially expanding)",
                "line_element": "ds² = -(1-r²/R²)dt² + dr²/(1-r²/R²) + r²dΩ²",
                "parameters": "R = √(3/Λ) (de Sitter radius)",
                "physics": "Maximally symmetric vacuum with Λ>0",
            },
            "ads": {
                "name": "Anti-de Sitter (negative cosmological constant)",
                "line_element": "ds² = -(1+r²/L²)dt² + dr²/(1+r²/L²) + r²dΩ²",
                "parameters": "L = AdS radius",
                "physics": "Maximally symmetric with Λ<0; boundary = CFT",
            },
        }
        return metrics.get(name)


# ══════════════════════════════════════════════════════════════════════════════
# GREEN'S FUNCTION DATABASE — Standard PDEs
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class GreenFunction:
    """A Green's function for a specific PDE and boundary condition."""
    name: str
    pde: str
    equation: str
    domain: str
    boundary: str
    dimension: int
    applications: List[str] = field(default_factory=list)


class GreensFunctionDB:
    """Database of Green's functions for standard PDEs in physics."""

    def __init__(self):
        self.greens: Dict[str, GreenFunction] = {}
        self._build()

    def get(self, name: str) -> Optional[GreenFunction]:
        return self.greens.get(name)

    def search(self, keyword: str) -> List[GreenFunction]:
        kw = keyword.lower()
        return [g for g in self.greens.values()
                if kw in g.name.lower() or kw in g.pde.lower() or
                kw in g.domain.lower() or any(kw in a.lower() for a in g.applications)]

    def by_pde(self, pde_type: str) -> List[GreenFunction]:
        pt = pde_type.lower()
        return [g for g in self.greens.values()
                if pt in g.pde.lower() or pt in g.name.lower() or pt in g.domain.lower()]

    def _add(self, name, pde, equation, domain, boundary, dimension, applications=None):
        self.greens[name] = GreenFunction(name, pde, equation, domain, boundary,
                                          dimension, applications or [])

    def _build(self):
        # ── Laplace / Poisson ──
        self._add("laplace_3d_free", "∇²G = -δ³(r-r')",
            "G(r,r') = 1/(4π|r-r'|)",
            "ℝ³ (free space)", "G→0 as |r|→∞", 3,
            ["electrostatics", "gravitational potential"])

        self._add("laplace_2d_free", "∇²G = -δ²(r-r')",
            "G(r,r') = -(1/2π)ln|r-r'|",
            "ℝ² (free space)", "logarithmic at infinity", 2,
            ["2D electrostatics", "fluid flow"])

        self._add("laplace_sphere_dirichlet", "∇²G = -δ³(r-r')",
            "G = (1/4π)[1/|r-r'| - a/(r'|r-a²r'/r'²|)]",
            "interior of sphere radius a", "G=0 on r=a", 3,
            ["image charges", "electrostatics in sphere"])

        self._add("laplace_half_space", "∇²G = -δ³(r-r')",
            "G = (1/4π)[1/|r-r'| - 1/|r-r'_image|]",
            "z > 0 half-space", "G=0 on z=0 (Dirichlet)", 3,
            ["grounded plane", "image method"])

        # ── Helmholtz ──
        self._add("helmholtz_3d", "(∇²+k²)G = -δ³(r-r')",
            "G(r,r') = e^{ik|r-r'|}/(4π|r-r'|) (outgoing)",
            "ℝ³", "Sommerfeld radiation condition", 3,
            ["scattering", "acoustics", "antenna radiation"])

        self._add("helmholtz_2d", "(∇²+k²)G = -δ²(r-r')",
            "G(r,r') = (i/4)H₀^(1)(k|r-r'|)",
            "ℝ²", "outgoing wave", 2,
            ["2D scattering", "waveguides"])

        # ── Wave equation ──
        self._add("wave_3d_retarded", "(∂²/∂t²-c²∇²)G = -δ³(r)δ(t)",
            "G_ret = δ(t-|r|/c)/(4πc²|r|)",
            "ℝ³ × t>0", "causal (retarded)", 3,
            ["EM radiation", "sound", "retarded potentials"])

        self._add("wave_3d_advanced", "(∂²/∂t²-c²∇²)G = -δ³(r)δ(t)",
            "G_adv = δ(t+|r|/c)/(4πc²|r|)",
            "ℝ³ × t<0", "anti-causal (advanced)", 3,
            ["Wheeler-Feynman", "time reversal"])

        self._add("wave_1d", "(∂²/∂t²-c²∂²/∂x²)G = -δ(x)δ(t)",
            "G = (1/2c)θ(t-|x|/c)",
            "ℝ¹ × t>0", "causal", 1,
            ["string vibrations", "1D waves"])

        # ── Heat / Diffusion ──
        self._add("heat_3d", "(∂/∂t-D∇²)G = δ³(r)δ(t)",
            "G = θ(t)/(4πDt)^{3/2} exp(-r²/4Dt)",
            "ℝ³ × t>0", "causal, G→0 as t→0⁺ (for r≠0)", 3,
            ["diffusion", "heat conduction", "Brownian motion"])

        self._add("heat_1d", "(∂/∂t-D∂²/∂x²)G = δ(x)δ(t)",
            "G = θ(t)/√(4πDt) exp(-x²/4Dt)",
            "ℝ¹ × t>0", "causal", 1,
            ["1D diffusion", "random walk"])

        # ── Schrödinger ──
        self._add("schrodinger_free_3d", "(iℏ∂/∂t+ℏ²∇²/2m)K = iℏδ³(r)δ(t)",
            "K = (m/2πiℏt)^{3/2} exp(imr²/2ℏt)",
            "ℝ³ × t>0", "causal propagator", 3,
            ["free particle propagation", "path integral kernel"])

        self._add("schrodinger_harmonic", "QM propagator for H=p²/2m+½mω²x²",
            "K = √(mω/2πiℏsinωt) exp{imω[(x²+x'²)cosωt-2xx']/(2ℏsinωt)}",
            "ℝ¹ × t>0", "Mehler kernel", 1,
            ["harmonic oscillator", "coherent states"])

        # ── Klein-Gordon (Feynman) ──
        self._add("feynman_propagator", "(□+m²)G_F = -δ⁴(x)",
            "G_F(x) = ∫d⁴k e^{-ikx}/(k²-m²+iε) × 1/(2π)⁴",
            "Minkowski space", "Feynman boundary (positive freq forward)", 4,
            ["QFT", "Feynman diagrams", "virtual particles"])

        self._add("retarded_propagator_kg", "(□+m²)G_ret = -δ⁴(x)",
            "G_ret = θ(t)[δ(s)/2π - mJ₁(m√s)/(4π√s)] where s=t²-r²",
            "Minkowski space", "causal support inside light cone", 4,
            ["classical field propagation", "causality"])

        # ── Yukawa ──
        self._add("yukawa", "(∇²-μ²)G = -δ³(r)",
            "G = e^{-μr}/(4πr)",
            "ℝ³", "G→0 as r→∞", 3,
            ["nuclear force", "screened Coulomb", "Debye shielding"])

        # ── Biharmonic ──
        self._add("biharmonic_2d", "∇⁴G = δ²(r-r')",
            "G = |r-r'|²(ln|r-r'|-1)/(8π)",
            "ℝ²", "free space", 2,
            ["thin plate bending", "Stokes flow"])

    def stats(self) -> Dict:
        return {"total": len(self.greens)}


# ══════════════════════════════════════════════════════════════════════════════
# SYMMETRY ENGINE — Lie groups, representations, physics applications
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class LieGroupInfo:
    """Information about a Lie group relevant to physics."""
    name: str
    algebra: str
    dimension: int  # of the group manifold
    rank: int
    generators: str
    casimir: str
    representations: List[str]
    physics: List[str]


class SymmetryEngine:
    """Lie groups and their representations in physics."""

    def __init__(self):
        self.groups: Dict[str, LieGroupInfo] = {}
        self._build()

    def get(self, name: str) -> Optional[LieGroupInfo]:
        name_l = name.lower().replace(" ", "").replace("(", "").replace(")", "")
        for key, val in self.groups.items():
            if name_l in key.lower().replace(" ", "").replace("(", "").replace(")", ""):
                return val
        return None

    def search(self, keyword: str) -> List[LieGroupInfo]:
        kw = keyword.lower()
        return [g for g in self.groups.values()
                if kw in g.name.lower() or kw in g.algebra.lower()
                or any(kw in p.lower() for p in g.physics)]

    def _build(self):
        self.groups["U(1)"] = LieGroupInfo(
            name="U(1)", algebra="u(1)", dimension=1, rank=1,
            generators="Single generator Q (charge)",
            casimir="Q² (trivial)",
            representations=["charge n ∈ ℤ: e^{inθ}"],
            physics=["Electromagnetism gauge group", "phase symmetry",
                    "charge conservation", "QED"])

        self.groups["SU(2)"] = LieGroupInfo(
            name="SU(2)", algebra="su(2): [Jᵢ,Jⱼ]=iεᵢⱼₖJₖ", dimension=3, rank=1,
            generators="J₁, J₂, J₃ (Pauli matrices σᵢ/2)",
            casimir="J² = J₁²+J₂²+J₃²; eigenvalue j(j+1)",
            representations=["spin j=0,½,1,3/2,...; dim=2j+1",
                           "j=0: scalar", "j=½: spinor (2D)", "j=1: vector (3D)"],
            physics=["Spin/angular momentum", "isospin (nuclear)",
                    "weak interaction SU(2)_L", "rotation group (double cover of SO(3))"])

        self.groups["SO(3)"] = LieGroupInfo(
            name="SO(3)", algebra="so(3) ≅ su(2): [Lᵢ,Lⱼ]=iεᵢⱼₖLₖ", dimension=3, rank=1,
            generators="L₁, L₂, L₃ (angular momentum)",
            casimir="L² = l(l+1)ℏ²",
            representations=["integer l=0,1,2,...; dim=2l+1",
                           "l=0: scalar", "l=1: vector", "l=2: tensor"],
            physics=["Spatial rotations", "orbital angular momentum",
                    "spherical harmonics Y_l^m", "multipole expansion"])

        self.groups["SU(3)"] = LieGroupInfo(
            name="SU(3)", algebra="su(3): 8 generators (Gell-Mann λ matrices)",
            dimension=8, rank=2,
            generators="λ₁...λ₈ (Gell-Mann matrices); T_a = λ_a/2",
            casimir="C₁ = Σ T_a²; C₂ (cubic)",
            representations=["(p,q) labels: dim = ½(p+1)(q+1)(p+q+2)",
                           "3 (fundamental, quarks)", "3̄ (anti-fundamental)",
                           "8 (adjoint, gluons)", "6, 10, 27..."],
            physics=["QCD color gauge group", "flavor SU(3) (u,d,s quarks)",
                    "Eightfold Way", "gluon self-interaction"])

        self.groups["Lorentz"] = LieGroupInfo(
            name="SO(3,1) Lorentz group", algebra="so(3,1): [Jᵢ,Jⱼ]=iεᵢⱼₖJₖ, [Kᵢ,Kⱼ]=-iεᵢⱼₖJₖ, [Jᵢ,Kⱼ]=iεᵢⱼₖKₖ",
            dimension=6, rank=2,
            generators="J₁,J₂,J₃ (rotations) + K₁,K₂,K₃ (boosts)",
            casimir="C₁ = J²-K² (= j₁(j₁+1)+j₂(j₂+1)); C₂ = J·K",
            representations=["(j₁,j₂) with j₁,j₂ = 0,½,1,...",
                           "(0,0): scalar", "(½,0)⊕(0,½): Dirac spinor",
                           "(½,½): 4-vector", "(1,0)⊕(0,1): antisym tensor (F_μν)"],
            physics=["Special relativity symmetry", "classification of particles by spin",
                    "Dirac/Weyl/Majorana spinors", "tensor fields"])

        self.groups["Poincare"] = LieGroupInfo(
            name="Poincaré group (ISO(3,1))", algebra="Lorentz + translations P_μ",
            dimension=10, rank=2,
            generators="J_{μν} (6 Lorentz) + P_μ (4 translations)",
            casimir="P² = P_μP^μ (mass²); W² = W_μW^μ (spin, Pauli-Lubanski)",
            representations=["Massive: (m,s) with m>0, spin s",
                           "Massless: (0,λ) helicity λ",
                           "Wigner classification of particles"],
            physics=["Full spacetime symmetry of SR", "particle classification",
                    "conservation of energy-momentum + angular momentum",
                    "Wigner's classification: particles = irreps of Poincaré"])

        self.groups["SU(2)xU(1)"] = LieGroupInfo(
            name="SU(2)_L × U(1)_Y", algebra="electroweak gauge algebra",
            dimension=4, rank=2,
            generators="T₁,T₂,T₃ (weak isospin) + Y (hypercharge)",
            casimir="T², Y; Q = T₃ + Y/2 (electric charge)",
            representations=["Left doublets (ν,e)_L with T=½, Y=-1",
                           "Right singlets e_R with T=0, Y=-2",
                           "Higgs doublet φ with T=½, Y=1"],
            physics=["Electroweak interaction before SSB",
                    "SSB → U(1)_EM; W±,Z get mass, γ stays massless",
                    "Weinberg angle: tanθ_W = g'/g"])

        self.groups["SU(5)"] = LieGroupInfo(
            name="SU(5) (Georgi-Glashow GUT)", algebra="su(5): 24 generators",
            dimension=24, rank=4,
            generators="24 generators (contains SM as subgroup)",
            casimir="C₂, C₃, C₄",
            representations=["5̄: (d_R^c, e_L, ν_L)", "10: (u_L, d_L, u_R^c, e_R^c)",
                           "24: adjoint (gauge bosons including X,Y)"],
            physics=["Grand Unified Theory", "proton decay prediction",
                    "charge quantization explanation", "sin²θ_W prediction"])

        self.groups["E8"] = LieGroupInfo(
            name="E₈ (exceptional)", algebra="e₈: 248-dimensional",
            dimension=248, rank=8,
            generators="248 generators",
            casimir="C₂ (Dynkin index 60 for adjoint)",
            representations=["248 (adjoint, smallest nontrivial)",
                           "No fundamental rep smaller than adjoint!"],
            physics=["Heterotic string theory E₈×E₈",
                    "largest exceptional Lie group", "lattice = densest sphere packing in 8D"])

    def noether_map(self) -> Dict[str, str]:
        """Map symmetries to conserved quantities (Noether's theorem)."""
        return {
            "time translation": "energy (Hamiltonian H)",
            "space translation": "momentum (p)",
            "rotation SO(3)": "angular momentum (L)",
            "boost (Lorentz)": "center-of-mass motion",
            "U(1) phase (global)": "electric charge Q",
            "U(1) phase (local/gauge)": "gauge invariance → photon",
            "SU(2) isospin": "isospin conservation (strong int.)",
            "SU(3) color": "color charge conservation",
            "scale invariance": "dilatation current (broken by mass)",
            "conformal": "special conformal current (in CFT)",
            "SUSY": "supercharge Q_α",
            "CPT": "CPT invariance (all local QFTs)",
            "parity P": "parity quantum number (violated by weak!)",
            "time reversal T": "T quantum number (violated by weak!)",
            "baryon number U(1)_B": "baryon number conservation",
            "lepton number U(1)_L": "lepton number (approx, violated by ν oscillations)",
        }

    def clebsch_gordan_su2(self, j1: float, j2: float) -> List[float]:
        """Decompose tensor product of SU(2) representations.
        j1 ⊗ j2 = |j1-j2| ⊕ |j1-j2|+1 ⊕ ... ⊕ j1+j2"""
        j_min = abs(j1 - j2)
        j_max = j1 + j2
        result = []
        j = j_min
        while j <= j_max + 0.01:
            result.append(j)
            j += 1
        return result

    def dimension_su2(self, j: float) -> int:
        """Dimension of SU(2) irrep with spin j."""
        return int(2*j + 1)

    def dimension_sun(self, n: int, rep: str) -> Optional[int]:
        """Dimension of common SU(N) representations."""
        dims = {
            "fundamental": n,
            "antifundamental": n,
            "adjoint": n*n - 1,
            "symmetric": n*(n+1)//2,
            "antisymmetric": n*(n-1)//2,
            "singlet": 1,
        }
        return dims.get(rep)

    def stats(self) -> Dict:
        return {"total_groups": len(self.groups)}


# ══════════════════════════════════════════════════════════════════════════════
# APPROXIMATION ENGINE — Taylor, WKB, perturbation, Padé, asymptotic
# ══════════════════════════════════════════════════════════════════════════════

class ApproximationEngine:
    """Methods for approximating solutions in physics."""

    # ── Taylor expansion ──

    @staticmethod
    def taylor(f: Callable[[float], float], x0: float, order: int = 5,
               h: float = 1e-4) -> List[float]:
        """Compute Taylor coefficients of f around x0 up to given order.
        Returns [f(x0), f'(x0), f''(x0)/2!, ...] — coefficients of (x-x0)^n."""
        coeffs = [f(x0)]
        # Use finite differences with appropriate step sizes
        for n in range(1, order + 1):
            hn = h * (2.0 ** (n//2))  # increase h for higher derivatives
            deriv = ApproximationEngine._nth_deriv_stable(f, x0, n, hn)
            coeffs.append(deriv / SpecialFunctions.factorial(n))
        return coeffs

    @staticmethod
    def _nth_deriv_stable(f: Callable, x: float, n: int, h: float) -> float:
        """Compute n-th derivative using central finite differences (stencil method)."""
        # Use the formula: f^(n)(x) ≈ (1/h^n) Σ_{k=0}^{n} (-1)^k C(n,k) f(x+(n/2-k)h)
        result = 0.0
        for k in range(n + 1):
            sign = (-1) ** k
            binom = SpecialFunctions.factorial(n) // (SpecialFunctions.factorial(k) * SpecialFunctions.factorial(n - k))
            xi = x + (n / 2.0 - k) * h
            result += sign * binom * f(xi)
        return result / (h ** n)

    @staticmethod
    def taylor_evaluate(coeffs: List[float], x: float, x0: float = 0.0) -> float:
        """Evaluate Taylor series at point x given coefficients around x0."""
        result = 0.0
        dx = x - x0
        for n, c in enumerate(coeffs):
            result += c * dx**n
        return result

    # ── Padé approximant ──

    @staticmethod
    def pade(coeffs: List[float], m: int, n: int) -> Tuple[List[float], List[float]]:
        """Compute [m/n] Padé approximant from Taylor coefficients.
        Returns (numerator_coeffs, denominator_coeffs) of P(x)/Q(x)
        where P has degree m, Q has degree n, Q(0)=1."""
        # Need m+n+1 Taylor coefficients
        N = m + n + 1
        if len(coeffs) < N:
            return coeffs[:m+1], [1.0]

        # Solve for denominator coefficients q₁...qₙ from linear system
        # Then numerator from p_k = c_k + Σ qⱼ c_{k-j}
        if n == 0:
            return coeffs[:m+1], [1.0]

        # Build system: Σⱼ qⱼ c_{m+1+i-j} = -c_{m+1+i} for i=0..n-1
        # This is a Toeplitz-like system
        A = [[0.0]*n for _ in range(n)]
        b = [0.0]*n
        for i in range(n):
            for j in range(n):
                idx = m + 1 + i - j - 1
                A[i][j] = coeffs[idx] if 0 <= idx < len(coeffs) else 0.0
            b[i] = -coeffs[m + 1 + i] if m + 1 + i < len(coeffs) else 0.0

        # Solve Aq = b (simple Gaussian elimination)
        q = ApproximationEngine._solve_linear(A, b)
        if q is None:
            return coeffs[:m+1], [1.0]

        denom = [1.0] + q

        # Compute numerator
        numer = []
        for k in range(m + 1):
            pk = coeffs[k]
            for j in range(1, min(k, n) + 1):
                pk += q[j-1] * (coeffs[k-j] if k-j >= 0 else 0.0)
            numer.append(pk)

        return numer, denom

    @staticmethod
    def _solve_linear(A: List[List[float]], b: List[float]) -> Optional[List[float]]:
        """Solve Ax=b via Gaussian elimination."""
        n = len(b)
        aug = [A[i][:] + [b[i]] for i in range(n)]
        for col in range(n):
            max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
            aug[col], aug[max_row] = aug[max_row], aug[col]
            if abs(aug[col][col]) < 1e-12:
                return None
            for row in range(col+1, n):
                factor = aug[row][col] / aug[col][col]
                for j in range(n+1):
                    aug[row][j] -= factor * aug[col][j]
        # Back substitution
        x = [0.0]*n
        for i in range(n-1, -1, -1):
            x[i] = aug[i][n]
            for j in range(i+1, n):
                x[i] -= aug[i][j] * x[j]
            x[i] /= aug[i][i]
        return x

    # ── WKB approximation ──

    @staticmethod
    def wkb_phase(V: Callable[[float], float], E: float, x1: float, x2: float,
                  m: float = 1.0, hbar: float = 1.0, steps: int = 1000) -> float:
        """WKB phase integral ∫√(2m(E-V(x)))/ℏ dx between turning points.
        Used for bound state quantization: ∫p dx = (n+½)πℏ"""
        dx = (x2 - x1) / steps
        phase = 0.0
        for i in range(steps):
            x = x1 + (i + 0.5) * dx
            arg = 2 * m * (E - V(x))
            if arg > 0:
                phase += math.sqrt(arg) * dx
        return phase / hbar

    @staticmethod
    def wkb_tunneling(V: Callable[[float], float], E: float, x1: float, x2: float,
                      m: float = 1.0, hbar: float = 1.0, steps: int = 1000) -> float:
        """WKB tunneling transmission coefficient.
        T ≈ exp(-2∫√(2m(V-E))/ℏ dx) through barrier."""
        dx = (x2 - x1) / steps
        kappa_integral = 0.0
        for i in range(steps):
            x = x1 + (i + 0.5) * dx
            arg = 2 * m * (V(x) - E)
            if arg > 0:
                kappa_integral += math.sqrt(arg) * dx
        return math.exp(-2 * kappa_integral / hbar)

    @staticmethod
    def wkb_bound_states(V: Callable[[float], float], m: float = 1.0,
                         hbar: float = 1.0, E_min: float = -10, E_max: float = 0,
                         x_range: Tuple[float, float] = (-10, 10),
                         max_n: int = 20) -> List[float]:
        """Find bound state energies using WKB quantization:
        ∮p dx = 2∫_{x1}^{x2} √(2m(E-V)) dx = (n+½)2πℏ"""
        energies = []
        dE = (E_max - E_min) / 1000

        for n in range(max_n):
            target = (n + 0.5) * math.pi * hbar
            # Bisection to find E where phase = target
            E_lo, E_hi = E_min, E_max
            for _ in range(50):
                E_mid = (E_lo + E_hi) / 2
                # Find turning points
                x1, x2 = ApproximationEngine._find_turning_points(V, E_mid, x_range)
                if x1 is None:
                    break
                phase = ApproximationEngine.wkb_phase(V, E_mid, x1, x2, m, hbar)
                if phase < target:
                    E_lo = E_mid
                else:
                    E_hi = E_mid
            if x1 is not None and abs(E_hi - E_lo) < 1e-10:
                energies.append((E_lo + E_hi) / 2)
            else:
                break
        return energies

    @staticmethod
    def _find_turning_points(V: Callable, E: float,
                             x_range: Tuple[float, float], steps: int = 500) -> Tuple:
        """Find classical turning points where V(x) = E."""
        x_min, x_max = x_range
        dx = (x_max - x_min) / steps
        points = []
        prev = V(x_min) - E
        for i in range(1, steps):
            x = x_min + i * dx
            curr = V(x) - E
            if prev * curr < 0:
                # Linear interpolation
                xc = x - dx * curr / (curr - prev)
                points.append(xc)
            prev = curr
        if len(points) >= 2:
            return points[0], points[-1]
        return None, None

    # ── Perturbation theory (quantum) ──

    @staticmethod
    def perturbation_energy_1st(H0_eigvals: List[float], V_matrix: List[List[float]],
                                 state: int) -> float:
        """First-order energy correction: E_n^(1) = ⟨n|V|n⟩."""
        return V_matrix[state][state]

    @staticmethod
    def perturbation_energy_2nd(H0_eigvals: List[float], V_matrix: List[List[float]],
                                 state: int) -> float:
        """Second-order energy correction: E_n^(2) = Σ_{m≠n} |V_{mn}|²/(E_n-E_m)."""
        E_n = H0_eigvals[state]
        correction = 0.0
        for m in range(len(H0_eigvals)):
            if m == state:
                continue
            V_mn = V_matrix[m][state]
            dE = E_n - H0_eigvals[m]
            if abs(dE) > 1e-15:
                correction += abs(V_mn)**2 / dE
        return correction

    @staticmethod
    def perturbation_state_1st(H0_eigvals: List[float], V_matrix: List[List[float]],
                                state: int) -> List[float]:
        """First-order state correction coefficients c_m = V_{mn}/(E_n-E_m)."""
        E_n = H0_eigvals[state]
        coeffs = []
        for m in range(len(H0_eigvals)):
            if m == state:
                coeffs.append(0.0)
            else:
                dE = E_n - H0_eigvals[m]
                if abs(dE) > 1e-15:
                    coeffs.append(V_matrix[m][state] / dE)
                else:
                    coeffs.append(0.0)
        return coeffs

    # ── Asymptotic expansion ──

    @staticmethod
    def stirling(n: float, terms: int = 5) -> float:
        """Stirling's approximation for Γ(n+1) ≈ n!.
        n! ~ √(2πn)(n/e)^n [1 + 1/12n + 1/288n² - ...]"""
        if n <= 0:
            return 1.0
        result = math.sqrt(2 * math.pi * n) * (n / math.e)**n
        # Correction terms
        corrections = [1.0, 1/(12*n), 1/(288*n**2), -139/(51840*n**3), -571/(2488320*n**4)]
        corr = sum(corrections[:terms])
        return result * corr

    @staticmethod
    def saddle_point_info() -> Dict[str, str]:
        """Information about the saddle-point (steepest descent) method."""
        return {
            "method": "Evaluate ∫e^{Nf(z)}dz for large N by deforming contour through saddle",
            "saddle_condition": "f'(z₀) = 0 (saddle point)",
            "result": "∫ ~ e^{Nf(z₀)} √(2π/(N|f''(z₀)|)) × phase",
            "validity": "N → ∞ (large parameter)",
            "applications": ["partition functions", "path integrals",
                           "Airy function asymptotics", "statistical mechanics"],
            "connection_to_wkb": "WKB is saddle-point of path integral",
        }

    @staticmethod
    def asymptotic_series_info() -> Dict[str, str]:
        """Properties of asymptotic series."""
        return {
            "definition": "Σaₙ/xⁿ is asymptotic to f(x) if |f(x)-Σ₀^N aₙ/xⁿ| = O(1/x^{N+1})",
            "key_property": "Series may DIVERGE but partial sums approximate f(x) for large x",
            "optimal_truncation": "Stop at smallest term for best approximation",
            "examples": ["Stirling series", "Ai(x) for x→+∞",
                        "perturbation series in QFT (often asymptotic!)"],
            "borel_summation": "Divergent series can sometimes be Borel-summed to recover f(x)",
        }
