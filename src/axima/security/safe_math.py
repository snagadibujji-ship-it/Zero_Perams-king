"""Safe mathematical expression evaluator using typed AST.

NEVER uses eval(), exec(), or compile() on user input.
Raises SecurityError for any injection attempt.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from axima.errors import EvalError, ParseError, SecurityError


# ---------------------------------------------------------------------------
# AST Node definitions
# ---------------------------------------------------------------------------


class NodeType(Enum):
    NUMBER = auto()
    BINOP = auto()
    UNARY = auto()
    FUNCTION = auto()
    VARIABLE = auto()


@dataclass
class MathNode:
    """Base class for math AST nodes."""

    node_type: NodeType


@dataclass
class NumberNode(MathNode):
    """Numeric literal."""

    value: float

    def __init__(self, value: float) -> None:
        super().__init__(NodeType.NUMBER)
        self.value = value


@dataclass
class BinOpNode(MathNode):
    """Binary operation: left op right."""

    op: str
    left: MathNode
    right: MathNode

    def __init__(self, op: str, left: MathNode, right: MathNode) -> None:
        super().__init__(NodeType.BINOP)
        self.op = op
        self.left = left
        self.right = right


@dataclass
class UnaryOpNode(MathNode):
    """Unary operation: -x or +x."""

    op: str
    operand: MathNode

    def __init__(self, op: str, operand: MathNode) -> None:
        super().__init__(NodeType.UNARY)
        self.op = op
        self.operand = operand


@dataclass
class FunctionCallNode(MathNode):
    """Function call: func(arg)."""

    name: str
    args: list[MathNode]

    def __init__(self, name: str, args: list[MathNode]) -> None:
        super().__init__(NodeType.FUNCTION)
        self.name = name
        self.args = args


@dataclass
class VariableNode(MathNode):
    """Variable reference."""

    name: str

    def __init__(self, name: str) -> None:
        super().__init__(NodeType.VARIABLE)
        self.name = name


# ---------------------------------------------------------------------------
# Token types for the lexer
# ---------------------------------------------------------------------------

class TokenType(Enum):
    NUMBER = auto()
    IDENT = auto()
    OP = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    pos: int


# ---------------------------------------------------------------------------
# Security: patterns that MUST be rejected before parsing
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS = [
    r"__\w+__",        # dunder access
    r"\bimport\b",     # import statements
    r"\bexec\b",       # exec calls
    r"\beval\b",       # eval calls
    r"\bcompile\b",    # compile calls
    r"\bopen\b",       # file access
    r"\bos\b",         # os module
    r"\bsys\b",       # sys module
    r"\bsubprocess\b", # subprocess
    r"\bglobals\b",    # globals access
    r"\blocals\b",     # locals access
    r"\bgetattr\b",    # attribute access
    r"\bsetattr\b",    # attribute setting
    r"\bdelattr\b",    # attribute deletion
    r"\btype\b",       # type manipulation
    r"\blambda\b",     # lambda creation
    r"\bclass\b",      # class definition
    r"\bdef\b",        # function definition
    r"[;{}\\]",        # statement separators, braces
    r"\[",             # list/subscript access
    r"\]",             # list/subscript access
]

_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# Allowed function names
ALLOWED_FUNCTIONS = frozenset({
    "sin", "cos", "tan", "sqrt", "abs", "log", "ln", "exp",
    "factorial", "gcd", "lcm", "floor", "ceil", "round",
    "asin", "acos", "atan", "sinh", "cosh", "tanh",
})

# Allowed binary operators
ALLOWED_OPS = frozenset({"+", "-", "*", "/", "//", "%", "**"})


# ---------------------------------------------------------------------------
# MathParser: tokenizes and parses into AST
# ---------------------------------------------------------------------------

class MathParser:
    """Tokenizes and parses math expressions into a safe MathNode AST.

    Grammar (precedence low to high):
      expr     -> term (('+' | '-') term)*
      term     -> power (('*' | '/' | '//' | '%') power)*
      power    -> unary ('**' power)?   (right-associative)
      unary    -> ('+' | '-') unary | call
      call     -> IDENT '(' args ')' | atom
      atom     -> NUMBER | IDENT | '(' expr ')'
    """

    MAX_EXPRESSION_LENGTH = 2000
    MAX_TOKEN_COUNT = 500

    def __init__(self, expression: str) -> None:
        if len(expression) > self.MAX_EXPRESSION_LENGTH:
            raise ParseError(
                f"Expression too long ({len(expression)} > {self.MAX_EXPRESSION_LENGTH})",
                context={"length": len(expression)},
            )

        # Security check BEFORE any parsing
        match = _INJECTION_RE.search(expression)
        if match:
            raise SecurityError(
                f"Injection attempt detected: '{match.group()}'",
                context={"pattern": match.group(), "position": match.start()},
            )

        self._source = expression
        self._tokens: list[Token] = []
        self._pos = 0
        self._tokenize()

        if len(self._tokens) > self.MAX_TOKEN_COUNT:
            raise ParseError(
                f"Too many tokens ({len(self._tokens)} > {self.MAX_TOKEN_COUNT})",
                context={"token_count": len(self._tokens)},
            )

    def _tokenize(self) -> None:
        """Lexer: split source into tokens."""
        i = 0
        src = self._source
        while i < len(src):
            ch = src[i]

            # Skip whitespace
            if ch in " \t\r\n":
                i += 1
                continue

            # Number (int or float)
            if ch.isdigit() or (ch == "." and i + 1 < len(src) and src[i + 1].isdigit()):
                start = i
                while i < len(src) and (src[i].isdigit() or src[i] == "."):
                    i += 1
                # Scientific notation
                if i < len(src) and src[i] in "eE":
                    i += 1
                    if i < len(src) and src[i] in "+-":
                        i += 1
                    while i < len(src) and src[i].isdigit():
                        i += 1
                self._tokens.append(Token(TokenType.NUMBER, src[start:i], start))
                continue

            # Identifier (function name or variable)
            if ch.isalpha() or ch == "_":
                start = i
                while i < len(src) and (src[i].isalnum() or src[i] == "_"):
                    i += 1
                word = src[start:i]
                # Constants
                if word == "pi":
                    self._tokens.append(Token(TokenType.NUMBER, str(math.pi), start))
                elif word == "e":
                    self._tokens.append(Token(TokenType.NUMBER, str(math.e), start))
                else:
                    self._tokens.append(Token(TokenType.IDENT, word, start))
                continue

            # Two-char operators
            if ch == "/" and i + 1 < len(src) and src[i + 1] == "/":
                self._tokens.append(Token(TokenType.OP, "//", i))
                i += 2
                continue
            if ch == "*" and i + 1 < len(src) and src[i + 1] == "*":
                self._tokens.append(Token(TokenType.OP, "**", i))
                i += 2
                continue

            # Single-char operators
            if ch in "+-*/%^":
                op = "**" if ch == "^" else ch
                self._tokens.append(Token(TokenType.OP, op, i))
                i += 1
                continue

            if ch == "(":
                self._tokens.append(Token(TokenType.LPAREN, "(", i))
                i += 1
                continue
            if ch == ")":
                self._tokens.append(Token(TokenType.RPAREN, ")", i))
                i += 1
                continue
            if ch == ",":
                self._tokens.append(Token(TokenType.COMMA, ",", i))
                i += 1
                continue

            raise ParseError(
                f"Unexpected character '{ch}' at position {i}",
                context={"char": ch, "position": i},
            )

        self._tokens.append(Token(TokenType.EOF, "", len(src)))

    def parse(self) -> MathNode:
        """Parse tokens into an AST."""
        self._pos = 0
        node = self._parse_expr()
        if self._current().type != TokenType.EOF:
            tok = self._current()
            raise ParseError(
                f"Unexpected token '{tok.value}' at position {tok.pos}",
                context={"token": tok.value, "position": tok.pos},
            )
        return node

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, ttype: TokenType, value: str | None = None) -> Token:
        tok = self._current()
        if tok.type != ttype or (value is not None and tok.value != value):
            raise ParseError(
                f"Expected {ttype.name}({value}) but got {tok.type.name}('{tok.value}')",
                context={"expected": value, "got": tok.value, "position": tok.pos},
            )
        return self._advance()

    def _parse_expr(self) -> MathNode:
        """expr -> term (('+' | '-') term)*"""
        left = self._parse_term()
        while self._current().type == TokenType.OP and self._current().value in ("+", "-"):
            op = self._advance().value
            right = self._parse_term()
            left = BinOpNode(op, left, right)
        return left

    def _parse_term(self) -> MathNode:
        """term -> power (('*' | '/' | '//' | '%') power)*"""
        left = self._parse_power()
        while self._current().type == TokenType.OP and self._current().value in (
            "*", "/", "//", "%"
        ):
            op = self._advance().value
            right = self._parse_power()
            left = BinOpNode(op, left, right)
        return left

    def _parse_power(self) -> MathNode:
        """power -> unary ('**' power)?  (right-associative)"""
        base = self._parse_unary()
        if self._current().type == TokenType.OP and self._current().value == "**":
            self._advance()
            exp = self._parse_power()  # right-associative recursion
            return BinOpNode("**", base, exp)
        return base

    def _parse_unary(self) -> MathNode:
        """unary -> ('+' | '-') unary | call"""
        if self._current().type == TokenType.OP and self._current().value in ("+", "-"):
            op = self._advance().value
            operand = self._parse_unary()
            if op == "-":
                return UnaryOpNode("-", operand)
            return operand  # +x is just x
        return self._parse_call()

    def _parse_call(self) -> MathNode:
        """call -> IDENT '(' args ')' | atom"""
        if (
            self._current().type == TokenType.IDENT
            and self._pos + 1 < len(self._tokens)
            and self._tokens[self._pos + 1].type == TokenType.LPAREN
        ):
            name_tok = self._advance()
            fname = name_tok.value
            if fname not in ALLOWED_FUNCTIONS:
                raise SecurityError(
                    f"Function '{fname}' is not allowed",
                    context={"function": fname, "allowed": list(ALLOWED_FUNCTIONS)},
                )
            self._advance()  # consume '('
            args: list[MathNode] = []
            if self._current().type != TokenType.RPAREN:
                args.append(self._parse_expr())
                while self._current().type == TokenType.COMMA:
                    self._advance()
                    args.append(self._parse_expr())
            self._expect(TokenType.RPAREN)
            return FunctionCallNode(fname, args)
        return self._parse_atom()

    def _parse_atom(self) -> MathNode:
        """atom -> NUMBER | IDENT | '(' expr ')'"""
        tok = self._current()

        if tok.type == TokenType.NUMBER:
            self._advance()
            try:
                return NumberNode(float(tok.value))
            except ValueError as exc:
                raise ParseError(
                    f"Invalid number: '{tok.value}'",
                    context={"value": tok.value},
                ) from exc

        if tok.type == TokenType.IDENT:
            self._advance()
            return VariableNode(tok.name if hasattr(tok, "name") else tok.value)

        if tok.type == TokenType.LPAREN:
            self._advance()
            node = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return node

        raise ParseError(
            f"Unexpected token '{tok.value}' at position {tok.pos}",
            context={"token": tok.value, "position": tok.pos},
        )


# ---------------------------------------------------------------------------
# MathEvaluator: walks AST and computes results safely
# ---------------------------------------------------------------------------

class MathEvaluator:
    """Evaluates a MathNode AST with safety constraints.

    Features:
      - Domain checking (no division by zero, no sqrt of negative)
      - Recursion depth limits
      - Value bounds (reject > 1e308)
      - Variable substitution
    """

    MAX_DEPTH = 100
    MAX_VALUE = 1e308

    def __init__(self, variables: dict[str, float] | None = None) -> None:
        self._variables: dict[str, float] = variables or {}
        self._depth = 0

    def evaluate(self, node: MathNode) -> float:
        """Evaluate an AST node and return the numeric result."""
        self._depth += 1
        if self._depth > self.MAX_DEPTH:
            raise EvalError(
                f"Recursion depth exceeded ({self.MAX_DEPTH})",
                context={"max_depth": self.MAX_DEPTH},
            )
        try:
            result = self._eval(node)
        finally:
            self._depth -= 1

        # Bounds check
        if not isinstance(result, (int, float)):
            raise EvalError(f"Non-numeric result: {type(result)}")
        if abs(result) > self.MAX_VALUE:
            raise EvalError(
                f"Result exceeds bounds: |{result}| > {self.MAX_VALUE}",
                context={"value": result, "bound": self.MAX_VALUE},
            )
        if math.isnan(result):
            raise EvalError("Result is NaN", context={"node_type": node.node_type.name})

        return float(result)

    def _eval(self, node: MathNode) -> float:
        if isinstance(node, NumberNode):
            return node.value
        if isinstance(node, VariableNode):
            return self._eval_variable(node)
        if isinstance(node, UnaryOpNode):
            return self._eval_unary(node)
        if isinstance(node, BinOpNode):
            return self._eval_binop(node)
        if isinstance(node, FunctionCallNode):
            return self._eval_function(node)
        raise EvalError(f"Unknown node type: {node.node_type}")

    def _eval_variable(self, node: VariableNode) -> float:
        if node.name not in self._variables:
            raise EvalError(
                f"Undefined variable: '{node.name}'",
                context={"variable": node.name, "defined": list(self._variables.keys())},
            )
        return self._variables[node.name]

    def _eval_unary(self, node: UnaryOpNode) -> float:
        val = self.evaluate(node.operand)
        if node.op == "-":
            return -val
        return val

    def _eval_binop(self, node: BinOpNode) -> float:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)

        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            if right == 0:
                raise EvalError("Division by zero", context={"left": left, "right": right})
            return left / right
        if node.op == "//":
            if right == 0:
                raise EvalError("Floor division by zero", context={"left": left, "right": right})
            return float(left // right)
        if node.op == "%":
            if right == 0:
                raise EvalError("Modulo by zero", context={"left": left, "right": right})
            return left % right
        if node.op == "**":
            # Prevent huge exponents that would hang
            if abs(right) > 1000 and abs(left) > 1:
                raise EvalError(
                    f"Exponent too large: {left}**{right}",
                    context={"base": left, "exponent": right},
                )
            try:
                result = left ** right
            except OverflowError as exc:
                raise EvalError(f"Overflow: {left}**{right}") from exc
            return float(result)

        raise EvalError(f"Unknown operator: '{node.op}'", context={"op": node.op})

    def _eval_function(self, node: FunctionCallNode) -> float:
        args = [self.evaluate(a) for a in node.args]
        fname = node.name

        if fname not in ALLOWED_FUNCTIONS:
            raise SecurityError(f"Function '{fname}' is not allowed")

        try:
            return self._dispatch_function(fname, args)
        except ValueError as exc:
            raise EvalError(
                f"Domain error in {fname}({args}): {exc}",
                context={"function": fname, "args": args},
            ) from exc
        except OverflowError as exc:
            raise EvalError(
                f"Overflow in {fname}({args})",
                context={"function": fname, "args": args},
            ) from exc

    def _dispatch_function(self, fname: str, args: list[float]) -> float:
        """Dispatch to the correct math function."""
        if fname == "sin":
            self._check_argc(fname, args, 1)
            return math.sin(args[0])
        if fname == "cos":
            self._check_argc(fname, args, 1)
            return math.cos(args[0])
        if fname == "tan":
            self._check_argc(fname, args, 1)
            return math.tan(args[0])
        if fname == "asin":
            self._check_argc(fname, args, 1)
            if abs(args[0]) > 1:
                raise ValueError(f"asin domain: |{args[0]}| > 1")
            return math.asin(args[0])
        if fname == "acos":
            self._check_argc(fname, args, 1)
            if abs(args[0]) > 1:
                raise ValueError(f"acos domain: |{args[0]}| > 1")
            return math.acos(args[0])
        if fname == "atan":
            self._check_argc(fname, args, 1)
            return math.atan(args[0])
        if fname == "sinh":
            self._check_argc(fname, args, 1)
            return math.sinh(args[0])
        if fname == "cosh":
            self._check_argc(fname, args, 1)
            return math.cosh(args[0])
        if fname == "tanh":
            self._check_argc(fname, args, 1)
            return math.tanh(args[0])
        if fname == "sqrt":
            self._check_argc(fname, args, 1)
            if args[0] < 0:
                raise ValueError(f"sqrt of negative number: {args[0]}")
            return math.sqrt(args[0])
        if fname == "abs":
            self._check_argc(fname, args, 1)
            return abs(args[0])
        if fname == "log":
            self._check_argc_range(fname, args, 1, 2)
            if args[0] <= 0:
                raise ValueError(f"log of non-positive number: {args[0]}")
            if len(args) == 2:
                if args[1] <= 0 or args[1] == 1:
                    raise ValueError(f"log base must be > 0 and != 1: {args[1]}")
                return math.log(args[0], args[1])
            # Single argument log = log base 10 (common convention; use ln for natural log)
            return math.log10(args[0])
        if fname == "ln":
            self._check_argc(fname, args, 1)
            if args[0] <= 0:
                raise ValueError(f"ln of non-positive number: {args[0]}")
            return math.log(args[0])
        if fname == "exp":
            self._check_argc(fname, args, 1)
            if args[0] > 709:
                raise OverflowError(f"exp({args[0]}) would overflow")
            return math.exp(args[0])
        if fname == "factorial":
            self._check_argc(fname, args, 1)
            n = args[0]
            if n < 0 or n != int(n):
                raise ValueError(f"factorial requires non-negative integer: {n}")
            if n > 170:
                raise OverflowError(f"factorial({int(n)}) too large")
            return float(math.factorial(int(n)))
        if fname == "gcd":
            self._check_argc(fname, args, 2)
            return float(math.gcd(int(args[0]), int(args[1])))
        if fname == "lcm":
            self._check_argc(fname, args, 2)
            return float(math.lcm(int(args[0]), int(args[1])))
        if fname == "floor":
            self._check_argc(fname, args, 1)
            return float(math.floor(args[0]))
        if fname == "ceil":
            self._check_argc(fname, args, 1)
            return float(math.ceil(args[0]))
        if fname == "round":
            self._check_argc_range(fname, args, 1, 2)
            if len(args) == 2:
                return float(round(args[0], int(args[1])))
            return float(round(args[0]))

        raise EvalError(f"Unimplemented function: {fname}")

    @staticmethod
    def _check_argc(fname: str, args: list[float], expected: int) -> None:
        if len(args) != expected:
            raise EvalError(
                f"{fname}() takes {expected} argument(s), got {len(args)}",
                context={"function": fname, "expected": expected, "got": len(args)},
            )

    @staticmethod
    def _check_argc_range(fname: str, args: list[float], lo: int, hi: int) -> None:
        if not (lo <= len(args) <= hi):
            raise EvalError(
                f"{fname}() takes {lo}-{hi} argument(s), got {len(args)}",
                context={"function": fname, "expected_range": (lo, hi), "got": len(args)},
            )


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def safe_eval(expression: str, variables: dict[str, float] | None = None) -> float:
    """Parse and evaluate a math expression safely.

    This is the drop-in replacement for eval() in the math engine.
    """
    parser = MathParser(expression)
    ast = parser.parse()
    evaluator = MathEvaluator(variables=variables)
    return evaluator.evaluate(ast)
