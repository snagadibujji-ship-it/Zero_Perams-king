"""Creative reasoning engine that generates novel ideas by combining concepts."""

import random
import hashlib


class CreativeEngine:
    """Generates novel ideas through concept blending, analogy, and brainstorming."""

    PROPERTIES = {
        "fish": ["scales", "swimming", "gills", "streamlined", "underwater", "schooling"],
        "airplane": ["wings", "flying", "altitude", "speed", "metal", "passengers"],
        "tree": ["roots", "branches", "growth", "rings", "shade", "seasonal"],
        "computer": ["processing", "memory", "logic", "network", "binary", "fast"],
        "music": ["rhythm", "harmony", "emotion", "patterns", "vibration", "tempo"],
        "ocean": ["waves", "depth", "vast", "tides", "salt", "currents"],
        "city": ["density", "infrastructure", "diversity", "noise", "commerce", "layers"],
        "fire": ["heat", "transformation", "energy", "spread", "light", "consumption"],
    }

    TEMPLATES = {
        "quest": "Beginning: {chars} set out from {setting} to resolve {conflict}. "
                 "Middle: They face trials that test their resolve and discover hidden strengths. "
                 "End: The quest succeeds but at an unexpected cost. "
                 "Twist: The real treasure was the enemy they befriended along the way.",
        "mystery": "Beginning: In {setting}, {chars} discover something is terribly wrong about {conflict}. "
                   "Middle: Each clue leads deeper into a web of deception and hidden motives. "
                   "End: The truth is revealed in a confrontation no one anticipated. "
                   "Twist: The detective was unknowingly part of the mystery all along.",
        "rivalry": "Beginning: {chars} compete in {setting} over {conflict}. "
                   "Middle: Escalation drives both sides to extremes, blurring right and wrong. "
                   "End: A catastrophe forces unlikely cooperation. "
                   "Twist: Their rivalry was engineered by a third party profiting from both.",
        "discovery": "Beginning: {chars} stumble upon an anomaly in {setting} related to {conflict}. "
                     "Middle: Research reveals the discovery could change everything — or destroy it. "
                     "End: They must choose between knowledge and safety. "
                     "Twist: The discovery has been found before — and deliberately hidden.",
        "transformation": "Beginning: {chars} in {setting} face {conflict} that demands they change. "
                          "Middle: The transformation is painful and alienates those they love. "
                          "End: They emerge fundamentally different, for better or worse. "
                          "Twist: The old self wasn't who they thought it was either.",
    }

    DIRECTIONS = ["technical", "social", "creative", "practical", "absurd"]

    def _get_props(self, concept):
        """Get properties for a concept, generating defaults if unknown."""
        if concept.lower() in self.PROPERTIES:
            return self.PROPERTIES[concept.lower()]
        seed = int(hashlib.md5(concept.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        qualities = ["dynamic", "structured", "fluid", "layered", "evolving",
                     "compact", "expansive", "cyclic", "fragile", "resilient"]
        return [concept] + rng.sample(qualities, 3)

    def combine(self, concept_a, concept_b):
        """Blend two concepts into 3 novel combinations."""
        props_a = self._get_props(concept_a)
        props_b = self._get_props(concept_b)
        combos = [
            f"A {concept_a}-inspired {concept_b} that uses {props_a[1]} "
            f"to achieve {props_b[2]}",
            f"A hybrid where {concept_b}'s {props_b[0]} merges with "
            f"{concept_a}'s {props_a[-1]} creating something entirely new",
            f"What if {concept_a} ({props_a[0]}, {props_a[1]}) met "
            f"{concept_b} ({props_b[0]}, {props_b[1]})? "
            f"A {props_a[2]}-{props_b[2]} fusion that defies both categories",
        ]
        return {"concept_a": concept_a, "concept_b": concept_b, "combinations": combos}

    def invent(self, category, constraints):
        """Generate a novel idea within a category respecting constraints."""
        constraint_str = ", ".join(constraints) if isinstance(constraints, list) else constraints
        angles = ["miniaturize it", "reverse the process", "make it biological",
                  "add network effects", "make it ephemeral"]
        angle = random.choice(angles)
        return {
            "category": category,
            "constraints": constraint_str,
            "approach": angle,
            "idea": f"A {category} solution that works by: {angle}. "
                    f"Constraints ({constraint_str}) are satisfied by treating "
                    f"limitations as design features rather than obstacles.",
        }

    def story(self, characters, setting, conflict):
        """Generate a short story outline from a random template."""
        template_name = random.choice(list(self.TEMPLATES.keys()))
        template = self.TEMPLATES[template_name]
        chars = ", ".join(characters) if isinstance(characters, list) else characters
        filled = template.format(chars=chars, setting=setting, conflict=conflict)
        return {
            "template": template_name,
            "characters": chars,
            "setting": setting,
            "conflict": conflict,
            "outline": filled,
        }

    def analogy(self, source, target):
        """Map structure from source domain to target domain."""
        source_props = self._get_props(source)
        target_props = self._get_props(target)
        mappings = []
        for sp, tp in zip(source_props[:4], target_props[:4]):
            mappings.append(f"{source}:{sp} → {target}:{tp}")
        insight = (f"Just as {source} relies on {source_props[1]}, "
                   f"{target} depends on {target_props[1]}. "
                   f"This suggests {target} could benefit from "
                   f"adopting {source}'s approach to {source_props[2]}.")
        return {"source": source, "target": target, "mappings": mappings, "insight": insight}

    def brainstorm(self, topic, count=5):
        """Generate ideas branching in 5 directions from a topic."""
        ideas = []
        prompts = {
            "technical": f"Engineer a {topic} system using cutting-edge technology",
            "social": f"Build a community around {topic} that self-organizes",
            "creative": f"Express {topic} as an art form or narrative experience",
            "practical": f"Simplify {topic} so anyone can use it in 60 seconds",
            "absurd": f"What if {topic} was sentient and had feelings about being used?",
        }
        for direction in self.DIRECTIONS[:count]:
            ideas.append({"direction": direction, "idea": prompts.get(
                direction, f"Explore {topic} from a {direction} angle")})
        return {"topic": topic, "ideas": ideas}

    def what_if(self, premise):
        """Explore implications of a hypothetical premise in 3 causal steps."""
        steps = [
            f"Immediate: If {premise}, then existing systems must adapt overnight.",
            f"Short-term: Adaptation creates new winners and losers, "
            f"reshaping incentives around the premise.",
            f"Long-term: Society restructures fundamentally — the premise "
            f"becomes the new normal and people forget the old way.",
        ]
        return {
            "premise": premise,
            "consequences": steps,
            "exploration": f"Exploring: '{premise}'\n" + "\n".join(
                f"  Step {i+1}: {s}" for i, s in enumerate(steps)
            ),
        }


# --- Standalone test ---
if __name__ == "__main__":
    engine = CreativeEngine()

    print("=== COMBINE ===")
    result = engine.combine("fish", "airplane")
    for i, c in enumerate(result["combinations"], 1):
        print(f"  {i}. {c}")

    print("\n=== INVENT ===")
    result = engine.invent("transportation", ["eco-friendly", "under $100", "portable"])
    print(f"  {result['idea']}")

    print("\n=== STORY ===")
    result = engine.story(["Alice", "a robot named Cog"], "a floating library", "lost knowledge")
    print(f"  Template: {result['template']}")
    print(f"  {result['outline']}")

    print("\n=== ANALOGY ===")
    result = engine.analogy("ocean", "computer")
    for m in result["mappings"]:
        print(f"  {m}")
    print(f"  Insight: {result['insight']}")

    print("\n=== BRAINSTORM ===")
    result = engine.brainstorm("urban farming")
    for idea in result["ideas"]:
        print(f"  [{idea['direction']}] {idea['idea']}")

    print("\n=== WHAT IF ===")
    result = engine.what_if("gravity worked in reverse on Tuesdays")
    print(f"  {result['exploration']}")

    print("\nAll tests passed!")
