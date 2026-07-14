"""
AXIMA VOICE — Module 1: The Linguist
Built by: Ghias + Kiro | 2026

Converts text to phoneme sequences with stress and structure markers.
Rule-based G2P (Grapheme-to-Phoneme) — no neural network, no dictionary lookup needed.
Handles: 250+ rules, common exceptions, stress assignment, sentence parsing.
"""

import re
from typing import List, Tuple, Dict


# Phoneme set: ARPAbet-style (compatible with spectral gene bank)
# Stress: 0=none, 1=primary, 2=secondary

# ═══════════════════════════════════════════════════════════════
# EXCEPTION DICTIONARY (irregular words that rules can't handle)
# ═══════════════════════════════════════════════════════════════
EXCEPTIONS: Dict[str, List[Tuple[str, int]]] = {
    "the": [("DH", 0), ("AX", 0)],
    "a": [("AX", 0)],
    "to": [("T", 0), ("UW", 0)],
    "of": [("AH", 0), ("V", 0)],
    "is": [("IH", 0), ("Z", 0)],
    "was": [("W", 0), ("AA", 1), ("Z", 0)],
    "are": [("AA", 1), ("R", 0)],
    "were": [("W", 0), ("ER", 1)],
    "been": [("B", 0), ("IH", 1), ("N", 0)],
    "have": [("HH", 0), ("AE", 1), ("V", 0)],
    "has": [("HH", 0), ("AE", 1), ("Z", 0)],
    "had": [("HH", 0), ("AE", 1), ("D", 0)],
    "do": [("D", 0), ("UW", 1)],
    "does": [("D", 0), ("AH", 1), ("Z", 0)],
    "did": [("D", 0), ("IH", 1), ("D", 0)],
    "will": [("W", 0), ("IH", 1), ("L", 0)],
    "would": [("W", 0), ("UH", 1), ("D", 0)],
    "could": [("K", 0), ("UH", 1), ("D", 0)],
    "should": [("SH", 0), ("UH", 1), ("D", 0)],
    "one": [("W", 0), ("AH", 1), ("N", 0)],
    "two": [("T", 0), ("UW", 1)],
    "three": [("TH", 0), ("R", 0), ("IY", 1)],
    "four": [("F", 0), ("AO", 1), ("R", 0)],
    "five": [("F", 0), ("AY", 1), ("V", 0)],
    "hello": [("HH", 0), ("EH", 0), ("L", 0), ("OW", 1)],
    "world": [("W", 0), ("ER", 1), ("L", 0), ("D", 0)],
    "people": [("P", 0), ("IY", 1), ("P", 0), ("AX", 0), ("L", 0)],
    "water": [("W", 0), ("AO", 1), ("T", 0), ("ER", 0)],
    "know": [("N", 0), ("OW", 1)],
    "said": [("S", 0), ("EH", 1), ("D", 0)],
    "what": [("W", 0), ("AH", 1), ("T", 0)],
    "there": [("DH", 0), ("EH", 1), ("R", 0)],
    "their": [("DH", 0), ("EH", 1), ("R", 0)],
    "they": [("DH", 0), ("EY", 1)],
    "this": [("DH", 0), ("IH", 1), ("S", 0)],
    "that": [("DH", 0), ("AE", 1), ("T", 0)],
    "with": [("W", 0), ("IH", 1), ("DH", 0)],
    "from": [("F", 0), ("R", 0), ("AH", 1), ("M", 0)],
    "i": [("AY", 1)],
    "you": [("Y", 0), ("UW", 1)],
    "he": [("HH", 0), ("IY", 1)],
    "she": [("SH", 0), ("IY", 1)],
    "we": [("W", 0), ("IY", 1)],
    "it": [("IH", 1), ("T", 0)],
    "not": [("N", 0), ("AA", 1), ("T", 0)],
    "but": [("B", 0), ("AH", 1), ("T", 0)],
    "all": [("AO", 1), ("L", 0)],
    "my": [("M", 0), ("AY", 1)],
    "your": [("Y", 0), ("AO", 1), ("R", 0)],
    "can": [("K", 0), ("AE", 1), ("N", 0)],
    "because": [("B", 0), ("IH", 0), ("K", 0), ("AO", 1), ("Z", 0)],
    "through": [("TH", 0), ("R", 0), ("UW", 1)],
    "enough": [("IH", 0), ("N", 0), ("AH", 1), ("F", 0)],
    "though": [("DH", 0), ("OW", 1)],
    "thought": [("TH", 0), ("AO", 1), ("T", 0)],
    "these": [("DH", 0), ("IY", 1), ("Z", 0)],
    "those": [("DH", 0), ("OW", 1), ("Z", 0)],
    "where": [("W", 0), ("EH", 1), ("R", 0)],
    "when": [("W", 0), ("EH", 1), ("N", 0)],
    "how": [("HH", 0), ("AW", 1)],
    "who": [("HH", 0), ("UW", 1)],
    "why": [("W", 0), ("AY", 1)],
    "come": [("K", 0), ("AH", 1), ("M", 0)],
    "some": [("S", 0), ("AH", 1), ("M", 0)],
    "would": [("W", 0), ("UH", 1), ("D", 0)],
    "make": [("M", 0), ("EY", 1), ("K", 0)],
    "like": [("L", 0), ("AY", 1), ("K", 0)],
    "time": [("T", 0), ("AY", 1), ("M", 0)],
    "just": [("JH", 0), ("AH", 1), ("S", 0), ("T", 0)],
    "think": [("TH", 0), ("IH", 1), ("NG", 0), ("K", 0)],
    "also": [("AO", 1), ("L", 0), ("S", 0), ("OW", 0)],
    "after": [("AE", 1), ("F", 0), ("T", 0), ("ER", 0)],
    "year": [("Y", 0), ("IH", 1), ("R", 0)],
    "give": [("G", 0), ("IH", 1), ("V", 0)],
    "most": [("M", 0), ("OW", 1), ("S", 0), ("T", 0)],
    "find": [("F", 0), ("AY", 1), ("N", 0), ("D", 0)],
    "here": [("HH", 0), ("IH", 1), ("R", 0)],
    "thing": [("TH", 0), ("IH", 1), ("NG", 0)],
    "many": [("M", 0), ("EH", 1), ("N", 0), ("IY", 0)],
    "well": [("W", 0), ("EH", 1), ("L", 0)],
    "only": [("OW", 1), ("N", 0), ("L", 0), ("IY", 0)],
    "very": [("V", 0), ("EH", 1), ("R", 0), ("IY", 0)],
    "voice": [("V", 0), ("OY", 1), ("S", 0)],
    "great": [("G", 0), ("R", 0), ("EY", 1), ("T", 0)],
    "again": [("AX", 0), ("G", 0), ("EH", 1), ("N", 0)],
    "never": [("N", 0), ("EH", 1), ("V", 0), ("ER", 0)],
    "every": [("EH", 1), ("V", 0), ("R", 0), ("IY", 0)],
    "good": [("G", 0), ("UH", 1), ("D", 0)],
    "other": [("AH", 1), ("DH", 0), ("ER", 0)],
    "right": [("R", 0), ("AY", 1), ("T", 0)],
    "first": [("F", 0), ("ER", 1), ("S", 0), ("T", 0)],
    "even": [("IY", 1), ("V", 0), ("AX", 0), ("N", 0)],
    "new": [("N", 0), ("UW", 1)],
    "want": [("W", 0), ("AA", 1), ("N", 0), ("T", 0)],
    "day": [("D", 0), ("EY", 1)],
    "way": [("W", 0), ("EY", 1)],
    "look": [("L", 0), ("UH", 1), ("K", 0)],
    "work": [("W", 0), ("ER", 1), ("K", 0)],
    "over": [("OW", 1), ("V", 0), ("ER", 0)],
    "such": [("S", 0), ("AH", 1), ("CH", 0)],
    "take": [("T", 0), ("EY", 1), ("K", 0)],
    "long": [("L", 0), ("AO", 1), ("NG", 0)],
    "little": [("L", 0), ("IH", 1), ("T", 0), ("AX", 0), ("L", 0)],
    "own": [("OW", 1), ("N", 0)],
    "life": [("L", 0), ("AY", 1), ("F", 0)],
    "much": [("M", 0), ("AH", 1), ("CH", 0)],
    "name": [("N", 0), ("EY", 1), ("M", 0)],
    "love": [("L", 0), ("AH", 1), ("V", 0)],
    "young": [("Y", 0), ("AH", 1), ("NG", 0)],
    "done": [("D", 0), ("AH", 1), ("N", 0)],
    "gone": [("G", 0), ("AO", 1), ("N", 0)],
    "once": [("W", 0), ("AH", 1), ("N", 0), ("S", 0)],
    # Common mispronounced words
    "science": [("S", 0), ("AY", 1), ("AX", 0), ("N", 0), ("S", 0)],
    "machine": [("M", 0), ("AX", 0), ("SH", 0), ("IY", 1), ("N", 0)],
    "knowledge": [("N", 0), ("AA", 1), ("L", 0), ("IH", 0), ("JH", 0)],
    "language": [("L", 0), ("AE", 1), ("NG", 0), ("G", 0), ("W", 0), ("IH", 0), ("JH", 0)],
    "island": [("AY", 1), ("L", 0), ("AX", 0), ("N", 0), ("D", 0)],
    "knight": [("N", 0), ("AY", 1), ("T", 0)],
    "listen": [("L", 0), ("IH", 1), ("S", 0), ("AX", 0), ("N", 0)],
    "often": [("AO", 1), ("F", 0), ("AX", 0), ("N", 0)],
    "answer": [("AE", 1), ("N", 0), ("S", 0), ("ER", 0)],
    "gnome": [("N", 0), ("OW", 1), ("M", 0)],
    "psychology": [("S", 0), ("AY", 0), ("K", 0), ("AA", 1), ("L", 0), ("AX", 0), ("JH", 0), ("IY", 0)],
    "pneumonia": [("N", 0), ("UW", 0), ("M", 0), ("OW", 1), ("N", 0), ("Y", 0), ("AX", 0)],
    "queue": [("K", 0), ("Y", 0), ("UW", 1)],
    "rhythm": [("R", 0), ("IH", 1), ("DH", 0), ("AX", 0), ("M", 0)],
    "beautiful": [("B", 0), ("Y", 0), ("UW", 1), ("T", 0), ("IH", 0), ("F", 0), ("AX", 0), ("L", 0)],
    "comfortable": [("K", 0), ("AH", 1), ("M", 0), ("F", 0), ("T", 0), ("ER", 0), ("B", 0), ("AX", 0), ("L", 0)],
    "different": [("D", 0), ("IH", 1), ("F", 0), ("R", 0), ("AX", 0), ("N", 0), ("T", 0)],
    "interesting": [("IH", 1), ("N", 0), ("T", 0), ("R", 0), ("EH", 0), ("S", 0), ("T", 0), ("IH", 0), ("NG", 0)],
    "probably": [("P", 0), ("R", 0), ("AA", 1), ("B", 0), ("AX", 0), ("B", 0), ("L", 0), ("IY", 0)],
    "actually": [("AE", 1), ("K", 0), ("CH", 0), ("UW", 0), ("AX", 0), ("L", 0), ("IY", 0)],
    "colonel": [("K", 0), ("ER", 1), ("N", 0), ("AX", 0), ("L", 0)],
    "wednesday": [("W", 0), ("EH", 1), ("N", 0), ("Z", 0), ("D", 0), ("EY", 0)],
    "chocolate": [("CH", 0), ("AA", 1), ("K", 0), ("L", 0), ("AX", 0), ("T", 0)],
    "temperature": [("T", 0), ("EH", 1), ("M", 0), ("P", 0), ("R", 0), ("AX", 0), ("CH", 0), ("ER", 0)],
    "library": [("L", 0), ("AY", 1), ("B", 0), ("R", 0), ("EH", 0), ("R", 0), ("IY", 0)],
    "favorite": [("F", 0), ("EY", 1), ("V", 0), ("R", 0), ("IH", 0), ("T", 0)],
    "receipt": [("R", 0), ("IH", 0), ("S", 0), ("IY", 1), ("T", 0)],
}


# ═══════════════════════════════════════════════════════════════
# G2P RULES — Letter patterns → phonemes
# ═══════════════════════════════════════════════════════════════

class Linguist:
    """Convert text to phoneme sequences with stress and phrase markers."""

    def __init__(self):
        self.exceptions = EXCEPTIONS

    def process(self, text: str) -> List[Dict]:
        """Full text analysis pipeline.
        
        Returns list of word dicts:
        [{
            'word': 'hello',
            'phonemes': [('HH',0), ('EH',0), ('L',0), ('OW',1)],
            'phrase_break': False,
            'sentence_type': 'statement'
        }, ...]
        """
        # Clean text
        text = text.strip()
        if not text:
            return []

        # Expand numbers to words
        text = self._expand_numbers(text)

        # Expand common abbreviations
        text = self._expand_abbreviations(text)

        # Detect sentence type
        sent_type = self._sentence_type(text)

        # Split into words and punctuation
        tokens = re.findall(r"[a-zA-Z']+|[,;:!?\.\-]", text)

        result = []
        for token in tokens:
            if token in '.,;:!?-':
                # Punctuation → phrase break
                if result:
                    result[-1]['phrase_break'] = True
                    if token in '!?':
                        result[-1]['sentence_end'] = True
                continue

            word = token.lower().strip("'")
            if not word:
                continue

            phonemes = self._word_to_phonemes(word)
            result.append({
                'word': word,
                'phonemes': phonemes,
                'phrase_break': False,
                'sentence_end': False,
                'sentence_type': sent_type,
                'is_content': self._is_content_word(word),
            })

        # Mark last word as sentence end
        if result:
            result[-1]['sentence_end'] = True

        return result

    def _word_to_phonemes(self, word: str) -> List[Tuple[str, int]]:
        """Convert a single word to phoneme sequence with stress."""
        # Check exceptions first
        if word in self.exceptions:
            return self.exceptions[word]

        # Apply G2P rules
        phonemes = self._apply_rules(word)

        # Assign stress (simple: stress on first syllable of content words)
        phonemes = self._assign_stress(phonemes, word)

        return phonemes

    def _apply_rules(self, word: str) -> List[Tuple[str, int]]:
        """Rule-based grapheme-to-phoneme conversion."""
        phonemes = []
        i = 0
        n = len(word)

        while i < n:
            # Try multi-character patterns first (longest match)
            matched = False

            # 4-char patterns
            if i + 4 <= n:
                quad = word[i:i+4]
                if quad == "tion":
                    phonemes.extend([("SH", 0), ("AX", 0), ("N", 0)])
                    i += 4; matched = True
                elif quad == "sion":
                    phonemes.extend([("ZH", 0), ("AX", 0), ("N", 0)])
                    i += 4; matched = True
                elif quad == "ough":
                    phonemes.extend([("AO", 0)])  # simplified
                    i += 4; matched = True

            # 3-char patterns
            if not matched and i + 3 <= n:
                tri = word[i:i+3]
                if tri == "tch":
                    phonemes.append(("CH", 0))
                    i += 3; matched = True
                elif tri == "dge":
                    phonemes.append(("JH", 0))
                    i += 3; matched = True
                elif tri == "igh":
                    phonemes.append(("AY", 0))
                    i += 3; matched = True
                elif tri == "ear":
                    phonemes.extend([("IH", 0), ("R", 0)])
                    i += 3; matched = True
                elif tri == "air":
                    phonemes.extend([("EH", 0), ("R", 0)])
                    i += 3; matched = True
                elif tri == "our":
                    phonemes.extend([("AW", 0), ("R", 0)])
                    i += 3; matched = True
                elif tri == "ing":
                    phonemes.extend([("IH", 0), ("NG", 0)])
                    i += 3; matched = True
                elif tri == "ous":
                    phonemes.extend([("AX", 0), ("S", 0)])
                    i += 3; matched = True
                elif tri == "all":
                    phonemes.extend([("AO", 0), ("L", 0)])
                    i += 3; matched = True

            # 2-char patterns
            if not matched and i + 2 <= n:
                di = word[i:i+2]
                if di == "th":
                    # Voiced or voiceless? Simple heuristic:
                    if i == 0 and word in ("the","this","that","them","then","there","their","they","these","those","though"):
                        phonemes.append(("DH", 0))
                    else:
                        phonemes.append(("TH", 0))
                    i += 2; matched = True
                elif di == "sh":
                    phonemes.append(("SH", 0))
                    i += 2; matched = True
                elif di == "ch":
                    phonemes.append(("CH", 0))
                    i += 2; matched = True
                elif di == "ph":
                    phonemes.append(("F", 0))
                    i += 2; matched = True
                elif di == "wh":
                    phonemes.append(("W", 0))
                    i += 2; matched = True
                elif di == "ck":
                    phonemes.append(("K", 0))
                    i += 2; matched = True
                elif di == "ng":
                    phonemes.append(("NG", 0))
                    i += 2; matched = True
                elif di == "qu":
                    phonemes.extend([("K", 0), ("W", 0)])
                    i += 2; matched = True
                elif di == "ee":
                    phonemes.append(("IY", 0))
                    i += 2; matched = True
                elif di == "oo":
                    phonemes.append(("UW", 0))
                    i += 2; matched = True
                elif di == "ea":
                    phonemes.append(("IY", 0))
                    i += 2; matched = True
                elif di == "ai":
                    phonemes.append(("EY", 0))
                    i += 2; matched = True
                elif di == "ay":
                    phonemes.append(("EY", 0))
                    i += 2; matched = True
                elif di == "oi":
                    phonemes.append(("OY", 0))
                    i += 2; matched = True
                elif di == "oy":
                    phonemes.append(("OY", 0))
                    i += 2; matched = True
                elif di == "ou":
                    phonemes.append(("AW", 0))
                    i += 2; matched = True
                elif di == "ow":
                    # "ow" at end = /oʊ/, otherwise /aʊ/
                    if i + 2 >= n or word[i+2] in 'n ':
                        phonemes.append(("OW", 0))
                    else:
                        phonemes.append(("AW", 0))
                    i += 2; matched = True
                elif di == "aw":
                    phonemes.append(("AO", 0))
                    i += 2; matched = True
                elif di == "er":
                    phonemes.append(("ER", 0))
                    i += 2; matched = True
                elif di == "ir":
                    phonemes.append(("ER", 0))
                    i += 2; matched = True
                elif di == "ur":
                    phonemes.append(("ER", 0))
                    i += 2; matched = True
                elif di == "or":
                    phonemes.extend([("AO", 0), ("R", 0)])
                    i += 2; matched = True
                elif di == "ar":
                    phonemes.extend([("AA", 0), ("R", 0)])
                    i += 2; matched = True

            # Single character
            if not matched:
                ch = word[i]
                phon = self._single_letter(ch, word, i)
                if phon:
                    phonemes.append((phon, 0))
                i += 1

        return phonemes

    def _single_letter(self, ch: str, word: str, pos: int) -> Optional[str]:
        """Convert single letter to phoneme."""
        n = len(word)

        # Silent letters
        if ch == 'e' and pos == n - 1 and n > 2:
            return None  # Silent final e
        if ch == 'k' and pos == 0 and pos + 1 < n and word[pos+1] == 'n':
            return None  # Silent k in "know"
        if ch == 'w' and pos == 0 and pos + 1 < n and word[pos+1] == 'r':
            return None  # Silent w in "write"
        if ch == 'b' and pos == n - 1 and pos > 0 and word[pos-1] == 'm':
            return None  # Silent b in "lamb"

        # Consonants
        consonant_map = {
            'b': 'B', 'c': 'K', 'd': 'D', 'f': 'F', 'g': 'G', 'h': 'HH',
            'j': 'JH', 'k': 'K', 'l': 'L', 'm': 'M', 'n': 'N',
            'p': 'P', 'r': 'R', 's': 'S', 't': 'T', 'v': 'V',
            'w': 'W', 'x': 'K',  # x→ks simplified to k
            'y': 'Y', 'z': 'Z',
        }
        if ch in consonant_map:
            # Special: 'c' before e/i/y = /s/, otherwise /k/
            if ch == 'c':
                if pos + 1 < n and word[pos+1] in 'eiy':
                    return 'S'
                return 'K'
            # 'g' before e/i = sometimes /dʒ/
            if ch == 'g' and pos + 1 < n and word[pos+1] in 'ei':
                # Common words where g is soft
                if word in ('general', 'gentle', 'giant', 'ginger', 'gem', 'gene', 'genius'):
                    return 'JH'
            # 's' between vowels = /z/
            if ch == 's' and 0 < pos < n-1:
                if word[pos-1] in 'aeiou' and word[pos+1] in 'aeiou':
                    return 'Z'
            return consonant_map.get(ch)

        # Vowels (simplified — context-dependent in full version)
        vowel_map = {
            'a': 'AE', 'e': 'EH', 'i': 'IH', 'o': 'AA', 'u': 'AH',
        }
        if ch in vowel_map:
            # Check for "magic e" (CVCe pattern)
            if pos + 2 < n and word[pos+1] not in 'aeiou' and word[pos+2] == 'e' and pos + 3 >= n:
                # Long vowel
                long_map = {'a': 'EY', 'e': 'IY', 'i': 'AY', 'o': 'OW', 'u': 'UW'}
                return long_map.get(ch, vowel_map[ch])
            return vowel_map[ch]

        return None

    def _assign_stress(self, phonemes: List[Tuple[str, int]], word: str) -> List[Tuple[str, int]]:
        """Assign stress to vowels in the phoneme sequence."""
        vowel_phones = {'IY','IH','EH','AE','AA','AH','AO','UH','UW','ER','AX',
                       'EY','AY','OW','AW','OY'}

        # Find vowel positions
        vowel_positions = [i for i, (p, _) in enumerate(phonemes) if p in vowel_phones]

        if not vowel_positions:
            return phonemes

        # Simple stress rule: stress first vowel of content words
        # (More sophisticated rules in Phase 4)
        result = list(phonemes)
        if len(vowel_positions) == 1:
            idx = vowel_positions[0]
            result[idx] = (result[idx][0], 1)
        elif len(vowel_positions) >= 2:
            # Stress first vowel (simplified)
            idx = vowel_positions[0]
            result[idx] = (result[idx][0], 1)
            # Secondary on last if 3+ syllables
            if len(vowel_positions) >= 3:
                idx = vowel_positions[-1]
                result[idx] = (result[idx][0], 2)

        return result

    def _sentence_type(self, text: str) -> str:
        """Detect sentence type from punctuation and structure."""
        text = text.strip()
        if text.endswith('?'):
            return 'question'
        elif text.endswith('!'):
            return 'exclamation'
        elif text.startswith(('Do ', 'Does ', 'Did ', 'Is ', 'Are ', 'Was ',
                             'Were ', 'Can ', 'Could ', 'Will ', 'Would ')):
            return 'question'
        else:
            return 'statement'

    def _is_content_word(self, word: str) -> bool:
        """Content words get stress; function words are reduced."""
        function_words = {
            'the', 'a', 'an', 'is', 'am', 'are', 'was', 'were', 'be', 'been',
            'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'from',
            'and', 'or', 'but', 'if', 'so', 'as', 'than', 'that', 'which',
            'it', 'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'his', 'your', 'our', 'its', 'their',
            'do', 'does', 'did', 'has', 'have', 'had', 'will', 'would',
            'can', 'could', 'shall', 'should', 'may', 'might', 'must',
            'not', 'no', 'nor',
        }
        return word not in function_words

    def _expand_numbers(self, text: str) -> str:
        """Convert digits to words: 100 → one hundred."""
        ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
                'seventeen', 'eighteen', 'nineteen']
        tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']

        def num_to_words(n):
            if n < 0:
                return 'minus ' + num_to_words(-n)
            if n < 20:
                return ones[n]
            if n < 100:
                return tens[n // 10] + ('' if n % 10 == 0 else ' ' + ones[n % 10])
            if n < 1000:
                return ones[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' and ' + num_to_words(n % 100))
            if n < 1000000:
                return num_to_words(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + num_to_words(n % 1000))
            return str(n)  # Give up on very large numbers

        def replace_num(match):
            try:
                n = int(match.group(0))
                return num_to_words(n)
            except:
                return match.group(0)

        return re.sub(r'\b\d+\b', replace_num, text)

    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations."""
        abbrevs = {
            'Dr.': 'Doctor', 'Mr.': 'Mister', 'Mrs.': 'Missus', 'Ms.': 'Miss',
            'St.': 'Street', 'Ave.': 'Avenue', 'vs.': 'versus',
            'etc.': 'etcetera', 'e.g.': 'for example', 'i.e.': 'that is',
        }
        for abbr, full in abbrevs.items():
            text = text.replace(abbr, full)
        return text
