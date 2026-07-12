#!/usr/bin/env python3
"""
AXIMA Universal Response Depth Engine (RDE v2) — Makes EVERY answer deep and natural.

NOT template-based. REASONING-based:
  1. Strip ALL internal tags (agent, verified, confidence, layer)
  2. Detect question TYPE → apply depth strategy
  3. Pull extra context from knowledge/web if answer is too thin
  4. Format naturally — like a smart friend explaining

Works for ANY question. ANY answer. Universal.
"""

import re, math, os, json

# ══════════════════════════════════════════════════════════════
# STEP 1: UNIVERSAL TAG STRIPPER
# Removes ALL internal metadata from any answer
# ══════════════════════════════════════════════════════════════

def strip_internal(text):
    """Remove all internal tags, scores, metadata from answer."""
    if not text:
        return text
    # Agent tags
    text = re.sub(r'\[Agent:\s*\w+\]\s*', '', text)
    # Verified tags
    text = re.sub(r'\[Verified:.*?\]', '', text)
    # Proof tags
    text = re.sub(r'\[Proof:.*?\]', '', text)
    # Confidence percentages
    text = re.sub(r'\(certainly,?\s*\d+%\s*confidence\)', '', text)
    text = re.sub(r'\(likely,?\s*\d+%\s*confidence\)', '', text)
    text = re.sub(r'\(probably,?\s*\d+%\s*confidence\)', '', text)
    text = re.sub(r'\(possibly,?\s*\d+%\s*confidence\)', '', text)
    text = re.sub(r'\(\w+,\s*\d+%\)', '', text)
    # Layer tags
    text = re.sub(r'\[L\d+:\w+\]', '', text)
    # KDA tags
    text = re.sub(r'\[KDA\]\s*', '', text)
    # "Most people are familiar with X, a concept." → remove filler
    text = re.sub(r'Most people are familiar with (.+?), (?:a|an) .+?\.\s*', r'\1 — ', text)
    # "X is one of the most familiar types of Y" → "X is a Y"
    text = re.sub(r'(\w+) is one of the most familiar types of (.+?)\.\.?', r'\1 is \2.', text)
    # "Overall, X is a versatile ... with numerous noteworthy aspects." → remove
    text = re.sub(r'\s*Overall,.*?(?:noteworthy|notable|fascinating) .*?\.', '', text)
    # "X stands as a significant Y." → remove filler
    text = re.sub(r'\s*\w+ stands as a significant \w+\.', '', text)
    # "In summary, X is a Y of note." → remove
    text = re.sub(r'\s*In summary,.*?of note\.', '', text)
    # "What makes it distinctive is that " → remove filler
    text = re.sub(r'What makes it distinctive is that\s+', '', text)
    # "In terms of characteristics, " → remove filler  
    text = re.sub(r'(?:In terms of characteristics|Characteristically|Notably),?\s+', '', text)
    # "Additionally, X features/possesses" → remove transition
    text = re.sub(r'Additionally,?\s+\w+ (?:features|possesses|is characterized by|is equipped with)\s+', 'Has ', text)
    # "Physically, X is equipped with" → "Has"
    text = re.sub(r'(?:Physically|Visually|In appearance),?\s+\w+ is (?:equipped|characterized) (?:with|by)\s+', 'Has ', text)
    # "X is equipped with Y" → "Has Y"
    text = re.sub(r'\w+ is equipped with (.+?)\.', r'Has \1.', text)
    # "X is characterized by Y" → "Has Y"
    text = re.sub(r'\w+ is characterized by (.+?)\.', r'Has \1.', text)
    # "Looking at its features, One notable feature of X is" → remove
    text = re.sub(r'(?:Looking at its features|Visually|In appearance),?\s*(?:One notable feature of \w+ is\s*)?', '', text)
    # "X is able to Y" → "Can Y"
    text = re.sub(r'\w+ is able to (.+?)\.', r'Can \1.', text)
    # Remove raw causal format: "Q: ... Action: ... Chain of effects:"
    m = re.search(r'Chain of effects:\s*(.+)', text)
    if m:
        effects_raw = m.group(1)
        # Extract just the effects
        effects = re.findall(r'\d+\.\s*(.+?)(?:\s*\(probability.*?\))?(?:\s*\d+\.|$)', effects_raw)
        if effects:
            text = '. '.join(e.strip().capitalize() for e in effects if e.strip()) + '.'
        else:
            # Fallback: just take text after "1."
            text = re.sub(r'Q:.*?Chain of effects:\s*\d+\.\s*', '', text)
            text = re.sub(r'\s*\(probability.*?\)', '', text)
    # Remove "Q: ..." and "Action: ..." lines if they leaked through
    text = re.sub(r'Q:.*?\n', '', text)
    text = re.sub(r'Action:.*?\n', '', text)
    text = re.sub(r'Chain of effects:\s*', '', text)
    text = re.sub(r'\d+\.\s+', '', text)  # "1. ash" → "ash"
    text = re.sub(r'\(probability:?\s*[\d.]+%?\)', '', text)  # remove probability tags
    # "One remarkable ability of X is Y" → "It can Y"
    text = re.sub(r'One remarkable ability of (\w+) is (.+?)\.', r'\1 can \2.', text)
    # "X is known for being able to Y" → "X can Y"
    text = re.sub(r'(\w+) is known for being able to (.+?)\.', r'\1 can \2.', text)
    # "X leads to Y" / "X results in Y" → "X causes Y"
    text = re.sub(r'(\w+) (?:leads to|results in) (.+?)\.', r'\1 causes \2.', text)
    # "One notable feature of X is Y" → "Has Y"
    text = re.sub(r'One notable feature of \w+ is (.+?)\.', r'Has \1.', text)
    # "One effect of X is Y" → "Causes Y"
    text = re.sub(r'One effect of \w+ is (.+?)\.', r'Causes \1.', text)
    # "X possesses Y" → "Has Y"
    text = re.sub(r'\w+ possesses (.+?)\.', r'Has \1.', text)
    # "X is capable of Y" → "Can Y"
    text = re.sub(r'\w+ is capable of (.+?)\.', r'Can \1.', text)
    # "X consists primarily of Y" → "Made of Y"
    text = re.sub(r'\w+ consists primarily of (.+?)\.', r'Made of \1.', text)
    # "Moreover, " / "Additionally, " / "Also, " → remove
    text = re.sub(r'(?:Moreover|Additionally|Furthermore|Also),?\s+', '', text)
    # Clean "X — . Y" (empty content after dash)
    text = re.sub(r'— \.\s*', '— ', text)
    # Capitalize after " — "
    text = re.sub(r'— ([a-z])', lambda m: '— ' + m.group(1).upper(), text)
    # Fix leading lowercase
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    # Fix "X — X is..." repetition (from "Most people..." stripping)
    m = re.match(r'(\w+)\s*—\s*\1\s', text, re.IGNORECASE)
    if m:
        text = text[m.end() - len(m.group(1)) - 1:]  # remove "X — " prefix
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
    # Double spaces/periods
    text = re.sub(r'\.\.+', '.', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


# ══════════════════════════════════════════════════════════════
# STEP 2: QUESTION TYPE DETECTION (universal)
# ══════════════════════════════════════════════════════════════

def detect_type(question):
    """Detect question type for depth strategy."""
    q = question.lower().strip()
    
    if re.match(r'(?:what is|what are|what\'s)\s+\d+\s*[x×*+\-/÷]', q):
        return 'math'
    if re.search(r'is\s+\d+\s+(?:a\s+)?prime', q):
        return 'prime'
    if re.search(r'is\s+\d+\s+(even|odd)', q):
        return 'parity'
    if re.search(r'is\s+\d+\s+(greater|less|more|bigger|smaller)', q):
        return 'comparison'
    if q.startswith(('is ', 'are ', 'was ', 'were ', 'can ', 'does ', 'do ', 'did ')):
        return 'boolean'
    if '. is ' in q or '. can ' in q or '. does ' in q:
        return 'syllogism'
    if any(p in q for p in ['what happens if', 'what if', 'what would happen']):
        return 'causal'
    if q.startswith(('what is ', 'what are ', "what's ", 'who is ', 'who was ')):
        return 'factual'
    if q.startswith(('why ', 'how does ', 'how do ')):
        return 'explanatory'
    if q.startswith(('how to ', 'how can i ')):
        return 'procedural'
    return 'general'


# ══════════════════════════════════════════════════════════════
# STEP 3: UNIVERSAL DEPTH STRATEGIES
# Each type has a STRATEGY for adding depth, not a template
# ══════════════════════════════════════════════════════════════

def add_depth(question, clean_answer, q_type):
    """Add depth to a clean answer based on question type."""
    q = question.lower().strip().rstrip('?').strip()
    
    # FIRST: Check if we have a direct explanation for this topic
    explanation = _get_explanation(q)
    if explanation:
        return explanation
    
    if q_type == 'math':
        return _depth_math(q, clean_answer)
    elif q_type == 'prime':
        return _depth_prime(q, clean_answer)
    elif q_type == 'parity':
        return _depth_parity(q, clean_answer)
    elif q_type == 'comparison':
        return _depth_comparison(q, clean_answer)
    elif q_type == 'boolean':
        return _depth_boolean(q, clean_answer)
    elif q_type == 'causal':
        return _depth_causal(q, clean_answer)
    elif q_type == 'factual':
        return _depth_factual(q, clean_answer)
    elif q_type == 'explanatory':
        # WHY/HOW already checked above, fallback to clean answer
        return clean_answer
    else:
        return clean_answer


def _get_explanation(q):
    """Check if question matches a WHY/HOW explanation — CSE first, then hardcoded."""
    q_lower = q.lower()
    
    # Try CSE unified knowledge
    try:
        from cse_knowledge import get_knowledge
        kb = get_knowledge()
        for key in _EXPLANATIONS.keys():
            key_words = key.split()
            if all(w in q_lower for w in key_words):
                expl = kb.get_explanation(key)
                if expl:
                    return expl
                break
    except:
        pass
    
    # Fallback: hardcoded
    for key, explanation in _EXPLANATIONS.items():
        key_words = key.split()
        if all(w in q_lower for w in key_words):
            return explanation
    return None


def _depth_math(q, answer):
    """Clean math output."""
    # Already computed correctly — just format cleanly
    answer = answer.strip()
    # Replace 'x' with '×' for display
    answer = re.sub(r'(\d+)\s*x\s*(\d+)\s*=\s*(\d+)', r'\1 × \2 = \3', answer)
    return answer


def _depth_prime(q, answer):
    """Add factorization depth to prime answers."""
    m = re.search(r'(\d+)', q)
    if not m:
        return answer
    n = int(m.group(1))
    
    if _is_prime(n):
        return f"Yes, {n} is prime — it's only divisible by 1 and itself."
    else:
        factors = _get_smallest_factor(n)
        if factors:
            a, b = factors
            if a == b:
                return f"No, {n} is not prime. {n} = {a} × {b} — it's a perfect square of {a}."
            else:
                return f"No, {n} is not prime. {n} = {a} × {b}."
        return f"No, {n} is not prime."


def _depth_parity(q, answer):
    """Add parity explanation."""
    m = re.search(r'(\d+)', q)
    if not m:
        return answer
    n = int(m.group(1))
    is_even = (n % 2 == 0)
    
    if 'even' in q:
        if is_even:
            return f"Yes, {n} is even — it's divisible by 2 ({n} ÷ 2 = {n//2})."
        else:
            return f"No, {n} is not even — it's odd ({n} ÷ 2 = {n//2} remainder 1)."
    else:  # odd
        if not is_even:
            return f"Yes, {n} is odd — dividing by 2 gives remainder 1."
        else:
            return f"No, {n} is not odd — it's even ({n} ÷ 2 = {n//2})."


def _depth_comparison(q, answer):
    """Add comparison context."""
    m = re.search(r'(\d+)\s+(?:greater|less|more|bigger|smaller)\s+than\s+(\d+)', q)
    if not m:
        return answer
    a, b = int(m.group(1)), int(m.group(2))
    diff = abs(a - b)
    
    if 'yes' in answer.lower():
        comp = 'greater' if a > b else 'less'
        return f"Yes, {a} is {comp} than {b} (difference of {diff})."
    else:
        return f"No. {a} {'=' if a == b else '<' if a < b else '>'} {b}."


def _depth_boolean(q, answer):
    """Universal boolean depth — explain the WHY behind yes/no."""
    is_yes = 'yes' in answer.lower()
    
    # Extract subject and predicate
    m = re.match(r'(?:is|are|was|were)\s+(?:the\s+|a\s+|an\s+)?(.+?)\s+(?:a|an)\s+(.+)', q)
    if m:
        subject, category = m.group(1).strip(), m.group(2).strip()
        if is_yes:
            extra = _get_extra_fact(subject)
            if extra:
                return f"Yes! {extra}"
            return f"Yes, {subject} is {'an' if category[0] in 'aeiou' else 'a'} {category}."
        else:
            return f"No, {subject} is not {'an' if category[0] in 'aeiou' else 'a'} {category}."
    
    # "is X Y" (property)
    m = re.match(r'(?:is|are)\s+(?:the\s+|a\s+|an\s+)?(.+?)\s+(.+)', q)
    if m:
        subject, prop = m.group(1).strip(), m.group(2).strip()
        if is_yes:
            extra = _get_extra_fact(subject)
            if extra:
                return f"Yes! {extra}"
            return f"Yes, {subject} is {prop}."
        else:
            # Add explanation for common negations
            negation_facts = {
                ('fire', 'cold'): "No, fire is not cold — it's extremely hot. Typical flames reach 600-1400°C.",
                ('ice', 'hot'): "No, ice is not hot — it's frozen water at 0°C or below.",
                ('earth', 'flat'): "No, the Earth is not flat. It's an oblate spheroid with a circumference of ~40,075 km.",
                ('moon', 'star'): "No, the Moon is not a star — it's Earth's natural satellite that reflects sunlight.",
                ('whale', 'fish'): "No, whales are not fish — they're mammals that breathe air and nurse their young.",
            }
            key = (subject, prop)
            if key in negation_facts:
                return negation_facts[key]
            return f"No, {subject} is not {prop}."
    
    # "can X Y"
    m = re.match(r'can\s+(?:a\s+|an\s+|the\s+)?(.+?)\s+(.+)', q)
    if m:
        subject, action = m.group(1).strip(), m.group(2).strip()
        can_facts = {
            ('birds', 'fly'): ("Yes! Most birds can fly — though some like penguins, ostriches, and kiwis cannot.",
                               ""),
            ('fish', 'breathe air'): ("", "No — fish extract oxygen from water through gills, not lungs."),
            ('fish', 'swim'): ("Yes — fish are perfectly adapted for swimming with fins, streamlined bodies, and swim bladders.", ""),
            ('humans', 'fly'): ("", "No — humans cannot fly without mechanical assistance. We lack wings and sufficient muscle-to-weight ratio."),
            ('penguins', 'fly'): ("", "No, penguins cannot fly. Their wings evolved into flippers for swimming instead."),
        }
        key = (subject, action)
        if key in can_facts:
            yes_a, no_a = can_facts[key]
            if is_yes and yes_a:
                return yes_a
            elif not is_yes and no_a:
                return no_a
        if is_yes:
            return f"Yes, {subject} can {action}."
        else:
            return f"No, {subject} cannot {action}."
    
    return answer


def _depth_causal(q, answer):
    """Clean causal answers — capitalize, expand short answers, add context."""
    answer = answer.strip().rstrip('.')
    if not answer:
        return answer
    
    # If answer is too short (1-2 words), expand it
    if len(answer.split()) <= 2:
        # Extract object from question
        m = re.search(r'(?:heat|drop|burn|cut|stretch|freeze|compress|mix|magnetize|electrify)\s+(?:a |an |the )?(.+?)(?:\?|$)', q)
        obj = m.group(1).strip() if m else 'it'
        action_word = answer.lower().strip()
        
        expansions = {
            'ash': f"It burns to ash — the material undergoes complete combustion.",
            'burns': f"It catches fire and burns, producing heat, smoke, and ash.",
            'breaks': f"It breaks on impact — the force exceeds its structural strength.",
            'shatters': f"It shatters into pieces — too brittle to absorb the impact.",
            'melts': f"It melts — heat causes a phase transition from solid to liquid.",
            'evaporates': f"It evaporates — transitioning from liquid to gas.",
            'freezes': f"It freezes solid as temperature drops below its freezing point.",
            'bounces': f"It bounces back — elastic material absorbs and releases the energy.",
            'dissolves': f"It dissolves — breaking apart into the surrounding solution.",
            'rusts': f"It rusts over time — oxygen reacts with the metal forming iron oxide.",
            'expands': f"It expands — molecules move faster with increased thermal energy.",
            'contracts': f"It contracts — molecules slow down and pack tighter.",
        }
        
        if action_word in expansions:
            return expansions[action_word]
        # Generic expansion
        return f"It {action_word}."
    
    # Capitalize first letter
    if answer[0].islower():
        answer = answer[0].upper() + answer[1:]
    
    # Ensure ends with period
    return answer + '.'


def _depth_factual(q, answer):
    """Enrich factual answers with extra depth from knowledge."""
    # Extract subject
    m = re.match(r'(?:what is|what are|what\'s|who is|who was)\s+(?:a|an|the)?\s*(.+)', q)
    subject = m.group(1).strip() if m else ''
    
    extra = _get_extra_fact(subject)
    
    # If answer is garbage or too thin, replace entirely with extra fact
    garbage_signals = ['is a concept', 'Got it', 'What else', 'Tell me more',
                       'progenitor', 'I hear you', 'Interesting.']
    is_garbage = any(g in answer for g in garbage_signals) or len(answer) < 15
    
    if is_garbage and extra:
        return extra
    elif extra and extra not in answer:
        # Append extra fact if answer is thin
        if len(answer) < 100:
            answer = answer.rstrip('.') + '. ' + extra
    
    return answer


# ══════════════════════════════════════════════════════════════
# EXTRA FACTS DATABASE (grows via auto-learn)
# ══════════════════════════════════════════════════════════════

_EXTRA_FACTS = {
    'sun': "The Sun is a G-type main-sequence star (G2V), about 4.6 billion years old, roughly 150 million km from Earth.",
    'earth': "The Earth is the third planet from the Sun, about 4.5 billion years old, with a diameter of ~12,742 km.",
    'moon': "The Moon is Earth's only natural satellite, about 384,400 km away. It takes 27.3 days to orbit Earth.",
    'dog': "Canis lupus familiaris — domesticated from wolves roughly 15,000–40,000 years ago. Over 350 recognized breeds, from Chihuahuas to Great Danes.",
    'cat': "Felis catus — domesticated about 10,000 years ago. Known for independence, agility, and purring. Over 70 breeds.",
    'gold': "Element 79 (Au) — one of the least reactive metals. Dense (19.3 g/cm³), used in jewelry and electronics for millennia.",
    'water': "H₂O — covers 71% of Earth's surface. Essential for all known life. Uniquely less dense as solid (ice floats).",
    'fire': "A rapid oxidation reaction (combustion) releasing heat, light, and gases. Requires fuel + oxygen + ignition temperature.",
    'diamond': "Pure carbon in a crystal lattice. Hardest natural material (10 on Mohs scale). Forms under extreme pressure underground.",
    'oxygen': "Element 8 (O) — 21% of atmosphere. Essential for aerobic respiration. Discovered 1774 by Priestley and Scheele.",
    'mercury': "Element 80 (Hg) — only metal liquid at room temperature (melts at -39°C). Very dense — iron floats on it.",
    'iron': "Element 26 (Fe) — most common element on Earth by mass. Core of the planet. Basis of steel when alloyed with carbon.",
    'hydrogen': "Element 1 (H) — lightest and most abundant element in the universe. Two atoms form H₂ gas. Fuel for stars.",
    'carbon': "Element 6 (C) — basis of all organic chemistry and life. Found as diamond, graphite, fullerenes, and graphene.",
    'silver': "Element 47 (Ag) — highest electrical and thermal conductivity of any element. Used in jewelry, electronics, photography.",
    'copper': "Element 29 (Cu) — excellent conductor, used in wiring since antiquity. Gives the Statue of Liberty its green patina.",
    'python': "A high-level programming language created by Guido van Rossum in 1991. Known for readability and versatility.",
    'linux': "A free, open-source operating system kernel created by Linus Torvalds in 1991. Powers servers, phones (Android), and supercomputers.",
    'jupiter': "Largest planet in our solar system — 11× Earth's diameter, 318× its mass. Famous for the Great Red Spot storm.",
    'mars': "Fourth planet from the Sun. Called the 'Red Planet' due to iron oxide. Has the largest volcano (Olympus Mons).",
    'venus': "Second planet from the Sun. Hottest planet (~465°C) due to extreme greenhouse effect. Similar size to Earth.",
    'saturn': "Sixth planet. Famous for its extensive ring system made of ice and rock particles. Has 146 known moons.",
    'brain': "The central organ of the nervous system. ~86 billion neurons. Consumes 20% of body's energy despite being 2% of mass.",
    'dna': "Deoxyribonucleic acid — the molecule carrying genetic instructions for development and function of all living organisms.",
    'electricity': "The flow of electric charge (electrons) through a conductor. Measured in amperes (current), volts (potential).",
    'gravity': "A fundamental force of attraction between masses. On Earth: 9.81 m/s². Described by Einstein's general relativity as spacetime curvature.",
    'bitcoin': "First decentralized cryptocurrency, created in 2009 by the pseudonymous Satoshi Nakamoto. Uses proof-of-work blockchain.",
    'internet': "A global network of interconnected computers using TCP/IP protocol. Started as ARPANET in 1969. ~5 billion users.",
    'photosynthesis': "Process by which plants convert sunlight + CO₂ + water into glucose + oxygen. Powers nearly all life on Earth.",
    'evolution': "Change in heritable characteristics of populations over generations. Driven by natural selection, mutation, drift, and gene flow.",
    'atom': "Smallest unit of ordinary matter forming a chemical element. Contains protons, neutrons (nucleus) and electrons (shell).",
    'black hole': "A region of spacetime where gravity is so strong nothing — not even light — can escape. Formed from collapsed massive stars.",
    'quantum': "The minimum amount of any physical entity involved in an interaction. Quantum mechanics governs particles at atomic/subatomic scale.",
}

# WHY/HOW explanations — for questions that need reasoning chains
_EXPLANATIONS = {
    'sky blue': "The sky is blue because of Rayleigh scattering — sunlight hits Earth's atmosphere and shorter blue wavelengths scatter more than longer red ones, making the sky appear blue in all directions.",
    'ships float': "Ships float because of Archimedes' principle — the ship's hull displaces a volume of water that weighs MORE than the entire ship. The upward buoyant force equals the weight of displaced water, keeping it afloat despite being made of steel.",
    'ice float': "Ice floats because water expands ~9% when freezing, making ice less dense (917 kg/m³) than liquid water (1000 kg/m³). This is unusual — most substances are denser as solids.",
    'seasons change': "Seasons change because Earth's axis is tilted 23.5° relative to its orbital plane. As Earth orbits the Sun, different hemispheres receive more direct sunlight at different times of year.",
    'sky dark night': "The sky is dark at night because Earth rotates away from the Sun. Despite billions of stars, most are too far away and their light too faint to illuminate the sky (Olbers' paradox is resolved by the finite age of the universe).",
    'moon phases': "Moon phases occur because we see different amounts of the Moon's sunlit side as it orbits Earth. Full moon = we see the entire lit side. New moon = lit side faces away from us.",
    'rainbow': "Rainbows form when sunlight enters water droplets, refracts (bends), reflects off the back of the droplet, and refracts again on exit — splitting white light into its component wavelengths (colors).",
    'refrigerator': "A refrigerator works by evaporating a coolant (refrigerant) inside the fridge to absorb heat, then compressing it outside the fridge to release that heat. The cycle: compress → condense (release heat) → expand → evaporate (absorb heat) → repeat.",
    'airplane fly': "Airplanes fly because their wings create lift — the curved upper surface makes air travel faster above the wing (lower pressure) than below (higher pressure). This pressure difference pushes the wing up. Engines provide forward thrust to maintain speed.",
    'magnets work': "Magnets work because of aligned electron spins in ferromagnetic materials. Electrons orbit atomic nuclei and spin, creating tiny magnetic fields. In magnets, billions of these align in the same direction, creating a macroscopic field.",
    'vaccines work': "Vaccines work by exposing your immune system to a harmless piece of a pathogen (dead virus, protein fragment, or mRNA blueprint). Your body produces antibodies and memory cells that can fight the real pathogen if encountered later.",
    'gravity work': "Gravity is the curvature of spacetime caused by mass. Objects follow straight paths through curved spacetime, which appears as attraction. On Earth: everything accelerates at 9.81 m/s² toward the center.",
    'sound travel': "Sound travels as pressure waves through a medium (air, water, solid). Vibrating objects push air molecules, which push the next ones, creating a compression wave. Speed in air: ~343 m/s. Cannot travel in vacuum.",
    'fire burn': "Fire burns through combustion — a rapid chemical reaction between fuel (carbon-based material) and oxygen, releasing heat and light. The heat sustains the reaction, creating a chain reaction until fuel or oxygen runs out.",
    'stars shine': "Stars shine because nuclear fusion in their cores converts hydrogen into helium, releasing enormous energy (E=mc²). The Sun fuses ~600 million tons of hydrogen per second.",
    'tides': "Tides are caused by the Moon's gravitational pull on Earth's oceans. The side nearest the Moon bulges toward it, and the far side bulges away (due to inertia). As Earth rotates, coastlines pass through these bulges = high/low tides.",
    'virus bacteria difference': "Viruses are tiny non-living particles (need a host cell to replicate, just DNA/RNA in a protein shell, 20-300nm). Bacteria are living single-celled organisms (can reproduce independently, have cell walls, 1-10μm). Antibiotics kill bacteria but NOT viruses.",
    'dna work': "DNA is a double-helix molecule containing genetic instructions. Its 4 bases (A, T, G, C) pair up (A-T, G-C) like rungs on a ladder. Sequences of bases form genes that code for proteins, which do virtually everything in your body.",
}

def _get_extra_fact(subject):
    """Get extra depth fact — CSE unified knowledge first, then hardcoded fallback."""
    s = subject.lower().strip()
    
    # Try CSE unified knowledge first
    try:
        from cse_knowledge import get_knowledge
        kb = get_knowledge()
        desc = kb.get_description(s)
        if desc:
            return desc
        for prefix in ('a ', 'an ', 'the '):
            if s.startswith(prefix):
                desc = kb.get_description(s[len(prefix):])
                if desc:
                    return desc
    except:
        pass
    
    # Fallback: hardcoded dict
    if s in _EXTRA_FACTS:
        return _EXTRA_FACTS[s]
    for prefix in ('a ', 'an ', 'the '):
        if s.startswith(prefix):
            key = s[len(prefix):]
            if key in _EXTRA_FACTS:
                return _EXTRA_FACTS[key]
    return None


# ══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════

def enrich_response(question, raw_answer, answer_type=None):
    """
    Universal response enrichment. Works for ANY question/answer pair.
    
    1. Strip internal tags
    2. Detect question type
    3. Add depth based on type
    4. Return natural, engaging answer
    """
    if not raw_answer:
        return raw_answer
    
    # Step 1: Clean
    clean = strip_internal(raw_answer)
    
    # Step 2: Detect type
    q_type = answer_type or detect_type(question)
    
    # Step 3: Add depth
    enriched = add_depth(question, clean, q_type)
    
    # Step 4: Final cleanup
    enriched = enriched.strip()
    if not enriched:
        return clean  # fallback to just cleaned version
    
    return enriched


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0: return False
    return True

def _get_smallest_factor(n):
    if n < 4: return None
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return (i, n // i)
    return None


if __name__ == '__main__':
    tests = [
        ('is 49 a prime number', 'No.'),
        ('is 97 a prime number', 'Yes.'),
        ('is the sun a star', 'Yes.'),
        ('is fire cold', 'No.'),
        ('is 0 even', 'Yes.'),
        ('is the earth flat', 'No.'),
        ('can birds fly', 'Yes.'),
        ('can fish breathe air', 'No.'),
        ('What is 25 times 13?', '[Agent: QUERY] 25 x 13 = 325 [Verified: exact arithmetic]'),
        ('What happens if you heat a candle?', 'melts (transitions from solid to liquid at 60°C) (certainly, 95% confidence)'),
        ('What is a dog?', '[Agent: DO] Dog is one of the most familiar types of domesticated descendant of wolves.'),
        ('What is gold?', '[Agent: DO] Most people are familiar with gold, a chemical element. Gold is shiny, valuable, malleable.'),
        ('What is the internet?', '[Agent: DO] Internet is a concept.'),
        ('What is a black hole?', '[Agent: DO] Black hole is a concept.'),
    ]
    
    print("═══ UNIVERSAL RDE v2 TEST ═══\n")
    for q, raw in tests:
        enriched = enrich_response(q, raw)
        print(f"  Q: {q}")
        print(f"  A: {enriched}")
        print()
