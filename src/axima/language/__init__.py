"""AXIMA Language Module — Native language realization, parsing, and register adaptation."""

from .parser import LanguageParser
from .realizer import MorphologyRule, LanguageProfile, NativeRealizer
from .register import Register, RegisterAdapter

__all__ = [
    "LanguageParser",
    "MorphologyRule",
    "LanguageProfile",
    "NativeRealizer",
    "Register",
    "RegisterAdapter",
]
