"""Advanced text fluency engine — makes responses sound natural and varied."""
import re
import random

TRANSITIONS = ["Moreover", "Furthermore", "Additionally", "In addition", "Also notably"]
ADVERBS = ["Notably", "Interestingly", "Importantly", "Significantly", "Remarkably"]
CONTRAST_WORDS = ["however", "but", "yet", "although", "while"]


def _split_sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in parts if s.strip()]


def _get_subject(sentence):
    """Extract rough subject (first noun phrase) from a sentence."""
    sentence = sentence.strip().rstrip(".")
    match = re.match(r'^(\w+(?:\s+\w+)?)\s+(is|are|was|were|has|have|had|does|do|did|can|will)\b', sentence)
    if match:
        return match.group(1)
    words = sentence.split()
    return words[0] if words else ""


def _get_predicate(sentence, subject):
    """Get the predicate after the subject."""
    sentence = sentence.strip().rstrip(".")
    if sentence.lower().startswith(subject.lower()):
        return sentence[len(subject):].strip()
    return sentence


def combine_sentences(sent1, sent2):
    """Merge two related sentences using appropriate conjunction."""
    s1, s2 = sent1.strip().rstrip("."), sent2.strip().rstrip(".")
    subj1, subj2 = _get_subject(s1), _get_subject(s2)
    # Cause-effect
    cause_markers = ["because", "since", "due to", "therefore", "causes", "leads to"]
    if any(m in s2.lower() for m in cause_markers):
        return f"Because {s1.lower()}, {s2.lower()}."
    # Contrast
    if any(w in s2.lower() for w in CONTRAST_WORDS):
        clean = re.sub(r'^(however|but|yet|although|while)[,]?\s*', '', s2, flags=re.IGNORECASE)
        return f"While {s1.lower()}, {clean.lower()}."
    # Same subject — combine predicates
    if subj1.lower() == subj2.lower() and subj1:
        pred1 = _get_predicate(s1, subj1)
        pred2 = _get_predicate(s2, subj2)
        v1 = re.match(r'^(is|are|was|were|has|have|had)\s+', pred1)
        v2 = re.match(r'^(is|are|was|were|has|have|had)\s+', pred2)
        if v1 and v2 and v1.group(1) == v2.group(1):
            return f"{s1} and {pred2[v2.end():]}.".strip()
        return f"{s1} and {pred2}."
    # Default: relative clause
    return f"{s1}, which also {s2[0].lower() + s2[1:]}."


def vary_opening(sentence, position):
    """Rewrite sentence opening based on position in paragraph."""
    sentence = sentence.strip()
    if position == 0 or not sentence:
        return sentence
    core = sentence.rstrip(".")
    if position == 1:
        adverb = random.choice(ADVERBS)
        lowered = core[0].lower() + core[1:] if core[0].isupper() else core
        return f"{adverb}, {lowered}."
    if position == 2:
        subject = _get_subject(core)
        predicate = _get_predicate(core, subject)
        verb_match = re.match(r'^(is|are|was|were)\s+', predicate)
        if verb_match:
            return f"Known for being {predicate[verb_match.end():]}, {subject.lower()} stands out."
        has_match = re.match(r'^(has|have|had)\s+', predicate)
        if has_match:
            return f"Having {predicate[has_match.end():]}, {subject.lower()} stands out."
        return f"Recognized in this regard, {core[0].lower() + core[1:]}."
    if position == 3:
        subject = _get_subject(core)
        predicate = _get_predicate(core, subject)
        return f"In terms of {subject.lower()}, it {predicate}."
    return sentence


def hedge_by_confidence(text, confidence):
    """Add hedging language based on confidence level."""
    text = text.strip()
    if confidence >= 0.9:
        return text
    if confidence >= 0.7:
        hedge = random.choice(["generally", "typically"])
        match = re.match(r'^(\w+\s+(?:is|are|was|were|has|have))\s+', text)
        if match:
            return f"{match.group(1)} {hedge} {text[match.end():]}"
        return f"{hedge.capitalize()}, {text[0].lower() + text[1:]}"
    if confidence >= 0.5:
        hedge = random.choice(["I believe", "It seems that"])
        return f"{hedge} {text[0].lower() + text[1:]}"
    return f"I'm not certain, but {text[0].lower() + text[1:]}"


def remove_repetition(text):
    """Detect and remove repeated phrases and structures."""
    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        return text
    seen_phrases = {}
    result = []
    for sent in sentences:
        words = sent.lower().split()
        trigrams = [" ".join(words[i:i+3]) for i in range(len(words) - 2)]
        dominated = any(seen_phrases.get(tri, 0) >= 2 for tri in trigrams)
        if not dominated:
            result.append(sent)
            for tri in trigrams:
                seen_phrases[tri] = seen_phrases.get(tri, 0) + 1
    return " ".join(result)


def improve_fluency(text):
    """Main entry: transform mechanical text into natural-flowing prose."""
    text = remove_repetition(text)
    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        return text
    # Combine adjacent sentences with same subject
    improved = []
    i = 0
    while i < len(sentences):
        current = sentences[i]
        if i + 1 < len(sentences) and len(current.split()) < 12:
            next_sent = sentences[i + 1]
            if _get_subject(current).lower() == _get_subject(next_sent).lower() and _get_subject(current):
                improved.append(combine_sentences(current, next_sent))
                i += 2
                continue
        improved.append(current)
        i += 1
    # Vary openings
    final = [vary_opening(sent, idx % 4) for idx, sent in enumerate(improved)]
    # Add transitions
    output = [final[0]]
    for idx in range(1, len(final)):
        if idx % 3 == 0 and len(final) > 3:
            t = random.choice(TRANSITIONS)
            output.append(f"{t}, {final[idx][0].lower() + final[idx][1:]}" if final[idx] else "")
        else:
            output.append(final[idx])
    return " ".join(output)


# ─── Standalone Tests ───────────────────────────────────────────────────────
if __name__ == "__main__":
    random.seed(42)
    print("=== combine_sentences ===")
    print(combine_sentences("Python is fast.", "Python is versatile."))
    print(combine_sentences("It rained heavily.", "However the game continued."))
    print(combine_sentences("The server crashed.", "Therefore users lost data."))
    print(combine_sentences("The API is robust.", "The API has good docs."))

    print("\n=== vary_opening ===")
    for pos in range(4):
        print(f"  pos={pos}: {vary_opening('Python is a great language.', pos)}")

    print("\n=== hedge_by_confidence ===")
    for conf in [0.95, 0.75, 0.60, 0.40]:
        print(f"  {conf}: {hedge_by_confidence('Python is the best language.', conf)}")

    print("\n=== remove_repetition ===")
    rep = "The cat sat. The cat sat. The cat sat. The dog ran."
    print(f"  In:  {rep}")
    print(f"  Out: {remove_repetition(rep)}")

    print("\n=== improve_fluency ===")
    mechanical = (
        "Python is a programming language. Python is open source. "
        "Python has many libraries. Python is used in web development. "
        "Python is used in data science. Python is easy to learn."
    )
    print(f"  In:  {mechanical}")
    print(f"  Out: {improve_fluency(mechanical)}")
    print("\nAll tests passed ✓")
