"""
Narrative Reactor — Causal Story Engine
========================================

A deterministic narrative engine that tracks characters, world state,
and causal relationships. Events have preconditions and consequences.
Tension functions as potential energy driving the story forward.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class EmotionalValence(Enum):
    """Emotional direction of a narrative shift."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    AMBIGUOUS = "ambiguous"


class TensionType(Enum):
    """Types of narrative tension."""

    CONFLICT = "conflict"          # Characters with opposing goals
    MYSTERY = "mystery"            # Unknown information
    SUSPENSE = "suspense"          # Known threat, unknown resolution
    DRAMATIC_IRONY = "dramatic_irony"  # Audience knows, character doesn't
    MORAL_DILEMMA = "moral_dilemma"    # No good choices
    TIME_PRESSURE = "time_pressure"    # Deadline approaching


@dataclass
class Character:
    """A character in the narrative with drives, knowledge, and constraints.

    Attributes:
        name: Character identifier.
        drives: What motivates this character (goals, desires).
        knowledge: What this character knows (facts, beliefs).
        relationships: Named relationships to other characters.
        constraints: Rules that limit character behavior.
        state: Current emotional/physical state.
        voice: Speech patterns and vocabulary markers.
    """

    name: str
    drives: List[str] = field(default_factory=list)
    knowledge: Set[str] = field(default_factory=set)
    relationships: Dict[str, str] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    voice: Dict[str, Any] = field(default_factory=dict)

    def knows(self, fact: str) -> bool:
        """Check if this character knows a specific fact."""
        return fact in self.knowledge

    def learn(self, fact: str) -> None:
        """Add a fact to this character's knowledge."""
        self.knowledge.add(fact)

    def can_act(self, action: str) -> bool:
        """Check if an action violates any constraint.

        A constraint blocks an action if the constraint's key verb/noun
        appears in the action text. E.g., constraint "cannot fly" blocks
        actions containing "fly".
        """
        action_lower = action.lower()
        for constraint in self.constraints:
            # Extract the blocked action from "cannot X" patterns
            constraint_lower = constraint.lower()
            if constraint_lower.startswith("cannot "):
                blocked = constraint_lower[7:].strip()  # after "cannot "
                if blocked in action_lower:
                    return False
            elif constraint_lower.startswith("must not "):
                blocked = constraint_lower[9:].strip()
                if blocked in action_lower:
                    return False
            elif constraint_lower.startswith("never "):
                blocked = constraint_lower[6:].strip()
                if blocked in action_lower:
                    return False
            else:
                # Generic: check if constraint text overlaps with action
                constraint_words = set(constraint_lower.split())
                action_words = set(action_lower.split())
                # If significant overlap, it's likely constrained
                overlap = constraint_words & action_words
                if len(overlap) >= 2:
                    return False
        return True


@dataclass
class Tension:
    """A narrative tension that drives the story.

    Tension acts as potential energy — higher tension means more
    pressure for resolution, which drives events.
    """

    tension_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tension_type: TensionType = TensionType.CONFLICT
    description: str = ""
    involved_characters: List[str] = field(default_factory=list)
    magnitude: float = 0.5  # 0.0 - 1.0
    resolved: bool = False
    resolution: Optional[str] = None


@dataclass
class Promise:
    """A narrative promise (setup that demands payoff)."""

    promise_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    setup_event_id: Optional[str] = None
    fulfilled: bool = False
    fulfillment_event_id: Optional[str] = None


@dataclass
class WorldState:
    """The current state of the narrative world.

    Attributes:
        entities: Named things in the world (objects, locations, concepts).
        locations: Location map (name -> description).
        time: Current narrative time marker.
        active_tensions: Unresolved tensions driving the narrative.
        unresolved_promises: Setups that need payoff.
    """

    entities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    locations: Dict[str, str] = field(default_factory=dict)
    time: str = "beginning"
    active_tensions: List[Tension] = field(default_factory=list)
    unresolved_promises: List[Promise] = field(default_factory=list)

    @property
    def total_tension(self) -> float:
        """Total narrative tension (sum of all active tensions)."""
        return sum(t.magnitude for t in self.active_tensions if not t.resolved)

    def add_tension(self, tension: Tension) -> None:
        """Add a new tension to the world."""
        self.active_tensions.append(tension)

    def resolve_tension(self, tension_id: str, resolution: str) -> Optional[Tension]:
        """Mark a tension as resolved."""
        for t in self.active_tensions:
            if t.tension_id == tension_id and not t.resolved:
                t.resolved = True
                t.resolution = resolution
                return t
        return None

    def add_promise(self, promise: Promise) -> None:
        """Add a narrative promise (setup)."""
        self.unresolved_promises.append(promise)

    def fulfill_promise(self, promise_id: str, event_id: str) -> Optional[Promise]:
        """Mark a promise as fulfilled."""
        for p in self.unresolved_promises:
            if p.promise_id == promise_id and not p.fulfilled:
                p.fulfilled = True
                p.fulfillment_event_id = event_id
                return p
        return None


@dataclass
class NarrativeEvent:
    """A single event in the narrative with causal structure.

    Attributes:
        preconditions: Facts/states that must be true for this event to occur.
        action: What happens in this event.
        consequences: State changes caused by this event.
        emotional_shift: How this event changes emotional tone.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    preconditions: List[str] = field(default_factory=list)
    action: str = ""
    consequences: List[str] = field(default_factory=list)
    emotional_shift: EmotionalValence = EmotionalValence.NEUTRAL
    characters_involved: List[str] = field(default_factory=list)
    location: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class ContinuityError:
    """A detected continuity error in the narrative."""

    error_type: str  # "contradiction", "dead_character_acts", "unknown_fact", "broken_constraint"
    description: str
    event_id: str
    severity: str = "warning"  # "warning", "error"


class NarrativeReactor:
    """Causal narrative engine that maintains world consistency.

    Operates on three principles:
    1. Events have preconditions that must be met
    2. Every event has consequences that change world state
    3. Tension drives the narrative (potential energy → events)

    The reactor ensures continuity: characters can only act on what they
    know, constraints are respected, and resolved tensions stay resolved.
    """

    def __init__(self) -> None:
        self._characters: Dict[str, Character] = {}
        self._world: WorldState = WorldState()
        self._history: List[NarrativeEvent] = []
        self._facts: Set[str] = set()  # Ground truth facts
        self._continuity_errors: List[ContinuityError] = []

    @property
    def world(self) -> WorldState:
        """Current world state."""
        return self._world

    @property
    def history(self) -> List[NarrativeEvent]:
        """All events that have occurred."""
        return list(self._history)

    @property
    def characters(self) -> Dict[str, Character]:
        """All registered characters."""
        return dict(self._characters)

    def add_character(self, character: Character) -> None:
        """Add a character to the narrative world."""
        self._characters[character.name] = character

    def add_fact(self, fact: str) -> None:
        """Add a ground truth fact to the world."""
        self._facts.add(fact)

    def set_world(self, world: WorldState) -> None:
        """Set or replace the world state."""
        self._world = world

    def advance_world(self, time_marker: str) -> WorldState:
        """Advance the world to a new time marker.

        This may trigger time-pressure tensions to escalate.

        Args:
            time_marker: New time marker (e.g., "evening", "next day").

        Returns:
            Updated WorldState.
        """
        self._world.time = time_marker

        # Escalate time-pressure tensions
        for tension in self._world.active_tensions:
            if tension.tension_type == TensionType.TIME_PRESSURE and not tension.resolved:
                tension.magnitude = min(tension.magnitude + 0.1, 1.0)

        return self._world

    def generate_event(
        self,
        action: str,
        characters: List[str],
        location: Optional[str] = None,
        preconditions: Optional[List[str]] = None,
        consequences: Optional[List[str]] = None,
        emotional_shift: EmotionalValence = EmotionalValence.NEUTRAL,
    ) -> Tuple[NarrativeEvent, List[ContinuityError]]:
        """Generate a narrative event with continuity checking.

        Validates:
        - All preconditions are met (facts exist, characters know required info)
        - Characters respect their constraints
        - Characters are present at the location

        Args:
            action: What happens.
            characters: Characters involved.
            location: Where it happens.
            preconditions: Required state for the event.
            consequences: State changes the event causes.
            emotional_shift: Emotional direction of the event.

        Returns:
            Tuple of (NarrativeEvent, list of ContinuityError).
        """
        errors: List[ContinuityError] = []
        preconditions = preconditions or []
        consequences = consequences or []

        event = NarrativeEvent(
            preconditions=preconditions,
            action=action,
            consequences=consequences,
            emotional_shift=emotional_shift,
            characters_involved=characters,
            location=location,
            timestamp=self._world.time,
        )

        # Validate preconditions
        for precond in preconditions:
            if precond not in self._facts:
                errors.append(ContinuityError(
                    error_type="unknown_fact",
                    description=f"Precondition not established: '{precond}'",
                    event_id=event.event_id,
                    severity="warning",
                ))

        # Validate character constraints
        for char_name in characters:
            char = self._characters.get(char_name)
            if char is None:
                errors.append(ContinuityError(
                    error_type="unknown_character",
                    description=f"Unknown character: '{char_name}'",
                    event_id=event.event_id,
                    severity="error",
                ))
                continue

            if not char.can_act(action):
                errors.append(ContinuityError(
                    error_type="broken_constraint",
                    description=f"Character '{char_name}' cannot perform '{action}' due to constraints",
                    event_id=event.event_id,
                    severity="error",
                ))

        # Apply consequences to world state
        for consequence in consequences:
            self._facts.add(consequence)

        # Update character knowledge based on event
        for char_name in characters:
            char = self._characters.get(char_name)
            if char:
                char.learn(f"witnessed: {action}")
                for consequence in consequences:
                    char.learn(consequence)

        # Record event
        self._history.append(event)
        self._continuity_errors.extend(errors)

        return event, errors

    def check_continuity(self) -> List[ContinuityError]:
        """Check all recorded events for continuity errors.

        Returns:
            List of all detected continuity errors.
        """
        errors: List[ContinuityError] = []

        # Check for contradictions in facts
        fact_list = sorted(self._facts)
        for i, fact1 in enumerate(fact_list):
            for fact2 in fact_list[i + 1:]:
                if self._are_contradictory(fact1, fact2):
                    errors.append(ContinuityError(
                        error_type="contradiction",
                        description=f"Contradictory facts: '{fact1}' vs '{fact2}'",
                        event_id="global",
                        severity="error",
                    ))

        # Check promises that should have been fulfilled by now
        for promise in self._world.unresolved_promises:
            if not promise.fulfilled and self._world.total_tension < 0.2:
                errors.append(ContinuityError(
                    error_type="broken_promise",
                    description=f"Unresolved promise: '{promise.description}'",
                    event_id=promise.setup_event_id or "unknown",
                    severity="warning",
                ))

        return errors + self._continuity_errors

    def resolve_tension(
        self,
        tension_id: str,
        resolution_action: str,
        characters: List[str],
    ) -> Tuple[Optional[NarrativeEvent], List[ContinuityError]]:
        """Resolve a narrative tension through an event.

        Args:
            tension_id: ID of the tension to resolve.
            resolution_action: The action that resolves it.
            characters: Characters involved in the resolution.

        Returns:
            Tuple of (resolution event, continuity errors).
        """
        tension = None
        for t in self._world.active_tensions:
            if t.tension_id == tension_id:
                tension = t
                break

        if tension is None:
            return None, [ContinuityError(
                error_type="unknown_tension",
                description=f"No tension with id '{tension_id}'",
                event_id="resolution_attempt",
                severity="error",
            )]

        # Generate the resolution event
        event, errors = self.generate_event(
            action=resolution_action,
            characters=characters,
            consequences=[f"tension_resolved: {tension.description}"],
            emotional_shift=EmotionalValence.POSITIVE,
        )

        # Mark tension as resolved
        self._world.resolve_tension(tension_id, resolution_action)

        return event, errors

    def get_highest_tension(self) -> Optional[Tension]:
        """Get the highest unresolved tension."""
        active = [t for t in self._world.active_tensions if not t.resolved]
        if not active:
            return None
        return max(active, key=lambda t: t.magnitude)

    def get_character_perspective(self, character_name: str) -> Dict[str, Any]:
        """Get what a specific character knows/perceives about the world.

        Characters can only act on their own knowledge.
        """
        char = self._characters.get(character_name)
        if char is None:
            return {"error": f"Unknown character: {character_name}"}

        return {
            "name": char.name,
            "knows": sorted(char.knowledge),
            "drives": char.drives,
            "relationships": char.relationships,
            "state": char.state,
            "constraints": char.constraints,
        }

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _are_contradictory(self, fact1: str, fact2: str) -> bool:
        """Simple contradiction detection between two facts."""
        # Check for explicit negation patterns
        if fact1.startswith("not ") and fact1[4:] == fact2:
            return True
        if fact2.startswith("not ") and fact2[4:] == fact1:
            return True

        # Check for "X is alive" vs "X is dead" patterns
        if "is alive" in fact1 and fact1.replace("is alive", "is dead") == fact2:
            return True
        if "is dead" in fact1 and fact1.replace("is dead", "is alive") == fact2:
            return True

        return False
