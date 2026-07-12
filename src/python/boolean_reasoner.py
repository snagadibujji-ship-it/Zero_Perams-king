#!/usr/bin/env python3
"""
AXIMA Boolean Reasoner — Answers YES/NO questions from knowledge + logic.
Handles: "is X a Y?", "is X Y?", "can X Y?", "does X Y?", comparisons, primes.
"""
import math

# ══════════════════════════════════════════════════════════════
# KNOWN FACTS (verified, for boolean questions)
# ══════════════════════════════════════════════════════════════

IS_A = {
    'sun': ['star', 'celestial body'],
    'earth': ['planet', 'celestial body'],
    'moon': ['satellite', 'celestial body'],
    'mars': ['planet'], 'venus': ['planet'], 'jupiter': ['planet'],
    'gold': ['metal', 'element', 'chemical element'],
    'silver': ['metal', 'element'], 'iron': ['metal', 'element'],
    'copper': ['metal', 'element'], 'aluminum': ['metal'],
    'platinum': ['metal'], 'titanium': ['metal'],
    'oxygen': ['gas', 'element'], 'nitrogen': ['gas', 'element'],
    'hydrogen': ['gas', 'element'], 'helium': ['gas', 'element'],
    'carbon': ['element'], 'neon': ['gas', 'element'],
    'mercury': ['metal', 'element', 'liquid', 'liquid metal'],
    'water': ['liquid', 'compound', 'molecule'],
    'ice': ['solid', 'frozen water'],
    'steam': ['gas', 'water vapor'],
    'diamond': ['mineral', 'crystal', 'gemstone'],
    'ruby': ['gemstone'], 'emerald': ['gemstone'],
    'dog': ['animal', 'mammal', 'pet'],
    'cat': ['animal', 'mammal', 'pet'],
    'whale': ['animal', 'mammal'], 'dolphin': ['animal', 'mammal'],
    'eagle': ['bird', 'animal'], 'penguin': ['bird', 'animal'],
    'shark': ['fish', 'animal'], 'salmon': ['fish', 'animal'],
    'snake': ['reptile', 'animal'], 'lizard': ['reptile', 'animal'],
    'frog': ['amphibian', 'animal'], 'ant': ['insect', 'animal'],
    'python': ['programming language', 'snake'],
    'javascript': ['programming language'],
    'linux': ['operating system'],
}

IS_PROPERTY = {
    'sun': ['hot', 'bright', 'massive', 'luminous'],
    'fire': ['hot', 'bright', 'dangerous'],
    'ice': ['cold', 'solid', 'frozen', 'slippery'],
    'water': ['wet', 'liquid', 'transparent', 'essential'],
    'snow': ['cold', 'white', 'frozen'],
    'earth': ['round', 'spherical', 'habitable'],
    'gold': ['shiny', 'valuable', 'malleable', 'yellow'],
    'diamond': ['hard', 'valuable', 'transparent'],
    'glass': ['transparent', 'fragile', 'brittle'],
    'rubber': ['elastic', 'flexible', 'waterproof'],
    'steel': ['strong', 'hard', 'durable'],
}

CAN_DO = {
    'birds': ['fly', 'sing', 'build nests'],
    'bird': ['fly', 'sing'],
    'fish': ['swim', 'breathe underwater'],
    'dogs': ['bark', 'swim', 'run', 'fetch'],
    'dog': ['bark', 'swim', 'run'],
    'cats': ['climb', 'purr', 'hunt'],
    'cat': ['climb', 'purr'],
    'humans': ['think', 'speak', 'write', 'run', 'swim'],
    'snakes': ['slither', 'bite', 'swim'],
    'penguins': ['swim'],
    'penguin': ['swim'],
    'eagles': ['fly', 'hunt'],
    'cheetah': ['run fast'],
}

CANNOT_DO = {
    'fish': ['breathe air', 'walk', 'fly', 'run'],
    'penguins': ['fly'],
    'penguin': ['fly'],
    'snakes': ['walk', 'run', 'fly'],
    'humans': ['fly', 'breathe underwater'],
}

IS_NOT = {
    'earth': ['flat'],
    'sun': ['cold', 'small', 'planet'],
    'fire': ['cold', 'wet'],
    'ice': ['hot', 'warm'],
    'water': ['dry'],
    'moon': ['star', 'planet'],
    'whale': ['fish'],
    'penguin': ['mammal'],
    'bat': ['bird'],
    'tomato': ['vegetable'],  # it's a fruit
}


def answer_boolean(question):
    """
    Answer a yes/no question. Returns (answer, confidence) or None.
    answer is 'yes' or 'no'.
    """
    q = question.lower().strip().rstrip('?').strip()
    
    # ─── PRIME NUMBER CHECK ───
    prime_match = _check_prime(q)
    if prime_match is not None:
        return prime_match
    
    # ─── NUMBER COMPARISON ───
    comp_match = _check_comparison(q)
    if comp_match is not None:
        return comp_match
    
    # ─── EVEN/ODD CHECK ───
    eo_match = _check_even_odd(q)
    if eo_match is not None:
        return eo_match
    
    # ─── "IS X A Y" / "IS X Y" ───
    # Pattern: "is [the] X a/an Y"
    import re
    m = re.match(r'is\s+(?:the\s+|a\s+|an\s+)?(.+?)\s+(?:a|an)\s+(.+)', q)
    if m:
        subject = m.group(1).strip()
        category = m.group(2).strip()
        return _check_is_a(subject, category)
    
    # Pattern: "is X Y" (property check)
    m = re.match(r'is\s+(?:the\s+|a\s+|an\s+)?(.+?)\s+(.+)', q)
    if m:
        subject = m.group(1).strip()
        prop = m.group(2).strip()
        
        # Check IS_NOT first
        if subject in IS_NOT and prop in IS_NOT[subject]:
            return 'no', 0.93
        
        # Check IS_PROPERTY
        if subject in IS_PROPERTY and prop in IS_PROPERTY[subject]:
            return 'yes', 0.92
        
        # Check IS_A (without article)
        result = _check_is_a(subject, prop)
        if result:
            return result
    
    # ─── "CAN X Y" / "DOES X Y" ───
    m = re.match(r'(?:can|does|do)\s+(?:a\s+|an\s+|the\s+)?(.+?)\s+(.+)', q)
    if m:
        subject = m.group(1).strip()
        action = m.group(2).strip()
        
        # Check CAN_DO
        if subject in CAN_DO and action in CAN_DO[subject]:
            return 'yes', 0.90
        if subject in CANNOT_DO and action in CANNOT_DO[subject]:
            return 'no', 0.90
        
        # Plural check
        subject_s = subject + 's' if not subject.endswith('s') else subject
        subject_ns = subject.rstrip('s') if subject.endswith('s') else subject
        for s in (subject, subject_s, subject_ns):
            if s in CAN_DO and action in CAN_DO[s]:
                return 'yes', 0.88
            if s in CANNOT_DO and action in CANNOT_DO[s]:
                return 'no', 0.88
    
    # ─── SYLLOGISM ("all X are Y. Z is X. is Z a Y") ───
    if '. ' in q:
        parts = [p.strip() for p in q.split('.') if p.strip()]
        if len(parts) >= 3:
            result = _check_syllogism(parts)
            if result:
                return result
    
    return None


def _check_is_a(subject, category):
    """Check if subject IS A category."""
    # Direct lookup
    if subject in IS_A:
        cats = IS_A[subject]
        if category in cats or any(category in c for c in cats):
            return 'yes', 0.93
        # Negative: subject exists but category not in list
        # Only say no if we're confident (subject has entries)
        if len(cats) >= 2:
            return 'no', 0.70
    
    # Check with/without 's'
    for s in (subject, subject.rstrip('s'), subject + 's'):
        if s in IS_A:
            if category in IS_A[s]:
                return 'yes', 0.90
    
    return None


def _check_prime(q):
    """Check 'is N a prime number' / 'is N prime'."""
    import re
    m = re.search(r'is\s+(\d+)\s+(?:a\s+)?prime', q)
    if m:
        n = int(m.group(1))
        is_prime = _is_prime(n)
        return ('yes' if is_prime else 'no'), 0.99


def _is_prime(n):
    """Deterministic prime check."""
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0: return False
    return True


def _check_comparison(q):
    """Check 'is N greater/less than M'."""
    import re
    m = re.search(r'is\s+(\d+)\s+(?:greater|more|bigger|larger)\s+than\s+(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return ('yes' if a > b else 'no'), 0.99
    
    m = re.search(r'is\s+(\d+)\s+(?:less|fewer|smaller)\s+than\s+(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return ('yes' if a < b else 'no'), 0.99
    
    m = re.search(r'is\s+(\d+)\s+equal\s+to\s+(\d+)', q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return ('yes' if a == b else 'no'), 0.99
    
    return None


def _check_even_odd(q):
    """Check 'is N even/odd'."""
    import re
    m = re.search(r'is\s+(\d+)\s+even', q)
    if m:
        n = int(m.group(1))
        return ('yes' if n % 2 == 0 else 'no'), 0.99
    
    m = re.search(r'is\s+(\d+)\s+odd', q)
    if m:
        n = int(m.group(1))
        return ('yes' if n % 2 != 0 else 'no'), 0.99
    
    return None


def _check_syllogism(parts):
    """Handle multi-statement logic: 'all X are Y. Z is X. is Z a Y'"""
    import re
    
    premises = {}
    question_part = None
    
    for part in parts:
        part = part.strip().lower()
        
        # "all X are Y" / "all X have Y" / "all X can Y"
        m = re.match(r'all\s+(.+?)\s+(?:are|is)\s+(.+)', part)
        if m:
            premises[('are', m.group(1).strip())] = m.group(2).strip()
            continue
        m = re.match(r'all\s+(.+?)\s+have\s+(.+)', part)
        if m:
            premises[('have', m.group(1).strip())] = m.group(2).strip()
            continue
        m = re.match(r'all\s+(.+?)\s+(?:can|do)\s+(.+)', part)
        if m:
            premises[('can', m.group(1).strip())] = m.group(2).strip()
            continue
        m = re.match(r'all\s+(.+?)\s+live\s+in\s+(.+)', part)
        if m:
            premises[('live', m.group(1).strip())] = m.group(2).strip()
            continue
        
        # "no X are Y"
        m = re.match(r'no\s+(.+?)\s+are\s+(.+)', part)
        if m:
            premises[('not_are', m.group(1).strip())] = m.group(2).strip()
            continue
        
        # Question: "is Z a Y" / "does Z have Y" / "can Z Y" — CHECK BEFORE INSTANCE
        m = re.match(r'is\s+(?:a\s+|an\s+|the\s+)?(.+?)\s+(?:a|an)\s+(.+)', part)
        if m:
            question_part = ('is_a', m.group(1).strip(), m.group(2).strip())
            continue
        m = re.match(r'does\s+(?:a\s+)?(.+?)\s+have\s+(.+)', part)
        if m:
            question_part = ('has', m.group(1).strip(), m.group(2).strip())
            continue
        m = re.match(r'does\s+(?:a\s+)?(.+?)\s+live\s+in\s+(.+)', part)
        if m:
            question_part = ('lives', m.group(1).strip(), m.group(2).strip())
            continue
        m = re.match(r'(?:can|does)\s+(?:a\s+)?(.+?)\s+(.+)', part)
        if m:
            question_part = ('can', m.group(1).strip(), m.group(2).strip())
            continue
        
        # "Z is a X" / "Z is X" — INSTANCE (after question check)
        m = re.match(r'(?:a\s+|an\s+)?(.+?)\s+is\s+(?:a|an)\s+(.+)', part)
        if m:
            premises[('instance', m.group(1).strip())] = m.group(2).strip()
            continue
    
    if not question_part:
        return None
    
    q_type, subject, target = question_part
    
    # Find subject's category
    subject_category = None
    for key, val in premises.items():
        if key[0] == 'instance' and key[1] == subject:
            subject_category = val
            break
    
    if not subject_category:
        return None
    
    # Check if category has the property (handle singular/plural)
    cat_variants = [subject_category, subject_category + 's',
                    subject_category.rstrip('s') if subject_category.endswith('s') else subject_category]
    
    if q_type == 'is_a':
        for cat in cat_variants:
            if ('are', cat) in premises:
                pval = premises[('are', cat)]
                # Check target matches (singular/plural)
                if pval == target or pval == target + 's' or pval.rstrip('s') == target:
                    return 'yes', 0.95
            if ('not_are', cat) in premises:
                pval = premises[('not_are', cat)]
                if pval == target or pval == target + 's' or pval.rstrip('s') == target:
                    return 'no', 0.95
    
    if q_type == 'has':
        for cat in cat_variants:
            if ('have', cat) in premises:
                if premises[('have', cat)] == target:
                    return 'yes', 0.95
    
    if q_type == 'can':
        for cat in cat_variants:
            if ('can', cat) in premises:
                if premises[('can', cat)] == target:
                    return 'yes', 0.95
    
    if q_type == 'lives':
        for cat in cat_variants:
            if ('live', cat) in premises:
                if premises[('live', cat)] == target:
                    return 'yes', 0.95
    
    return None


if __name__ == '__main__':
    tests = [
        "is the sun a star",
        "is water wet",
        "is fire cold",
        "is ice hot",
        "is the earth flat",
        "is gold a metal",
        "is oxygen a gas",
        "is mercury a liquid",
        "can birds fly",
        "can fish breathe air",
        "is 2 greater than 1",
        "is 5 less than 3",
        "is 7 a prime number",
        "is 4 a prime number",
        "is 0 even",
        "is 1 odd",
        "all cats are animals. tom is a cat. is tom an animal",
        "all dogs are mammals. rex is a dog. is rex a mammal",
        "no reptiles are mammals. a snake is a reptile. is a snake a mammal",
    ]
    
    passed = 0
    for q in tests:
        result = answer_boolean(q)
        if result:
            ans, conf = result
            print(f"  ✅ {q} → {ans} ({conf:.0%})")
            passed += 1
        else:
            print(f"  ❌ {q} → NO ANSWER")
    
    print(f"\n  Result: {passed}/{len(tests)} ({passed*100//len(tests)}%)")
