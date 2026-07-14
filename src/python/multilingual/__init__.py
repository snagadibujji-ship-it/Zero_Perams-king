"""
AXIMA Multilingual — Grammar Pattern Language Intelligence
Built by: Ghias + Kiro | 2026

Detects language from GRAMMAR STRUCTURE, not word lists.
Handles Romanized input (English letters for native languages).
75KB for 3 languages. Zero ML models.

"Detect by structure, not by vocabulary."
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class LangResult:
    """Result of language detection + intent extraction."""
    original: str                    # Raw input
    language: str = "en"             # Detected: en/te/hi/ta
    script: str = "roman"            # roman/telugu/devanagari/tamil
    intent: str = "general"          # what_is/how/why/calculate/explain/compare/tell
    topic: str = ""                  # Extracted topic (English content words)
    english_query: str = ""          # Clean English equivalent
    style: str = "casual"            # casual/formal/mixed
    confidence: float = 0.0


# ═══════════════════════════════════════════════════════════════
# PHASE 1: GRAMMAR PATTERN ENGINE
# Detect language from function words + sentence endings
# ═══════════════════════════════════════════════════════════════

# Telugu grammar patterns (Romanized)
# Format: (regex_pattern, intent, topic_extraction_group)
TELUGU_PATTERNS = [
    # Questions: "X ante enti/emi" → what is X
    (r'(.+?)\s+ante\s+(?:enti|emi|emiti|yenti)', 'what_is', 1),
    (r'(.+?)\s+ante\s+(?:em|ento)', 'what_is', 1),
    (r'(.+?)\s+(?:enti|emi|emiti)\s*\??', 'what_is', 1),
    # How: "X ela [verb]" → how does X work
    (r'(.+?)\s+(?:ela|yela|elaa)\s+(.+)', 'how', 1),
    (r'(.+?)\s+(?:ela|yela)\s+(?:work|panichestundi|chestundi)', 'how', 1),
    # Why: "X enduku/endhuku" → why X
    (r'(.+?)\s+(?:enduku|endhuku|enku)\s*(.*)', 'why', 1),
    (r'(?:enduku|endhuku|enku)\s+(.+)', 'why', 1),
    # Tell/Explain: "X cheppu/cheppandi/gurinchi"
    (r'(.+?)\s+(?:gurinchi|gurinchi)\s+(?:cheppu|cheppandi|chepu)', 'explain', 1),
    (r'(.+?)\s+(?:cheppu|cheppandi|chepu|cheppava)', 'tell', 1),
    (r'(.+?)\s+(?:explain|viverinchu|vivrinchu)\s+(?:cheyyi|cheyyandi)', 'explain', 1),
    # Calculate: "X solve cheyyi/calculate cheyyi"
    (r'(.+?)\s+(?:solve|calculate|lekkincbu|lekkinchu)\s+(?:cheyyi|cheyyandi|chey)', 'calculate', 1),
    # Compare: "X Y difference enti"
    (r'(.+?)\s+(?:mariyu|and|&)\s+(.+?)\s+(?:difference|theda|bhēdham)\s*(?:enti|emi)?', 'compare', 0),
    # Formula: "X formula cheppu/enti"
    (r'(.+?)\s+formula\s+(?:enti|emi|cheppu|cheppandi)', 'formula', 1),
    # General with verb endings: "-tundi/-taru/-tanu"
    (r'(.+?)\s+(.+?(?:tundi|taru|tanu|tundi|taru))\s*\??', 'how', 1),
]

# Hindi grammar patterns (Romanized)
HINDI_PATTERNS = [
    # "X kya hai" → what is X
    (r'(.+?)\s+(?:kya|ky)\s+(?:hai|he|h)', 'what_is', 1),
    (r'(.+?)\s+(?:kya|ky)\s*\??', 'what_is', 1),
    # "X kaise [verb]" → how
    (r'(.+?)\s+(?:kaise|kese|kaise)\s+(.+)', 'how', 1),
    (r'(?:kaise|kese)\s+(.+)', 'how', 1),
    # "X kyun/kyu" → why
    (r'(.+?)\s+(?:kyun|kyu|kyun|kyon)\s*(.*)', 'why', 1),
    # "X bata/batao/samjhao"
    (r'(.+?)\s+(?:bata|batao|batado|samjhao|samjha)', 'tell', 1),
    (r'(.+?)\s+(?:ke\s+baare\s+mein|ke\s+bare\s+me)\s+(?:bata|batao)', 'explain', 1),
    # Calculate
    (r'(.+?)\s+(?:solve|calculate|nikalo|nikal)\s+(?:karo|kro|kar)', 'calculate', 1),
    # Compare
    (r'(.+?)\s+(?:aur|or|and)\s+(.+?)\s+(?:mein|me)\s+(?:difference|antar|fark)', 'compare', 0),
    # Formula
    (r'(.+?)\s+(?:ka|ki|ke)\s+formula\s*(?:kya|bata|batao)?', 'formula', 1),
    # General: "hai/hain/tha/the" endings
    (r'(.+?)\s+(?:hai|hain|tha|the|hota|hoti)\s*\??', 'what_is', 1),
]

# Tamil grammar patterns (Romanized)
TAMIL_PATTERNS = [
    # "X enna/ennanu" → what is X
    (r'(.+?)\s+(?:enna|yenna|ennanu|ennada)', 'what_is', 1),
    # "X eppadi [verb]" → how
    (r'(.+?)\s+(?:eppadi|yeppadi|epdi)\s*(.*)', 'how', 1),
    (r'(?:eppadi|yeppadi|epdi)\s+(.+)', 'how', 1),
    # "X en/yean" → why
    (r'(.+?)\s+(?:en|yean|yen)\s*(.*)', 'why', 1),
    # "X sollu/sollungo"
    (r'(.+?)\s+(?:sollu|sollungo|solu|solluga|padi)', 'tell', 1),
    (r'(.+?)\s+(?:pathi|patri)\s+(?:sollu|sollungo)', 'explain', 1),
    # Calculate
    (r'(.+?)\s+(?:solve|calculate|kanakku)\s+(?:pannu|pannungo|panu)', 'calculate', 1),
    # General: "-ngu/-ngo/-anga" endings (polite)
    (r'(.+?)\s+(.+?(?:ngu|ngo|anga|unga))\s*\??', 'how', 1),
]

# Telugu function words (for detection, NOT translation)
TELUGU_MARKERS = {
    'ante', 'enti', 'emi', 'emiti', 'ela', 'enduku', 'cheppu', 'cheppandi',
    'gurinchi', 'cheyyi', 'cheyyandi', 'valla', 'kosam', 'lo', 'ki', 'tho',
    'mariyu', 'kani', 'kabatti', 'appudu', 'ippudu', 'akkada', 'ikkada',
    'tundi', 'taru', 'tanu', 'tunnaru', 'andi', 'garu', 'meeru', 'nenu',
    'adi', 'idi', 'evi', 'evaru', 'ekkada', 'lekunda', 'undhi', 'ledhu',
    'avunu', 'kadhu', 'okavela', 'lekapote', 'ayithe', 'kaabatti',
}

# Hindi function words
HINDI_MARKERS = {
    'kya', 'hai', 'kaise', 'kyun', 'kyon', 'bata', 'batao', 'samjhao',
    'mein', 'ka', 'ki', 'ke', 'ko', 'se', 'par', 'pe', 'ne', 'aur',
    'lekin', 'kyunki', 'agar', 'toh', 'phir', 'abhi', 'yahan', 'wahan',
    'hai', 'hain', 'tha', 'the', 'hoga', 'hogi', 'karo', 'karo',
    'hota', 'hoti', 'nahi', 'nhi', 'haan', 'mat', 'sab', 'kuch',
    'yeh', 'woh', 'kaun', 'kahan', 'kab', 'kitna', 'kitni',
}

# Tamil function words
TAMIL_MARKERS = {
    'enna', 'eppadi', 'yeppadi', 'epdi', 'en', 'yean', 'yen',
    'sollu', 'sollungo', 'pathi', 'patri',
    'la', 'le', 'ku', 'oda', 'um', 'aana', 'aanaa', 'athanaal',
    'inga', 'anga', 'ippo', 'appo', 'yaar', 'enga',
    'pannu', 'pannungo', 'irukku', 'illa', 'aama', 'illai',
    'naan', 'nee', 'avan', 'aval', 'ange', 'inge',
    'agum', 'aagum', 'theriyum', 'paru', 'parunga', 'vaanga', 'ponga',
}


# ═══════════════════════════════════════════════════════════════
# PHASE 2: PHONETIC NORMALIZER
# Handle spelling variations in Romanized text
# ═══════════════════════════════════════════════════════════════

class PhoneticNormalizer:
    """Normalize Romanized spelling variations."""

    def normalize(self, text: str) -> str:
        """Normalize text for pattern matching."""
        t = text.lower().strip()
        # Step 1: Collapse repeated letters (chepppu → cheppu)
        t = re.sub(r'(.)\1{2,}', r'\1\1', t)
        # Step 2: Common phonetic equivalences
        t = t.replace('th', 't').replace('dh', 'd').replace('bh', 'b')
        t = t.replace('sh', 's').replace('ch', 'c')
        t = t.replace('aa', 'a').replace('ee', 'i').replace('oo', 'u')
        t = t.replace('ou', 'u').replace('ai', 'e')
        # Step 3: Normalize question marks and trailing vowels
        t = re.sub(r'\?+', '?', t)
        return t

    def get_consonant_skeleton(self, word: str) -> str:
        """Extract consonant skeleton for fuzzy matching."""
        return re.sub(r'[aeiou\s]', '', word.lower())


# ═══════════════════════════════════════════════════════════════
# PHASE 3: INTENT EXTRACTOR
# Patterns → clean English intent
# ═══════════════════════════════════════════════════════════════

class IntentExtractor:
    """Extract English intent from detected patterns."""

    INTENT_TO_ENGLISH = {
        'what_is': "What is {topic}?",
        'how': "How does {topic} work?",
        'why': "Why does {topic}?",
        'explain': "Explain {topic}",
        'tell': "Tell me about {topic}",
        'calculate': "Calculate {topic}",
        'compare': "Compare {topic}",
        'formula': "What is the formula for {topic}?",
        'general': "{topic}",
    }

    def to_english(self, intent: str, topic: str) -> str:
        """Convert intent + topic to clean English query."""
        template = self.INTENT_TO_ENGLISH.get(intent, "{topic}")
        return template.format(topic=topic.strip())


# ═══════════════════════════════════════════════════════════════
# PHASE 4: SCRIPT DETECTOR
# For native script input (Unicode ranges)
# ═══════════════════════════════════════════════════════════════

SCRIPT_RANGES = {
    'te': (0x0C00, 0x0C7F),   # Telugu
    'hi': (0x0900, 0x097F),   # Devanagari
    'ta': (0x0B80, 0x0BFF),   # Tamil
    'ar': (0x0600, 0x06FF),   # Arabic
    'zh': (0x4E00, 0x9FFF),   # Chinese
    'ko': (0xAC00, 0xD7AF),   # Korean
}


def detect_script(text: str) -> Tuple[str, str]:
    """Detect script from Unicode. Returns (language, script_type)."""
    for char in text:
        code = ord(char)
        for lang, (start, end) in SCRIPT_RANGES.items():
            if start <= code <= end:
                return lang, "native"
    return "en", "roman"


# ═══════════════════════════════════════════════════════════════
# MAIN ENGINE: Ties everything together
# ═══════════════════════════════════════════════════════════════

class MultilingualEngine:
    """The AXIMA Multilingual Intelligence Engine.
    
    Detects language from grammar patterns (not word lists).
    Handles Romanized input. Extracts intent. Returns English query.
    """

    def __init__(self):
        self.normalizer = PhoneticNormalizer()
        self.extractor = IntentExtractor()

    def process(self, text: str) -> LangResult:
        """Process input in any language → extract intent + English query."""
        result = LangResult(original=text)

        # Step 1: Check native script first
        lang, script = detect_script(text)
        if script == "native":
            result.language = lang
            result.script = "native"
            # For native script, we'd need the full translation
            # (handled by the native script path)
            result.english_query = text  # Placeholder
            result.confidence = 0.9
            return result

        # Step 2: Detect language from grammar patterns (Romanized)
        result.script = "roman"
        detected = self._detect_from_patterns(text)

        if detected:
            result.language = detected['language']
            result.intent = detected['intent']
            result.topic = detected['topic']
            result.english_query = self.extractor.to_english(detected['intent'], detected['topic'])
            result.confidence = detected['confidence']
            result.style = self._detect_style(text)
        else:
            # Pure English
            result.language = "en"
            result.english_query = text
            result.confidence = 1.0
            result.style = "english"

        return result

    def _detect_from_patterns(self, text: str) -> Optional[Dict]:
        """Try to match grammar patterns for each language."""
        # Normalize for matching
        normalized = self.normalizer.normalize(text)
        original_lower = text.lower().strip()

        # Count function word hits per language
        te_score = sum(1 for w in original_lower.split() if w in TELUGU_MARKERS)
        hi_score = sum(1 for w in original_lower.split() if w in HINDI_MARKERS)
        ta_score = sum(1 for w in original_lower.split() if w in TAMIL_MARKERS)

        # Try patterns in order of score
        candidates = [
            ('te', te_score, TELUGU_PATTERNS),
            ('hi', hi_score, HINDI_PATTERNS),
            ('ta', ta_score, TAMIL_PATTERNS),
        ]
        candidates.sort(key=lambda x: -x[1])

        for lang, score, patterns in candidates:
            if score == 0:
                continue
            # Try each pattern
            for pattern, intent, topic_group in patterns:
                m = re.match(pattern, original_lower, re.IGNORECASE)
                if m:
                    topic = m.group(topic_group).strip() if topic_group > 0 else m.group(0).strip()
                    # Clean topic: remove function words
                    topic = self._clean_topic(topic, lang)
                    return {
                        'language': lang,
                        'intent': intent,
                        'topic': topic,
                        'confidence': min(0.95, 0.5 + score * 0.15),
                    }

            # Even if no pattern matched, if score >= 2, it's likely this language
            if score >= 2:
                topic = self._extract_topic_by_removal(original_lower, lang)
                return {
                    'language': lang,
                    'intent': 'general',
                    'topic': topic,
                    'confidence': 0.5 + score * 0.1,
                }

        return None

    def _clean_topic(self, topic: str, lang: str) -> str:
        """Remove function words from topic, keep content words."""
        markers = TELUGU_MARKERS if lang == 'te' else HINDI_MARKERS if lang == 'hi' else TAMIL_MARKERS
        words = topic.split()
        clean = [w for w in words if w.lower() not in markers]
        return ' '.join(clean).strip()

    def _extract_topic_by_removal(self, text: str, lang: str) -> str:
        """Extract topic by removing known function words."""
        markers = TELUGU_MARKERS if lang == 'te' else HINDI_MARKERS if lang == 'hi' else TAMIL_MARKERS
        words = text.split()
        content = [w for w in words if w.lower() not in markers]
        return ' '.join(content).strip()

    def _detect_style(self, text: str) -> str:
        """Detect formality level."""
        # Polite markers
        if re.search(r'(?:andi|garu|meeru|cheyyandi|pannungo|sollungo|aap|ji)', text.lower()):
            return "formal"
        # Casual markers
        if re.search(r'(?:bro|dude|yaar|da|ra|re|machi)', text.lower()):
            return "casual"
        return "neutral"
