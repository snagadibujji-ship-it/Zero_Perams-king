"""Phase R7: Specialist Superiority — domain-specific reasoning engines."""

from axima.specialist.math_specialist import MathSpecialist
from axima.specialist.physics_specialist import PhysicsSpecialist
from axima.specialist.knowledge_specialist import KnowledgeSpecialist
from axima.specialist.causal_specialist import CausalSpecialist
from axima.specialist.document_specialist import DocumentSpecialist

__all__ = [
    "MathSpecialist",
    "PhysicsSpecialist",
    "KnowledgeSpecialist",
    "CausalSpecialist",
    "DocumentSpecialist",
]
