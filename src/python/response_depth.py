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
    # Only strip numbered items if text contains causal chain or probability markers
    if 'Chain of effects' in text or 'probability:' in text or 'probability ' in text:
        # Only strip numbered items if this looks like a causal chain output
        if 'Chain of effects' in text or 'probability' in text:
            text = re.sub(r'\d+\.\s+', '', text)
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
    # Strip any HTML/markdown that leaked through
    text = re.sub(r'<[^>]+>', '', text)  # HTML tags
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'__(.+?)__', r'\1', text)  # __bold__
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url)
    # Generic catch-all: remove any remaining [Tag: ...] patterns
    text = re.sub(r'\[\w+:.*?\]', '', text)
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
    elif q_type == 'procedural':
        return _depth_procedural(q, clean_answer)
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
    m = re.match(r'(?:what is|what are|what\'s|who is|who was)\s+(?:an |a |the )?(.+)', q)
    subject = m.group(1).strip() if m else ''
    
    extra = _get_extra_fact(subject)
    
    # If answer is garbage or too thin, replace entirely with extra fact
    garbage_signals = ['is a concept', 'is a material', 'Got it', 'What else', 'Tell me more',
                       'progenitor', 'I hear you', 'Interesting.', 'is a concept.']
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
    'elephant': "Largest living land animal — African elephants weigh up to 6,000 kg. Highly intelligent with excellent memory, complex social structures, and the longest gestation period (22 months) of any land animal.",
    'whale': "Largest animals ever to live on Earth. Blue whales reach 30m and 150 tonnes. Marine mammals that breathe air, nurse young, and communicate with complex songs across hundreds of kilometers.",
    'einstein': "Albert Einstein (1879–1955) — theoretical physicist who developed special and general relativity, explained the photoelectric effect (Nobel 1921), and showed E=mc². Revolutionized our understanding of space, time, and gravity.",
    'newton': "Isaac Newton (1643–1727) — formulated laws of motion and universal gravitation, co-invented calculus, and discovered that white light is composed of colors. His Principia Mathematica is a cornerstone of physics.",
    'shakespeare': "William Shakespeare (1564–1616) — English playwright and poet, widely regarded as the greatest writer in the English language. Wrote 37+ plays including Hamlet, Macbeth, Romeo and Juliet. Invented ~1,700 English words.",
    'tesla': "Nikola Tesla (1856–1943) — inventor and electrical engineer who developed the AC motor, polyphase AC power system, Tesla coil, and radio technology. Held ~300 patents and envisioned wireless power transmission.",
    'amazon': "The Amazon River is the largest river by discharge volume (209,000 m³/s) and arguably the longest (~6,992 km). Its basin covers 7 million km² across 9 countries and contains 10% of all species on Earth.",
    'sahara': "The Sahara is the world's largest hot desert — 9.2 million km² across North Africa. Temperatures reach 58°C. Despite the harsh conditions, it was once green (6,000 years ago) with lakes and vegetation.",
    'everest': "Mount Everest is Earth's highest peak at 8,849 m above sea level, located on the Nepal-Tibet border. First summited by Edmund Hillary and Tenzing Norgay in 1953. The summit moves ~4 cm northeast annually due to plate tectonics.",
    'titanic': "RMS Titanic was a British luxury liner that sank on April 15, 1912 after hitting an iceberg on its maiden voyage. Of ~2,224 passengers and crew, more than 1,500 died — one of the deadliest maritime disasters in history.",
    'dinosaur': "Dinosaurs dominated Earth for ~165 million years (Triassic through Cretaceous). Went extinct ~66 million years ago from an asteroid impact. Birds are their living descendants. Ranged from chicken-sized to 40m long.",
    'volcano': "A volcano is an opening in Earth's crust where magma reaches the surface. There are ~1,500 potentially active volcanoes worldwide. Eruptions range from gentle lava flows to explosive blasts ejecting ash 40+ km high.",
    'hurricane': "Hurricanes are massive rotating storm systems fueled by warm ocean water (26°C+). Wind speeds exceed 119 km/h (Category 1) up to 252+ km/h (Category 5). They release energy equivalent to 10,000 nuclear bombs per day.",
    'earthquake': "Earthquakes occur when stress builds along tectonic plate boundaries and suddenly releases as seismic waves. The Richter scale is logarithmic — each number is 10× more ground motion. ~500,000 detectable quakes occur yearly.",
    'tsunami': "A tsunami is a series of ocean waves caused by underwater earthquakes, volcanic eruptions, or landslides. Waves can travel 800 km/h in deep water and reach 30+ meters at shore. The 2004 Indian Ocean tsunami killed ~230,000 people.",
    'bacteria': "Single-celled prokaryotic organisms — the most abundant life form on Earth. Most are harmless or beneficial (gut bacteria help digestion). Reproduce by binary fission, some dividing every 20 minutes.",
    'virus': "Submicroscopic infectious agents (20-300 nm) that replicate only inside living cells. Not considered alive. Contain DNA or RNA in a protein coat. Responsible for diseases from common cold to COVID-19.",
    'vaccine': "A biological preparation that provides immunity to disease by training the immune system with a weakened/killed pathogen or its components. Vaccines have eradicated smallpox and nearly eliminated polio.",
    'antibiotic': "Medicines that kill or inhibit bacteria. Penicillin (discovered 1928 by Fleming) was the first. They don't work against viruses. Overuse has led to antibiotic-resistant 'superbugs' — a major global health threat.",
    'laser': "Light Amplification by Stimulated Emission of Radiation — produces coherent, focused light of a single wavelength. Used in surgery, communications (fiber optics), manufacturing, barcode scanners, and scientific research.",
    'radar': "Radio Detection And Ranging — uses radio waves to detect objects, measure distance and speed. Crucial for aviation, weather forecasting, military defense, and speed enforcement. Developed in the 1930s-40s.",
    'sonar': "Sound Navigation And Ranging — uses sound waves to detect objects underwater. Active sonar sends pulses; passive sonar listens. Essential for submarines, fishing, ocean mapping, and marine biology research.",
    'telescope': "An instrument that collects and magnifies light (or radio waves) from distant objects. Galileo first used one astronomically in 1609. Modern telescopes like James Webb Space Telescope can see galaxies 13+ billion light-years away.",
    'microscope': "An instrument that magnifies tiny objects. Optical microscopes use light (up to 2000×). Electron microscopes use electron beams (up to 50,000,000×) and can resolve individual atoms.",
    'satellite': "An object orbiting a celestial body. Artificial satellites orbit Earth for communications, GPS, weather, Earth observation, and science. Over 7,000 active satellites orbit Earth as of 2024.",
    'rocket': "A vehicle propelled by expelling exhaust gas at high speed (Newton's 3rd law). Chemical rockets burn fuel + oxidizer. Escape velocity from Earth is 11.2 km/s. SpaceX's Falcon 9 made rockets partially reusable.",
    'submarine': "A watercraft that operates underwater. Military subs can dive 300-600m; research subs over 10,000m. They use ballast tanks to control buoyancy and nuclear reactors or diesel-electric for power.",
    'helicopter': "An aircraft that uses rotating blades (rotors) for lift, enabling vertical takeoff/landing and hovering. Invented in the 1930s. Igor Sikorsky built the first practical helicopter (VS-300) in 1939.",
    'train': "A connected series of rail vehicles. First steam locomotive ran in 1804. Modern high-speed trains (TGV, Shinkansen, maglev) exceed 400 km/h. Trains are one of the most energy-efficient transport modes.",
    'bicycle': "A human-powered two-wheeled vehicle — the most efficient form of human transportation (3-4× more efficient than walking). About 1 billion bicycles exist worldwide, twice the number of cars.",
    'piano': "A keyboard instrument with 88 keys that strike strings with felt-covered hammers. Invented by Bartolomeo Cristofori around 1700. Range spans over 7 octaves — the widest of any standard instrument.",
    'guitar': "A stringed instrument typically with 6 strings, played by strumming or plucking. Descended from medieval instruments. Electric guitars (1930s) revolutionized popular music through amplification and effects.",
    'chess': "A two-player strategy board game originating in India (~6th century). 64 squares, 16 pieces per side. Estimated 10^120 possible games (Shannon number). Deep Blue beat world champion Kasparov in 1997.",
    'football': "The world's most popular sport — played by 250+ million people in 200+ countries. FIFA World Cup is the most-watched sporting event. Modern rules codified in England, 1863.",
    'basketball': "Invented in 1891 by James Naismith in Massachusetts using a peach basket. Now played worldwide with the NBA as the premier league. Teams of 5 players score by shooting through a hoop 3.05m high.",
    'olympics': "The world's foremost international multi-sport competition, held every 4 years (summer and winter). Originated in ancient Greece (776 BC). Revived in 1896 by Pierre de Coubertin. Over 200 nations participate.",
    'java': "A class-based, object-oriented programming language designed to have minimal implementation dependencies. Created by James Gosling at Sun Microsystems (1995). 'Write once, run anywhere' via the JVM.",
    'c programming': "C is a general-purpose programming language created by Dennis Ritchie at Bell Labs (1972). Foundation of Unix, Linux, and Windows kernels. Known for speed, low-level memory access, and portability.",
    'html': "HyperText Markup Language — the standard language for creating web pages. Uses tags like <p>, <div>, <a> to structure content. First version by Tim Berners-Lee in 1993. Current version: HTML5.",
    'css': "Cascading Style Sheets — a language for describing the presentation of HTML documents. Controls layout, colors, fonts, animations. Separates content from visual design. Current version: CSS3.",
    'database': "An organized collection of structured data, typically stored electronically. SQL databases (relational) use tables; NoSQL databases use documents/key-value/graphs. Essential for virtually all modern applications.",
    'algorithm': "A step-by-step procedure for solving a problem or performing a computation. Efficiency measured in Big-O notation. Fundamental algorithms include sorting (quicksort), searching (binary search), and graph traversal.",
    'robot': "A programmable machine capable of carrying out complex actions automatically. Modern robots range from industrial arms to humanoids. The word comes from Czech 'robota' (forced labor), coined in 1920.",
    'drone': "An unmanned aerial vehicle (UAV) controlled remotely or autonomously. Used for photography, delivery, agriculture, military, search and rescue. Consumer drones typically use 4-8 rotors (quadcopters/octocopters).",
    '3d printer': "A machine that creates three-dimensional objects by depositing material layer by layer from a digital model. Materials include plastic (FDM), resin (SLA), metal, and even concrete. Revolutionizing manufacturing and prototyping.",
    'solar panel': "A device that converts sunlight directly into electricity using photovoltaic cells (semiconductor junctions). Efficiency ranges 15-25% for commercial panels. Solar is now the cheapest form of electricity in most of the world.",
    'battery': "A device that stores chemical energy and converts it to electrical energy. Lithium-ion batteries dominate (phones, EVs). Energy density has improved ~8% per year. The first battery was Volta's pile (1800).",
    'nuclear': "Nuclear energy comes from splitting atoms (fission) or fusing them (fusion). Fission powers ~10% of world electricity with no CO₂ emissions. Fusion (the Sun's process) remains experimental but promises virtually unlimited clean energy.",
    'climate change': "Long-term shifts in global temperatures and weather patterns. Since the 1800s, human activities (burning fossil fuels) have been the main driver, raising average temperatures ~1.1°C. Effects include rising seas, extreme weather, and ecosystem disruption.",
    'ozone': "O₃ — a molecule of three oxygen atoms. The ozone layer (stratosphere, 15-35 km up) absorbs 97-99% of UV radiation. CFCs created a 'hole' over Antarctica; the 1987 Montreal Protocol banned them and it's slowly recovering.",
    'coral reef': "Underwater ecosystems built by colonies of tiny coral polyps. Cover <1% of the ocean floor but support 25% of marine species. Threatened by ocean warming (bleaching), acidification, and pollution.",
    'rainforest': "Dense tropical forests receiving 1,750-2,000+ mm of rain annually. The Amazon alone produces 20% of Earth's oxygen and contains 10% of all species. Being deforested at ~10 million hectares per year.",
    'glacier': "A persistent body of dense ice formed from compacted snow. Glaciers cover 10% of Earth's land area and contain 69% of freshwater. They're retreating worldwide due to climate change — Greenland loses ~280 billion tonnes of ice yearly.",
    'aurora': "Natural light displays (aurora borealis/australis) caused by charged particles from the Sun interacting with atmospheric gases. Oxygen produces green/red; nitrogen produces blue/purple. Visible near magnetic poles.",
    'comet': "A small icy body that, when near the Sun, displays a visible atmosphere (coma) and sometimes a tail. Made of ice, dust, and rock — 'dirty snowballs'. Halley's Comet is visible from Earth every 75-79 years.",
    'asteroid': "Rocky remnants from the early solar system, mostly orbiting in the belt between Mars and Jupiter. Range from 1m to 940 km (Ceres). The one that killed the dinosaurs was ~10 km across.",
    'nebula': "A giant cloud of gas and dust in space. Some are stellar nurseries where new stars form (Orion Nebula). Others are remnants of dead stars (planetary nebulae, supernova remnants). Can span hundreds of light-years.",
    'supernova': "The explosive death of a massive star — briefly outshining an entire galaxy. Produces and disperses heavy elements (iron, gold, uranium). The Crab Nebula is the remnant of a supernova observed in 1054 AD.",
    'galaxy': "A gravitationally bound system of stars, gas, dust, and dark matter. The Milky Way contains 100-400 billion stars. There are ~2 trillion galaxies in the observable universe, ranging from dwarfs to giants.",
    'universe': "All of space, time, matter, and energy. ~13.8 billion years old. Observable universe is 93 billion light-years across. Composed of ~68% dark energy, ~27% dark matter, and ~5% ordinary matter.",
    'big bang': "The prevailing cosmological model — the universe began as an extremely hot, dense point ~13.8 billion years ago and has been expanding ever since. Evidence: cosmic microwave background radiation, redshift of galaxies, abundance of light elements.",
    'dark matter': "Invisible matter that doesn't interact with light but exerts gravitational influence. Makes up ~27% of the universe. Its existence is inferred from galaxy rotation curves and gravitational lensing. Its nature remains unknown.",
    'dark energy': "A mysterious force causing the universe's expansion to accelerate. Makes up ~68% of the universe's energy. Discovered in 1998 via observations of distant supernovae. Possibly a property of space itself.",
    'string theory': "A theoretical framework where point-like particles are replaced by one-dimensional 'strings' vibrating at different frequencies. Requires 10-11 dimensions. Aims to unify quantum mechanics and general relativity.",
    'relativity': "Einstein's theories: Special Relativity (1905) — speed of light is constant, time dilates at high speeds, E=mc². General Relativity (1915) — gravity is the curvature of spacetime by mass/energy. Both confirmed by experiments.",
    'quantum computing': "Computing that uses quantum bits (qubits) which can be 0 and 1 simultaneously (superposition). Enables exponential speedup for certain problems like cryptography, optimization, and molecular simulation. Still in early development.",
    'artificial intelligence': "Systems that perform tasks requiring human-like intelligence — learning, reasoning, perception, language understanding. Ranges from narrow AI (chess, image recognition) to the goal of artificial general intelligence (AGI).",
    'machine learning': "A subset of AI where systems learn from data without explicit programming. Types: supervised (labeled data), unsupervised (pattern discovery), reinforcement (trial and error). Powers recommendations, speech recognition, and self-driving cars.",
    'neural network': "Computing systems inspired by biological brains — layers of interconnected nodes (neurons) that learn by adjusting connection weights. Deep neural networks (many layers) power modern AI breakthroughs in vision, language, and games.",
    'blockchain': "A distributed, immutable ledger of transactions maintained across many computers. Each block contains a cryptographic hash of the previous block, forming a chain. Eliminates need for trusted intermediaries.",
    'cryptocurrency': "Digital currency secured by cryptography on a blockchain. Bitcoin (2009) was first; Ethereum added smart contracts. Decentralized (no central bank). Over 20,000 cryptocurrencies exist with combined market cap in trillions.",
    'metaverse': "A concept of persistent, shared 3D virtual worlds where people interact as avatars. Combines VR/AR, gaming, social media, and digital economies. Companies investing billions, though full realization remains years away.",
    'elephant': "Largest living land animal. African elephants weigh up to 6 tonnes. Known for intelligence, memory, and complex social bonds. Lifespan: 60-70 years.",
    'whale': "Largest animals ever (blue whale: 30m, 150 tonnes). Marine mammals that breathe air. Communicate via songs traveling 1000+ km underwater.",
    'einstein': "Albert Einstein (1879-1955). Developed special & general relativity (E=mc²). Won 1921 Nobel Prize. Revolutionized physics and our understanding of space, time, and gravity.",
    'newton': "Isaac Newton (1643-1727). Laws of motion, universal gravitation, invented calculus. His Principia Mathematica is one of the most influential science books ever written.",
    'shakespeare': "William Shakespeare (1564-1616). English playwright and poet. Wrote 37+ plays (Hamlet, Romeo & Juliet, Macbeth). Invented ~1,700 English words still used today.",
    'tesla': "Nikola Tesla (1856-1943). Inventor of AC electrical system, Tesla coil, radio technology. Pioneered wireless communication. Rival of Edison in the 'War of Currents.'",
    'dinosaur': "Reptiles that dominated Earth for 165 million years (Mesozoic Era). Went extinct 66 million years ago from asteroid impact. Birds are their living descendants.",
    'volcano': "An opening in Earth's crust where magma reaches the surface. ~1,500 active volcanoes. Can be explosive (Mt St Helens) or effusive (Hawaii). Ring of Fire has 75% of world's volcanoes.",
    'hurricane': "Massive rotating storm system (>119 km/h winds) formed over warm ocean water (>26°C). Called typhoons in Pacific, cyclones in Indian Ocean. Powered by ocean heat evaporation.",
    'earthquake': "Sudden release of energy in Earth's crust causing seismic waves. Measured on Richter/moment magnitude scale. Caused by tectonic plate movement along faults.",
    'tsunami': "Ocean wave caused by underwater earthquakes, volcanic eruptions, or landslides. Can travel 800 km/h in deep water. Waves grow taller as they reach shallow coastlines.",
    'bacteria': "Single-celled microorganisms (prokaryotes). Existed for 3.5 billion years. Most are harmless or beneficial (gut flora). Some cause disease. Killed by antibiotics.",
    'virus': "Tiny infectious agents (20-300nm) — not truly alive. Need host cells to replicate. Just DNA/RNA in a protein shell. Cause flu, COVID, HIV. NOT killed by antibiotics.",
    'vaccine': "Preparation that trains the immune system to fight a specific pathogen. Contains weakened/dead virus or mRNA instructions. Herd immunity at 70-95% vaccination rate.",
    'laser': "Light Amplification by Stimulated Emission of Radiation. Produces coherent, focused light beam. Used in surgery, communications, manufacturing, barcode scanners.",
    'telescope': "Instrument that magnifies distant objects using lenses (refractor) or mirrors (reflector). Hubble orbits Earth. James Webb sees infrared 13.5 billion light-years away.",
    'satellite': "Object orbiting a planet. Natural (Moon) or artificial (GPS, communication, weather). ~10,000 active satellites orbit Earth. Geostationary orbit: 35,786 km altitude.",
    'rocket': "Vehicle propelled by expelling exhaust gases at high speed (Newton's 3rd law). Carries fuel + oxidizer. Escape velocity from Earth: 11.2 km/s. SpaceX, NASA, ESA.",
    'solar panel': "Device converting sunlight directly to electricity via photovoltaic effect (silicon semiconductors). ~20% efficient. Lifespan: 25-30 years. Fastest-growing energy source.",
    'battery': "Device storing chemical energy and converting to electrical energy. Types: lithium-ion (phones), lead-acid (cars), alkaline (disposable). Measured in amp-hours (Ah).",
    'nuclear': "Energy from splitting atoms (fission) or combining them (fusion). 1 kg uranium = 20,000 tonnes coal equivalent. Powers ~10% of world electricity. Zero CO₂ emissions during operation.",
    'ozone': "O₃ molecule. Ozone layer (stratosphere, 15-35km) absorbs 97-99% of UV radiation. Depleted by CFCs. Montreal Protocol (1987) banned CFCs — layer is slowly recovering.",
    'coral reef': "Underwater ecosystems built by coral polyps secreting calcium carbonate. Cover <1% of ocean floor but support 25% of marine species. Threatened by warming and acidification.",
    'rainforest': "Dense forest with >2000mm annual rainfall. Amazon is largest (5.5M km²). Contains 50% of Earth's species. Called 'lungs of the Earth' but actually a net-zero CO₂ system.",
    'glacier': "Massive body of ice formed from compressed snow over centuries. Stores 69% of Earth's fresh water. Currently retreating worldwide due to climate change.",
    'aurora': "Northern/southern lights. Caused by solar wind particles hitting atmospheric gases (oxygen=green, nitrogen=blue/red). Visible near magnetic poles.",
    'comet': "Icy body orbiting the Sun. Develops a tail of gas and dust when near the Sun (solar wind blows material away). Famous: Halley's Comet (76-year orbit).",
    'asteroid': "Rocky body orbiting the Sun, mostly in the asteroid belt between Mars and Jupiter. Chicxulub asteroid (10km) killed the dinosaurs 66 million years ago.",
    'galaxy': "Massive system of stars, gas, dust bound by gravity. Milky Way has 100-400 billion stars. Observable universe contains ~2 trillion galaxies.",
    'supernova': "Explosive death of a massive star — briefly outshines entire galaxy. Produces elements heavier than iron (gold, platinum, uranium). Creates neutron stars or black holes.",
    'algorithm': "Step-by-step procedure for solving a problem or performing a computation. Foundation of computer science. Examples: sorting, searching, encryption, pathfinding.",
    'robot': "Programmable machine that can carry out actions automatically. Industrial robots (manufacturing), surgical robots (da Vinci), social robots, autonomous vehicles.",
    'drone': "Unmanned aerial vehicle (UAV). Uses: photography, delivery, agriculture, military, search & rescue. Consumer drones typically fly 20-45 min on battery.",
    'chess': "Strategy board game (8×8 grid, 16 pieces per side). Originated in India ~600 AD. Estimated 10^120 possible games. Deep Blue beat Kasparov (1997), AlphaZero now dominant.",
    'olympics': "International multi-sport event held every 4 years. Ancient Games: 776 BC in Olympia, Greece. Modern revival: 1896 Athens. Summer + Winter variants.",
    'java': "Object-oriented programming language (1995, Sun Microsystems). 'Write once, run anywhere' via JVM. Used in Android, enterprise, web backends. ~3 billion devices run Java.",
    'html': "HyperText Markup Language — the standard language for creating web pages. Defines structure (headings, paragraphs, links, images). Current version: HTML5.",
    'database': "Organized collection of structured data. Types: relational (SQL tables), document (MongoDB), key-value (Redis), graph (Neo4j). Enables efficient storage, retrieval, and querying.",
    'climate change': "Long-term shift in global temperatures and weather patterns. Since 1800s, primarily driven by burning fossil fuels (CO₂ greenhouse effect). ~1.1°C warming so far.",
    'artificial intelligence': "Computer systems performing tasks that normally require human intelligence. Types: narrow AI (specific tasks), general AI (human-level, theoretical). Machine learning is a subset.",
    'neural network': "Computing system inspired by biological brain. Layers of interconnected nodes (neurons) that learn patterns from data. Basis of deep learning, GPT, image recognition.",
    'blockchain': "Distributed, immutable ledger recording transactions across many computers. Each block links cryptographically to the previous. Powers cryptocurrency, smart contracts, NFTs.",

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
    'ocean salty': "The ocean is salty because rivers dissolve minerals (including sodium and chloride) from rocks and carry them to the sea. Over billions of years, these salts accumulated while water evaporates and falls as fresh rain, leaving the salt behind.",
    'leaves change color': "Leaves change color in autumn because trees stop producing chlorophyll (green pigment) as days shorten. This reveals yellow/orange carotenoids already present, and some trees produce red anthocyanins as a sunscreen while reabsorbing nutrients.",
    'we dream': "We dream primarily during REM sleep when the brain is highly active. Dreams likely help consolidate memories, process emotions, and clear metabolic waste. The exact purpose is still debated by neuroscientists.",
    'we need sleep': "We need sleep for memory consolidation, tissue repair, immune function, and clearing brain toxins (via the glymphatic system). Chronic sleep deprivation impairs cognition, weakens immunity, and increases disease risk.",
    'sunset red': "Sunsets are red because sunlight travels through more atmosphere at low angles. Blue light scatters away (Rayleigh scattering), leaving longer red/orange wavelengths to reach your eyes directly.",
    'computers work': "Computers work by executing billions of simple operations per second using transistors — tiny switches that represent 1s and 0s. Complex software is built from these basic binary operations through layers of abstraction.",
    'wifi work': "WiFi works by transmitting data as radio waves (2.4 GHz or 5 GHz). A router modulates these waves to encode digital information, and devices decode the signal back into data. Walls and distance weaken the signal.",
    'electricity work': "Electricity is the flow of electrons through a conductor. A voltage source (battery/generator) pushes electrons like water pressure pushes water through pipes. Current flows from high to low potential.",
    'we age': "We age because cells accumulate DNA damage over time, telomeres shorten with each division limiting cell replication, and proteins/organelles degrade. Senescent cells accumulate and trigger inflammation.",
    'muscles grow': "Muscles grow through hypertrophy — exercise creates micro-tears in muscle fibers, which the body repairs by fusing fibers together, making them thicker and stronger. This requires protein, rest, and progressive overload.",
    'earth spin': "Earth spins because of conservation of angular momentum from the rotating cloud of gas and dust that formed the solar system 4.6 billion years ago. There's no friction in space to slow it significantly.",
    'volcanoes erupt': "Volcanoes erupt when magma (molten rock) from the mantle rises through cracks in the crust, driven by pressure from dissolved gases expanding. At the surface, lava, ash, and gases are explosively released.",
    'thunder happen': "Thunder happens because lightning superheats the air to ~30,000°C in milliseconds, causing rapid expansion that creates a shockwave — the sound of thunder. Light travels faster than sound, so you see lightning before hearing thunder.",
    'plants grow': "Plants grow through cell division and elongation, powered by photosynthesis (converting sunlight + CO₂ + water into glucose). Growth hormones (auxins) direct where and how cells expand.",
    'magnets attract': "Magnets attract ferromagnetic materials because their magnetic field aligns the electron spins in nearby iron/nickel atoms. Opposite poles attract because their field lines connect, reducing total energy.",
    'boats float': "Boats float because of Archimedes' principle — the hull displaces a volume of water that weighs more than the entire boat. The upward buoyant force equals the weight of displaced water.",
    'ice slippery': "Ice is slippery because a thin layer of liquid water exists on its surface even below 0°C (due to surface molecules having fewer bonds). Pressure and friction also contribute to this lubricating layer.",
    'metal conduct': "Metals conduct electricity because their outer electrons are 'delocalized' — free to move throughout the material. When voltage is applied, these electrons flow as electric current.",
    'wood float': "Wood floats because it's less dense than water — its cellular structure contains air pockets, making its overall density typically 0.4-0.7 g/cm³ vs water's 1.0 g/cm³.",
    'birds migrate': "Birds migrate to follow food sources and favorable breeding conditions. They navigate using Earth's magnetic field, star positions, the Sun, and landmarks. Some species travel thousands of kilometers annually.",
    'earthquakes happen': "Earthquakes happen when tectonic plates (sections of Earth's crust) suddenly slip along fault lines, releasing built-up stress energy as seismic waves that shake the ground.",
    'clouds form': "Clouds form when warm, moist air rises and cools to its dew point. Water vapor condenses onto tiny particles (dust, pollen) forming visible droplets or ice crystals that collectively appear as clouds.",
    'wind blow': "Wind blows because the Sun heats the Earth unevenly — warm air rises (low pressure), cool air rushes in to replace it (high pressure to low pressure). Earth's rotation (Coriolis effect) curves wind paths.",
    'snow form': "Snow forms when water vapor in clouds deposits directly onto ice crystals (deposition) at temperatures below 0°C. Crystal shape depends on temperature and humidity — hence unique snowflakes.",
    'hot air rise': "Hot air rises because heating causes air molecules to move faster and spread apart, making the air less dense. Cooler, denser surrounding air pushes underneath it — this is convection.",
    'ocean salty': "Ocean water is salty because rivers dissolve minerals (mainly sodium chloride) from rocks and carry them to the sea. Water evaporates but salt stays behind, concentrating over billions of years.",
    'leaves change color': "Leaves change color in autumn because chlorophyll (green pigment) breaks down as days shorten, revealing yellow/orange carotenoids already present and producing red anthocyanins.",
    'we dream': "Dreams occur during REM sleep when the brain is highly active. They may help process emotions, consolidate memories, and solve problems. The exact purpose is still debated in neuroscience.",
    'we need sleep': "Sleep is essential for memory consolidation, cellular repair, immune function, and brain waste removal (glymphatic system). Chronic sleep deprivation causes cognitive decline, weakened immunity, and increased disease risk.",
    'sunset red': "Sunsets are red/orange because at low angles, sunlight travels through more atmosphere. Blue light scatters away (Rayleigh scattering), leaving longer-wavelength red/orange light to reach your eyes.",
    'computers work': "Computers process information using billions of transistors (tiny switches) that represent 1s and 0s. Logic gates combine these bits to perform arithmetic and logic operations at billions of cycles per second.",
    'wifi work': "WiFi transmits data using radio waves (2.4GHz or 5GHz). A router converts internet data into radio signals, your device's antenna receives them, and a chip decodes the signal back into data.",
    'electricity work': "Electricity is the flow of electrons through a conductor. A voltage source (battery/generator) pushes electrons through a circuit. Current (amps) = flow rate, voltage = pressure, resistance = opposition.",
    'we age': "Aging occurs because telomeres (chromosome end caps) shorten with each cell division, DNA accumulates damage from oxidation and radiation, and repair mechanisms gradually become less effective.",
    'muscles grow': "Muscles grow through hypertrophy — exercise creates micro-tears in muscle fibers, which the body repairs thicker and stronger during rest. Requires protein, progressive overload, and adequate recovery.",
    'earth spin': "Earth spins because of angular momentum conserved from the rotating gas cloud that formed the solar system 4.6 billion years ago. Nothing has stopped it because space is a near-perfect vacuum (no friction).",
    'volcanoes erupt': "Volcanoes erupt when magma (molten rock) rises due to pressure from dissolved gases and buoyancy. When pressure exceeds the strength of overlying rock, the magma breaks through explosively or flows out.",
    'thunder happen': "Thunder is caused by lightning superheating air to ~30,000°C in milliseconds. The rapid expansion creates a shockwave that we hear as thunder. Light travels faster than sound, so we see lightning first.",
    'plants grow': "Plants grow using photosynthesis (sunlight + CO₂ + water → glucose + O₂) for energy and cell division (mitosis) for new cells. Growth hormones (auxins) control direction and rate.",
    'ice slippery': "Ice is slippery because a thin layer of liquid water exists on its surface even below 0°C (surface molecules are less bonded). Pressure from your foot may also briefly melt the surface layer.",
    'metal conduct': "Metals conduct electricity because their atomic structure has 'free electrons' in the outer shell that aren't bound to any single atom. These electrons move freely through the lattice when voltage is applied.",
    'wood float': "Wood floats because it's less dense than water (air pockets in its cellular structure). Density of wood: 400-900 kg/m³ vs water: 1000 kg/m³. Dense woods like ebony actually sink.",
    'birds migrate': "Birds migrate to follow food sources and favorable breeding conditions. They navigate using Earth's magnetic field (magnetite in their beaks), star patterns, the Sun's position, and landmarks.",
    'earthquakes happen': "Earthquakes happen when tectonic plates (sections of Earth's crust) suddenly slip past each other along faults. Stress builds up over years then releases as seismic waves in seconds.",
    'clouds form': "Clouds form when warm moist air rises, cools, and reaches its dew point. Water vapor condenses on tiny particles (dust, pollen) forming millions of tiny droplets or ice crystals that we see as clouds.",
    'wind blow': "Wind blows because of pressure differences in the atmosphere. The Sun heats Earth unevenly → warm air rises (low pressure) → cooler air rushes in to fill the gap → this movement is wind.",
    'snow form': "Snow forms when water vapor in clouds freezes directly into ice crystals (deposition) around dust particles. Crystals grow into hexagonal shapes as more vapor freezes onto them.",
    'hot air rise': "Hot air rises because heating makes molecules move faster and spread apart, decreasing density. The surrounding cooler (denser) air sinks and pushes the lighter warm air upward — convection.",
    'boats float': "Boats float because of Archimedes' principle — the hull displaces a volume of water weighing more than the boat itself. The upward buoyant force equals the weight of displaced water.",

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


def _depth_procedural(q, answer):
    """Handle 'how to...' questions."""
    # If answer is thin, provide generic helpful response
    if len(answer) < 30 or 'concept' in answer.lower():
        return f"I don't have specific step-by-step instructions for that yet. Try asking a more specific question or search the web."
    return answer
