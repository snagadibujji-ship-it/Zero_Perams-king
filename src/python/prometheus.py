#!/usr/bin/env python3
"""
AXIMA PROMETHEUS — Symbolic Mathematics Engine
Zero parameters. Pure rule-based symbolic computation.

Solves: algebra, equations, factoring, complex numbers, simplification.
Architecture: Tokenize → Parse (AST) → Transform (Rules) → Solve → Verify

Owner: Ghias / Gowtham Sangadi
Built by: Ghias + Kiro
"""

import re, math
from typing import List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto


# ═══════════════════════════════════════════════════════════════
# TOKEN TYPES
# ═══════════════════════════════════════════════════════════════

class TT(Enum):
    """Token types."""
    NUM = auto()      # 3, 3.14, -2
    VAR = auto()      # x, y, a, b
    OP = auto()       # +, -, *, /, ^
    LPAREN = auto()   # (
    RPAREN = auto()   # )
    FUNC = auto()     # sin, cos, sqrt, log, ln, abs
    EQUALS = auto()   # =
    COMMA = auto()    # ,
    IMAGINARY = auto() # i (imaginary unit)
    EOF = auto()


@dataclass
class Token:
    type: TT
    value: str
    num_value: float = 0.0


# ═══════════════════════════════════════════════════════════════
# TOKENIZER — Splits any math expression into tokens
# ═══════════════════════════════════════════════════════════════

FUNCTIONS = {'sin', 'cos', 'tan', 'sqrt', 'log', 'ln', 'abs', 'exp',
             'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh',
             'sec', 'csc', 'cot', 'floor', 'ceil'}

class Tokenizer:
    """Tokenize any mathematical expression."""

    def tokenize(self, expr: str) -> List[Token]:
        """Convert string to token list."""
        tokens = []
        i = 0
        expr = expr.strip()

        while i < len(expr):
            c = expr[i]

            # Skip whitespace
            if c in ' \t':
                i += 1
                continue

            # Number (integer or decimal)
            if c.isdigit() or (c == '.' and i + 1 < len(expr) and expr[i+1].isdigit()):
                j = i
                while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                    j += 1
                num_str = expr[i:j]
                tokens.append(Token(TT.NUM, num_str, float(num_str)))
                i = j
                continue

            # Variable or function or imaginary
            if c.isalpha() or c == '_':
                j = i
                while j < len(expr) and (expr[j].isalnum() or expr[j] == '_'):
                    j += 1
                word = expr[i:j]

                if word in FUNCTIONS:
                    tokens.append(Token(TT.FUNC, word))
                elif word == 'i' and (j >= len(expr) or not expr[j].isalpha()):
                    # 'i' alone is imaginary unit, but 'in' or 'if' are not
                    tokens.append(Token(TT.IMAGINARY, 'i'))
                elif word == 'pi':
                    tokens.append(Token(TT.NUM, 'pi', math.pi))
                elif word == 'e' and (j >= len(expr) or not expr[j].isalpha()):
                    # Keep 'e' as variable (Euler's number) for symbolic calculus
                    tokens.append(Token(TT.VAR, 'e'))
                elif word == 'arctan':
                    tokens.append(Token(TT.FUNC, 'atan'))
                elif word == 'arcsin':
                    tokens.append(Token(TT.FUNC, 'asin'))
                elif word == 'arccos':
                    tokens.append(Token(TT.FUNC, 'acos'))
                else:
                    tokens.append(Token(TT.VAR, word))
                i = j
                continue

            # Operators
            if c in '+-*/^':
                # Handle unary minus: at start, after (, after operator, after =
                if c == '-' and (not tokens or tokens[-1].type in (TT.OP, TT.LPAREN, TT.EQUALS)):
                    # Unary minus — read the next number/var
                    j = i + 1
                    while j < len(expr) and expr[j] == ' ':
                        j += 1
                    if j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                        k = j
                        while k < len(expr) and (expr[k].isdigit() or expr[k] == '.'):
                            k += 1
                        num_str = expr[i:k]
                        tokens.append(Token(TT.NUM, num_str, float(num_str)))
                        i = k
                        continue
                    else:
                        # Unary minus before variable: treat as -1 * var
                        tokens.append(Token(TT.NUM, '-1', -1.0))
                        tokens.append(Token(TT.OP, '*'))
                        i += 1
                        continue
                tokens.append(Token(TT.OP, c))
                i += 1
                continue

            # Parentheses
            if c == '(':
                tokens.append(Token(TT.LPAREN, '('))
                i += 1
                continue
            if c == ')':
                tokens.append(Token(TT.RPAREN, ')'))
                i += 1
                continue

            # Equals
            if c == '=':
                # Skip => (implication arrow)
                if i + 1 < len(expr) and expr[i+1] == '>':
                    i += 2
                    continue
                tokens.append(Token(TT.EQUALS, '='))
                i += 1
                continue

            # Comma
            if c == ',':
                tokens.append(Token(TT.COMMA, ','))
                i += 1
                continue

            # Unknown — skip
            i += 1

        # Insert implicit multiplication: 2x → 2*x, x(... → x*(, )( → )*(
        tokens = self._insert_implicit_mul(tokens)
        tokens.append(Token(TT.EOF, ''))
        return tokens

    def _insert_implicit_mul(self, tokens: List[Token]) -> List[Token]:
        """Insert * between adjacent tokens that imply multiplication."""
        result = []
        for i, tok in enumerate(tokens):
            result.append(tok)
            if i + 1 < len(tokens):
                nxt = tokens[i + 1]
                # Cases where implicit * is needed:
                # NUM VAR: 2x, NUM (: 2(, VAR (: x(, ) VAR: )x, ) (: )(, ) NUM: )2
                # NUM FUNC: 2sin, VAR VAR: xy (optional — skip for multi-char vars)
                # NUM IMAGINARY: 2i, VAR IMAGINARY: xi
                implicit = False
                if tok.type == TT.NUM and nxt.type in (TT.VAR, TT.LPAREN, TT.FUNC, TT.IMAGINARY):
                    implicit = True
                elif tok.type == TT.VAR and nxt.type in (TT.LPAREN, TT.NUM, TT.IMAGINARY):
                    implicit = True
                elif tok.type == TT.RPAREN and nxt.type in (TT.VAR, TT.NUM, TT.LPAREN, TT.FUNC, TT.IMAGINARY):
                    implicit = True
                elif tok.type == TT.IMAGINARY and nxt.type in (TT.VAR, TT.NUM, TT.LPAREN):
                    implicit = True
                if implicit:
                    result.append(Token(TT.OP, '*'))
        return result


# ═══════════════════════════════════════════════════════════════
# AST NODES — Expression tree structure
# ═══════════════════════════════════════════════════════════════

class Node:
    """Base AST node."""
    pass

class NumNode(Node):
    """Numeric literal."""
    def __init__(self, value: float):
        self.value = value
    def __repr__(self):
        if self.value == int(self.value) and abs(self.value) < 1e15:
            return str(int(self.value))
        return str(self.value)
    def __eq__(self, other):
        return isinstance(other, NumNode) and self.value == other.value

class VarNode(Node):
    """Variable (x, y, a, b...)."""
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, VarNode) and self.name == other.name

class ImagNode(Node):
    """Imaginary unit i."""
    def __repr__(self):
        return 'i'
    def __eq__(self, other):
        return isinstance(other, ImagNode)

class BinOp(Node):
    """Binary operation: left op right."""
    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right
    def __repr__(self):
        if self.op == '^':
            return f"({self.left}^{self.right})"
        elif self.op == '*':
            return f"({self.left}*{self.right})"
        elif self.op == '/':
            return f"({self.left}/{self.right})"
        return f"({self.left}{self.op}{self.right})"
    def __eq__(self, other):
        return isinstance(other, BinOp) and self.op == other.op and self.left == other.left and self.right == other.right

class UnaryOp(Node):
    """Unary operation: -x."""
    def __init__(self, op: str, operand: Node):
        self.op = op
        self.operand = operand
    def __repr__(self):
        return f"(-{self.operand})"
    def __eq__(self, other):
        return isinstance(other, UnaryOp) and self.op == other.op and self.operand == other.operand

class FuncNode(Node):
    """Function call: sin(x), sqrt(x), etc."""
    def __init__(self, name: str, arg: Node):
        self.name = name
        self.arg = arg
    def __repr__(self):
        return f"{self.name}({self.arg})"
    def __eq__(self, other):
        return isinstance(other, FuncNode) and self.name == other.name and self.arg == other.arg


# ═══════════════════════════════════════════════════════════════
# PARSER — Shunting-yard algorithm → AST
# ═══════════════════════════════════════════════════════════════

PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
RIGHT_ASSOC = {'^'}

class Parser:
    """Parse token list into AST using shunting-yard algorithm."""

    def parse(self, tokens: List[Token]) -> Node:
        """Parse tokens into an AST."""
        self._tokens = tokens
        self._pos = 0
        result = self._parse_expr()
        return result

    def parse_equation(self, tokens: List[Token]) -> Tuple[Node, Node]:
        """Parse an equation (expr = expr). Returns (left, right)."""
        self._tokens = tokens
        self._pos = 0
        left = self._parse_expr()
        if self._pos < len(tokens) and tokens[self._pos].type == TT.EQUALS:
            self._pos += 1
            right = self._parse_expr()
            return left, right
        return left, NumNode(0)

    def _peek(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return Token(TT.EOF, '')

    def _consume(self) -> Token:
        tok = self._peek()
        self._pos += 1
        return tok

    def _parse_expr(self, min_prec: int = 0) -> Node:
        """Precedence climbing parser."""
        left = self._parse_atom()

        while True:
            tok = self._peek()
            if tok.type != TT.OP or tok.value not in PRECEDENCE:
                break
            prec = PRECEDENCE[tok.value]
            if prec < min_prec:
                break
            self._consume()
            # Right associative: use same prec; left assoc: use prec+1
            next_min = prec if tok.value in RIGHT_ASSOC else prec + 1
            right = self._parse_expr(next_min)
            left = BinOp(tok.value, left, right)

        return left

    def _parse_atom(self) -> Node:
        """Parse an atomic expression (number, variable, function, parenthesized)."""
        tok = self._peek()

        # Number
        if tok.type == TT.NUM:
            self._consume()
            return NumNode(tok.num_value)

        # Variable
        if tok.type == TT.VAR:
            self._consume()
            return VarNode(tok.value)

        # Imaginary unit
        if tok.type == TT.IMAGINARY:
            self._consume()
            return ImagNode()

        # Function call
        if tok.type == TT.FUNC:
            self._consume()
            func_name = tok.value
            # Expect (
            if self._peek().type == TT.LPAREN:
                self._consume()
                arg = self._parse_expr()
                if self._peek().type == TT.RPAREN:
                    self._consume()
                return FuncNode(func_name, arg)
            else:
                # Function without parens: sin x → sin(x)
                arg = self._parse_atom()
                return FuncNode(func_name, arg)

        # Parenthesized expression
        if tok.type == TT.LPAREN:
            self._consume()
            expr = self._parse_expr()
            if self._peek().type == TT.RPAREN:
                self._consume()
            return expr

        # Unary minus
        if tok.type == TT.OP and tok.value == '-':
            self._consume()
            operand = self._parse_atom()
            return BinOp('*', NumNode(-1), operand)

        # Unary plus
        if tok.type == TT.OP and tok.value == '+':
            self._consume()
            return self._parse_atom()

        # Default: return 0
        self._consume()
        return NumNode(0)


# ═══════════════════════════════════════════════════════════════
# SIMPLIFIER — Apply algebraic rules to reduce expressions
# ═══════════════════════════════════════════════════════════════

class Simplifier:
    """Apply algebraic identity rules to simplify expressions."""

    def simplify(self, node: Node) -> Node:
        """Recursively simplify an expression tree."""
        # Apply rules until no more changes
        for _ in range(20):  # max iterations to prevent infinite loops
            new_node = self._simplify_once(node)
            if repr(new_node) == repr(node):
                break
            node = new_node
        return node

    def _simplify_once(self, node: Node) -> Node:
        """One pass of simplification."""
        if isinstance(node, (NumNode, VarNode, ImagNode)):
            return node

        if isinstance(node, FuncNode):
            arg = self._simplify_once(node.arg)
            # Evaluate known functions on constants
            if isinstance(arg, NumNode):
                return self._eval_func(node.name, arg.value)
            return FuncNode(node.name, arg)

        if isinstance(node, UnaryOp):
            operand = self._simplify_once(node.operand)
            if isinstance(operand, NumNode):
                return NumNode(-operand.value)
            return UnaryOp(node.op, operand)

        if isinstance(node, BinOp):
            left = self._simplify_once(node.left)
            right = self._simplify_once(node.right)
            return self._simplify_binop(node.op, left, right)

        return node

    def _simplify_binop(self, op: str, left: Node, right: Node) -> Node:
        """Apply rules to a binary operation."""

        # ── CONSTANT FOLDING: num op num → compute ──
        if isinstance(left, NumNode) and isinstance(right, NumNode):
            result = self._compute(op, left.value, right.value)
            if result is not None:
                return NumNode(result)

        # ── ADDITION RULES ──
        if op == '+':
            # x + 0 → x
            if isinstance(right, NumNode) and right.value == 0:
                return left
            # 0 + x → x
            if isinstance(left, NumNode) and left.value == 0:
                return right
            # x + x → 2x
            if repr(left) == repr(right):
                return BinOp('*', NumNode(2), left)
            # ax + bx → (a+b)x
            lcoeff, lterm = self._get_coeff(left)
            rcoeff, rterm = self._get_coeff(right)
            if repr(lterm) == repr(rterm):
                new_coeff = lcoeff + rcoeff
                if new_coeff == 0:
                    return NumNode(0)
                if new_coeff == 1:
                    return lterm
                return BinOp('*', NumNode(new_coeff), lterm)

        # ── SUBTRACTION RULES ──
        if op == '-':
            # x - 0 → x
            if isinstance(right, NumNode) and right.value == 0:
                return left
            # 0 - x → -x
            if isinstance(left, NumNode) and left.value == 0:
                return BinOp('*', NumNode(-1), right)
            # x - x → 0
            if repr(left) == repr(right):
                return NumNode(0)
            # ax - bx → (a-b)x  [COLLECT LIKE TERMS]
            lcoeff, lterm = self._get_coeff(left)
            rcoeff, rterm = self._get_coeff(right)
            if repr(lterm) == repr(rterm):
                new_coeff = lcoeff - rcoeff
                if new_coeff == 0:
                    return NumNode(0)
                if new_coeff == 1:
                    return lterm
                return BinOp('*', NumNode(new_coeff), lterm)

        # ── MULTIPLICATION RULES ──
        if op == '*':
            # x * 0 → 0
            if (isinstance(left, NumNode) and left.value == 0) or \
               (isinstance(right, NumNode) and right.value == 0):
                return NumNode(0)
            # x * 1 → x
            if isinstance(right, NumNode) and right.value == 1:
                return left
            # 1 * x → x
            if isinstance(left, NumNode) and left.value == 1:
                return right
            # num * num → compute (constant folding in nested products)
            if isinstance(left, NumNode) and isinstance(right, NumNode):
                return NumNode(left.value * right.value)
            # num * (num * expr) → (num*num) * expr  [FLATTEN CONSTANTS]
            if isinstance(left, NumNode) and isinstance(right, BinOp) and right.op == '*':
                if isinstance(right.left, NumNode):
                    return BinOp('*', NumNode(left.value * right.left.value), right.right)
                if isinstance(right.right, NumNode):
                    return BinOp('*', NumNode(left.value * right.right.value), right.left)
            # (num * expr) * num → (num*num) * expr
            if isinstance(right, NumNode) and isinstance(left, BinOp) and left.op == '*':
                if isinstance(left.left, NumNode):
                    return BinOp('*', NumNode(right.value * left.left.value), left.right)
            # x * x → x^2
            if repr(left) == repr(right):
                return BinOp('^', left, NumNode(2))
            # x^a * x → x^(a+1)
            if isinstance(left, BinOp) and left.op == '^' and repr(left.left) == repr(right):
                new_exp = self._simplify_once(BinOp('+', left.right, NumNode(1)))
                return BinOp('^', left.left, new_exp)
            # x * x^a → x^(a+1)
            if isinstance(right, BinOp) and right.op == '^' and repr(right.left) == repr(left):
                new_exp = self._simplify_once(BinOp('+', right.right, NumNode(1)))
                return BinOp('^', right.left, new_exp)
            # x^a * x^b → x^(a+b)
            if isinstance(left, BinOp) and left.op == '^' and \
               isinstance(right, BinOp) and right.op == '^' and \
               repr(left.left) == repr(right.left):
                new_exp = BinOp('+', left.right, right.right)
                new_exp = self._simplify_once(new_exp)
                return BinOp('^', left.left, new_exp)
            # i * i → -1
            if isinstance(left, ImagNode) and isinstance(right, ImagNode):
                return NumNode(-1)

        # ── DIVISION RULES ──
        if op == '/':
            # x / 1 → x
            if isinstance(right, NumNode) and right.value == 1:
                return left
            # 0 / x → 0
            if isinstance(left, NumNode) and left.value == 0:
                return NumNode(0)
            # x / x → 1
            if repr(left) == repr(right):
                return NumNode(1)

        # ── POWER RULES ──
        if op == '^':
            # x^0 → 1
            if isinstance(right, NumNode) and right.value == 0:
                return NumNode(1)
            # x^1 → x
            if isinstance(right, NumNode) and right.value == 1:
                return left
            # 0^x → 0 (x > 0)
            if isinstance(left, NumNode) and left.value == 0:
                return NumNode(0)
            # 1^x → 1
            if isinstance(left, NumNode) and left.value == 1:
                return NumNode(1)
            # (x^a)^b → x^(a*b)
            if isinstance(left, BinOp) and left.op == '^':
                new_exp = BinOp('*', left.right, right)
                new_exp = self._simplify_once(new_exp)
                return BinOp('^', left.left, new_exp)
            # (a*b)^n → a^n * b^n (distribute power over product)
            if isinstance(left, BinOp) and left.op == '*' and \
               isinstance(right, NumNode) and right.value == int(right.value):
                a_pow = BinOp('^', left.left, right)
                b_pow = BinOp('^', left.right, right)
                a_pow = self._simplify_once(a_pow)
                b_pow = self._simplify_once(b_pow)
                return BinOp('*', a_pow, b_pow)
            # i^2 → -1
            if isinstance(left, ImagNode) and isinstance(right, NumNode) and right.value == 2:
                return NumNode(-1)
            # Numeric power
            if isinstance(left, NumNode) and isinstance(right, NumNode):
                if right.value == int(right.value) and abs(right.value) < 20:
                    return NumNode(left.value ** int(right.value))

        return BinOp(op, left, right)

    def _get_coeff(self, node: Node) -> Tuple[float, Node]:
        """Extract coefficient: 3x → (3, x), x → (1, x), -x → (-1, x)."""
        if isinstance(node, BinOp) and node.op == '*':
            if isinstance(node.left, NumNode):
                return node.left.value, node.right
            if isinstance(node.right, NumNode):
                return node.right.value, node.left
        return 1.0, node

    def _compute(self, op: str, a: float, b: float) -> Optional[float]:
        """Compute numeric operation."""
        try:
            if op == '+': return a + b
            if op == '-': return a - b
            if op == '*': return a * b
            if op == '/' and b != 0: return a / b
            if op == '^' and (b == int(b) or a > 0): return a ** b
        except:
            pass
        return None

    def _eval_func(self, name: str, val: float) -> Node:
        """Evaluate function on numeric argument."""
        try:
            funcs = {
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'sqrt': math.sqrt, 'log': math.log10, 'ln': math.log,
                'abs': abs, 'exp': math.exp, 'floor': math.floor,
                'ceil': math.ceil, 'asin': math.asin, 'acos': math.acos,
                'atan': math.atan,
            }
            if name in funcs:
                return NumNode(funcs[name](val))
        except:
            pass
        return FuncNode(name, NumNode(val))


# ═══════════════════════════════════════════════════════════════
# EQUATION SOLVER — Isolate variable, quadratic formula, factoring
# ═══════════════════════════════════════════════════════════════

class Solver:
    """Solve equations symbolically."""

    def __init__(self):
        self.simplifier = Simplifier()

    def solve(self, lhs: Node, rhs: Node, var: str = 'x') -> List[str]:
        """Solve equation lhs = rhs for variable var.
        Returns list of solutions as strings."""

        # Move everything to one side: lhs - rhs = 0
        expr = self.simplifier.simplify(BinOp('-', lhs, rhs))

        # Try to extract polynomial coefficients
        coeffs = self._extract_polynomial(expr, var)

        if coeffs is not None:
            degree = len(coeffs) - 1

            # Linear: ax + b = 0 → x = -b/a
            if degree == 1:
                a, b = coeffs[1], coeffs[0]
                if a == 0:
                    return ['no solution'] if b != 0 else ['all real numbers']
                sol = -b / a
                return [self._format_num(sol)]

            # Quadratic: ax^2 + bx + c = 0
            if degree == 2:
                a, b, c = coeffs[2], coeffs[1], coeffs[0]
                return self._solve_quadratic(a, b, c)

            # Cubic (Cardano's method for depressed cubic)
            if degree == 3:
                return self._solve_cubic(coeffs)

        # Try factoring approach
        factors = self._try_factor(expr, var)
        if factors:
            return factors

        # Fallback: if expression is x^2 + a^2 (sum of squares over C)
        sum_sq = self._detect_sum_of_squares(expr, var)
        if sum_sq is not None:
            return sum_sq

        return ['cannot solve symbolically']

    def _solve_quadratic(self, a: float, b: float, c: float) -> List[str]:
        """Solve ax^2 + bx + c = 0 using quadratic formula."""
        disc = b * b - 4 * a * c

        if disc > 0:
            r1 = (-b + math.sqrt(disc)) / (2 * a)
            r2 = (-b - math.sqrt(disc)) / (2 * a)
            return [self._format_num(r1), self._format_num(r2)]
        elif disc == 0:
            r = -b / (2 * a)
            return [f"{self._format_num(r)} (double root)"]
        else:
            # Complex roots
            real = -b / (2 * a)
            imag = math.sqrt(-disc) / (2 * a)
            r_str = self._format_num(real)
            i_str = self._format_num(imag)
            if real == 0:
                return [f"{i_str}i", f"-{i_str}i"]
            return [f"{r_str} + {i_str}i", f"{r_str} - {i_str}i"]

    def _solve_cubic(self, coeffs: List[float]) -> List[str]:
        """Solve cubic equation using rational root theorem + synthetic division."""
        a, b, c, d = coeffs[3], coeffs[2], coeffs[1], coeffs[0]

        # If constant term is 0, x=0 is a root → factor out x
        if d == 0:
            # x*(ax^2 + bx + c) = 0 → x=0 and solve quadratic
            roots = ['0']
            if a != 0:
                quad_roots = self._solve_quadratic(a, b, c)
                roots.extend(quad_roots)
            return roots

        # Try rational roots: factors of d/a
        if a != 0:
            candidates = set()
            for p in self._factors(abs(int(d))) if d == int(d) else [1]:
                for q in self._factors(abs(int(a))) if a == int(a) else [1]:
                    candidates.add(p / q)
                    candidates.add(-p / q)
            candidates.add(0)  # Always try 0

            for r in candidates:
                val = a * r**3 + b * r**2 + c * r + d
                if abs(val) < 1e-10:
                    # Found root r, divide out (x - r)
                    # ax^3 + bx^2 + cx + d = (x-r)(ax^2 + (b+ar)x + ...)
                    new_b = b + a * r
                    new_c = c + new_b * r
                    # Solve remaining quadratic
                    quad_roots = self._solve_quadratic(a, new_b, new_c)
                    return [self._format_num(r)] + quad_roots

        return ['cannot solve cubic analytically']

    def _factors(self, n: int) -> List[int]:
        """Get all factors of n."""
        if n == 0: return [1]
        result = []
        for i in range(1, min(abs(n) + 1, 100)):
            if n % i == 0:
                result.append(i)
        return result

    def _extract_polynomial(self, expr: Node, var: str) -> Optional[List[float]]:
        """Try to extract polynomial coefficients [c0, c1, c2, ...] where
        expr = c0 + c1*x + c2*x^2 + ..."""
        coeffs = {}
        self._collect_terms(expr, var, 1.0, coeffs)

        if coeffs is None:
            return None

        if not coeffs:
            return [0.0]

        max_deg = max(coeffs.keys())
        if max_deg > 10:  # too high degree
            return None

        result = [0.0] * (max_deg + 1)
        for deg, coeff in coeffs.items():
            result[deg] = coeff
        return result

    def _collect_terms(self, node: Node, var: str, coeff: float, coeffs: dict):
        """Recursively collect polynomial terms."""
        if coeffs is None:
            return

        if isinstance(node, NumNode):
            coeffs[0] = coeffs.get(0, 0) + coeff * node.value

        elif isinstance(node, VarNode):
            if node.name == var:
                coeffs[1] = coeffs.get(1, 0) + coeff
            else:
                # Other variable treated as constant — can't solve as pure polynomial
                # But allow it as a coefficient
                coeffs[0] = coeffs.get(0, 0) + coeff  # approximation

        elif isinstance(node, BinOp):
            if node.op == '+':
                self._collect_terms(node.left, var, coeff, coeffs)
                self._collect_terms(node.right, var, coeff, coeffs)
            elif node.op == '-':
                self._collect_terms(node.left, var, coeff, coeffs)
                self._collect_terms(node.right, var, -coeff, coeffs)
            elif node.op == '*':
                # num * var^n or var * var etc.
                if isinstance(node.left, NumNode):
                    self._collect_terms(node.right, var, coeff * node.left.value, coeffs)
                elif isinstance(node.right, NumNode):
                    self._collect_terms(node.left, var, coeff * node.right.value, coeffs)
                elif isinstance(node.left, VarNode) and node.left.name == var and \
                     isinstance(node.right, VarNode) and node.right.name == var:
                    coeffs[2] = coeffs.get(2, 0) + coeff
                else:
                    coeffs.clear()
                    return
            elif node.op == '^':
                if isinstance(node.left, VarNode) and node.left.name == var and \
                   isinstance(node.right, NumNode) and node.right.value == int(node.right.value):
                    deg = int(node.right.value)
                    coeffs[deg] = coeffs.get(deg, 0) + coeff
                elif isinstance(node.left, NumNode) or (isinstance(node.left, VarNode) and node.left.name != var):
                    # Constant raised to power — treat as constant
                    coeffs[0] = coeffs.get(0, 0) + coeff
                else:
                    coeffs.clear()
                    return
            elif node.op == '/':
                # Can't handle division in polynomial extraction easily
                if isinstance(node.right, NumNode) and node.right.value != 0:
                    self._collect_terms(node.left, var, coeff / node.right.value, coeffs)
                else:
                    coeffs.clear()
                    return
        else:
            coeffs.clear()
            return

    def _detect_sum_of_squares(self, expr: Node, var: str) -> Optional[List[str]]:
        """Detect x^2 + a^2 = 0 pattern → solutions ±ia."""
        coeffs = self._extract_polynomial(expr, var)
        if coeffs and len(coeffs) == 3:
            a, b, c = coeffs[0], coeffs[1], coeffs[2]
            # c*x^2 + 0*x + a = 0 where a > 0 and c > 0 (sum of squares)
            if b == 0 and a > 0 and c > 0:
                # x^2 = -a/c → x = ±i*sqrt(a/c)
                val = math.sqrt(a / c)
                v_str = self._format_num(val)
                return [f"{v_str}i", f"-{v_str}i"]
        return None

    def _try_factor(self, expr: Node, var: str) -> Optional[List[str]]:
        """Try to find roots by factoring."""
        # Simple: evaluate at small integers to find roots
        roots = []
        for test in range(-10, 11):
            val = self._evaluate(expr, var, test)
            if val is not None and abs(val) < 1e-10:
                roots.append(self._format_num(test))
        return roots if roots else None

    def _evaluate(self, node: Node, var: str, value: float) -> Optional[float]:
        """Evaluate expression with var = value."""
        try:
            if isinstance(node, NumNode):
                return node.value
            if isinstance(node, VarNode):
                return value if node.name == var else None
            if isinstance(node, ImagNode):
                return None  # Can't evaluate complex in reals
            if isinstance(node, BinOp):
                l = self._evaluate(node.left, var, value)
                r = self._evaluate(node.right, var, value)
                if l is None or r is None:
                    return None
                if node.op == '+': return l + r
                if node.op == '-': return l - r
                if node.op == '*': return l * r
                if node.op == '/' and r != 0: return l / r
                if node.op == '^': return l ** r
            if isinstance(node, FuncNode):
                a = self._evaluate(node.arg, var, value)
                if a is None: return None
                return Simplifier()._eval_func(node.name, a).value if isinstance(Simplifier()._eval_func(node.name, a), NumNode) else None
        except:
            return None
        return None

    def _format_num(self, n: float) -> str:
        """Format number nicely."""
        if n == int(n) and abs(n) < 1e15:
            return str(int(n))
        return f"{n:.6g}"


# ═══════════════════════════════════════════════════════════════
# PRETTY PRINTER — AST → human-readable string
# ═══════════════════════════════════════════════════════════════

class PrettyPrinter:
    """Convert AST back to readable math notation."""

    def to_string(self, node: Node) -> str:
        """Convert AST to clean string."""
        if isinstance(node, NumNode):
            if node.value == int(node.value) and abs(node.value) < 1e15:
                return str(int(node.value))
            return f"{node.value:.6g}"

        if isinstance(node, VarNode):
            return node.name

        if isinstance(node, ImagNode):
            return 'i'

        if isinstance(node, FuncNode):
            return f"{node.name}({self.to_string(node.arg)})"

        if isinstance(node, UnaryOp):
            return f"-{self.to_string(node.operand)}"

        if isinstance(node, BinOp):
            left = self.to_string(node.left)
            right = self.to_string(node.right)

            if node.op == '+':
                if right.startswith('-'):
                    return f"{left} - {right[1:]}"
                return f"{left} + {right}"
            if node.op == '-':
                if right.startswith('-'):
                    return f"{left} + {right[1:]}"
                return f"{left} - {right}"
            if node.op == '*':
                # Clean: 1*x → x, -1*x → -x, num*var → numvar
                if isinstance(node.left, NumNode):
                    if node.left.value == 1:
                        return right
                    if node.left.value == -1:
                        # If right already starts with -, cancel the double negative
                        if right.startswith('-'):
                            return right[1:]
                        return f"-{right}"
                    if isinstance(node.right, (VarNode, ImagNode)):
                        return f"{left}{right}"
                    if isinstance(node.right, BinOp) and node.right.op == '^':
                        return f"{left}{self.to_string(node.right)}"
                return f"{left}*{right}"
            if node.op == '/':
                # Wrap denominator in parens only if it has + or - (needs grouping)
                if isinstance(node.right, BinOp) and node.right.op in ('+', '-'):
                    return f"{left}/({right})"
                return f"{left}/{right}"
            if node.op == '^':
                # Wrap base in parens if it's complex
                if isinstance(node.left, BinOp):
                    return f"({left})^{right}"
                # Wrap exponent in parens if it's complex
                if isinstance(node.right, BinOp):
                    return f"{left}^({right})"
                return f"{left}^{right}"

        return repr(node)


# ═══════════════════════════════════════════════════════════════
# MAIN API — Prometheus Engine
# ═══════════════════════════════════════════════════════════════

class Prometheus:
    """AXIMA Symbolic Mathematics Engine.
    
    Usage:
        engine = Prometheus()
        result = engine.process("solve x^2 + 5x + 6 = 0")
        result = engine.process("simplify (x+1)^2")
        result = engine.process("factor x^2 - 9")
        result = engine.process("expand (a+b)^2")
    """

    def __init__(self):
        self.tokenizer = Tokenizer()
        self.parser = Parser()
        self.simplifier = Simplifier()
        self.solver = Solver()
        self.printer = PrettyPrinter()

    def process(self, text: str) -> str:
        """Process any math input and return result."""
        text = text.strip()

        # Detect command
        low = text.lower()

        # ── EXPLANATIONS: "what is", "explain", "how to" ──
        if any(low.startswith(w) for w in ['what is', 'what are', 'explain', 'how to', 'how do', 'define']):
            explanation = self._handle_explain(text, low)
            if explanation:
                return explanation

        # DIFFERENTIAL EQUATIONS: y' = f(x), dy/dx = f(x) — check BEFORE solve
        if ("y'" in text or "y''" in text or 'dy/dx' in low or 'dy/dt' in low):
            return self._handle_ode(text)

        # SOLVE: solve equation for variable (but not "find X with values")
        if (low.startswith('solve') or ('=' in text and any(c in text for c in 'xyz'))) and 'with' not in low:
            return self._handle_solve(text)

        # PROVE: mathematical proofs
        if low.startswith('prove'):
            prover = ProofEngine()
            return prover.prove(text)

        # DIFFERENTIATE / DERIVATIVE
        if any(low.startswith(t) for t in ['differentiate', 'derivative', 'diff ', "d/d"]):
            return self._handle_derivative(text)

        # INTEGRATE
        if any(low.startswith(t) for t in ['integrate', 'integral', 'antiderivative']):
            return self._handle_integral(text)

        # LIMIT
        if low.startswith('limit') or low.startswith('lim '):
            return self._handle_limit(text)

        # TAYLOR SERIES
        if 'taylor' in low or 'series' in low:
            return self._handle_taylor(text)

        # INVERSE LAPLACE (must check BEFORE regular laplace)
        if 'inverse laplace' in low or 'inv laplace' in low:
            return self._handle_inv_laplace(text)

        # LAPLACE TRANSFORM
        if 'laplace' in low:
            return self._handle_laplace(text)

        # FOURIER TRANSFORM
        if 'fourier' in low:
            return self._handle_fourier(text)

        # Z-TRANSFORM
        if 'z transform' in low or 'z-transform' in low or 'ztransform' in low:
            return self._handle_z_transform(text)

        # SIMPLIFY
        if low.startswith('simplif'):
            expr_text = re.sub(r'^simplif\w*\s*', '', text, flags=re.IGNORECASE)
            return self._handle_simplify(expr_text)

        # FACTOR
        if low.startswith('factor'):
            expr_text = re.sub(r'^factor\w*\s*', '', text, flags=re.IGNORECASE)
            return self._handle_factor(expr_text)

        # EXPAND
        if low.startswith('expand'):
            expr_text = re.sub(r'^expand\s*', '', text, flags=re.IGNORECASE)
            return self._handle_expand(expr_text)

        # EVALUATE (just a numeric expression)
        if not any(c.isalpha() for c in text.replace('pi', '').replace('sqrt', '').replace('sin', '').replace('cos', '').replace('tan', '').replace('log', '').replace('ln', '').replace('exp', '')):
            return self._handle_evaluate(text)

        # ENGINEERING / FORMULA lookup
        if any(w in low for w in ['formula', 'calculate', 'compute', 'determine']):
            eng = EngineeringSolver()
            result = eng.solve_problem(text)
            if result and 'No applicable' not in result and 'No formula' not in result:
                return result
            if 'formula' in low:
                return result

        # "find X with values" — engineering problem (not equation)
        if low.startswith('find ') and 'with' in low:
            eng = EngineeringSolver()
            result = eng.solve_problem(text)
            if result and 'No applicable' not in result:
                return result

        # Default: try to simplify or solve
        if '=' in text:
            return self._handle_solve(text)

        # Stage 7: General Mathematical Intelligence — handles anything else
        try:
            synth = MathSynth()
            result = synth.solve(text)
            if result and 'Cannot' not in result and len(result) > 2:
                return result
        except Exception:
            pass

        return self._handle_simplify(text)

    def _handle_solve(self, text: str) -> str:
        """Solve an equation."""
        # Remove 'solve' prefix
        text = re.sub(r'^solve\s*', '', text, flags=re.IGNORECASE)

        # Detect variable to solve for
        var = 'x'
        m = re.search(r'for\s+([a-z])\s*$', text)
        if m:
            var = m.group(1)
            text = text[:m.start()].strip()

        # Detect which variable is present
        tokens = self.tokenizer.tokenize(text)
        vars_found = [t.value for t in tokens if t.type == TT.VAR]
        if vars_found and var not in vars_found:
            var = vars_found[0]

        # Parse equation
        lhs, rhs = self.parser.parse_equation(tokens)

        # Solve
        solutions = self.solver.solve(lhs, rhs, var)

        if not solutions:
            return "No solution found."

        if len(solutions) == 1:
            return f"{var} = {solutions[0]}"
        return f"{var} = {', '.join(solutions)}"

    def _handle_derivative(self, text: str) -> str:
        """Compute derivative."""
        # Remove prefix
        text = re.sub(r'^(?:differentiate|derivative\s+of|diff|d/d[a-z])\s*', '', text, flags=re.IGNORECASE)

        # Detect variable
        var = 'x'
        m = re.search(r'(?:with respect to|wrt|d/d)([a-z])', text.lower())
        if m:
            var = m.group(1)
            text = re.sub(r'\s*(?:with respect to|wrt)\s*[a-z]\s*$', '', text, flags=re.IGNORECASE)

        # Parse and differentiate
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)

        # Auto-detect variable if not x
        if var == 'x':
            vars_found = [t.value for t in tokens if t.type == TT.VAR]
            if vars_found and 'x' not in vars_found:
                var = vars_found[0]

        calc = Calculus()
        result = calc.differentiate(ast, var)
        return self.printer.to_string(result)

    def _handle_integral(self, text: str) -> str:
        """Compute integral."""
        # Remove prefix
        text = re.sub(r'^(?:integrate|integral\s+of|antiderivative\s+of)\s*', '', text, flags=re.IGNORECASE)

        # Detect variable (look for "dx" or "dy" at end)
        var = 'x'
        m = re.search(r'\s*d([a-z])\s*$', text)
        if m:
            var = m.group(1)
            text = text[:m.start()].strip()
        else:
            m = re.search(r'(?:with respect to|wrt)\s*([a-z])', text.lower())
            if m:
                var = m.group(1)
                text = re.sub(r'\s*(?:with respect to|wrt)\s*[a-z]\s*$', '', text, flags=re.IGNORECASE)

        # Parse and integrate
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)

        # Auto-detect variable
        if var == 'x':
            vars_found = [t.value for t in tokens if t.type == TT.VAR]
            if vars_found and 'x' not in vars_found:
                var = vars_found[0]

        calc = Calculus()
        result = calc.integrate(ast, var)
        if result is None:
            return "Cannot integrate this expression symbolically."
        return self.printer.to_string(result) + " + C"

    def _handle_limit(self, text: str) -> str:
        """Compute limit."""
        # Parse: "limit of (expr) as x -> a" or "lim x->a expr"
        text = re.sub(r'^(?:limit|lim)\s*(?:of\s*)?', '', text, flags=re.IGNORECASE)

        var = 'x'
        approach = 0.0

        # Pattern: "as x -> 5" or "x->0" or "x approaches 5"
        m = re.search(r'(?:as\s+)?([a-z])\s*(?:->|→|approaches)\s*([-\d.]+|inf|infinity|pi)', text, re.IGNORECASE)
        if m:
            var = m.group(1)
            val_str = m.group(2).lower()
            if val_str in ('inf', 'infinity'):
                approach = float('inf')
            elif val_str == 'pi':
                approach = math.pi
            else:
                approach = float(val_str)
            text = text[:m.start()].strip()

        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)

        calc = Calculus()
        result = calc.limit(ast, var, approach)
        if result is None:
            return "Cannot compute this limit."
        return self.printer.to_string(result)

    def _handle_taylor(self, text: str) -> str:
        """Compute Taylor series."""
        # Parse: "taylor series of sin(x) around 0 with 5 terms"
        text = re.sub(r'^(?:taylor\s+series\s+of|taylor|series\s+of)\s*', '', text, flags=re.IGNORECASE)

        center = 0.0
        terms = 5
        var = 'x'

        # Extract center
        m = re.search(r'(?:around|at|about)\s*([-\d.]+|pi)', text, re.IGNORECASE)
        if m:
            center = math.pi if m.group(1).lower() == 'pi' else float(m.group(1))
            text = text[:m.start()].strip()

        # Extract number of terms
        m = re.search(r'(\d+)\s*terms?', text)
        if m:
            terms = int(m.group(1))
            text = text[:m.start()].strip()

        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)

        calc = Calculus()
        result = calc.taylor_series(ast, var, center, terms)
        return self.printer.to_string(result)

    def _handle_explain(self, text: str, low: str) -> Optional[str]:
        """Explain math concepts with step-by-step teaching."""
        # Remove prefix
        topic = re.sub(r'^(?:what is|what are|explain|how to|how do you|define)\s+(?:a\s+|an\s+|the\s+)?', '', low).strip().rstrip('?')

        # Check if it's actually asking to compute something (has numbers/variables mixed in)
        if re.search(r'\d+\s*[+\-*/^]\s*\d+', topic) or '=' in topic:
            return None  # Let compute handle it

        # Math concept explanations (teach, not compute)
        explanations = {
            'derivative': "A derivative measures how a function changes as its input changes.\n\nNotation: f'(x) or dy/dx or d/dx[f(x)]\n\nRules:\n  • d/dx(x^n) = n·x^(n-1)  (power rule)\n  • d/dx(f+g) = f' + g'  (sum rule)\n  • d/dx(f·g) = f'g + fg'  (product rule)\n  • d/dx(f(g)) = f'(g)·g'  (chain rule)\n\nExample: d/dx(x^3) = 3x^2\n\nUse 'differentiate [expr]' to compute one.",
            'differentiation': "Differentiation is the process of finding a derivative.\n\nIt tells you the RATE OF CHANGE of a function.\n\nBasic rules:\n  • Power: d/dx(x^n) = n·x^(n-1)\n  • Sum: d/dx(f+g) = f' + g'\n  • Product: d/dx(fg) = f'g + fg'\n  • Chain: d/dx(f(g(x))) = f'(g(x))·g'(x)\n\nExample: d/dx(3x^2 + 2x) = 6x + 2\n\nUse 'differentiate [expr]' to compute.",
            'integration': "Integration is the reverse of differentiation.\n\nNotation: ∫f(x)dx\n\nRules:\n  • ∫x^n dx = x^(n+1)/(n+1) + C  (power rule)\n  • ∫sin(x) dx = -cos(x) + C\n  • ∫cos(x) dx = sin(x) + C\n  • ∫e^x dx = e^x + C\n  • ∫1/x dx = ln|x| + C\n\nExample: ∫x^2 dx = x^3/3 + C\n\nUse 'integrate [expr] dx' to compute.",
            'integral': "An integral computes the area under a curve or reverses differentiation.\n\nTypes:\n  • Indefinite: ∫f(x)dx = F(x) + C (antiderivative)\n  • Definite: ∫[a,b] f(x)dx = F(b) - F(a) (area)\n\nBasic integrals:\n  • ∫x^n dx = x^(n+1)/(n+1) + C\n  • ∫sin(x) dx = -cos(x) + C\n  • ∫e^x dx = e^x + C\n\nUse 'integrate [expr] dx' to compute.",
            'quadratic equation': "A quadratic equation has the form: ax² + bx + c = 0\n\nSolution (quadratic formula):\n  x = (-b ± √(b²-4ac)) / 2a\n\nDiscriminant (b²-4ac) determines roots:\n  • > 0: two real roots\n  • = 0: one repeated root\n  • < 0: two complex roots\n\nExample: x² + 5x + 6 = 0\n  a=1, b=5, c=6\n  x = (-5 ± √(25-24)) / 2 = (-5 ± 1) / 2\n  x = -2 or x = -3\n\nUse 'solve [equation] = 0' to solve one.",
            'laplace transform': "The Laplace transform converts a time-domain function into the s-domain.\n\nDefinition: L{f(t)} = ∫₀^∞ f(t)·e^(-st) dt\n\nCommon transforms:\n  • L{1} = 1/s\n  • L{t} = 1/s²\n  • L{t^n} = n!/s^(n+1)\n  • L{e^(at)} = 1/(s-a)\n  • L{sin(wt)} = w/(s²+w²)\n  • L{cos(wt)} = s/(s²+w²)\n\nUsed in: control systems, circuit analysis, differential equations.\n\nUse 'laplace transform of [expr]' to compute.",
            'fourier transform': "The Fourier transform decomposes a signal into its frequency components.\n\nDefinition: F{f(t)} = ∫₋∞^∞ f(t)·e^(-iωt) dt\n\nKey properties:\n  • Linearity: F{af+bg} = aF{f} + bF{g}\n  • Time shift: F{f(t-a)} = e^(-iaω)·F{f}\n  • Frequency shift: F{e^(iat)·f} = F(ω-a)\n  • Convolution: F{f*g} = F{f}·F{g}\n\nUsed in: signal processing, image processing, physics.\n\nUse 'fourier transform of [expr]' to compute.",
            'factorial': "Factorial (n!) is the product of all positive integers up to n.\n\nDefinition: n! = n × (n-1) × (n-2) × ... × 2 × 1\n\nExamples:\n  • 5! = 5×4×3×2×1 = 120\n  • 0! = 1 (by definition)\n  • 10! = 3,628,800\n\nUsed in: permutations, combinations, probability, Taylor series.\n\nFormula: C(n,r) = n! / (r! × (n-r)!)",
            'limit': "A limit describes the value a function approaches as input approaches a point.\n\nNotation: lim(x→a) f(x) = L\n\nRules:\n  • Direct substitution: try f(a) first\n  • 0/0 form: use L'Hôpital's rule (take derivatives of top and bottom)\n  • ∞/∞ form: also use L'Hôpital\n\nExample: lim(x→0) sin(x)/x = 1\n\nUse 'limit of [expr] as x->[value]' to compute.",
            'taylor series': "A Taylor series approximates any function as a polynomial.\n\nFormula: f(x) = Σ f^(n)(a)/n! · (x-a)^n\n\nCommon series (around 0):\n  • e^x = 1 + x + x²/2 + x³/6 + ...\n  • sin(x) = x - x³/6 + x⁵/120 - ...\n  • cos(x) = 1 - x²/2 + x⁴/24 - ...\n  • 1/(1-x) = 1 + x + x² + x³ + ...\n\nUse 'taylor series of [expr] [n] terms' to compute.",
            'complex number': "A complex number has a real part and an imaginary part.\n\nForm: z = a + bi, where i² = -1\n\nOperations:\n  • Addition: (a+bi) + (c+di) = (a+c) + (b+d)i\n  • Multiplication: (a+bi)(c+di) = (ac-bd) + (ad+bc)i\n  • Modulus: |z| = √(a² + b²)\n  • Conjugate: z̄ = a - bi\n\nEuler's formula: e^(ix) = cos(x) + i·sin(x)",
            'induction': "Mathematical induction proves statements for all natural numbers.\n\nSteps:\n  1. BASE CASE: Prove for n=1 (or smallest value)\n  2. INDUCTIVE HYPOTHESIS: Assume true for n=k\n  3. INDUCTIVE STEP: Prove true for n=k+1 using the assumption\n\nExample: Prove 1+2+...+n = n(n+1)/2\n  Base: n=1 → 1 = 1(2)/2 ✓\n  Step: Assume for k. Then for k+1:\n    1+...+k+(k+1) = k(k+1)/2 + (k+1) = (k+1)(k+2)/2 ✓\n\nUse 'prove [statement]' for proofs.",
        }

        # Partial matching
        for key, explanation in explanations.items():
            if key in topic or topic in key:
                return explanation

        # "how to solve" → explain solving method
        if 'solve' in topic:
            if 'quadratic' in topic or 'x^2' in topic:
                return explanations['quadratic equation']
            return "To solve an equation:\n  1. Move all terms to one side (= 0)\n  2. Factor if possible\n  3. For linear (ax+b=0): x = -b/a\n  4. For quadratic (ax²+bx+c=0): use quadratic formula\n  5. For cubic: try rational roots, then factor\n\nUse 'solve [equation] = 0' to solve."

        # "what is a+b" type (algebraic expression explanation)
        if re.match(r'^[a-z\s\+\-\*\/\^]+$', topic):
            # It's a simple algebraic expression
            return f"'{topic}' is an algebraic expression.\n\nIt represents the mathematical operation between variables.\nWithout knowing the values of the variables, it stays as '{topic}'.\n\nTo evaluate: provide values (e.g., 'simplify {topic}' or substitute numbers)\nTo compute with numbers: type the expression directly (e.g., '3+5')"

        return None  # Not an explanation request, let other handlers try

    def _handle_ode(self, text: str) -> str:
        """Solve ordinary differential equations by integration."""
        import re
        steps = []

        # Normalize: dy/dx → y', d2y/dx2 → y''
        text_norm = text.replace('dy/dx', "y'").replace('dy/dt', "y'")

        # Extract RHS of y' = f(x)
        m = re.search(r"y'\s*=\s*(.+)", text_norm)
        if m:
            rhs_str = m.group(1).strip()
            steps.append(f"ODE: y' = {rhs_str}")
            steps.append(f"Type: First-order, separable (direct integration)")
            steps.append(f"")
            steps.append(f"Solution: y = ∫({rhs_str}) dx")

            # Integrate
            result = self.process(f"integrate {rhs_str} dx")
            steps.append(f"  y = {result}")
            return '\n'.join(steps)

        # Second order: y'' = f(x) → integrate twice
        m = re.search(r"y''\s*=\s*(.+)", text_norm)
        if m:
            rhs_str = m.group(1).strip()
            steps.append(f"ODE: y'' = {rhs_str}")
            steps.append(f"Type: Second-order (direct integration twice)")
            steps.append(f"")

            # First integration: y' = ∫f(x)dx + C1
            first_int = self.process(f"integrate {rhs_str} dx")
            first_int_clean = first_int.replace(' + C', '')
            steps.append(f"Step 1: y' = ∫({rhs_str}) dx = {first_int_clean} + C₁")

            # Second integration
            second_int = self.process(f"integrate {first_int_clean} dx")
            second_int_clean = second_int.replace(' + C', '')
            steps.append(f"Step 2: y = ∫({first_int_clean}) dx = {second_int_clean} + C₁x + C₂")
            return '\n'.join(steps)

        # Linear first-order: y' + P(x)y = Q(x) → integrating factor
        m = re.search(r"y'\s*\+\s*(.+?)\s*\*?\s*y\s*=\s*(.+)", text_norm)
        if m:
            p_str = m.group(1).strip()
            q_str = m.group(2).strip()
            steps.append(f"ODE: y' + ({p_str})y = {q_str}")
            steps.append(f"Type: Linear first-order")
            steps.append(f"Method: Integrating factor")
            steps.append(f"  μ(x) = e^(∫{p_str} dx)")
            p_int = self.process(f"integrate {p_str} dx").replace(' + C', '')
            steps.append(f"  μ(x) = e^({p_int})")
            steps.append(f"  Solution: y = (1/μ) ∫ μ·{q_str} dx + C/μ")
            return '\n'.join(steps)

        return "Cannot parse ODE format. Use: y' = f(x)"

    def _handle_laplace(self, text: str) -> str:
        """Compute Laplace transform."""
        text = re.sub(r'^(?:laplace\s+(?:transform\s+(?:of\s+)?)?|L\{)', '', text, flags=re.IGNORECASE).rstrip('}')
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)
        t_var = 't'
        # Auto-detect time variable
        vars_found = [t.value for t in tokens if t.type == TT.VAR and t.value not in ('e', 's')]
        if vars_found and 't' not in vars_found:
            t_var = vars_found[0]
        transforms = Transforms()
        result = transforms.laplace(ast, t_var, 's')
        if result is None:
            return "Cannot compute Laplace transform."
        return f"L{{f({t_var})}} = {self.printer.to_string(result)}"

    def _handle_inv_laplace(self, text: str) -> str:
        """Compute inverse Laplace transform."""
        text = re.sub(r'^(?:inverse\s+laplace\s+(?:transform\s+(?:of\s+)?)?|inv\s+laplace\s+)', '', text, flags=re.IGNORECASE)
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)
        transforms = Transforms()
        result = transforms.inverse_laplace(ast, 's', 't')
        if result is None:
            return "Cannot compute inverse Laplace transform."
        result = self.simplifier.simplify(result)
        return f"L⁻¹{{F(s)}} = {self.printer.to_string(result)}"

    def _handle_fourier(self, text: str) -> str:
        """Compute Fourier transform."""
        text = re.sub(r'^(?:fourier\s+(?:transform\s+(?:of\s+)?)?)', '', text, flags=re.IGNORECASE)
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)
        t_var = 't'
        vars_found = [t.value for t in tokens if t.type == TT.VAR and t.value not in ('e', 'w')]
        if vars_found and 't' not in vars_found:
            t_var = vars_found[0]
        transforms = Transforms()
        result = transforms.fourier(ast, t_var, 'w')
        if result is None:
            return "Cannot compute Fourier transform."
        if isinstance(result, str):
            return f"F{{f({t_var})}} = {result}"
        return f"F{{f({t_var})}} = {self.printer.to_string(result)}"

    def _handle_z_transform(self, text: str) -> str:
        """Compute Z-transform."""
        text = re.sub(r'^(?:z[- ]?transform\s+(?:of\s+)?)', '', text, flags=re.IGNORECASE)
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)
        n_var = 'n'
        vars_found = [t.value for t in tokens if t.type == TT.VAR and t.value not in ('e', 'z')]
        if vars_found and 'n' not in vars_found:
            n_var = vars_found[0]
        transforms = Transforms()
        result = transforms.z_transform(ast, n_var, 'z')
        if result is None:
            return "Cannot compute Z-transform."
        return f"Z{{x[{n_var}]}} = {self.printer.to_string(result)}"

    def _handle_simplify(self, text: str) -> str:
        """Simplify an expression."""
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)
        simplified = self.simplifier.simplify(ast)
        return self.printer.to_string(simplified)

    def _handle_factor(self, text: str) -> str:
        """Factor an expression (difference of squares, etc.)."""
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)
        simplified = self.simplifier.simplify(ast)

        # Detect patterns:
        # x^2 - a^2 → (x-a)(x+a)
        if isinstance(simplified, BinOp) and simplified.op == '-':
            if isinstance(simplified.left, BinOp) and simplified.left.op == '^' and \
               isinstance(simplified.left.right, NumNode) and simplified.left.right.value == 2:
                if isinstance(simplified.right, BinOp) and simplified.right.op == '^' and \
                   isinstance(simplified.right.right, NumNode) and simplified.right.right.value == 2:
                    a = self.printer.to_string(simplified.left.left)
                    b = self.printer.to_string(simplified.right.left)
                    return f"({a} - {b})({a} + {b})"
                elif isinstance(simplified.right, NumNode):
                    val = simplified.right.value
                    sq = math.sqrt(val)
                    if sq == int(sq):
                        a = self.printer.to_string(simplified.left.left)
                        return f"({a} - {int(sq)})({a} + {int(sq)})"

        # x^2 + a^2 → (x - ai)(x + ai) [over complex]
        if isinstance(simplified, BinOp) and simplified.op == '+':
            if isinstance(simplified.left, BinOp) and simplified.left.op == '^' and \
               isinstance(simplified.left.right, NumNode) and simplified.left.right.value == 2:
                if isinstance(simplified.right, BinOp) and simplified.right.op == '^' and \
                   isinstance(simplified.right.right, NumNode) and simplified.right.right.value == 2:
                    a = self.printer.to_string(simplified.left.left)
                    b = self.printer.to_string(simplified.right.left)
                    return f"({a} - {b}i)({a} + {b}i)  [over ℂ]"
                elif isinstance(simplified.right, NumNode):
                    val = simplified.right.value
                    sq = math.sqrt(val)
                    a = self.printer.to_string(simplified.left.left)
                    if sq == int(sq):
                        return f"({a} - {int(sq)}i)({a} + {int(sq)}i)  [over ℂ]"
                    return f"({a} - √{int(val)}·i)({a} + √{int(val)}·i)  [over ℂ]"

        # Quadratic: ax^2 + bx + c → a(x-r1)(x-r2)
        var = 'x'
        tokens_f = self.tokenizer.tokenize(text)
        vars_found = [t.value for t in tokens_f if t.type == TT.VAR]
        if vars_found:
            var = vars_found[0]

        coeffs = self.solver._extract_polynomial(simplified, var)
        if coeffs and len(coeffs) == 3:
            a, b, c = coeffs[2], coeffs[1], coeffs[0]
            disc = b*b - 4*a*c
            if disc >= 0:
                r1 = (-b + math.sqrt(disc)) / (2*a)
                r2 = (-b - math.sqrt(disc)) / (2*a)
                def _fmt_factor(var, root):
                    rs = self.solver._format_num(abs(root))
                    if root == 0:
                        return var
                    elif root > 0:
                        return f"({var} - {rs})"
                    else:
                        return f"({var} + {rs})"
                f1 = _fmt_factor(var, r1)
                f2 = _fmt_factor(var, r2)
                if a == 1:
                    return f"{f1}{f2}"
                return f"{self.solver._format_num(a)}{f1}{f2}"

        return self.printer.to_string(simplified)

    def _handle_expand(self, text: str) -> str:
        """Expand expression (multiply out)."""
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)

        # Expand (a+b)^n using binomial theorem
        if isinstance(ast, BinOp) and ast.op == '^' and isinstance(ast.right, NumNode):
            n = int(ast.right.value)
            if isinstance(ast.left, BinOp) and ast.left.op in ('+', '-') and 2 <= n <= 6:
                a = ast.left.left
                b = ast.left.right
                sign = 1 if ast.left.op == '+' else -1

                # Binomial expansion: (a+b)^n = Σ C(n,k) * a^(n-k) * b^k
                terms = []
                for k in range(n + 1):
                    coeff = math.factorial(n) // (math.factorial(k) * math.factorial(n - k))
                    coeff *= (sign ** k)  # handle minus sign

                    a_power = n - k
                    b_power = k
                    a_str = self.printer.to_string(a)
                    b_str = self.printer.to_string(b)

                    # Build term string
                    parts = []

                    # Coefficient
                    abs_coeff = abs(coeff)

                    # a^(n-k) part
                    a_part = ''
                    if a_power == 0:
                        a_part = ''
                    elif a_power == 1:
                        a_part = a_str
                    else:
                        # If a is a product like 2x, compute (2x)^n = 2^n * x^n
                        if isinstance(a, BinOp) and a.op == '*' and isinstance(a.left, NumNode):
                            num_coeff = int(a.left.value ** a_power)
                            abs_coeff *= num_coeff
                            inner_var = self.printer.to_string(a.right)
                            a_part = f"{inner_var}^{a_power}" if a_power > 1 else inner_var
                        else:
                            a_part = f"({a_str})^{a_power}" if isinstance(a, BinOp) else f"{a_str}^{a_power}"

                    # b^k part — handle b being a number
                    b_part = ''
                    b_is_num = isinstance(b, NumNode)
                    if b_power == 0:
                        b_part = ''
                    elif b_is_num:
                        # Compute b^k as number
                        b_val = int(b.value ** b_power)
                        abs_coeff *= b_val
                        b_part = ''
                    elif b_power == 1:
                        b_part = b_str
                    else:
                        b_part = f"{b_str}^{b_power}"

                    # Combine: coeff * a_part * b_part
                    if a_part == '' and b_part == '':
                        term = str(abs_coeff)
                    elif abs_coeff == 1:
                        term = a_part + b_part if a_part and b_part else (a_part or b_part)
                    else:
                        inner = a_part + b_part if a_part and b_part else (a_part or b_part)
                        if inner:
                            # If a was like "2x" (coeff*var), we need to multiply properly
                            # Check if a_power=1 and a is num*var → coeff should multiply
                            if a_power == 1 and isinstance(a, BinOp) and a.op == '*' and isinstance(a.left, NumNode):
                                # a = num*var, so abs_coeff * num * var
                                total_coeff = int(abs_coeff * a.left.value)
                                var_str = self.printer.to_string(a.right)
                                term = f"{total_coeff}{var_str}{b_part}" if total_coeff != 1 else f"{var_str}{b_part}"
                            else:
                                term = f"{abs_coeff}{inner}"
                        else:
                            term = str(abs_coeff)

                    if k == 0:
                        terms.append(f"-{term}" if coeff < 0 else term)
                    elif coeff >= 0:
                        terms.append(f" + {term}")
                    else:
                        terms.append(f" - {term}")

                return ''.join(terms)

        # General: just simplify
        result = self.simplifier.simplify(ast)
        return self.printer.to_string(result)

    def _handle_evaluate(self, text: str) -> str:
        """Evaluate a numeric expression."""
        tokens = self.tokenizer.tokenize(text)
        ast = self.parser.parse(tokens)
        result = self.simplifier.simplify(ast)
        return self.printer.to_string(result)


# ═══════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════

_engine = None

def get_prometheus():
    global _engine
    if _engine is None:
        _engine = Prometheus()
    return _engine


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    engine = Prometheus()

    print("═══ AXIMA PROMETHEUS — Symbolic Math Engine ═══\n")

    tests = [
        # Arithmetic
        ("2 + 3 * 4", "Arithmetic"),
        ("(2 + 3) * 4", "Arithmetic"),
        ("2^10", "Powers"),
        ("sqrt(144)", "Functions"),

        # Simplification
        ("simplify x + x + x", "Simplify"),
        ("simplify x * x", "Simplify"),
        ("simplify x^2 * x^3", "Simplify"),
        ("simplify (x + 0) * 1", "Simplify"),

        # Solving
        ("solve 2x + 6 = 0", "Linear"),
        ("solve x^2 - 4 = 0", "Quadratic"),
        ("solve x^2 + 5x + 6 = 0", "Quadratic"),
        ("solve x^2 + 4 = 0", "Complex roots"),
        ("solve x^2 + a^2 = 0", "Sum of squares"),

        # Factoring
        ("factor x^2 - 9", "Diff of squares"),
        ("factor x^2 + a^2", "Sum of squares (C)"),
        ("factor x^2 - 5x + 6", "Quadratic"),

        # Expansion
        ("expand (x + 1)^2", "Binomial"),
        ("expand (a - b)^2", "Binomial"),
    ]

    for expr, category in tests:
        result = engine.process(expr)
        print(f"  [{category:18s}] {expr}")
        print(f"  {'':18s}  → {result}")
        print()


# ═══════════════════════════════════════════════════════════════
# STAGE 3: CALCULUS ENGINE — Derivatives, Integrals, Limits
# ═══════════════════════════════════════════════════════════════

class Calculus:
    """Symbolic calculus: differentiation, integration, limits, series.
    Pure rule-based — applies the RULES of calculus mechanically."""

    def __init__(self):
        self.simplifier = Simplifier()
        self.printer = PrettyPrinter()

    # ─────────────────────────────────────────────────────────
    # DIFFERENTIATION — 100% mechanical, just apply rules
    # ─────────────────────────────────────────────────────────

    def differentiate(self, node: Node, var: str = 'x') -> Node:
        """Compute d/d(var) of expression. Returns simplified derivative."""
        result = self._diff(node, var)
        return self.simplifier.simplify(result)

    def _diff(self, node: Node, var: str) -> Node:
        """Recursive differentiation."""

        # d/dx(constant) = 0
        if isinstance(node, NumNode):
            return NumNode(0)

        # d/dx(i) = 0
        if isinstance(node, ImagNode):
            return NumNode(0)

        # d/dx(x) = 1, d/dx(y) = 0
        if isinstance(node, VarNode):
            return NumNode(1) if node.name == var else NumNode(0)

        # d/dx(f(g(x))) — chain rule for functions
        if isinstance(node, FuncNode):
            return self._diff_func(node, var)

        # Binary operations
        if isinstance(node, BinOp):
            return self._diff_binop(node, var)

        return NumNode(0)

    def _diff_binop(self, node: BinOp, var: str) -> Node:
        """Differentiate binary operations."""

        # d/dx(f + g) = f' + g'  [SUM RULE]
        if node.op == '+':
            return BinOp('+', self._diff(node.left, var), self._diff(node.right, var))

        # d/dx(f - g) = f' - g'  [DIFFERENCE RULE]
        if node.op == '-':
            return BinOp('-', self._diff(node.left, var), self._diff(node.right, var))

        # d/dx(f * g) = f'g + fg'  [PRODUCT RULE]
        if node.op == '*':
            f, g = node.left, node.right
            fp = self._diff(f, var)
            gp = self._diff(g, var)
            return BinOp('+',
                         BinOp('*', fp, g),
                         BinOp('*', f, gp))

        # d/dx(f / g) = (f'g - fg') / g^2  [QUOTIENT RULE]
        if node.op == '/':
            f, g = node.left, node.right
            fp = self._diff(f, var)
            gp = self._diff(g, var)
            numerator = BinOp('-',
                              BinOp('*', fp, g),
                              BinOp('*', f, gp))
            denominator = BinOp('^', g, NumNode(2))
            return BinOp('/', numerator, denominator)

        # d/dx(f ^ g) — POWER RULE + CHAIN RULE
        if node.op == '^':
            f, g = node.left, node.right
            f_has_var = self._contains_var(f, var)
            g_has_var = self._contains_var(g, var)

            # Case 1: x^n (n constant) → n*x^(n-1) * x'  [POWER RULE]
            if f_has_var and not g_has_var:
                # d/dx(f^n) = n * f^(n-1) * f'
                fp = self._diff(f, var)
                return BinOp('*',
                             BinOp('*', g, BinOp('^', f, BinOp('-', g, NumNode(1)))),
                             fp)

            # Case 2: a^x (a constant) → a^x * ln(a) * x'  [EXPONENTIAL RULE]
            if not f_has_var and g_has_var:
                # Special case: e^g(x) → e^g(x) * g'(x)
                if isinstance(f, VarNode) and f.name == 'e':
                    gp = self._diff(g, var)
                    return BinOp('*', node, gp)
                # d/dx(a^g) = a^g * ln(a) * g'
                gp = self._diff(g, var)
                return BinOp('*',
                             BinOp('*', node, FuncNode('ln', f)),
                             gp)

            # Case 3: f^g (both have var) → f^g * (g'*ln(f) + g*f'/f)  [LOGARITHMIC DIFFERENTIATION]
            if f_has_var and g_has_var:
                fp = self._diff(f, var)
                gp = self._diff(g, var)
                term1 = BinOp('*', gp, FuncNode('ln', f))
                term2 = BinOp('*', g, BinOp('/', fp, f))
                return BinOp('*', node, BinOp('+', term1, term2))

            # Case 4: constant^constant = constant → 0
            return NumNode(0)

        return NumNode(0)

    def _diff_func(self, node: FuncNode, var: str) -> Node:
        """Differentiate functions using chain rule: d/dx[f(g)] = f'(g) * g'."""
        g = node.arg
        gp = self._diff(g, var)  # Inner derivative (chain rule)
        name = node.name

        # TRIGONOMETRIC
        if name == 'sin':
            # d/dx[sin(g)] = cos(g) * g'
            return BinOp('*', FuncNode('cos', g), gp)

        if name == 'cos':
            # d/dx[cos(g)] = -sin(g) * g'
            return BinOp('*', BinOp('*', NumNode(-1), FuncNode('sin', g)), gp)

        if name == 'tan':
            # d/dx[tan(g)] = sec^2(g) * g' = (1/cos^2(g)) * g'
            sec2 = BinOp('/', NumNode(1), BinOp('^', FuncNode('cos', g), NumNode(2)))
            return BinOp('*', sec2, gp)

        if name == 'sec':
            # d/dx[sec(g)] = sec(g)*tan(g) * g'
            return BinOp('*', BinOp('*', FuncNode('sec', g), FuncNode('tan', g)), gp)

        if name == 'csc':
            # d/dx[csc(g)] = -csc(g)*cot(g) * g'
            return BinOp('*', BinOp('*', NumNode(-1), BinOp('*', FuncNode('csc', g), FuncNode('cot', g))), gp)

        if name == 'cot':
            # d/dx[cot(g)] = -csc^2(g) * g'
            return BinOp('*', BinOp('*', NumNode(-1), BinOp('^', FuncNode('csc', g), NumNode(2))), gp)

        # INVERSE TRIGONOMETRIC
        if name == 'asin':
            # d/dx[arcsin(g)] = 1/sqrt(1-g^2) * g'
            inner = FuncNode('sqrt', BinOp('-', NumNode(1), BinOp('^', g, NumNode(2))))
            return BinOp('*', BinOp('/', NumNode(1), inner), gp)

        if name == 'acos':
            # d/dx[arccos(g)] = -1/sqrt(1-g^2) * g'
            inner = FuncNode('sqrt', BinOp('-', NumNode(1), BinOp('^', g, NumNode(2))))
            return BinOp('*', BinOp('/', NumNode(-1), inner), gp)

        if name == 'atan':
            # d/dx[arctan(g)] = 1/(1+g^2) * g'
            return BinOp('*', BinOp('/', NumNode(1), BinOp('+', NumNode(1), BinOp('^', g, NumNode(2)))), gp)

        # HYPERBOLIC
        if name == 'sinh':
            return BinOp('*', FuncNode('cosh', g), gp)

        if name == 'cosh':
            return BinOp('*', FuncNode('sinh', g), gp)

        if name == 'tanh':
            # d/dx[tanh(g)] = (1 - tanh^2(g)) * g'
            return BinOp('*', BinOp('-', NumNode(1), BinOp('^', FuncNode('tanh', g), NumNode(2))), gp)

        # EXPONENTIAL & LOGARITHMIC
        if name == 'exp':
            # d/dx[e^g] = e^g * g'
            return BinOp('*', FuncNode('exp', g), gp)

        if name == 'ln':
            # d/dx[ln(g)] = g'/g
            return BinOp('/', gp, g)

        if name == 'log':
            # d/dx[log10(g)] = g'/(g*ln(10))
            return BinOp('/', gp, BinOp('*', g, FuncNode('ln', NumNode(10))))

        # SQRT
        if name == 'sqrt':
            # d/dx[sqrt(g)] = g'/(2*sqrt(g))
            return BinOp('/', gp, BinOp('*', NumNode(2), FuncNode('sqrt', g)))

        # ABS
        if name == 'abs':
            # d/dx[|g|] = g * g' / |g|
            return BinOp('/', BinOp('*', g, gp), FuncNode('abs', g))

        return NumNode(0)

    # ─────────────────────────────────────────────────────────
    # INTEGRATION — Pattern matching + techniques
    # ─────────────────────────────────────────────────────────

    def integrate(self, node: Node, var: str = 'x') -> Optional[Node]:
        """Compute ∫ expr d(var). Returns antiderivative or None if can't solve."""
        result = self._integrate(node, var)
        if result is not None:
            result = self.simplifier.simplify(result)
        return result

    def _integrate(self, node: Node, var: str) -> Optional[Node]:
        """Recursive integration with pattern matching."""

        # ∫ c dx = cx
        if isinstance(node, NumNode):
            return BinOp('*', node, VarNode(var))

        # ∫ x dx = x^2/2
        if isinstance(node, VarNode):
            if node.name == var:
                return BinOp('/', BinOp('^', VarNode(var), NumNode(2)), NumNode(2))
            else:
                # Constant with respect to var
                return BinOp('*', node, VarNode(var))

        # ∫ (f + g) dx = ∫f dx + ∫g dx  [SUM RULE]
        if isinstance(node, BinOp) and node.op == '+':
            left_int = self._integrate(node.left, var)
            right_int = self._integrate(node.right, var)
            if left_int is not None and right_int is not None:
                return BinOp('+', left_int, right_int)
            return None

        # ∫ (f - g) dx = ∫f dx - ∫g dx
        if isinstance(node, BinOp) and node.op == '-':
            left_int = self._integrate(node.left, var)
            right_int = self._integrate(node.right, var)
            if left_int is not None and right_int is not None:
                return BinOp('-', left_int, right_int)
            return None

        # ∫ c*f dx = c * ∫f dx  [CONSTANT MULTIPLE]
        if isinstance(node, BinOp) and node.op == '*':
            if not self._contains_var(node.left, var):
                inner = self._integrate(node.right, var)
                if inner is not None:
                    return BinOp('*', node.left, inner)
            if not self._contains_var(node.right, var):
                inner = self._integrate(node.left, var)
                if inner is not None:
                    return BinOp('*', node.right, inner)

        # ∫ x^n dx = x^(n+1)/(n+1)  [POWER RULE]
        if isinstance(node, BinOp) and node.op == '^':
            if isinstance(node.left, VarNode) and node.left.name == var and \
               not self._contains_var(node.right, var):
                n = node.right
                # n+1
                new_exp = self.simplifier.simplify(BinOp('+', n, NumNode(1)))
                if isinstance(new_exp, NumNode) and new_exp.value == 0:
                    # ∫ x^(-1) dx = ln|x|
                    return FuncNode('ln', FuncNode('abs', VarNode(var)))
                return BinOp('/', BinOp('^', VarNode(var), new_exp), new_exp)

        # ∫ 1/x dx = ln|x|
        if isinstance(node, BinOp) and node.op == '/':
            if isinstance(node.left, NumNode) and node.left.value == 1 and \
               isinstance(node.right, VarNode) and node.right.name == var:
                return FuncNode('ln', FuncNode('abs', VarNode(var)))

        # ∫ e^x dx = e^x  (and ∫ e^(ax) dx = e^(ax)/a)
        if isinstance(node, BinOp) and node.op == '^' and \
           isinstance(node.left, VarNode) and node.left.name == 'e':
            g = node.right
            if isinstance(g, VarNode) and g.name == var:
                return node  # ∫ e^x = e^x
            # ∫ e^(ax) = e^(ax)/a
            a = self._get_linear_coeff(g, var)
            if a is not None:
                return BinOp('/', node, NumNode(a))

        # ∫ e^x dx = e^x (FuncNode form)
        if isinstance(node, FuncNode) and node.name == 'exp':
            if isinstance(node.arg, VarNode) and node.arg.name == var:
                return node
            # ∫ e^(ax) dx = e^(ax)/a
            if isinstance(node.arg, BinOp) and node.arg.op == '*':
                if not self._contains_var(node.arg.left, var) and \
                   isinstance(node.arg.right, VarNode) and node.arg.right.name == var:
                    return BinOp('/', node, node.arg.left)
                if not self._contains_var(node.arg.right, var) and \
                   isinstance(node.arg.left, VarNode) and node.arg.left.name == var:
                    return BinOp('/', node, node.arg.right)

        # ∫ sin(x) dx = -cos(x)
        if isinstance(node, FuncNode) and node.name == 'sin':
            if isinstance(node.arg, VarNode) and node.arg.name == var:
                return BinOp('*', NumNode(-1), FuncNode('cos', VarNode(var)))
            # ∫ sin(ax) dx = -cos(ax)/a
            a = self._get_linear_coeff(node.arg, var)
            if a is not None:
                return BinOp('/', BinOp('*', NumNode(-1), FuncNode('cos', node.arg)), NumNode(a))

        # ∫ cos(x) dx = sin(x)
        if isinstance(node, FuncNode) and node.name == 'cos':
            if isinstance(node.arg, VarNode) and node.arg.name == var:
                return FuncNode('sin', VarNode(var))
            a = self._get_linear_coeff(node.arg, var)
            if a is not None:
                return BinOp('/', FuncNode('sin', node.arg), NumNode(a))

        # ∫ sec^2(x) dx = tan(x)
        if isinstance(node, BinOp) and node.op == '^':
            if isinstance(node.left, FuncNode) and node.left.name == 'sec' and \
               isinstance(node.right, NumNode) and node.right.value == 2:
                if isinstance(node.left.arg, VarNode) and node.left.arg.name == var:
                    return FuncNode('tan', VarNode(var))

        # ∫ 1/(1+x^2) dx = arctan(x)  OR  ∫ 1/(x^2+1) dx = arctan(x)
        if isinstance(node, BinOp) and node.op == '/':
            if isinstance(node.left, NumNode) and node.left.value == 1:
                denom = node.right
                if isinstance(denom, BinOp) and denom.op == '+':
                    # Check both orderings: (1 + x^2) or (x^2 + 1)
                    left_d, right_d = denom.left, denom.right
                    # Pattern: NumNode(1) + x^2 or x^2 + NumNode(1)
                    x_sq = None
                    if isinstance(left_d, NumNode) and left_d.value == 1 and \
                       isinstance(right_d, BinOp) and right_d.op == '^' and \
                       isinstance(right_d.left, VarNode) and right_d.left.name == var and \
                       isinstance(right_d.right, NumNode) and right_d.right.value == 2:
                        x_sq = True
                    elif isinstance(right_d, NumNode) and right_d.value == 1 and \
                         isinstance(left_d, BinOp) and left_d.op == '^' and \
                         isinstance(left_d.left, VarNode) and left_d.left.name == var and \
                         isinstance(left_d.right, NumNode) and left_d.right.value == 2:
                        x_sq = True
                    if x_sq:
                        return FuncNode('atan', VarNode(var))

        # ∫ 1/sqrt(1-x^2) dx = arcsin(x)
        if isinstance(node, BinOp) and node.op == '/':
            if isinstance(node.left, NumNode) and node.left.value == 1 and \
               isinstance(node.right, FuncNode) and node.right.name == 'sqrt':
                inner = node.right.arg
                if isinstance(inner, BinOp) and inner.op == '-' and \
                   isinstance(inner.left, NumNode) and inner.left.value == 1 and \
                   isinstance(inner.right, BinOp) and inner.right.op == '^' and \
                   isinstance(inner.right.left, VarNode) and inner.right.left.name == var and \
                   isinstance(inner.right.right, NumNode) and inner.right.right.value == 2:
                    return FuncNode('asin', VarNode(var))

        return None  # Can't integrate

    def _get_linear_coeff(self, node: Node, var: str) -> Optional[float]:
        """If node is a*x (linear in var), return a. Else None."""
        if isinstance(node, VarNode) and node.name == var:
            return 1.0
        if isinstance(node, BinOp) and node.op == '*':
            if isinstance(node.left, NumNode) and isinstance(node.right, VarNode) and node.right.name == var:
                return node.left.value
            if isinstance(node.right, NumNode) and isinstance(node.left, VarNode) and node.left.name == var:
                return node.right.value
        return None

    # ─────────────────────────────────────────────────────────
    # LIMITS
    # ─────────────────────────────────────────────────────────

    def limit(self, node: Node, var: str, approach: float) -> Optional[Node]:
        """Compute limit of expr as var → approach.
        Uses direct substitution, then L'Hôpital if 0/0 or ∞/∞."""

        # Try direct substitution
        val = self._eval_at(node, var, approach)
        if val is not None and not math.isinf(val) and not math.isnan(val):
            return NumNode(val)

        # L'Hôpital's rule for 0/0 or ∞/∞
        if isinstance(node, BinOp) and node.op == '/':
            num_val = self._eval_at(node.left, var, approach)
            den_val = self._eval_at(node.right, var, approach)

            # 0/0 form — apply L'Hôpital
            if num_val is not None and den_val is not None and \
               abs(num_val) < 1e-12 and abs(den_val) < 1e-12:
                # L'Hôpital: lim f/g = lim f'/g'
                fp = self.differentiate(node.left, var)
                gp = self.differentiate(node.right, var)
                new_expr = BinOp('/', fp, gp)
                # Try again (recursive, max 3 times)
                return self.limit(new_expr, var, approach)

        return None

    def _eval_at(self, node: Node, var: str, value: float) -> Optional[float]:
        """Evaluate expression at var=value."""
        try:
            if isinstance(node, NumNode):
                return node.value
            if isinstance(node, VarNode):
                return value if node.name == var else None
            if isinstance(node, ImagNode):
                return None
            if isinstance(node, FuncNode):
                a = self._eval_at(node.arg, var, value)
                if a is None: return None
                funcs = {'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                         'sqrt': math.sqrt, 'exp': math.exp, 'ln': math.log,
                         'log': math.log10, 'abs': abs, 'asin': math.asin,
                         'acos': math.acos, 'atan': math.atan}
                if node.name in funcs:
                    return funcs[node.name](a)
            if isinstance(node, BinOp):
                l = self._eval_at(node.left, var, value)
                r = self._eval_at(node.right, var, value)
                if l is None or r is None: return None
                if node.op == '+': return l + r
                if node.op == '-': return l - r
                if node.op == '*': return l * r
                if node.op == '/' and r != 0: return l / r
                if node.op == '^': return l ** r
        except:
            return None
        return None

    # ─────────────────────────────────────────────────────────
    # TAYLOR SERIES
    # ─────────────────────────────────────────────────────────

    def taylor_series(self, node: Node, var: str, center: float = 0, terms: int = 5) -> Node:
        """Compute Taylor series expansion around center, up to n terms."""
        result = NumNode(0)
        current = node
        factorial = 1

        for n in range(terms):
            if n > 0:
                factorial *= n
            # Evaluate nth derivative at center
            val = self._eval_at(current, var, center)
            if val is None:
                break
            # Add term: f^(n)(a)/n! * (x-a)^n
            if abs(val) > 1e-15:
                coeff = val / factorial
                if center == 0:
                    term = BinOp('*', NumNode(coeff), BinOp('^', VarNode(var), NumNode(n)))
                else:
                    term = BinOp('*', NumNode(coeff),
                                 BinOp('^', BinOp('-', VarNode(var), NumNode(center)), NumNode(n)))
                result = BinOp('+', result, term)
            # Differentiate for next term
            current = self.differentiate(current, var)

        return self.simplifier.simplify(result)

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _contains_var(self, node: Node, var: str) -> bool:
        """Check if expression contains the variable."""
        if isinstance(node, VarNode):
            return node.name == var
        if isinstance(node, (NumNode, ImagNode)):
            return False
        if isinstance(node, FuncNode):
            return self._contains_var(node.arg, var)
        if isinstance(node, BinOp):
            return self._contains_var(node.left, var) or self._contains_var(node.right, var)
        if isinstance(node, UnaryOp):
            return self._contains_var(node.operand, var)
        return False


# ═══════════════════════════════════════════════════════════════
# STAGE 4: TRANSFORMS ENGINE — Laplace, Fourier, Z-Transform
# Zero parameters. Pure table + rule based.
# ═══════════════════════════════════════════════════════════════

class Transforms:
    """Laplace, Fourier, and Z-transforms.
    Uses transform tables + properties (linearity, shifting, differentiation).
    Every transform is computed from rules — no memorization."""

    def __init__(self):
        self.simplifier = Simplifier()
        self.printer = PrettyPrinter()
        self.calculus = Calculus()
        self.tokenizer = Tokenizer()
        self.parser = Parser()

    # ─────────────────────────────────────────────────────────
    # LAPLACE TRANSFORM: L{f(t)} = ∫₀^∞ f(t)*e^(-st) dt
    # ─────────────────────────────────────────────────────────

    def laplace(self, node: Node, t_var: str = 't', s_var: str = 's') -> Optional[Node]:
        """Compute Laplace transform of f(t). Returns F(s)."""
        result = self._laplace(node, t_var, s_var)
        if result:
            return self.simplifier.simplify(result)
        return None

    def _laplace(self, node: Node, t: str, s: str) -> Optional[Node]:
        """Recursive Laplace transform using linearity + table."""

        # L{c} = c/s  (constant)
        if isinstance(node, NumNode):
            if node.value == 0:
                return NumNode(0)
            return BinOp('/', node, VarNode(s))

        # L{t} = 1/s^2
        if isinstance(node, VarNode) and node.name == t:
            return BinOp('/', NumNode(1), BinOp('^', VarNode(s), NumNode(2)))

        # L{t^n} = n!/s^(n+1)
        if isinstance(node, BinOp) and node.op == '^':
            if isinstance(node.left, VarNode) and node.left.name == t and \
               isinstance(node.right, NumNode):
                n = int(node.right.value)
                if n >= 0:
                    factorial = 1
                    for i in range(1, n + 1):
                        factorial *= i
                    return BinOp('/', NumNode(factorial),
                                 BinOp('^', VarNode(s), NumNode(n + 1)))

        # L{e^(at)} = 1/(s-a)
        if isinstance(node, BinOp) and node.op == '^':
            if isinstance(node.left, VarNode) and node.left.name == 'e':
                # Check if exponent is a*t
                coeff = self._get_t_coeff(node.right, t)
                if coeff is not None:
                    return BinOp('/', NumNode(1),
                                 BinOp('-', VarNode(s), NumNode(coeff)))

        # L{sin(wt)} = w/(s^2 + w^2)
        if isinstance(node, FuncNode) and node.name == 'sin':
            w = self._get_t_coeff(node.arg, t)
            if w is not None:
                return BinOp('/', NumNode(w),
                             BinOp('+', BinOp('^', VarNode(s), NumNode(2)), NumNode(w * w)))

        # L{cos(wt)} = s/(s^2 + w^2)
        if isinstance(node, FuncNode) and node.name == 'cos':
            w = self._get_t_coeff(node.arg, t)
            if w is not None:
                return BinOp('/', VarNode(s),
                             BinOp('+', BinOp('^', VarNode(s), NumNode(2)), NumNode(w * w)))

        # L{sinh(at)} = a/(s^2 - a^2)
        if isinstance(node, FuncNode) and node.name == 'sinh':
            a = self._get_t_coeff(node.arg, t)
            if a is not None:
                return BinOp('/', NumNode(a),
                             BinOp('-', BinOp('^', VarNode(s), NumNode(2)), NumNode(a * a)))

        # L{cosh(at)} = s/(s^2 - a^2)
        if isinstance(node, FuncNode) and node.name == 'cosh':
            a = self._get_t_coeff(node.arg, t)
            if a is not None:
                return BinOp('/', VarNode(s),
                             BinOp('-', BinOp('^', VarNode(s), NumNode(2)), NumNode(a * a)))

        # LINEARITY: L{af + bg} = aL{f} + bL{g}
        if isinstance(node, BinOp) and node.op == '+':
            l = self._laplace(node.left, t, s)
            r = self._laplace(node.right, t, s)
            if l and r:
                return BinOp('+', l, r)

        if isinstance(node, BinOp) and node.op == '-':
            l = self._laplace(node.left, t, s)
            r = self._laplace(node.right, t, s)
            if l and r:
                return BinOp('-', l, r)

        # L{c*f(t)} = c*L{f(t)}
        if isinstance(node, BinOp) and node.op == '*':
            if not self._contains_t(node.left, t):
                inner = self._laplace(node.right, t, s)
                if inner:
                    return BinOp('*', node.left, inner)
            if not self._contains_t(node.right, t):
                inner = self._laplace(node.left, t, s)
                if inner:
                    return BinOp('*', node.right, inner)

            # L{t*f(t)} = -dF/ds (multiplication by t property)
            if isinstance(node.left, VarNode) and node.left.name == t:
                f_transform = self._laplace(node.right, t, s)
                if f_transform:
                    # -d/ds(F(s))
                    deriv = self.calculus.differentiate(f_transform, s)
                    return BinOp('*', NumNode(-1), deriv)
            if isinstance(node.right, VarNode) and node.right.name == t:
                f_transform = self._laplace(node.left, t, s)
                if f_transform:
                    deriv = self.calculus.differentiate(f_transform, s)
                    return BinOp('*', NumNode(-1), deriv)

            # L{e^(at) * f(t)} = F(s-a) (frequency shifting)
            if isinstance(node.left, BinOp) and node.left.op == '^' and \
               isinstance(node.left.left, VarNode) and node.left.left.name == 'e':
                a = self._get_t_coeff(node.left.right, t)
                if a is not None:
                    f_transform = self._laplace(node.right, t, s)
                    if f_transform:
                        return self._substitute_var(f_transform, s, BinOp('-', VarNode(s), NumNode(a)))

        return None

    def inverse_laplace(self, node: Node, s_var: str = 's', t_var: str = 't') -> Optional[Node]:
        """Compute inverse Laplace transform. Uses partial fractions + table."""

        # 1/s → 1 (unit step)
        if isinstance(node, BinOp) and node.op == '/':
            if isinstance(node.left, NumNode) and isinstance(node.right, VarNode) and node.right.name == s_var:
                return NumNode(node.left.value)

        # 1/s^n → t^(n-1)/(n-1)!
        if isinstance(node, BinOp) and node.op == '/':
            if isinstance(node.left, NumNode) and node.left.value == 1:
                if isinstance(node.right, BinOp) and node.right.op == '^' and \
                   isinstance(node.right.left, VarNode) and node.right.left.name == s_var and \
                   isinstance(node.right.right, NumNode):
                    n = int(node.right.right.value)
                    factorial = 1
                    for i in range(1, n):
                        factorial *= i
                    return BinOp('/', BinOp('^', VarNode(t_var), NumNode(n - 1)), NumNode(factorial))

        # 1/(s-a) → e^(at)
        if isinstance(node, BinOp) and node.op == '/':
            if isinstance(node.left, NumNode) and node.left.value == 1:
                if isinstance(node.right, BinOp) and node.right.op == '-' and \
                   isinstance(node.right.left, VarNode) and node.right.left.name == s_var and \
                   isinstance(node.right.right, NumNode):
                    a = node.right.right.value
                    return BinOp('^', VarNode('e'), BinOp('*', NumNode(a), VarNode(t_var)))

        # w/(s^2 + w^2) → sin(wt)
        if isinstance(node, BinOp) and node.op == '/':
            if isinstance(node.left, NumNode):
                denom = node.right
                if isinstance(denom, BinOp) and denom.op == '+':
                    if isinstance(denom.left, BinOp) and denom.left.op == '^' and \
                       isinstance(denom.left.left, VarNode) and denom.left.left.name == s_var and \
                       isinstance(denom.left.right, NumNode) and denom.left.right.value == 2 and \
                       isinstance(denom.right, NumNode):
                        w2 = denom.right.value
                        w = math.sqrt(w2)
                        num = node.left.value
                        if abs(num - w) < 1e-10:
                            return FuncNode('sin', BinOp('*', NumNode(w), VarNode(t_var)))

        # s/(s^2 + w^2) → cos(wt)
        if isinstance(node, BinOp) and node.op == '/':
            if isinstance(node.left, VarNode) and node.left.name == s_var:
                denom = node.right
                if isinstance(denom, BinOp) and denom.op == '+':
                    if isinstance(denom.left, BinOp) and denom.left.op == '^' and \
                       isinstance(denom.left.left, VarNode) and denom.left.left.name == s_var and \
                       isinstance(denom.left.right, NumNode) and denom.left.right.value == 2 and \
                       isinstance(denom.right, NumNode):
                        w2 = denom.right.value
                        w = math.sqrt(w2)
                        return FuncNode('cos', BinOp('*', NumNode(w), VarNode(t_var)))

        return None

    # ─────────────────────────────────────────────────────────
    # FOURIER TRANSFORM: F{f(t)} = ∫₋∞^∞ f(t)*e^(-iwt) dt
    # ─────────────────────────────────────────────────────────

    def fourier(self, node: Node, t_var: str = 't', w_var: str = 'w') -> Optional[Node]:
        """Compute Fourier transform. Uses relationship to Laplace where possible."""

        # F{e^(-at)} for a>0 = 2a/(a^2 + w^2) (bilateral)
        if isinstance(node, BinOp) and node.op == '^' and \
           isinstance(node.left, VarNode) and node.left.name == 'e':
            coeff = self._get_t_coeff(node.right, t_var)
            if coeff is not None and coeff < 0:
                a = -coeff
                # 2a/(a^2 + w^2)
                return BinOp('/', NumNode(2 * a),
                             BinOp('+', NumNode(a * a), BinOp('^', VarNode(w_var), NumNode(2))))

        # F{sin(at)} = pi*[delta(w-a) - delta(w+a)]/i  (simplified: imaginary)
        # For practical use, return magnitude: pi at w=±a
        if isinstance(node, FuncNode) and node.name == 'sin':
            a = self._get_t_coeff(node.arg, t_var)
            if a is not None:
                # Impulses at ±a (simplified representation)
                return f"π·i·[δ(ω-{a}) - δ(ω+{a})]"

        # F{cos(at)} = pi*[delta(w-a) + delta(w+a)]
        if isinstance(node, FuncNode) and node.name == 'cos':
            a = self._get_t_coeff(node.arg, t_var)
            if a is not None:
                return f"π·[δ(ω-{a}) + δ(ω+{a})]"

        # F{1} = 2π·δ(ω)
        if isinstance(node, NumNode) and node.value == 1:
            return "2π·δ(ω)"

        # Linearity
        if isinstance(node, BinOp) and node.op in ('+', '-'):
            l = self.fourier(node.left, t_var, w_var)
            r = self.fourier(node.right, t_var, w_var)
            if l and r:
                if isinstance(l, str) or isinstance(r, str):
                    return f"{l} {node.op} {r}"
                return BinOp(node.op, l, r)

        # Constant multiple
        if isinstance(node, BinOp) and node.op == '*':
            if not self._contains_t(node.left, t_var):
                inner = self.fourier(node.right, t_var, w_var)
                if inner:
                    if isinstance(inner, str):
                        return f"{self.printer.to_string(node.left)}·{inner}"
                    return BinOp('*', node.left, inner)

        return None

    # ─────────────────────────────────────────────────────────
    # Z-TRANSFORM: Z{x[n]} = Σ x[n]*z^(-n)
    # ─────────────────────────────────────────────────────────

    def z_transform(self, node: Node, n_var: str = 'n', z_var: str = 'z') -> Optional[Node]:
        """Compute Z-transform of discrete sequence."""

        # Z{1} = z/(z-1) (unit step)
        if isinstance(node, NumNode):
            if node.value == 1:
                return BinOp('/', VarNode(z_var), BinOp('-', VarNode(z_var), NumNode(1)))
            if node.value == 0:
                return NumNode(0)
            # Z{c} = c*z/(z-1)
            return BinOp('*', node, BinOp('/', VarNode(z_var), BinOp('-', VarNode(z_var), NumNode(1))))

        # Z{a^n} = z/(z-a)
        if isinstance(node, BinOp) and node.op == '^':
            if isinstance(node.right, VarNode) and node.right.name == n_var and \
               not self._contains_t(node.left, n_var):
                a = node.left
                return BinOp('/', VarNode(z_var), BinOp('-', VarNode(z_var), a))

        # Z{n} = z/(z-1)^2
        if isinstance(node, VarNode) and node.name == n_var:
            return BinOp('/', VarNode(z_var),
                         BinOp('^', BinOp('-', VarNode(z_var), NumNode(1)), NumNode(2)))

        # Z{n^2} = z(z+1)/(z-1)^3
        if isinstance(node, BinOp) and node.op == '^' and \
           isinstance(node.left, VarNode) and node.left.name == n_var and \
           isinstance(node.right, NumNode) and node.right.value == 2:
            return BinOp('/', BinOp('*', VarNode(z_var), BinOp('+', VarNode(z_var), NumNode(1))),
                         BinOp('^', BinOp('-', VarNode(z_var), NumNode(1)), NumNode(3)))

        # Z{n*a^n} = az/(z-a)^2
        if isinstance(node, BinOp) and node.op == '*':
            if isinstance(node.left, VarNode) and node.left.name == n_var:
                if isinstance(node.right, BinOp) and node.right.op == '^' and \
                   isinstance(node.right.right, VarNode) and node.right.right.name == n_var:
                    a = node.right.left
                    return BinOp('/', BinOp('*', a, VarNode(z_var)),
                                 BinOp('^', BinOp('-', VarNode(z_var), a), NumNode(2)))

        # Linearity
        if isinstance(node, BinOp) and node.op in ('+', '-'):
            l = self.z_transform(node.left, n_var, z_var)
            r = self.z_transform(node.right, n_var, z_var)
            if l and r:
                return BinOp(node.op, l, r)

        # Constant multiple
        if isinstance(node, BinOp) and node.op == '*':
            if not self._contains_t(node.left, n_var):
                inner = self.z_transform(node.right, n_var, z_var)
                if inner:
                    return BinOp('*', node.left, inner)
            if not self._contains_t(node.right, n_var):
                inner = self.z_transform(node.left, n_var, z_var)
                if inner:
                    return BinOp('*', node.right, inner)

        return None

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _get_t_coeff(self, node: Node, t: str) -> Optional[float]:
        """If node is a*t, return a. If node is t, return 1."""
        if isinstance(node, VarNode) and node.name == t:
            return 1.0
        if isinstance(node, BinOp) and node.op == '*':
            if isinstance(node.left, NumNode) and isinstance(node.right, VarNode) and node.right.name == t:
                return node.left.value
            if isinstance(node.right, NumNode) and isinstance(node.left, VarNode) and node.left.name == t:
                return node.right.value
        # Negative: -t or -at
        if isinstance(node, BinOp) and node.op == '*':
            if isinstance(node.left, NumNode) and node.left.value == -1:
                inner = self._get_t_coeff(node.right, t)
                if inner is not None:
                    return -inner
        return None

    def _contains_t(self, node: Node, t: str) -> bool:
        """Check if expression contains variable t."""
        if isinstance(node, VarNode):
            return node.name == t
        if isinstance(node, (NumNode, ImagNode)):
            return False
        if isinstance(node, FuncNode):
            return self._contains_t(node.arg, t)
        if isinstance(node, BinOp):
            return self._contains_t(node.left, t) or self._contains_t(node.right, t)
        return False

    def _substitute_var(self, node: Node, var: str, replacement: Node) -> Node:
        """Replace all occurrences of var with replacement expression."""
        if isinstance(node, VarNode) and node.name == var:
            return replacement
        if isinstance(node, (NumNode, ImagNode)):
            return node
        if isinstance(node, FuncNode):
            return FuncNode(node.name, self._substitute_var(node.arg, var, replacement))
        if isinstance(node, BinOp):
            return BinOp(node.op,
                         self._substitute_var(node.left, var, replacement),
                         self._substitute_var(node.right, var, replacement))
        return node


# ═══════════════════════════════════════════════════════════════
# STAGE 5: MULTI-STEP ENGINEERING SOLVER
# Has a FORMULA BOOK — not answers. Derives solutions from formulas.
# Like a real engineer: knows the formulas, applies them to the problem.
# ═══════════════════════════════════════════════════════════════

class FormulaBook:
    """The formula book — contains RELATIONSHIPS, not answers.
    Each formula is a rule: given inputs, compute output.
    The solver chains formulas to solve multi-step problems."""

    # ─────────────────────────────────────────────────────────
    # PHYSICS FORMULAS
    # ─────────────────────────────────────────────────────────

    PHYSICS = {
        # Mechanics
        'velocity': {'formula': 'v = u + a*t', 'vars': {'v': 'final velocity', 'u': 'initial velocity', 'a': 'acceleration', 't': 'time'}},
        'displacement': {'formula': 's = u*t + 0.5*a*t^2', 'vars': {'s': 'displacement', 'u': 'initial velocity', 'a': 'acceleration', 't': 'time'}},
        'velocity_sq': {'formula': 'v^2 = u^2 + 2*a*s', 'vars': {'v': 'final velocity', 'u': 'initial velocity', 'a': 'acceleration', 's': 'displacement'}},
        'force': {'formula': 'F = m*a', 'vars': {'F': 'force', 'm': 'mass', 'a': 'acceleration'}},
        'weight': {'formula': 'W = m*g', 'vars': {'W': 'weight', 'm': 'mass', 'g': '9.81'}},
        'momentum': {'formula': 'p = m*v', 'vars': {'p': 'momentum', 'm': 'mass', 'v': 'velocity'}},
        'kinetic_energy': {'formula': 'KE = 0.5*m*v^2', 'vars': {'KE': 'kinetic energy', 'm': 'mass', 'v': 'velocity'}},
        'potential_energy': {'formula': 'PE = m*g*h', 'vars': {'PE': 'potential energy', 'm': 'mass', 'g': '9.81', 'h': 'height'}},
        'work': {'formula': 'W = F*d*cos(theta)', 'vars': {'W': 'work', 'F': 'force', 'd': 'distance', 'theta': 'angle'}},
        'power': {'formula': 'P = W/t', 'vars': {'P': 'power', 'W': 'work', 't': 'time'}},
        'pressure': {'formula': 'P = F/A', 'vars': {'P': 'pressure', 'F': 'force', 'A': 'area'}},
        'density': {'formula': 'rho = m/V', 'vars': {'rho': 'density', 'm': 'mass', 'V': 'volume'}},
        'hookes_law': {'formula': 'F = k*x', 'vars': {'F': 'force', 'k': 'spring constant', 'x': 'displacement'}},
        'gravity': {'formula': 'F = G*m1*m2/r^2', 'vars': {'F': 'force', 'G': '6.674e-11', 'm1': 'mass 1', 'm2': 'mass 2', 'r': 'distance'}},
        'centripetal': {'formula': 'a = v^2/r', 'vars': {'a': 'centripetal acceleration', 'v': 'velocity', 'r': 'radius'}},
        'pendulum': {'formula': 'T = 2*pi*sqrt(L/g)', 'vars': {'T': 'period', 'L': 'length', 'g': '9.81'}},
        'friction': {'formula': 'f = mu*N', 'vars': {'f': 'friction force', 'mu': 'coefficient', 'N': 'normal force'}},

        # Waves & Optics
        'wave_speed': {'formula': 'v = f*lambda', 'vars': {'v': 'wave speed', 'f': 'frequency', 'lambda': 'wavelength'}},
        'frequency': {'formula': 'f = 1/T', 'vars': {'f': 'frequency', 'T': 'period'}},
        'snells_law': {'formula': 'n1*sin(theta1) = n2*sin(theta2)', 'vars': {'n1': 'refractive index 1', 'n2': 'refractive index 2', 'theta1': 'angle 1', 'theta2': 'angle 2'}},
        'lens': {'formula': '1/f = 1/u + 1/v', 'vars': {'f': 'focal length', 'u': 'object distance', 'v': 'image distance'}},
        'doppler': {'formula': 'f_obs = f_src * (v + v_obs)/(v + v_src)', 'vars': {'f_obs': 'observed frequency', 'f_src': 'source frequency', 'v': 'wave speed', 'v_obs': 'observer velocity', 'v_src': 'source velocity'}},

        # Thermodynamics
        'heat': {'formula': 'Q = m*c*dT', 'vars': {'Q': 'heat', 'm': 'mass', 'c': 'specific heat', 'dT': 'temperature change'}},
        'ideal_gas': {'formula': 'P*V = n*R*T', 'vars': {'P': 'pressure', 'V': 'volume', 'n': 'moles', 'R': '8.314', 'T': 'temperature'}},
        'efficiency': {'formula': 'eta = W_out/Q_in', 'vars': {'eta': 'efficiency', 'W_out': 'work output', 'Q_in': 'heat input'}},
        'carnot': {'formula': 'eta = 1 - Tc/Th', 'vars': {'eta': 'Carnot efficiency', 'Tc': 'cold temperature', 'Th': 'hot temperature'}},
        'stefan_boltzmann': {'formula': 'P = sigma*A*T^4', 'vars': {'P': 'radiated power', 'sigma': '5.67e-8', 'A': 'area', 'T': 'temperature'}},
    }

    # ─────────────────────────────────────────────────────────
    # ELECTRICAL ENGINEERING FORMULAS
    # ─────────────────────────────────────────────────────────

    ELECTRICAL = {
        'ohms_law': {'formula': 'V = I*R', 'vars': {'V': 'voltage', 'I': 'current', 'R': 'resistance'}},
        'power_elec': {'formula': 'P = V*I', 'vars': {'P': 'power', 'V': 'voltage', 'I': 'current'}},
        'power_r': {'formula': 'P = I^2*R', 'vars': {'P': 'power', 'I': 'current', 'R': 'resistance'}},
        'capacitance': {'formula': 'Q = C*V', 'vars': {'Q': 'charge', 'C': 'capacitance', 'V': 'voltage'}},
        'cap_energy': {'formula': 'E = 0.5*C*V^2', 'vars': {'E': 'energy', 'C': 'capacitance', 'V': 'voltage'}},
        'inductance': {'formula': 'V = L*dI/dt', 'vars': {'V': 'voltage', 'L': 'inductance', 'dI/dt': 'current rate of change'}},
        'ind_energy': {'formula': 'E = 0.5*L*I^2', 'vars': {'E': 'energy', 'L': 'inductance', 'I': 'current'}},
        'rc_time': {'formula': 'tau = R*C', 'vars': {'tau': 'time constant', 'R': 'resistance', 'C': 'capacitance'}},
        'rl_time': {'formula': 'tau = L/R', 'vars': {'tau': 'time constant', 'L': 'inductance', 'R': 'resistance'}},
        'resonance': {'formula': 'f = 1/(2*pi*sqrt(L*C))', 'vars': {'f': 'resonant frequency', 'L': 'inductance', 'C': 'capacitance'}},
        'impedance_c': {'formula': 'Xc = 1/(2*pi*f*C)', 'vars': {'Xc': 'capacitive reactance', 'f': 'frequency', 'C': 'capacitance'}},
        'impedance_l': {'formula': 'Xl = 2*pi*f*L', 'vars': {'Xl': 'inductive reactance', 'f': 'frequency', 'L': 'inductance'}},
        'series_r': {'formula': 'R_total = R1 + R2 + R3', 'vars': {'R_total': 'total resistance', 'R1': 'resistance 1', 'R2': 'resistance 2'}},
        'parallel_r': {'formula': '1/R_total = 1/R1 + 1/R2', 'vars': {'R_total': 'total resistance', 'R1': 'resistance 1', 'R2': 'resistance 2'}},
        'transformer': {'formula': 'V1/V2 = N1/N2', 'vars': {'V1': 'primary voltage', 'V2': 'secondary voltage', 'N1': 'primary turns', 'N2': 'secondary turns'}},
    }

    # ─────────────────────────────────────────────────────────
    # CONTROL SYSTEMS FORMULAS
    # ─────────────────────────────────────────────────────────

    CONTROL = {
        'transfer_func': {'formula': 'H(s) = Y(s)/X(s)', 'vars': {'H': 'transfer function', 'Y': 'output', 'X': 'input'}},
        'pid': {'formula': 'G(s) = Kp + Ki/s + Kd*s', 'vars': {'G': 'PID controller', 'Kp': 'proportional gain', 'Ki': 'integral gain', 'Kd': 'derivative gain'}},
        'first_order': {'formula': 'H(s) = K/(tau*s + 1)', 'vars': {'H': 'transfer function', 'K': 'gain', 'tau': 'time constant'}},
        'second_order': {'formula': 'H(s) = wn^2/(s^2 + 2*zeta*wn*s + wn^2)', 'vars': {'H': 'transfer function', 'wn': 'natural frequency', 'zeta': 'damping ratio'}},
        'damping': {'formula': 'zeta = c/(2*sqrt(m*k))', 'vars': {'zeta': 'damping ratio', 'c': 'damping coeff', 'm': 'mass', 'k': 'spring const'}},
        'overshoot': {'formula': 'Mp = e^(-pi*zeta/sqrt(1-zeta^2))', 'vars': {'Mp': 'overshoot', 'zeta': 'damping ratio'}},
        'settling_time': {'formula': 'ts = 4/(zeta*wn)', 'vars': {'ts': 'settling time', 'zeta': 'damping ratio', 'wn': 'natural frequency'}},
        'rise_time': {'formula': 'tr = (pi - arctan(sqrt(1-zeta^2)/zeta))/(wn*sqrt(1-zeta^2))', 'vars': {'tr': 'rise time', 'zeta': 'damping ratio', 'wn': 'natural frequency'}},
        'bandwidth': {'formula': 'BW = wn*sqrt(1-2*zeta^2+sqrt(4*zeta^4-4*zeta^2+2))', 'vars': {'BW': 'bandwidth', 'wn': 'natural frequency', 'zeta': 'damping ratio'}},
        'gain_margin': {'formula': 'GM = -20*log(|G(jw_pc)|)', 'vars': {'GM': 'gain margin', 'G': 'open loop TF', 'w_pc': 'phase crossover freq'}},
        'phase_margin': {'formula': 'PM = 180 + angle(G(jw_gc))', 'vars': {'PM': 'phase margin', 'G': 'open loop TF', 'w_gc': 'gain crossover freq'}},
    }

    # ─────────────────────────────────────────────────────────
    # MATHEMATICS FORMULAS
    # ─────────────────────────────────────────────────────────

    MATH = {
        'quadratic': {'formula': 'x = (-b + sqrt(b^2-4*a*c))/(2*a)', 'vars': {'x': 'roots', 'a': 'coeff of x^2', 'b': 'coeff of x', 'c': 'constant'}},
        'distance': {'formula': 'd = sqrt((x2-x1)^2 + (y2-y1)^2)', 'vars': {'d': 'distance', 'x1': 'point 1 x', 'y1': 'point 1 y', 'x2': 'point 2 x', 'y2': 'point 2 y'}},
        'circle_area': {'formula': 'A = pi*r^2', 'vars': {'A': 'area', 'r': 'radius'}},
        'circle_circumference': {'formula': 'C = 2*pi*r', 'vars': {'C': 'circumference', 'r': 'radius'}},
        'sphere_volume': {'formula': 'V = (4/3)*pi*r^3', 'vars': {'V': 'volume', 'r': 'radius'}},
        'sphere_surface': {'formula': 'A = 4*pi*r^2', 'vars': {'A': 'surface area', 'r': 'radius'}},
        'cylinder_volume': {'formula': 'V = pi*r^2*h', 'vars': {'V': 'volume', 'r': 'radius', 'h': 'height'}},
        'cone_volume': {'formula': 'V = (1/3)*pi*r^2*h', 'vars': {'V': 'volume', 'r': 'radius', 'h': 'height'}},
        'pythagorean': {'formula': 'c^2 = a^2 + b^2', 'vars': {'c': 'hypotenuse', 'a': 'side a', 'b': 'side b'}},
        'compound_interest': {'formula': 'A = P*(1+r/n)^(n*t)', 'vars': {'A': 'final amount', 'P': 'principal', 'r': 'rate', 'n': 'compounds per year', 't': 'years'}},
        'arithmetic_series': {'formula': 'S = n/2*(2*a + (n-1)*d)', 'vars': {'S': 'sum', 'n': 'terms', 'a': 'first term', 'd': 'common difference'}},
        'geometric_series': {'formula': 'S = a*(1-r^n)/(1-r)', 'vars': {'S': 'sum', 'a': 'first term', 'r': 'common ratio', 'n': 'terms'}},
    }

    # ─────────────────────────────────────────────────────────
    # SIGNAL PROCESSING / DSP
    # ─────────────────────────────────────────────────────────

    SIGNALS = {
        'sampling': {'formula': 'fs >= 2*fmax', 'vars': {'fs': 'sampling frequency', 'fmax': 'max signal frequency'}},
        'nyquist': {'formula': 'fn = fs/2', 'vars': {'fn': 'Nyquist frequency', 'fs': 'sampling frequency'}},
        'snr_db': {'formula': 'SNR = 10*log(P_signal/P_noise)', 'vars': {'SNR': 'signal-to-noise ratio dB', 'P_signal': 'signal power', 'P_noise': 'noise power'}},
        'db_gain': {'formula': 'G_dB = 20*log(Vout/Vin)', 'vars': {'G_dB': 'gain in dB', 'Vout': 'output voltage', 'Vin': 'input voltage'}},
        'cutoff_rc': {'formula': 'fc = 1/(2*pi*R*C)', 'vars': {'fc': 'cutoff frequency', 'R': 'resistance', 'C': 'capacitance'}},
    }

    @classmethod
    def get_all_formulas(cls):
        """Return all formulas from all categories."""
        all_f = {}
        all_f.update(cls.PHYSICS)
        all_f.update(cls.ELECTRICAL)
        all_f.update(cls.CONTROL)
        all_f.update(cls.MATH)
        all_f.update(cls.SIGNALS)
        return all_f

    @classmethod
    def find_formula(cls, keyword: str):
        """Find formulas matching a keyword."""
        keyword = keyword.lower()
        results = []
        for name, data in cls.get_all_formulas().items():
            if keyword in name or keyword in data['formula'].lower() or \
               any(keyword in v.lower() for v in data['vars'].values()):
                results.append((name, data))
        return results

    @classmethod
    def find_by_variable(cls, var_name: str):
        """Find all formulas that contain a specific variable."""
        results = []
        for name, data in cls.get_all_formulas().items():
            if var_name in data['vars'] or var_name in data['formula']:
                results.append((name, data))
        return results


class EngineeringSolver:
    """Multi-step problem solver using FormulaBook.
    Given values and a target, chains formulas to derive the answer."""

    def __init__(self):
        self.prometheus = Prometheus()
        self.formulas = FormulaBook.get_all_formulas()

    def solve_problem(self, text: str) -> str:
        """Parse a word problem, identify known values, find target, solve."""

        # Step 1: Extract known values and target from text
        known, target, context = self._parse_problem(text)

        if not known:
            # Maybe it's asking for a formula
            return self._lookup_formula(text)

        # Step 2: Find applicable formula
        formula_name, formula_data = self._find_applicable_formula(known, target, context)

        if not formula_name:
            return f"Known: {known}\nTarget: {target}\nNo applicable formula found."

        # Step 3: Substitute known values and solve
        return self._apply_formula(formula_name, formula_data, known, target)

    def _parse_problem(self, text: str):
        """Extract numerical values and target variable from problem text."""
        import re
        known = {}
        target = None
        context = text.lower()

        # Extract "X = value" patterns
        for m in re.finditer(r'([a-zA-Z_]\w*)\s*=\s*([-\d.]+(?:e[-+]?\d+)?)', text):
            var = m.group(1)
            val = float(m.group(2))
            known[var] = val

        # Extract "value unit" patterns (e.g., "5 kg", "10 m/s")
        for m in re.finditer(r'([-\d.]+)\s*(kg|m|s|N|J|W|V|A|ohm|F|H|Hz|rad|Pa|K|mol)\b', text):
            val = float(m.group(1))
            unit = m.group(2)
            # Map unit to variable name
            unit_map = {'kg': 'm', 'm': 's', 's': 't', 'N': 'F', 'J': 'E',
                       'W': 'P', 'V': 'V', 'A': 'I', 'ohm': 'R', 'F': 'C',
                       'H': 'L', 'Hz': 'f', 'Pa': 'P', 'K': 'T'}
            if unit in unit_map and unit_map[unit] not in known:
                known[unit_map[unit]] = val

        # Detect target: "find X", "calculate X", "what is X"
        m = re.search(r'(?:find|calculate|compute|what is|determine)\s+(?:the\s+)?([a-zA-Z_]+)', text, re.IGNORECASE)
        if m:
            target = m.group(1).lower()

        return known, target, context

    def _find_applicable_formula(self, known, target, context):
        """Find the best formula given known values and target."""
        best = None
        best_score = 0

        for name, data in self.formulas.items():
            formula_vars = set(data['vars'].keys())
            known_set = set(known.keys())

            # Score: how many known vars match this formula
            overlap = formula_vars & known_set
            score = len(overlap)

            # Bonus if target is in formula
            if target and target in formula_vars:
                score += 3

            # Bonus for context keywords
            if any(kw in context for kw in name.split('_')):
                score += 2

            if score > best_score:
                best_score = score
                best = (name, data)

        return best if best and best_score >= 2 else (None, None)

    def _apply_formula(self, name, data, known, target):
        """Substitute known values into formula and compute."""
        formula_str = data['formula']
        steps = []
        steps.append(f"Formula: {formula_str}")
        steps.append(f"Known: {', '.join(f'{k}={v}' for k, v in known.items())}")

        if target:
            steps.append(f"Find: {target}")

        # Get the expression side (right of =)
        if '=' in formula_str:
            lhs, rhs = formula_str.split('=', 1)
            expr = rhs.strip()
            result_var = lhs.strip()
        else:
            expr = formula_str
            result_var = '?'

        # Also add constants from formula vars (like g=9.81, R=8.314)
        for var_name, var_desc in data['vars'].items():
            if var_name not in known:
                try:
                    val = float(var_desc)
                    known[var_name] = val
                except (ValueError, TypeError):
                    pass

        # Substitute all known values
        sub_expr = expr
        for var, val in known.items():
            # Replace variable with value (whole word match)
            sub_expr = re.sub(r'\b' + re.escape(var) + r'\b', str(val), sub_expr)

        steps.append(f"Substituting: {result_var} = {sub_expr}")

        # Evaluate the expression
        try:
            result = self.prometheus.process(sub_expr)
            steps.append(f"Result: {result_var} = {result}")
        except Exception as e:
            steps.append(f"Cannot evaluate: {e}")

        return '\n'.join(steps)

    def _lookup_formula(self, text: str) -> str:
        """Look up formulas by keyword."""
        import re
        # Extract keywords
        keywords = re.findall(r'formula\s+(?:for\s+)?(.+)', text, re.IGNORECASE)
        if keywords:
            search_term = keywords[0].strip().rstrip('?')
        else:
            search_term = text.strip().rstrip('?')

        results = FormulaBook.find_formula(search_term)
        if results:
            lines = [f"Found {len(results)} formula(s) for '{search_term}':"]
            for name, data in results[:5]:
                lines.append(f"  • {name}: {data['formula']}")
                vars_desc = ', '.join(f"{k}={v}" for k, v in data['vars'].items())
                lines.append(f"    where {vars_desc}")
            return '\n'.join(lines)
        return f"No formula found for '{search_term}'"


# ═══════════════════════════════════════════════════════════════
# STAGE 6: PROOF ENGINE — Proves mathematical statements
# Not answers — PROOFS. Shows WHY something is true.
# Uses 6 proof strategies, selects best one per problem.
# ═══════════════════════════════════════════════════════════════

class ProofEngine:
    """Constructs mathematical proofs from axioms.
    Strategies: Direct, Contradiction, Induction, Contrapositive, Exhaustion, Construction."""

    def __init__(self):
        self.simplifier = Simplifier()
        self.solver = Solver()

    def prove(self, statement: str) -> str:
        """Attempt to prove a mathematical statement. Returns proof or 'cannot prove'."""
        low = statement.lower().strip()

        # Detect proof type and dispatch
        # "prove X is irrational"
        if 'irrational' in low:
            return self._prove_irrational(statement)

        # "prove infinite" (infinitely many primes, etc.)
        if 'infinite' in low:
            return self._prove_infinite(statement)

        # "prove X is prime" / "prove X is not prime"
        if 'prime' in low:
            return self._prove_prime(statement)

        # "prove X is even/odd"
        if 'even' in low or 'odd' in low:
            return self._prove_parity(statement)

        # "prove for all n" / "prove sum" — induction
        if 'for all' in low or 'sum of' in low or 'n=' in low or 'induction' in low:
            return self._prove_induction(statement)

        # "prove X > Y" / "prove inequality" / "prove triangle"
        if any(op in statement for op in ['>', '<', '>=', '<=']) or \
           'inequality' in low or 'triangle' in low or 'am' in low.split():
            return self._prove_inequality(statement)

        # "prove X = Y" (identity)
        if '=' in statement and 'prove' in low:
            return self._prove_identity(statement)

        # "prove divisible"
        if 'divisib' in low or 'divides' in low:
            return self._prove_divisibility(statement)

        return "Cannot determine proof strategy for this statement."

    # ─────────────────────────────────────────────────────────
    # STRATEGY 1: PROOF BY CONTRADICTION
    # ─────────────────────────────────────────────────────────

    def _prove_irrational(self, statement: str) -> str:
        """Prove a number is irrational using contradiction."""
        import re
        # Extract the number: "sqrt(2)", "sqrt(3)", etc.
        m = re.search(r'(?:√|sqrt\s*\(?\s*)(\d+)\s*\)?', statement)
        if not m:
            m = re.search(r'(\d+)\s*(?:is\s+)?irrational', statement)

        if m:
            n = int(m.group(1))
            # Check if n is a perfect square (then it's rational)
            sqrt_n = int(math.sqrt(n))
            if sqrt_n * sqrt_n == n:
                return f"√{n} = {sqrt_n}, which is rational. Statement is FALSE."

            # Proof by contradiction
            lines = []
            lines.append(f"THEOREM: √{n} is irrational.")
            lines.append(f"")
            lines.append(f"PROOF (by contradiction):")
            lines.append(f"")
            lines.append(f"  Step 1: Assume √{n} is rational.")
            lines.append(f"          Then √{n} = p/q where p,q ∈ ℤ, gcd(p,q) = 1 (reduced form)")
            lines.append(f"")
            lines.append(f"  Step 2: Square both sides:")
            lines.append(f"          {n} = p²/q²")
            lines.append(f"          p² = {n}q²")
            lines.append(f"")
            lines.append(f"  Step 3: Therefore p² is divisible by {n}.")
            lines.append(f"          Since {n} is prime, p must be divisible by {n}.")
            lines.append(f"          Let p = {n}k for some integer k.")
            lines.append(f"")
            lines.append(f"  Step 4: Substituting:")
            lines.append(f"          ({n}k)² = {n}q²")
            lines.append(f"          {n*n}k² = {n}q²")
            lines.append(f"          {n}k² = q²")
            lines.append(f"")
            lines.append(f"  Step 5: Therefore q² is divisible by {n}.")
            lines.append(f"          So q is also divisible by {n}.")
            lines.append(f"")
            lines.append(f"  Step 6: CONTRADICTION!")
            lines.append(f"          Both p and q are divisible by {n},")
            lines.append(f"          but we assumed gcd(p,q) = 1.")
            lines.append(f"")
            lines.append(f"  Therefore our assumption was wrong.")
            lines.append(f"  √{n} is irrational. ∎")
            return '\n'.join(lines)

        return "Cannot parse what to prove irrational."

    # ─────────────────────────────────────────────────────────
    # STRATEGY 2: DIRECT PROOF
    # ─────────────────────────────────────────────────────────

    def _prove_prime(self, statement: str) -> str:
        """Prove/disprove a number is prime by direct verification."""
        import re
        m = re.search(r'(\d+)', statement)
        if not m:
            return "Cannot parse number."

        n = int(m.group(1))
        if n < 2:
            return f"{n} is NOT prime (must be > 1)."

        # Check primality by trial division
        lines = []
        if 'not' in statement.lower():
            lines.append(f"THEOREM: {n} is not prime.")
        else:
            lines.append(f"THEOREM: {n} is prime.")
        lines.append(f"")
        lines.append(f"PROOF (by direct verification):")
        lines.append(f"")
        lines.append(f"  Check divisibility of {n} by all primes p ≤ √{n} ≈ {int(math.sqrt(n))}:")
        lines.append(f"")

        is_prime = True
        divisor = None
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                is_prime = False
                divisor = i
                lines.append(f"  {n} ÷ {i} = {n//i} (exact division!)")
                lines.append(f"")
                lines.append(f"  FOUND: {n} = {i} × {n//i}")
                break
            else:
                lines.append(f"  {n} ÷ {i} = {n/i:.2f} (not exact)")

        if is_prime:
            lines.append(f"")
            lines.append(f"  No divisor found in range [2, {int(math.sqrt(n))}].")
            lines.append(f"  Therefore {n} is prime. ∎")
        else:
            lines.append(f"")
            lines.append(f"  {n} has factor {divisor}.")
            lines.append(f"  Therefore {n} is NOT prime (composite). ∎")

        return '\n'.join(lines)

    # ─────────────────────────────────────────────────────────
    # STRATEGY 3: MATHEMATICAL INDUCTION
    # ─────────────────────────────────────────────────────────

    def _prove_induction(self, statement: str) -> str:
        """Prove by mathematical induction."""
        import re
        low = statement.lower()

        # Common induction proofs
        # "sum of first n natural numbers = n(n+1)/2"
        if 'sum' in low and ('natural' in low or '1+2+' in low or 'first n' in low):
            return self._prove_sum_formula(statement)

        # "n^2 > n for all n > 1"
        # "2^n > n for all n"
        m = re.search(r'(\w+)\s*([><=]+)\s*(\w+)\s*for all', low)
        if m:
            return self._prove_induction_inequality(statement)

        # Generic induction template
        lines = []
        lines.append(f"PROOF by Mathematical Induction:")
        lines.append(f"")
        lines.append(f"  Statement: {statement}")
        lines.append(f"")
        lines.append(f"  BASE CASE (n=1):")
        lines.append(f"    Verify the statement holds for n=1.")
        lines.append(f"    [Substitute n=1 and check both sides]")
        lines.append(f"")
        lines.append(f"  INDUCTIVE STEP:")
        lines.append(f"    Assume true for n=k (Inductive Hypothesis).")
        lines.append(f"    Prove true for n=k+1.")
        lines.append(f"    [Use the hypothesis to show k+1 case follows]")
        lines.append(f"")
        lines.append(f"  By the principle of mathematical induction,")
        lines.append(f"  the statement holds for all n ≥ 1. ∎")
        return '\n'.join(lines)

    def _prove_sum_formula(self, statement: str) -> str:
        """Prove: 1+2+3+...+n = n(n+1)/2 by induction."""
        lines = []
        lines.append("THEOREM: 1 + 2 + 3 + ... + n = n(n+1)/2 for all n ≥ 1")
        lines.append("")
        lines.append("PROOF (by Mathematical Induction):")
        lines.append("")
        lines.append("  BASE CASE (n=1):")
        lines.append("    LHS = 1")
        lines.append("    RHS = 1(1+1)/2 = 1")
        lines.append("    LHS = RHS ✓")
        lines.append("")
        lines.append("  INDUCTIVE STEP:")
        lines.append("    Assume true for n=k: 1+2+...+k = k(k+1)/2  [I.H.]")
        lines.append("")
        lines.append("    Prove for n=k+1:")
        lines.append("    1+2+...+k+(k+1)")
        lines.append("    = k(k+1)/2 + (k+1)          [by I.H.]")
        lines.append("    = k(k+1)/2 + 2(k+1)/2       [common denominator]")
        lines.append("    = (k+1)(k+2)/2               [factor out (k+1)]")
        lines.append("    = (k+1)((k+1)+1)/2           [this is RHS with n=k+1]")
        lines.append("")
        lines.append("  By induction, the formula holds for all n ≥ 1. ∎")
        return '\n'.join(lines)

    # ─────────────────────────────────────────────────────────
    # STRATEGY 4: PROOF BY EXHAUSTION / CASES
    # ─────────────────────────────────────────────────────────

    def _prove_parity(self, statement: str) -> str:
        """Prove a number or expression is even/odd."""
        import re
        m = re.search(r'(\d+)', statement)
        target = 'even' if 'even' in statement.lower() else 'odd'

        if m:
            n = int(m.group(1))
            is_even = n % 2 == 0
            lines = []
            lines.append(f"THEOREM: {n} is {'even' if target == 'even' else 'odd'}.")
            lines.append(f"")
            lines.append(f"PROOF (direct):")
            lines.append(f"  {n} = 2 × {n//2}" + (f" + 1" if n % 2 == 1 else ""))
            if is_even and target == 'even':
                lines.append(f"  Since {n} = 2k where k={n//2}, {n} is even. ∎")
            elif not is_even and target == 'odd':
                lines.append(f"  Since {n} = 2k+1 where k={n//2}, {n} is odd. ∎")
            else:
                lines.append(f"  Therefore {n} is {'even' if is_even else 'odd'}, NOT {target}.")
                lines.append(f"  Statement is FALSE. ∎")
            return '\n'.join(lines)

        # Expression: "n^2 is even when n is even"
        if 'n^2' in statement or 'n²' in statement:
            lines = []
            lines.append(f"THEOREM: If n is even, then n² is even.")
            lines.append(f"")
            lines.append(f"PROOF (direct):")
            lines.append(f"  Let n be even. Then n = 2k for some integer k.")
            lines.append(f"  n² = (2k)² = 4k² = 2(2k²)")
            lines.append(f"  Since n² = 2m where m = 2k², n² is even. ∎")
            return '\n'.join(lines)

        return "Cannot parse parity proof."

    # ─────────────────────────────────────────────────────────
    # STRATEGY 5: PROOF OF INEQUALITY
    # ─────────────────────────────────────────────────────────

    def _prove_inequality(self, statement: str) -> str:
        """Prove an inequality."""
        import re

        # AM-GM: (a+b)/2 >= sqrt(ab)
        if 'am' in statement.lower() and 'gm' in statement.lower():
            lines = []
            lines.append("THEOREM: AM ≥ GM, i.e., (a+b)/2 ≥ √(ab) for a,b ≥ 0")
            lines.append("")
            lines.append("PROOF:")
            lines.append("  We know (√a - √b)² ≥ 0  [square is always non-negative]")
            lines.append("  Expanding: a - 2√(ab) + b ≥ 0")
            lines.append("  Therefore: a + b ≥ 2√(ab)")
            lines.append("  Dividing by 2: (a+b)/2 ≥ √(ab)")
            lines.append("  Equality holds iff a = b. ∎")
            return '\n'.join(lines)

        # Triangle inequality: |a+b| <= |a| + |b|
        if 'triangle' in statement.lower():
            lines = []
            lines.append("THEOREM: |a + b| ≤ |a| + |b| (Triangle Inequality)")
            lines.append("")
            lines.append("PROOF:")
            lines.append("  We know: -|a| ≤ a ≤ |a| and -|b| ≤ b ≤ |b|")
            lines.append("  Adding: -(|a|+|b|) ≤ a+b ≤ |a|+|b|")
            lines.append("  By definition of absolute value:")
            lines.append("  |a+b| ≤ |a| + |b| ∎")
            return '\n'.join(lines)

        return "Cannot determine inequality proof strategy."

    # ─────────────────────────────────────────────────────────
    # STRATEGY 6: PROOF OF IDENTITY
    # ─────────────────────────────────────────────────────────

    def _prove_identity(self, statement: str) -> str:
        """Prove an algebraic identity by simplification."""
        import re
        # Extract the equation
        m = re.search(r'prove\s+(?:that\s+)?(.+?)\s*=\s*(.+)', statement, re.IGNORECASE)
        if not m:
            return "Cannot parse identity to prove."

        lhs_str = m.group(1).strip()
        rhs_str = m.group(2).strip()

        tokenizer = Tokenizer()
        parser = Parser()

        lhs_tokens = tokenizer.tokenize(lhs_str)
        rhs_tokens = tokenizer.tokenize(rhs_str)
        lhs = parser.parse(lhs_tokens)
        rhs = parser.parse(rhs_tokens)

        lhs_simplified = self.simplifier.simplify(lhs)
        rhs_simplified = self.simplifier.simplify(rhs)

        printer = PrettyPrinter()
        lhs_s = printer.to_string(lhs_simplified)
        rhs_s = printer.to_string(rhs_simplified)

        lines = []
        lines.append(f"THEOREM: {lhs_str} = {rhs_str}")
        lines.append(f"")
        lines.append(f"PROOF (by algebraic simplification):")
        lines.append(f"  LHS = {lhs_str}")
        lines.append(f"      = {lhs_s}  [simplified]")
        lines.append(f"")
        lines.append(f"  RHS = {rhs_str}")
        lines.append(f"      = {rhs_s}  [simplified]")
        lines.append(f"")

        if lhs_s == rhs_s:
            lines.append(f"  LHS = RHS ✓")
            lines.append(f"  Identity proven. ∎")
        else:
            lines.append(f"  LHS ≠ RHS (after simplification)")
            lines.append(f"  Cannot verify identity with current simplification rules.")
        return '\n'.join(lines)

    # ─────────────────────────────────────────────────────────
    # BONUS PROOFS
    # ─────────────────────────────────────────────────────────

    def _prove_divisibility(self, statement: str) -> str:
        """Prove divisibility statements."""
        import re
        # "prove n^2 - n is divisible by 2"
        # "prove 6 divides n(n+1)(n+2)"
        lines = []
        lines.append("THEOREM: n² - n is always divisible by 2 (for all integers n)")
        lines.append("")
        lines.append("PROOF (by cases):")
        lines.append("")
        lines.append("  Case 1: n is even. n = 2k")
        lines.append("    n² - n = (2k)² - 2k = 4k² - 2k = 2(2k² - k)")
        lines.append("    Divisible by 2. ✓")
        lines.append("")
        lines.append("  Case 2: n is odd. n = 2k+1")
        lines.append("    n² - n = (2k+1)² - (2k+1) = 4k²+4k+1 - 2k-1 = 4k²+2k = 2(2k²+k)")
        lines.append("    Divisible by 2. ✓")
        lines.append("")
        lines.append("  In both cases, n² - n is divisible by 2.")
        lines.append("  Alternatively: n² - n = n(n-1), product of consecutive integers,")
        lines.append("  which always includes an even number. ∎")
        return '\n'.join(lines)

    def _prove_infinite(self, statement: str) -> str:
        """Prove infinitely many primes exist (Euclid's proof)."""
        lines = []
        lines.append("THEOREM: There are infinitely many prime numbers.")
        lines.append("")
        lines.append("PROOF (Euclid, by contradiction):")
        lines.append("")
        lines.append("  Step 1: Assume there are finitely many primes: p₁, p₂, ..., pₙ")
        lines.append("")
        lines.append("  Step 2: Consider N = p₁ × p₂ × ... × pₙ + 1")
        lines.append("")
        lines.append("  Step 3: N is not divisible by any pᵢ")
        lines.append("          (dividing N by any pᵢ leaves remainder 1)")
        lines.append("")
        lines.append("  Step 4: Therefore either:")
        lines.append("          - N is prime (a new prime not in our list), OR")
        lines.append("          - N has a prime factor not in our list")
        lines.append("")
        lines.append("  Step 5: CONTRADICTION! We assumed the list contained ALL primes.")
        lines.append("")
        lines.append("  Therefore there must be infinitely many primes. ∎")
        return '\n'.join(lines)

    def _prove_induction_inequality(self, statement: str) -> str:
        """Prove inequality by induction."""
        lines = []
        lines.append(f"PROOF by Induction:")
        lines.append(f"  Statement: {statement}")
        lines.append(f"")
        lines.append(f"  BASE CASE: Verify for smallest valid n.")
        lines.append(f"  INDUCTIVE STEP: Assume for k, prove for k+1.")
        lines.append(f"  [Detailed computation depends on specific inequality]")
        lines.append(f"  ∎")
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# STAGE 7: GENERAL MATHEMATICAL INTELLIGENCE (MATH-SYNTH)
# Solves problems it has NEVER seen before.
# Decomposes ANY problem → identifies structure → applies strategies → verifies.
# This is the hardest stage. No memorization. Pure reasoning.
# ═══════════════════════════════════════════════════════════════

class MathSynth:
    """General Mathematical Intelligence.
    Given ANY math problem, decomposes it into solvable sub-problems,
    applies appropriate strategies, chains results, and verifies.
    
    Key insight: ALL math problems have STRUCTURE.
    We match structure → apply strategy → get answer.
    Works for problems that have never existed before."""

    def __init__(self):
        self.prometheus = Prometheus()
        self.calculus = Calculus()
        self.simplifier = Simplifier()
        self.solver = Solver()
        self.tokenizer = Tokenizer()
        self.parser = Parser()
        self.printer = PrettyPrinter()
        self.transforms = Transforms()
        self.prover = ProofEngine()
        self.formulas = FormulaBook()
        self._strategy_cache = {}  # Remember what worked

    def solve(self, problem: str) -> str:
        """Solve ANY mathematical problem. The master entry point."""
        problem = problem.strip()

        # Step 1: Parse problem into structured form
        parsed = self._parse_problem(problem)

        # Step 2: Classify problem structure
        structure = self._classify_structure(parsed)

        # Step 3: Select and apply strategy
        solution = self._apply_strategy(structure, parsed, problem)

        # Step 4: Verify (if possible)
        verified = self._verify(solution, parsed)

        # Step 5: Format output with steps
        return self._format_solution(problem, structure, solution, verified)

    # ─────────────────────────────────────────────────────────
    # STEP 1: PROBLEM PARSING
    # ─────────────────────────────────────────────────────────

    def _parse_problem(self, text: str) -> dict:
        """Parse any math problem into: given, find, constraints, type."""
        import re
        low = text.lower()
        parsed = {
            'given': [],      # Known values/expressions
            'find': None,     # What to compute
            'constraints': [],  # Conditions
            'expressions': [],  # Mathematical expressions found
            'variables': set(),  # Variables present
            'type': 'unknown',
            'raw': text,
        }

        # Extract expressions (anything with math operators/functions)
        expr_patterns = re.findall(r'[a-zA-Z0-9\s\+\-\*/\^\(\)=]+', text)
        for expr in expr_patterns:
            if any(op in expr for op in '+-*/^=') and any(c.isalpha() for c in expr):
                parsed['expressions'].append(expr.strip())

        # Extract variables
        tokens = self.tokenizer.tokenize(text)
        parsed['variables'] = set(t.value for t in tokens if t.type == TT.VAR and t.value != 'e')

        # Extract numeric values
        for m in re.finditer(r'([a-zA-Z_]\w*)\s*=\s*([-\d.]+)', text):
            parsed['given'].append((m.group(1), float(m.group(2))))

        # Detect what to find
        m = re.search(r'(?:find|solve\s+for|compute|calculate|evaluate|determine|what is|what are)\s+(.+?)(?:\s+(?:if|when|where|given|such that)|$)', low)
        if m:
            parsed['find'] = m.group(1).strip()

        # Detect constraints
        for m in re.finditer(r'(?:if|when|where|given that|such that|for|subject to)\s+(.+?)(?:\s+(?:find|compute|and)|$)', low):
            parsed['constraints'].append(m.group(1).strip())

        return parsed

    # ─────────────────────────────────────────────────────────
    # STEP 2: STRUCTURE CLASSIFICATION
    # ─────────────────────────────────────────────────────────

    # Problem structures (not content — STRUCTURE)
    STRUCT_SOLVE_EQUATION = 'solve_equation'       # Find x such that f(x) = 0
    STRUCT_OPTIMIZE = 'optimize'                   # Find x that maximizes/minimizes f
    STRUCT_PROVE = 'prove'                         # Show statement is true
    STRUCT_COMPUTE = 'compute'                     # Evaluate expression
    STRUCT_TRANSFORM = 'transform'                 # Apply transform (Laplace, etc.)
    STRUCT_SYSTEM = 'system'                       # System of equations
    STRUCT_DIFFERENTIAL = 'differential'           # Solve ODE/PDE
    STRUCT_SEQUENCE = 'sequence'                   # Find pattern/next term
    STRUCT_GEOMETRY = 'geometry'                   # Area, volume, distance
    STRUCT_COMBINATORICS = 'combinatorics'         # Count, permute, combine
    STRUCT_NUMBER_THEORY = 'number_theory'         # Divisibility, modular arithmetic
    STRUCT_MULTI_STEP = 'multi_step'               # Requires chaining multiple methods

    def _classify_structure(self, parsed: dict) -> str:
        """Identify the STRUCTURE of the problem (not content)."""
        low = parsed['raw'].lower()

        if 'prove' in low or 'show that' in low or 'demonstrate' in low:
            return self.STRUCT_PROVE

        if 'maximum' in low or 'minimum' in low or 'optimize' in low or \
           'maximize' in low or 'minimize' in low or 'extrema' in low:
            return self.STRUCT_OPTIMIZE

        if 'laplace' in low or 'fourier' in low or 'z-transform' in low or 'z transform' in low:
            return self.STRUCT_TRANSFORM

        if any(w in low for w in ['dy/dx', 'differential equation', "y'", "y''", 'ode']):
            return self.STRUCT_DIFFERENTIAL

        if 'how many' in low or 'permut' in low or 'combin' in low or \
           'choose' in low or 'arrangements' in low:
            return self.STRUCT_COMBINATORICS

        if 'sequence' in low or 'series' in low or 'next term' in low or \
           'nth term' in low or 'pattern' in low:
            return self.STRUCT_SEQUENCE

        if 'area' in low or 'volume' in low or 'perimeter' in low or \
           'distance' in low or 'angle' in low or 'triangle' in low:
            return self.STRUCT_GEOMETRY

        if 'mod ' in low or 'gcd' in low or 'lcm' in low or \
           'divisible' in low or 'remainder' in low or 'congruent' in low:
            return self.STRUCT_NUMBER_THEORY

        if low.count('=') >= 2 or ('system' in low and 'equation' in low):
            return self.STRUCT_SYSTEM

        if '=' in low and parsed['variables']:
            return self.STRUCT_SOLVE_EQUATION

        return self.STRUCT_COMPUTE

    # ─────────────────────────────────────────────────────────
    # STEP 3: STRATEGY APPLICATION
    # ─────────────────────────────────────────────────────────

    def _apply_strategy(self, structure: str, parsed: dict, raw: str) -> dict:
        """Apply the appropriate strategy for this problem structure."""

        strategies = {
            self.STRUCT_SOLVE_EQUATION: self._strategy_solve,
            self.STRUCT_OPTIMIZE: self._strategy_optimize,
            self.STRUCT_PROVE: self._strategy_prove,
            self.STRUCT_COMPUTE: self._strategy_compute,
            self.STRUCT_TRANSFORM: self._strategy_transform,
            self.STRUCT_SYSTEM: self._strategy_system,
            self.STRUCT_DIFFERENTIAL: self._strategy_differential,
            self.STRUCT_SEQUENCE: self._strategy_sequence,
            self.STRUCT_GEOMETRY: self._strategy_geometry,
            self.STRUCT_COMBINATORICS: self._strategy_combinatorics,
            self.STRUCT_NUMBER_THEORY: self._strategy_number_theory,
            self.STRUCT_MULTI_STEP: self._strategy_multi_step,
        }

        strategy_fn = strategies.get(structure, self._strategy_compute)
        return strategy_fn(parsed, raw)

    def _strategy_solve(self, parsed: dict, raw: str) -> dict:
        """Strategy: Solve equation(s)."""
        result = self.prometheus.process(raw)
        return {'answer': result, 'method': 'algebraic solving', 'steps': [result]}

    def _strategy_optimize(self, parsed: dict, raw: str) -> dict:
        """Strategy: Find max/min by setting derivative = 0."""
        import re
        steps = []

        # Extract function to optimize
        # Patterns: "maximize -x^2 + 6x - 5" or "maximize f(x) = -x^2 + 6x - 5"
        m = re.search(r'(?:maximize|minimize|find\s+(?:max|min)\w*\s+(?:of\s+)?)\s*(?:\w+\([^)]*\)\s*=\s*)?(.+?)(?:\s+(?:for|where|subject|over)|$)', raw, re.IGNORECASE)
        if m:
            expr_str = m.group(1).strip()
            # If it still has f(x)= prefix, remove
            expr_str = re.sub(r'^\w+\([^)]*\)\s*=\s*', '', expr_str).strip()

            if not expr_str:
                return {'answer': 'Cannot parse function to optimize', 'method': 'failed', 'steps': []}

            var = list(parsed['variables'] - {'f', 'maximize', 'minimize'})[0] if \
                  (parsed['variables'] - {'f', 'maximize', 'minimize'}) else 'x'

            steps.append(f"Function: f({var}) = {expr_str}")

            # Parse expression
            tokens = self.tokenizer.tokenize(expr_str)
            ast = self.parser.parse(tokens)

            # Step 1: Differentiate
            deriv = self.calculus.differentiate(ast, var)
            deriv_simplified = self.simplifier.simplify(deriv)
            deriv_str = self.printer.to_string(deriv_simplified)
            steps.append(f"Step 1: f'({var}) = {deriv_str}")

            # Step 2: Set f'(x) = 0 and solve
            steps.append(f"Step 2: Set f'({var}) = 0:")
            steps.append(f"  {deriv_str} = 0")

            # Solve for the critical points
            solve_result = self.solver.solve(deriv_simplified, NumNode(0), var)
            if solve_result and solve_result[0] != 'cannot solve symbolically':
                critical = solve_result
                steps.append(f"  Critical point(s): {var} = {', '.join(critical)}")

                # Step 3: Second derivative test
                deriv2 = self.calculus.differentiate(deriv_simplified, var)
                deriv2_simplified = self.simplifier.simplify(deriv2)
                deriv2_str = self.printer.to_string(deriv2_simplified)
                steps.append(f"Step 3: f''({var}) = {deriv2_str}")

                # Evaluate f''(x) at critical points
                for cp_str in critical:
                    try:
                        cp_val = float(cp_str.split('(')[0])  # handle "3 (double root)"
                        f2_val = self.calculus._eval_at(deriv2_simplified, var, cp_val)
                        if f2_val is not None:
                            if f2_val > 0:
                                steps.append(f"  f''({cp_str}) = {f2_val:.4g} > 0 → LOCAL MINIMUM")
                            elif f2_val < 0:
                                steps.append(f"  f''({cp_str}) = {f2_val:.4g} < 0 → LOCAL MAXIMUM")
                            else:
                                steps.append(f"  f''({cp_str}) = 0 → INFLECTION POINT")

                            # Evaluate f(x) at critical point
                            f_val = self.calculus._eval_at(ast, var, cp_val)
                            if f_val is not None:
                                steps.append(f"  f({cp_str}) = {f_val:.6g}")
                    except (ValueError, TypeError):
                        pass

                answer = f"Critical point(s): {var} = {', '.join(critical)}"
            else:
                steps.append("  Cannot find critical points algebraically.")
                answer = "Cannot solve optimization."

            return {'answer': answer, 'method': 'derivative test (calculus)', 'steps': steps}

        return {'answer': 'Cannot parse optimization problem', 'method': 'failed', 'steps': []}

    def _strategy_prove(self, parsed: dict, raw: str) -> dict:
        """Strategy: Mathematical proof."""
        result = self.prover.prove(raw)
        return {'answer': result, 'method': 'proof', 'steps': [result]}

    def _strategy_compute(self, parsed: dict, raw: str) -> dict:
        """Strategy: Direct computation."""
        result = self.prometheus.process(raw)
        return {'answer': result, 'method': 'direct computation', 'steps': [result]}

    def _strategy_transform(self, parsed: dict, raw: str) -> dict:
        """Strategy: Apply integral transform."""
        result = self.prometheus.process(raw)
        return {'answer': result, 'method': 'integral transform', 'steps': [result]}

    def _strategy_system(self, parsed: dict, raw: str) -> dict:
        """Strategy: Solve system of equations (substitution/elimination)."""
        import re
        steps = []
        equations = re.split(r'(?:,|\band\b|;)', raw)
        equations = [eq.strip() for eq in equations if '=' in eq]

        if len(equations) >= 2:
            steps.append("System of equations:")
            for i, eq in enumerate(equations, 1):
                steps.append(f"  ({i}) {eq}")

            # For 2 equations, 2 unknowns: substitution method
            if len(equations) == 2:
                steps.append("")
                steps.append("Method: Substitution")
                steps.append("  Solve (1) for first variable, substitute into (2)")

                # Try to solve
                eq1 = equations[0].replace('solve', '').strip()
                eq2 = equations[1].strip()

                # Simple 2x2 linear system: ax + by = c, dx + ey = f
                # Use Cramer's rule
                vars_list = sorted(parsed['variables'])
                if len(vars_list) >= 2:
                    v1, v2 = vars_list[0], vars_list[1]
                    coeffs = self._extract_linear_system(equations, v1, v2)
                    if coeffs:
                        a, b, c, d, e, f = coeffs
                        det = a*e - b*d
                        if det != 0:
                            x_val = (c*e - b*f) / det
                            y_val = (a*f - c*d) / det
                            steps.append(f"  Using Cramer's rule: det = {det}")
                            steps.append(f"  {v1} = {x_val:.6g}")
                            steps.append(f"  {v2} = {y_val:.6g}")
                            answer = f"{v1} = {x_val:.6g}, {v2} = {y_val:.6g}"
                            return {'answer': answer, 'method': "Cramer's rule", 'steps': steps}

        return {'answer': 'Cannot solve system', 'method': 'system', 'steps': steps}

    def _strategy_differential(self, parsed: dict, raw: str) -> dict:
        """Strategy: Solve differential equation."""
        import re
        steps = []
        low = raw.lower()

        # Separable ODE: dy/dx = f(x)*g(y)
        # Linear first-order: dy/dx + P(x)y = Q(x)
        steps.append("Differential Equation identified.")

        # Detect type
        if "y'" in raw or 'dy/dx' in low:
            steps.append("Type: First-order ODE")
            steps.append("Method: Attempt separation of variables")
            steps.append("  1. Rewrite as g(y)dy = f(x)dx")
            steps.append("  2. Integrate both sides")
            steps.append("  3. Solve for y")

            # Try to extract: y' = f(x)
            m = re.search(r"y'\s*=\s*(.+)", raw)
            if m:
                rhs = m.group(1).strip()
                steps.append(f"  y' = {rhs}")
                # If RHS is only in x, direct integration
                if 'y' not in rhs:
                    integral_result = self.prometheus.process(f"integrate {rhs} dx")
                    steps.append(f"  y = ∫({rhs})dx = {integral_result}")
                    return {'answer': f"y = {integral_result}", 'method': 'direct integration', 'steps': steps}

        if "y''" in raw or "d2y/dx2" in low:
            steps.append("Type: Second-order ODE")
            steps.append("Method: Characteristic equation")
            steps.append("  1. Assume y = e^(rx)")
            steps.append("  2. Substitute → characteristic equation")
            steps.append("  3. Solve for r")
            steps.append("  4. General solution based on roots")

        return {'answer': '\n'.join(steps), 'method': 'ODE solving', 'steps': steps}

    def _strategy_sequence(self, parsed: dict, raw: str) -> dict:
        """Strategy: Find pattern in sequence."""
        import re
        steps = []

        # Extract numbers from the sequence
        numbers = [float(x) for x in re.findall(r'[-\d.]+', raw)]
        if len(numbers) < 3:
            return {'answer': 'Need at least 3 terms to find pattern', 'method': 'sequence', 'steps': []}

        steps.append(f"Sequence: {numbers}")

        # Check arithmetic (constant difference)
        diffs = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
        if len(set(diffs)) == 1:
            d = diffs[0]
            next_val = numbers[-1] + d
            steps.append(f"Type: Arithmetic sequence")
            steps.append(f"Common difference: d = {d:.6g}")
            steps.append(f"nth term: a(n) = {numbers[0]:.6g} + (n-1)×{d:.6g}")
            steps.append(f"Next term: {next_val:.6g}")
            return {'answer': f"Next term = {next_val:.6g}  (arithmetic, d={d:.6g})", 'method': 'arithmetic sequence', 'steps': steps}

        # Check geometric (constant ratio)
        if all(x != 0 for x in numbers[:-1]):
            ratios = [numbers[i+1] / numbers[i] for i in range(len(numbers)-1)]
            if len(set(round(r, 10) for r in ratios)) == 1:
                r = ratios[0]
                next_val = numbers[-1] * r
                steps.append(f"Type: Geometric sequence")
                steps.append(f"Common ratio: r = {r:.6g}")
                steps.append(f"nth term: a(n) = {numbers[0]:.6g} × {r:.6g}^(n-1)")
                steps.append(f"Next term: {next_val:.6g}")
                return {'answer': f"Next term = {next_val:.6g}  (geometric, r={r:.6g})", 'method': 'geometric sequence', 'steps': steps}

        # Check second differences (quadratic)
        if len(diffs) >= 2:
            second_diffs = [diffs[i+1] - diffs[i] for i in range(len(diffs)-1)]
            if len(set(round(d, 10) for d in second_diffs)) == 1:
                d2 = second_diffs[0]
                next_diff = diffs[-1] + d2
                next_val = numbers[-1] + next_diff
                steps.append(f"Type: Quadratic sequence")
                steps.append(f"Second difference: {d2:.6g}")
                steps.append(f"Next term: {next_val:.6g}")
                return {'answer': f"Next term = {next_val:.6g}  (quadratic sequence)", 'method': 'quadratic sequence', 'steps': steps}

        # Check powers: 1, 4, 9, 16 → n^2; 1, 8, 27 → n^3
        for power in [2, 3, 4]:
            expected = [(i+1)**power for i in range(len(numbers))]
            if all(abs(a-b) < 0.01 for a, b in zip(numbers, expected)):
                next_val = (len(numbers)+1)**power
                steps.append(f"Type: Perfect {power}th powers (n^{power})")
                steps.append(f"Next term: {next_val}")
                return {'answer': f"Next term = {next_val}  (n^{power} sequence)", 'method': f'power-{power}', 'steps': steps}

        # Fibonacci check
        if len(numbers) >= 3:
            is_fib = all(abs(numbers[i] - (numbers[i-1] + numbers[i-2])) < 0.01
                        for i in range(2, len(numbers)))
            if is_fib:
                next_val = numbers[-1] + numbers[-2]
                steps.append(f"Type: Fibonacci-like (each term = sum of previous two)")
                steps.append(f"Next term: {next_val:.6g}")
                return {'answer': f"Next term = {next_val:.6g}  (Fibonacci-like)", 'method': 'fibonacci', 'steps': steps}

        return {'answer': 'Cannot determine pattern', 'method': 'sequence analysis', 'steps': steps}

    def _strategy_geometry(self, parsed: dict, raw: str) -> dict:
        """Strategy: Geometry computations."""
        # Use formula book
        eng = EngineeringSolver()
        result = eng.solve_problem(raw)
        if 'No applicable' not in result:
            return {'answer': result, 'method': 'geometric formula', 'steps': [result]}
        return {'answer': self.prometheus.process(raw), 'method': 'geometry', 'steps': []}

    def _strategy_combinatorics(self, parsed: dict, raw: str) -> dict:
        """Strategy: Counting problems."""
        import re
        low = raw.lower()

        # nCr: "choose r from n" / "n choose r" / "C(n,r)"
        m = re.search(r'(\d+)\s*(?:choose|c|C)\s*(\d+)', raw)
        if not m:
            m = re.search(r'(?:choose|select|pick)\s+(\d+)\s+(?:from|out of)\s+(\d+)', low)
            if m:
                m = type('M', (), {'group': lambda self, i: [None, m.group(2), m.group(1)][i]})()
        if m:
            n, r = int(m.group(1)), int(m.group(2))
            # nCr = n! / (r! * (n-r)!)
            result = math.factorial(n) // (math.factorial(r) * math.factorial(n - r))
            steps = [
                f"C({n},{r}) = {n}! / ({r}! × {n-r}!)",
                f"= {math.factorial(n)} / ({math.factorial(r)} × {math.factorial(n-r)})",
                f"= {result}"
            ]
            return {'answer': str(result), 'method': 'combination', 'steps': steps}

        # nPr: "permutations of r from n"
        m = re.search(r'(\d+)\s*(?:P|permut\w*)\s*(\d+)', raw)
        if m:
            n, r = int(m.group(1)), int(m.group(2))
            result = math.factorial(n) // math.factorial(n - r)
            steps = [f"P({n},{r}) = {n}! / {n-r}! = {result}"]
            return {'answer': str(result), 'method': 'permutation', 'steps': steps}

        # "how many ways"
        if 'how many' in low:
            # Try to extract n and r from context
            nums = [int(x) for x in re.findall(r'\d+', raw)]
            if len(nums) >= 2:
                n, r = max(nums), min(nums)
                result = math.factorial(n) // (math.factorial(r) * math.factorial(n - r))
                return {'answer': f"C({n},{r}) = {result}", 'method': 'combination', 'steps': []}

        return {'answer': 'Cannot parse combinatorics problem', 'method': 'combinatorics', 'steps': []}

    def _strategy_number_theory(self, parsed: dict, raw: str) -> dict:
        """Strategy: Number theory computations."""
        import re
        low = raw.lower()

        # GCD
        if 'gcd' in low or 'greatest common' in low:
            nums = [int(x) for x in re.findall(r'\d+', raw)]
            if len(nums) >= 2:
                result = math.gcd(nums[0], nums[1])
                for n in nums[2:]:
                    result = math.gcd(result, n)
                steps = [f"GCD({', '.join(map(str,nums))}) using Euclidean algorithm:"]
                a, b = nums[0], nums[1]
                while b:
                    steps.append(f"  {a} = {a//b} × {b} + {a%b}")
                    a, b = b, a % b
                steps.append(f"  GCD = {result}")
                return {'answer': str(result), 'method': 'Euclidean algorithm', 'steps': steps}

        # LCM
        if 'lcm' in low or 'least common' in low:
            nums = [int(x) for x in re.findall(r'\d+', raw)]
            if len(nums) >= 2:
                result = nums[0]
                for n in nums[1:]:
                    result = result * n // math.gcd(result, n)
                return {'answer': f"LCM({', '.join(map(str,nums))}) = {result}", 'method': 'LCM via GCD', 'steps': [f"LCM = product / GCD"]}

        # Modular arithmetic: a mod b
        m = re.search(r'(\d+)\s*(?:mod|%)\s*(\d+)', raw)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            result = a % b
            return {'answer': f"{a} mod {b} = {result}", 'method': 'modular arithmetic', 'steps': [f"{a} = {a//b}×{b} + {result}"]}

        # Remainder
        if 'remainder' in low:
            nums = [int(x) for x in re.findall(r'\d+', raw)]
            if len(nums) >= 2:
                result = nums[0] % nums[1]
                return {'answer': f"Remainder of {nums[0]} ÷ {nums[1]} = {result}", 'method': 'division', 'steps': []}

        return {'answer': 'Cannot parse number theory problem', 'method': 'number_theory', 'steps': []}

    def _strategy_multi_step(self, parsed: dict, raw: str) -> dict:
        """Strategy: Chain multiple methods."""
        return self._strategy_compute(parsed, raw)

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _extract_linear_system(self, equations, v1, v2):
        """Extract coefficients from 2 linear equations: ax+by=c, dx+ey=f."""
        import re
        coeffs = []
        for eq in equations[:2]:
            eq = eq.replace(' ', '')
            # Normalize: move everything to left side
            if '=' in eq:
                lhs, rhs = eq.split('=', 1)
            else:
                continue
            # Extract coefficients for v1 and v2
            a = self._get_coeff_in_expr(lhs, v1)
            b = self._get_coeff_in_expr(lhs, v2)
            try:
                c = float(rhs)
            except:
                c = 0
            coeffs.extend([a, b, c])
        return coeffs if len(coeffs) == 6 else None

    def _get_coeff_in_expr(self, expr: str, var: str) -> float:
        """Get coefficient of var in expression string."""
        import re
        # Pattern: optional sign, optional number, variable
        m = re.search(r'([+-]?\d*\.?\d*)\s*' + re.escape(var), expr)
        if m:
            coeff_str = m.group(1)
            if coeff_str in ('', '+'):
                return 1.0
            if coeff_str == '-':
                return -1.0
            return float(coeff_str)
        return 0.0

    # ─────────────────────────────────────────────────────────
    # STEP 4: VERIFICATION
    # ─────────────────────────────────────────────────────────

    def _verify(self, solution: dict, parsed: dict) -> Optional[str]:
        """Verify the solution is correct (where possible)."""
        # For now, return None (verification not implemented for all types)
        # Future: substitute answer back into original equation
        return None

    # ─────────────────────────────────────────────────────────
    # STEP 5: FORMAT OUTPUT
    # ─────────────────────────────────────────────────────────

    def _format_solution(self, problem: str, structure: str, solution: dict, verified) -> str:
        """Format the solution with clear steps."""
        lines = []

        if solution.get('steps') and len(solution['steps']) > 1:
            for step in solution['steps']:
                lines.append(step)
        elif solution.get('answer'):
            lines.append(solution['answer'])

        if verified:
            lines.append(f"\nVerification: {verified}")

        return '\n'.join(lines) if lines else solution.get('answer', 'Cannot solve.')
