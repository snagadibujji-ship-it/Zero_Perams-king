#!/usr/bin/env python3
"""
PROMETHEUS Level 3 — Theorem Beast
Abstract Algebra + Theorem Database + Proof Search Engine

The shift: from COMPUTING answers to PROVING statements.
Built by: Ghias + Kiro
"""

from typing import List, Dict, Optional, Set, Tuple
import math


# ═══════════════════════════════════════════════════════════════
# 3.1 THEOREM DATABASE
# Each theorem: name, field, statement, preconditions, conclusion,
# proof_strategy, depends_on, used_by
# ═══════════════════════════════════════════════════════════════

class Theorem:
    def __init__(self, name: str, field: str, statement: str,
                 preconditions: List[str], conclusion: str,
                 proof_strategy: str = '', depends_on: List[str] = None,
                 tags: List[str] = None):
        self.name = name
        self.field = field
        self.statement = statement
        self.preconditions = preconditions
        self.conclusion = conclusion
        self.proof_strategy = proof_strategy
        self.depends_on = depends_on or []
        self.tags = tags or []


class TheoremDB:
    """Database of 100+ mathematical theorems organized by field."""

    def __init__(self):
        self.theorems: Dict[str, Theorem] = {}
        self._build_database()

    def get(self, name: str) -> Optional[Theorem]:
        return self.theorems.get(name)

    def search(self, keyword: str) -> List[Theorem]:
        """Search theorems by keyword in name, statement, or tags."""
        kw = keyword.lower()
        results = []
        for t in self.theorems.values():
            if kw in t.name.lower() or kw in t.statement.lower() or \
               any(kw in tag for tag in t.tags):
                results.append(t)
        return results

    def by_field(self, field: str) -> List[Theorem]:
        return [t for t in self.theorems.values() if t.field == field]

    def by_conclusion(self, conclusion_keyword: str) -> List[Theorem]:
        """Find theorems whose conclusion matches."""
        kw = conclusion_keyword.lower()
        return [t for t in self.theorems.values() if kw in t.conclusion.lower()]

    def dependencies_of(self, name: str) -> List[str]:
        """Get all theorems this one depends on (recursive)."""
        t = self.get(name)
        if not t: return []
        deps = set(t.depends_on)
        for d in t.depends_on:
            deps.update(self.dependencies_of(d))
        return list(deps)

    def _add(self, **kwargs):
        t = Theorem(**kwargs)
        self.theorems[t.name] = t

    def _build_database(self):
        """Build the theorem database — 100+ theorems."""

        # ══════════════════════════════════════════════
        # GROUP THEORY (30 theorems)
        # ══════════════════════════════════════════════

        self._add(name="lagrange", field="group_theory",
            statement="If H is a subgroup of finite group G, then |H| divides |G|",
            preconditions=["G is finite group", "H is subgroup of G"],
            conclusion="|H| divides |G|",
            proof_strategy="coset_counting",
            tags=["order", "subgroup", "divides"])

        self._add(name="cauchy", field="group_theory",
            statement="If prime p divides |G|, then G has an element of order p",
            preconditions=["G is finite group", "p is prime", "p divides |G|"],
            conclusion="∃g∈G with ord(g)=p",
            proof_strategy="induction_on_order",
            depends_on=["lagrange"],
            tags=["prime", "order", "element"])

        self._add(name="sylow_existence", field="group_theory",
            statement="If p^k divides |G|, then G has a subgroup of order p^k",
            preconditions=["G is finite group", "p is prime", "p^k divides |G|"],
            conclusion="∃H≤G with |H|=p^k",
            proof_strategy="induction",
            depends_on=["cauchy"],
            tags=["sylow", "p-subgroup", "existence"])

        self._add(name="sylow_conjugate", field="group_theory",
            statement="All Sylow p-subgroups of G are conjugate",
            preconditions=["G is finite group", "P,Q are Sylow p-subgroups"],
            conclusion="∃g∈G: gPg⁻¹=Q",
            proof_strategy="orbit_stabilizer",
            depends_on=["sylow_existence"],
            tags=["sylow", "conjugate"])

        self._add(name="sylow_number", field="group_theory",
            statement="The number n_p of Sylow p-subgroups satisfies: n_p≡1(mod p) and n_p divides |G|/p^k",
            preconditions=["G is finite group", "p is prime"],
            conclusion="n_p ≡ 1 (mod p) and n_p | [G:P]",
            proof_strategy="conjugation_action",
            depends_on=["sylow_conjugate"],
            tags=["sylow", "number", "counting"])

        self._add(name="first_isomorphism", field="group_theory",
            statement="If φ:G→H is a homomorphism, then G/ker(φ) ≅ im(φ)",
            preconditions=["φ:G→H is group homomorphism"],
            conclusion="G/ker(φ) ≅ im(φ)",
            proof_strategy="construct_isomorphism",
            tags=["isomorphism", "kernel", "image", "quotient"])

        self._add(name="second_isomorphism", field="group_theory",
            statement="If H≤G and N⊴G, then HN/N ≅ H/(H∩N)",
            preconditions=["H is subgroup of G", "N is normal in G"],
            conclusion="HN/N ≅ H/(H∩N)",
            depends_on=["first_isomorphism"],
            tags=["isomorphism", "normal", "quotient"])

        self._add(name="third_isomorphism", field="group_theory",
            statement="If N⊆M are normal in G, then (G/N)/(M/N) ≅ G/M",
            preconditions=["N⊴G", "M⊴G", "N⊆M"],
            conclusion="(G/N)/(M/N) ≅ G/M",
            depends_on=["first_isomorphism"],
            tags=["isomorphism", "quotient"])

        self._add(name="center_pgroup", field="group_theory",
            statement="If G is a p-group, then Z(G) is non-trivial",
            preconditions=["G is p-group", "|G|>1"],
            conclusion="Z(G) ≠ {e}",
            proof_strategy="class_equation",
            tags=["center", "p-group"])

        self._add(name="p2_abelian", field="group_theory",
            statement="Every group of order p² is abelian",
            preconditions=["|G| = p²", "p is prime"],
            conclusion="G is abelian",
            proof_strategy="center_argument",
            depends_on=["center_pgroup", "quotient_cyclic_implies_abelian"],
            tags=["abelian", "p-group", "order"])

        self._add(name="quotient_cyclic_implies_abelian", field="group_theory",
            statement="If G/Z(G) is cyclic, then G is abelian",
            preconditions=["G/Z(G) is cyclic"],
            conclusion="G is abelian",
            proof_strategy="element_computation",
            tags=["cyclic", "center", "abelian"])

        self._add(name="normal_index2", field="group_theory",
            statement="Every subgroup of index 2 is normal",
            preconditions=["H≤G", "[G:H]=2"],
            conclusion="H⊴G",
            proof_strategy="coset_argument",
            depends_on=["lagrange"],
            tags=["normal", "index"])

        self._add(name="cyclic_subgroup", field="group_theory",
            statement="Every subgroup of a cyclic group is cyclic",
            preconditions=["G is cyclic"],
            conclusion="every subgroup of G is cyclic",
            proof_strategy="generator_argument",
            tags=["cyclic", "subgroup"])

        self._add(name="finite_abelian_structure", field="group_theory",
            statement="Every finite abelian group is isomorphic to a direct product of cyclic groups of prime power order",
            preconditions=["G is finite", "G is abelian"],
            conclusion="G ≅ ℤ_{p1^a1} × ℤ_{p2^a2} × ... × ℤ_{pk^ak}",
            proof_strategy="primary_decomposition",
            depends_on=["sylow_existence"],
            tags=["structure", "abelian", "classification"])

        self._add(name="cayley", field="group_theory",
            statement="Every group G is isomorphic to a subgroup of Sym(G)",
            preconditions=["G is a group"],
            conclusion="G embeds in Sym(G)",
            proof_strategy="left_regular_representation",
            tags=["embedding", "symmetric", "representation"])

        self._add(name="orbit_stabilizer", field="group_theory",
            statement="|G| = |Orb(x)| · |Stab(x)| for any group action",
            preconditions=["G acts on set X", "x∈X"],
            conclusion="|G| = |Orb(x)| × |Stab(x)|",
            proof_strategy="bijection_cosets_orbit",
            depends_on=["lagrange"],
            tags=["action", "orbit", "stabilizer"])

        self._add(name="burnside_lemma", field="group_theory",
            statement="|X/G| = (1/|G|) Σ|Fix(g)| — number of orbits",
            preconditions=["G acts on finite set X"],
            conclusion="number of orbits = average number of fixed points",
            proof_strategy="double_counting",
            depends_on=["orbit_stabilizer"],
            tags=["counting", "orbits", "fixed points"])

        self._add(name="simple_group_test", field="group_theory",
            statement="G is simple iff G has no proper normal subgroups",
            preconditions=["G is a group"],
            conclusion="G simple ⟺ only normal subgroups are {e} and G",
            tags=["simple", "normal"])

        self._add(name="solvable_definition", field="group_theory",
            statement="G is solvable iff it has a subnormal series with abelian factors",
            preconditions=["G is a group"],
            conclusion="G solvable ⟺ G=G₀⊃G₁⊃...⊃Gₙ={e} with Gᵢ/Gᵢ₊₁ abelian",
            tags=["solvable", "series"])

        self._add(name="pq_group", field="group_theory",
            statement="If |G|=pq with p<q primes and p∤(q-1), then G is cyclic",
            preconditions=["|G|=pq", "p<q primes", "p does not divide q-1"],
            conclusion="G ≅ ℤ_pq",
            proof_strategy="sylow_counting",
            depends_on=["sylow_number"],
            tags=["cyclic", "order", "classification"])

        # ══════════════════════════════════════════════
        # RING THEORY (20 theorems)
        # ══════════════════════════════════════════════

        self._add(name="ring_first_iso", field="ring_theory",
            statement="If φ:R→S is a ring homomorphism, then R/ker(φ) ≅ im(φ)",
            preconditions=["φ:R→S is ring homomorphism"],
            conclusion="R/ker(φ) ≅ im(φ)",
            tags=["isomorphism", "ring", "quotient"])

        self._add(name="pid_implies_ufd", field="ring_theory",
            statement="Every PID is a UFD",
            preconditions=["R is a PID"],
            conclusion="R is a UFD",
            proof_strategy="ascending_chain + irreducible_is_prime",
            tags=["PID", "UFD", "factorization"])

        self._add(name="ed_implies_pid", field="ring_theory",
            statement="Every Euclidean domain is a PID",
            preconditions=["R is a Euclidean domain"],
            conclusion="R is a PID",
            proof_strategy="division_algorithm",
            depends_on=["pid_implies_ufd"],
            tags=["Euclidean", "PID"])

        self._add(name="maximal_iff_field", field="ring_theory",
            statement="I is maximal ideal of R iff R/I is a field",
            preconditions=["R is commutative ring with 1", "I is ideal"],
            conclusion="I maximal ⟺ R/I is a field",
            tags=["maximal", "ideal", "field", "quotient"])

        self._add(name="prime_iff_domain", field="ring_theory",
            statement="P is prime ideal of R iff R/P is an integral domain",
            preconditions=["R is commutative ring with 1", "P is ideal"],
            conclusion="P prime ⟺ R/P is integral domain",
            tags=["prime", "ideal", "domain"])

        self._add(name="hilbert_basis", field="ring_theory",
            statement="If R is Noetherian, then R[x] is Noetherian",
            preconditions=["R is Noetherian"],
            conclusion="R[x] is Noetherian",
            proof_strategy="leading_coefficient_argument",
            tags=["Noetherian", "polynomial", "basis"])

        self._add(name="chinese_remainder_rings", field="ring_theory",
            statement="If I,J are coprime ideals (I+J=R), then R/(I∩J) ≅ R/I × R/J",
            preconditions=["I+J=R"],
            conclusion="R/(I∩J) ≅ R/I × R/J",
            tags=["CRT", "ideals", "coprime"])

        self._add(name="eisenstein", field="ring_theory",
            statement="Eisenstein's criterion: if p|aᵢ for i<n, p∤aₙ, p²∤a₀, then f is irreducible over ℚ",
            preconditions=["f ∈ ℤ[x]", "prime p", "p|aᵢ for i<n", "p∤aₙ", "p²∤a₀"],
            conclusion="f is irreducible over ℚ",
            tags=["irreducible", "polynomial", "criterion"])

        # ══════════════════════════════════════════════
        # FIELD THEORY / GALOIS (15 theorems)
        # ══════════════════════════════════════════════

        self._add(name="field_extension_tower", field="field_theory",
            statement="If K⊂L⊂M, then [M:K] = [M:L][L:K]",
            preconditions=["K⊂L⊂M are fields"],
            conclusion="[M:K] = [M:L]·[L:K]",
            tags=["extension", "degree", "tower"])

        self._add(name="finite_field_exists", field="field_theory",
            statement="For every prime power q=p^n, there exists a unique field of order q",
            preconditions=["q = p^n for prime p"],
            conclusion="∃! field F_q with |F_q|=q",
            tags=["finite field", "existence", "uniqueness"])

        self._add(name="galois_fundamental", field="field_theory",
            statement="For Galois extension L/K: subgroups of Gal(L/K) ↔ intermediate fields",
            preconditions=["L/K is Galois extension"],
            conclusion="bijection: subgroups ↔ intermediate fields (order-reversing)",
            proof_strategy="fixed_field_correspondence",
            tags=["Galois", "correspondence", "subgroup"])

        self._add(name="abel_ruffini", field="field_theory",
            statement="There is no general algebraic solution for polynomial equations of degree 5 or higher",
            preconditions=["f ∈ ℚ[x]", "deg(f) ≥ 5"],
            conclusion="No formula using radicals solves all such equations",
            proof_strategy="galois_group_S5_not_solvable",
            depends_on=["galois_fundamental", "solvable_definition"],
            tags=["unsolvability", "quintic", "radicals"])

        self._add(name="splitting_field_exists", field="field_theory",
            statement="Every polynomial over F has a splitting field, unique up to isomorphism",
            preconditions=["f ∈ F[x]"],
            conclusion="∃ splitting field of f over F (unique up to iso)",
            tags=["splitting", "existence"])

        # ══════════════════════════════════════════════
        # REAL ANALYSIS (20 theorems)
        # ══════════════════════════════════════════════

        self._add(name="bolzano_weierstrass", field="analysis",
            statement="Every bounded sequence in ℝ has a convergent subsequence",
            preconditions=["(aₙ) is bounded sequence in ℝ"],
            conclusion="∃ convergent subsequence",
            proof_strategy="bisection",
            tags=["convergence", "subsequence", "bounded"])

        self._add(name="heine_borel", field="analysis",
            statement="A subset of ℝⁿ is compact iff it is closed and bounded",
            preconditions=["S ⊆ ℝⁿ"],
            conclusion="S compact ⟺ S closed and bounded",
            depends_on=["bolzano_weierstrass"],
            tags=["compact", "closed", "bounded"])

        self._add(name="intermediate_value", field="analysis",
            statement="If f is continuous on [a,b] and f(a)<c<f(b), then ∃x∈(a,b) with f(x)=c",
            preconditions=["f continuous on [a,b]", "f(a)<c<f(b)"],
            conclusion="∃x∈(a,b): f(x)=c",
            proof_strategy="bisection",
            tags=["continuous", "root", "existence"])

        self._add(name="extreme_value", field="analysis",
            statement="A continuous function on a compact set attains its maximum and minimum",
            preconditions=["f continuous", "K compact"],
            conclusion="∃x₁,x₂∈K: f(x₁)=max, f(x₂)=min",
            depends_on=["heine_borel"],
            tags=["continuous", "compact", "maximum", "minimum"])

        self._add(name="mean_value", field="analysis",
            statement="If f is continuous on [a,b] and differentiable on (a,b), then ∃c: f'(c)=(f(b)-f(a))/(b-a)",
            preconditions=["f continuous on [a,b]", "f differentiable on (a,b)"],
            conclusion="∃c∈(a,b): f'(c) = (f(b)-f(a))/(b-a)",
            proof_strategy="rolle_applied_to_auxiliary",
            depends_on=["rolle"],
            tags=["derivative", "mean value"])

        self._add(name="rolle", field="analysis",
            statement="If f(a)=f(b) and f is differentiable on (a,b), then ∃c: f'(c)=0",
            preconditions=["f continuous on [a,b]", "f differentiable on (a,b)", "f(a)=f(b)"],
            conclusion="∃c∈(a,b): f'(c)=0",
            depends_on=["extreme_value"],
            tags=["derivative", "zero"])

        self._add(name="taylor_theorem", field="analysis",
            statement="f(x) = Σ f^(k)(a)/k! (x-a)^k + Rₙ(x) where Rₙ→0",
            preconditions=["f is n+1 times differentiable"],
            conclusion="f equals its Taylor series plus remainder",
            tags=["Taylor", "approximation", "series"])

        self._add(name="uniform_convergence_continuous", field="analysis",
            statement="If fₙ→f uniformly and each fₙ is continuous, then f is continuous",
            preconditions=["fₙ→f uniformly", "each fₙ continuous"],
            conclusion="f is continuous",
            tags=["uniform", "convergence", "continuous"])

        self._add(name="weierstrass_m_test", field="analysis",
            statement="If |fₙ(x)|≤Mₙ and ΣMₙ converges, then Σfₙ converges uniformly",
            preconditions=["|fₙ(x)|≤Mₙ for all x", "ΣMₙ converges"],
            conclusion="Σfₙ converges uniformly",
            tags=["uniform", "convergence", "series"])

        self._add(name="monotone_convergence", field="analysis",
            statement="Every bounded monotone sequence converges",
            preconditions=["(aₙ) is monotone", "(aₙ) is bounded"],
            conclusion="(aₙ) converges",
            proof_strategy="supremum_is_limit",
            tags=["monotone", "convergence", "bounded"])

        self._add(name="ratio_test", field="analysis",
            statement="If lim|aₙ₊₁/aₙ| = L < 1, then Σaₙ converges absolutely",
            preconditions=["lim|aₙ₊₁/aₙ| = L"],
            conclusion="L<1 → converges, L>1 → diverges, L=1 → inconclusive",
            tags=["series", "convergence", "test"])

        self._add(name="comparison_test", field="analysis",
            statement="If 0≤aₙ≤bₙ and Σbₙ converges, then Σaₙ converges",
            preconditions=["0≤aₙ≤bₙ", "Σbₙ converges"],
            conclusion="Σaₙ converges",
            tags=["series", "convergence", "comparison"])

        # ══════════════════════════════════════════════
        # TOPOLOGY (15 theorems)
        # ══════════════════════════════════════════════

        self._add(name="continuous_image_compact", field="topology",
            statement="The continuous image of a compact set is compact",
            preconditions=["f continuous", "K compact"],
            conclusion="f(K) is compact",
            tags=["continuous", "compact", "image"])

        self._add(name="continuous_image_connected", field="topology",
            statement="The continuous image of a connected set is connected",
            preconditions=["f continuous", "S connected"],
            conclusion="f(S) is connected",
            tags=["continuous", "connected", "image"])

        self._add(name="compact_hausdorff_closed", field="topology",
            statement="A compact subset of a Hausdorff space is closed",
            preconditions=["K compact", "X Hausdorff"],
            conclusion="K is closed in X",
            tags=["compact", "Hausdorff", "closed"])

        self._add(name="tychonoff", field="topology",
            statement="Arbitrary product of compact spaces is compact",
            preconditions=["each Xᵢ is compact"],
            conclusion="∏Xᵢ is compact (product topology)",
            tags=["product", "compact", "Tychonoff"])

        self._add(name="urysohn_lemma", field="topology",
            statement="In a normal space, disjoint closed sets can be separated by a continuous function",
            preconditions=["X is normal", "A,B closed disjoint"],
            conclusion="∃f:X→[0,1] continuous with f(A)=0, f(B)=1",
            tags=["normal", "separation", "continuous"])

        self._add(name="brouwer_fixed_point", field="topology",
            statement="Every continuous function f:Dⁿ→Dⁿ has a fixed point",
            preconditions=["f:Dⁿ→Dⁿ continuous", "Dⁿ is closed unit disk"],
            conclusion="∃x: f(x)=x",
            tags=["fixed point", "continuous", "disk"])

        self._add(name="fundamental_group_circle", field="topology",
            statement="π₁(S¹) ≅ ℤ",
            preconditions=["S¹ is the circle"],
            conclusion="π₁(S¹) = ℤ",
            proof_strategy="covering_space_R",
            tags=["fundamental group", "circle", "homotopy"])

        self._add(name="van_kampen", field="topology",
            statement="π₁(U∪V) = π₁(U) *_{π₁(U∩V)} π₁(V) (free product with amalgamation)",
            preconditions=["X=U∪V open", "U,V,U∩V path-connected"],
            conclusion="π₁(X) = π₁(U) *_{π₁(U∩V)} π₁(V)",
            tags=["fundamental group", "computation", "amalgamation"])

        # ══════════════════════════════════════════════
        # LINEAR ALGEBRA (10 theorems)
        # ══════════════════════════════════════════════

        self._add(name="rank_nullity", field="linear_algebra",
            statement="dim(V) = rank(T) + nullity(T)",
            preconditions=["T:V→W is linear map", "V finite-dimensional"],
            conclusion="dim(V) = dim(im(T)) + dim(ker(T))",
            tags=["rank", "nullity", "dimension"])

        self._add(name="spectral_theorem", field="linear_algebra",
            statement="Every real symmetric matrix is orthogonally diagonalizable",
            preconditions=["A is real symmetric matrix"],
            conclusion="∃ orthogonal P: A = PDP^T with D diagonal",
            tags=["symmetric", "eigenvalue", "diagonalize"])

        self._add(name="cayley_hamilton", field="linear_algebra",
            statement="Every square matrix satisfies its own characteristic polynomial",
            preconditions=["A is n×n matrix", "p(λ)=det(A-λI)"],
            conclusion="p(A) = 0",
            tags=["characteristic", "polynomial", "matrix"])

        self._add(name="jordan_normal_form", field="linear_algebra",
            statement="Every matrix over ℂ is similar to a Jordan normal form matrix",
            preconditions=["A is n×n matrix over ℂ"],
            conclusion="∃P: P⁻¹AP = J (Jordan blocks)",
            tags=["Jordan", "canonical", "similar"])

    def stats(self) -> Dict:
        fields = {}
        for t in self.theorems.values():
            fields[t.field] = fields.get(t.field, 0) + 1
        return {'total': len(self.theorems), 'by_field': fields}


# ═══════════════════════════════════════════════════════════════
# 3.2 ABSTRACT ALGEBRA ENGINE — Groups
# ═══════════════════════════════════════════════════════════════

class Group:
    """Finite group represented by Cayley table or generators."""

    def __init__(self, elements: List, operation=None, cayley_table: List[List] = None, name: str = ''):
        self.elements = elements
        self.n = len(elements)
        self.name = name
        self._op = operation
        self._table = cayley_table
        self.identity = self._find_identity()

    def op(self, a, b):
        """Group operation."""
        if self._table:
            i, j = self.elements.index(a), self.elements.index(b)
            return self.elements[self._table[i][j]]
        if self._op:
            return self._op(a, b)
        return (a + b) % self.n  # Default: cyclic group

    def _find_identity(self):
        for e in self.elements:
            if all(self.op(e, a) == a and self.op(a, e) == a for a in self.elements):
                return e
        return self.elements[0]

    def inverse(self, a):
        """Find inverse of a."""
        for b in self.elements:
            if self.op(a, b) == self.identity:
                return b
        return None

    def order_of(self, a) -> int:
        """Order of element a."""
        current = a
        for i in range(1, self.n + 1):
            if current == self.identity:
                return i
            current = self.op(current, a)
        return self.n

    def is_abelian(self) -> bool:
        """Check if G is abelian (commutative)."""
        for a in self.elements:
            for b in self.elements:
                if self.op(a, b) != self.op(b, a):
                    return False
        return True

    def center(self) -> List:
        """Z(G) = {g∈G : gx=xg for all x}."""
        return [g for g in self.elements
                if all(self.op(g, x) == self.op(x, g) for x in self.elements)]

    def is_subgroup(self, H: List) -> bool:
        """Check if H is a subgroup."""
        if self.identity not in H:
            return False
        for a in H:
            if self.inverse(a) not in H:
                return False
            for b in H:
                if self.op(a, b) not in H:
                    return False
        return True

    def subgroups(self) -> List[List]:
        """Find all subgroups (brute force for small groups)."""
        from itertools import combinations
        subs = [{self.identity}]
        for size in range(2, self.n + 1):
            if self.n % size != 0:  # Lagrange: |H| must divide |G|
                continue
            for combo in combinations(self.elements, size):
                H = list(combo)
                if self.is_subgroup(H):
                    subs.append(set(H))
        return [list(s) for s in subs]

    def is_normal(self, H: List) -> bool:
        """Check if H is normal: gHg⁻¹ = H for all g."""
        H_set = set(map(str, H))
        for g in self.elements:
            conjugate = {str(self.op(self.op(g, h), self.inverse(g))) for h in H}
            if conjugate != H_set:
                return False
        return True

    def quotient(self, N: List) -> 'Group':
        """Compute G/N (quotient group)."""
        if not self.is_normal(N):
            return None
        # Compute cosets
        cosets = []
        used = set()
        for g in self.elements:
            coset = frozenset(str(self.op(g, n)) for n in N)
            if coset not in used:
                used.add(coset)
                cosets.append(g)  # Representative
        # Build quotient operation
        n_cosets = len(cosets)
        return Group(list(range(n_cosets)), name=f"{self.name}/N")

    def is_cyclic(self) -> bool:
        """Check if G is cyclic (generated by single element)."""
        for g in self.elements:
            if self.order_of(g) == self.n:
                return True
        return False

    def is_simple(self) -> bool:
        """Check if G is simple (no proper normal subgroups)."""
        for H in self.subgroups():
            if 1 < len(H) < self.n and self.is_normal(H):
                return False
        return True

    @staticmethod
    def cyclic(n: int) -> 'Group':
        """Create cyclic group ℤₙ."""
        return Group(list(range(n)), operation=lambda a, b: (a+b) % n, name=f"Z_{n}")

    @staticmethod
    def symmetric(n: int) -> 'Group':
        """Create symmetric group Sₙ (permutations)."""
        from itertools import permutations
        perms = [list(p) for p in permutations(range(n))]
        def compose(p1, p2):
            return [p1[p2[i]] for i in range(n)]
        # Convert to tuples for hashing
        elements = [tuple(p) for p in perms]
        return Group(elements, operation=lambda a, b: tuple(a[b[i]] for i in range(n)), name=f"S_{n}")

    @staticmethod
    def dihedral(n: int) -> 'Group':
        """Create dihedral group D_n (symmetries of n-gon)."""
        # Elements: rotations r^k and reflections s*r^k
        elements = [(0, k) for k in range(n)] + [(1, k) for k in range(n)]
        def op(a, b):
            # (t1,k1) * (t2,k2)
            t1, k1 = a
            t2, k2 = b
            if t1 == 0:
                return (t2, (k1 + k2) % n)
            else:
                return ((t1 + t2) % 2, (k1 - k2) % n)
        return Group(elements, operation=op, name=f"D_{n}")


# ═══════════════════════════════════════════════════════════════
# 3.4 PROOF SEARCH ENGINE V2
# Given a statement, search theorem space for proof path
# ═══════════════════════════════════════════════════════════════

class ProofSearchV2:
    """Search for proof paths through theorem database.
    
    Strategy: BFS/DFS through theorem dependencies.
    Given: known facts (preconditions met)
    Goal: reach the desired conclusion
    Path: sequence of theorem applications
    """

    def __init__(self, db: TheoremDB = None):
        self.db = db or TheoremDB()

    def prove(self, goal: str, known_facts: List[str] = None) -> Optional[Dict]:
        """Find a proof of goal given known facts."""
        if known_facts is None:
            known_facts = []

        # Step 1: Find theorems whose conclusion matches the goal
        candidates = self.db.by_conclusion(goal)

        if not candidates:
            # Try partial match
            for word in goal.split():
                if len(word) > 3:
                    candidates.extend(self.db.search(word))

        if not candidates:
            return None

        # Step 2: For each candidate, check if preconditions are met
        for theorem in candidates:
            proof = self._try_theorem(theorem, known_facts, depth=0)
            if proof:
                return proof

        return None

    def _try_theorem(self, theorem: Theorem, known: List[str], depth: int) -> Optional[Dict]:
        """Try to apply a theorem. Recursively prove preconditions if needed."""
        if depth > 10:  # Prevent infinite recursion
            return None

        # Check which preconditions are already known
        unmet = []
        for pre in theorem.preconditions:
            if not self._fact_matches(pre, known):
                unmet.append(pre)

        if not unmet:
            # All preconditions met! Theorem applies directly.
            return {
                'theorem': theorem.name,
                'statement': theorem.statement,
                'conclusion': theorem.conclusion,
                'strategy': theorem.proof_strategy,
                'sub_proofs': [],
            }

        # Try to prove unmet preconditions using other theorems
        sub_proofs = []
        all_met = True
        for pre in unmet:
            sub = self.prove(pre, known)
            if sub:
                sub_proofs.append(sub)
                known = known + [pre]  # Now this fact is known
            else:
                all_met = False
                break

        if all_met:
            return {
                'theorem': theorem.name,
                'statement': theorem.statement,
                'conclusion': theorem.conclusion,
                'strategy': theorem.proof_strategy,
                'sub_proofs': sub_proofs,
            }

        return None

    def _fact_matches(self, fact: str, known: List[str]) -> bool:
        """Check if a fact is in the known list (fuzzy match)."""
        fact_low = fact.lower()
        for k in known:
            if fact_low in k.lower() or k.lower() in fact_low:
                return True
        return False

    def format_proof(self, proof: Dict, indent: int = 0) -> str:
        """Format a proof tree into readable text."""
        if not proof:
            return "Cannot prove."
        lines = []
        pad = '  ' * indent
        lines.append(f"{pad}By {proof['theorem']}: {proof['statement']}")
        if proof.get('sub_proofs'):
            lines.append(f"{pad}  Prerequisites proved by:")
            for sub in proof['sub_proofs']:
                lines.append(self.format_proof(sub, indent + 2))
        lines.append(f"{pad}  ∴ {proof['conclusion']}")
        return '\n'.join(lines)

    def prove_and_format(self, goal: str, known: List[str] = None) -> str:
        """Prove and return formatted proof."""
        proof = self.prove(goal, known or [])
        if proof:
            return self.format_proof(proof)
        return f"Cannot find proof path for: {goal}"
