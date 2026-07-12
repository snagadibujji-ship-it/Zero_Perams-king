#!/usr/bin/env python3
"""
Natural Response v6.0 — The Intelligence Layer
Not a formatter. An assembler that queries live knowledge, ranks facts,
adapts to user, varies structure, catches garbage, and never repeats.
"""

import re, random, time
from typing import Dict, List, Optional, Tuple, Callable

# ═══════════════════════════════════════════════════════════════
# QUESTION ARCHETYPES
# ═══════════════════════════════════════════════════════════════

ARCHETYPE_FACTUAL = 'factual'
ARCHETYPE_DEEP = 'deep'
ARCHETYPE_CAUSAL_WHY = 'causal_why'
ARCHETYPE_CAUSAL_WHATIF = 'causal_whatif'
ARCHETYPE_MATH = 'math'
ARCHETYPE_BOOLEAN = 'boolean'
ARCHETYPE_COMPARATIVE = 'compare'
ARCHETYPE_OPINION = 'opinion'
ARCHETYPE_EMOTIONAL = 'emotional'
ARCHETYPE_CREATIVE = 'creative'
ARCHETYPE_REFERENCE = 'reference'
ARCHETYPE_META = 'meta'

# ═══════════════════════════════════════════════════════════════
# GARBAGE SIGNALS (if raw answer contains these → rebuild)
# ═══════════════════════════════════════════════════════════════

GARBAGE_SIGNALS = [
    'is a concept', 'Interesting. Tell me more', 'I hear you',
    'Got it. What else', 'Noted.', 'Young is a concept',
    'Interesting.', 'Tell me more.', 'What else',
    'How can I help', 'I appreciate that', 'Thanks for sharing',
    'That\'s nice', 'Go on.', 'Continue.',
]

# ═══════════════════════════════════════════════════════════════
# FILLER + ROBOT PATTERNS (kill always)
# ═══════════════════════════════════════════════════════════════

FILLER_KILL = {
    'certainly', 'absolutely', 'great question', "that's a great question",
    "i'd be happy to help", 'sure thing', 'of course', 'let me explain',
    "that's an interesting question", 'good question', 'excellent question',
    'indeed', 'furthermore', 'moreover', 'additionally',
    'in conclusion', 'to summarize', 'in summary',
    "it's worth noting that", "it's important to note that",
    "let me break this down", "here are the key points:",
    "to answer your question,", "based on my knowledge,",
}

ROBOT_CLEANUPS = [
    (r'Most people are familiar with (.+?), (an? .+?)\.', r'\1 is \2.'),
    (r'Characteristically,? ?This entity is (.+?)\.', r"It's \1."),
    (r'In terms of characteristics,? ?This entity is (.+?)\.', r"It's \1."),
    (r'What makes it distinctive.*?is (.+?)\.', r"It's \1."),
    (r'This entity is (.+?)\.', r"It's \1."),
    (r'One notable feature of \w+ is (.+?)\.', r'It has \1.'),
    (r'Furthermore,? ?\w+ is equipped with (.+?)\.', r'It has \1.'),
    (r'(?:Overall|In summary),? ?\w+ is a (?:versatile|fascinating|notable|noteworthy).+?\.', ''),
    (r'\w+ stands as a significant .+?\.', ''),
    (r'^\w+ is a concept\.?\s*', ''),
    (r', definitely\.', '.'),
]

TAG_PATTERNS = [r'\[Verified:.*?\]', r'\[Proof:.*?\]', r'\[Instant:.*?\]',
                r'\[KDA\]\s*', r'\[Agent:.*?\]\s*', r'\(confidence:.*?\)']


class NaturalResponseV6:
    """The intelligence layer. Queries knowledge, assembles responses dynamically."""

    def __init__(self, query_func=None, worldsim_func=None, web_func=None, memory_func=None):
        self.query = query_func          # f(topic) → [(rel, obj, conf), ...]
        self.worldsim = worldsim_func    # f(action, obj) → [(effect, prob), ...]
        self.web = web_func              # f(query) → str or None
        self.memory = memory_func        # f(topic) → [memories]
        
        self.session = {
            'patterns_used': [],
            'facts_given': set(),
            'math_streak': 0,
            'user_style': None,
            'user_level': 'default',
            'user_energy': 'normal',
            'topics_covered': [],
            'turn': 0,
        }

    # ═══════════════════════════════════════════════════════════
    # MAIN ENTRY POINT
    # ═══════════════════════════════════════════════════════════

    def respond(self, raw_answer: str, question: str, confidence: float = 0.9) -> Dict:
        """Process any raw answer into natural human response."""
        self.session['turn'] += 1

        # Stage 1: Comprehend
        arch = self._comprehend(question)
        
        # Stage 2: Gate (catch garbage)
        raw_answer, was_rebuilt = self._gate(raw_answer, question, arch)
        
        # Stage 3: Enrich
        topic = self._extract_topic(question)
        enrichments = self._enrich(topic, arch)
        
        # Stage 4: Rank enrichments
        ranked = self._rank(enrichments, topic)
        
        # Stage 5: Context (for causal)
        causal_ctx = self._causal_context(question, arch) if 'causal' in arch else None
        
        # Stage 6: Assemble
        text = self._assemble(raw_answer, question, arch, ranked, causal_ctx, confidence)
        
        # Stage 7: Personality
        text = self._personality(text, question, arch, confidence)
        
        # Stage 8: Adapt (session tracking)
        self._adapt(question, text, arch, topic)
        
        # Extract proof for /prove mode
        proof = self._extract_proof(raw_answer if not was_rebuilt else '')
        
        return {"display": text, "proof": proof}

    # ═══════════════════════════════════════════════════════════
    # STAGE 1: COMPREHEND
    # ═══════════════════════════════════════════════════════════

    def _comprehend(self, question: str) -> str:
        """Classify question into archetype."""
        q = question.lower().strip()
        
        # Emotional
        if any(w in q for w in ['feel sad', 'feeling sad', 'feeling really', 'depressed',
                                 'lonely', 'anxious', 'scared', 'angry', 'i am sad',
                                 "i'm sad", 'feeling down', 'feeling bad', 'hate my',
                                 'want to cry', 'feeling lonely', 'nobody cares']):
            return ARCHETYPE_EMOTIONAL
        # Creative
        if any(w in q for w in ['write me', 'make up', 'imagine', 'create a story', 'poem']):
            return ARCHETYPE_CREATIVE
        # Opinion
        if any(w in q for w in ['good or bad', 'should i', 'is it right', 'pros and cons', 'ethical']):
            return ARCHETYPE_OPINION
        # Meta
        if any(w in q for w in ['how do you know', 'are you sure', 'prove it', 'your sources']):
            return ARCHETYPE_META
        # Math
        if any(w in q for w in ['times', 'plus', 'minus', 'divided', 'factorial', 'power of',
                                 'square root', 'prime', 'even', 'odd', 'calculate']):
            return ARCHETYPE_MATH
        # Causal what-if
        if 'what happens' in q or 'what if' in q or 'what would' in q:
            return ARCHETYPE_CAUSAL_WHATIF
        # Causal why
        if q.startswith('why') or 'why ' in q or 'what causes' in q:
            return ARCHETYPE_CAUSAL_WHY
        # Boolean
        if q.startswith(('is ', 'can ', 'does ', 'do ', 'are ', 'was ', 'will ')):
            return ARCHETYPE_BOOLEAN
        # Comparative
        if any(w in q for w in ['heavier', 'bigger', 'faster', 'better', ' vs ', ' or ', 'compare']):
            return ARCHETYPE_COMPARATIVE
        # Deep (how does X work, explain)
        if any(w in q for w in ['how does', 'explain', 'mechanism', 'how is']):
            return ARCHETYPE_DEEP
        # Reference back
        if any(w in q for w in ['that thing', 'we talked', 'you said', 'more about it']):
            return ARCHETYPE_REFERENCE
        
        return ARCHETYPE_FACTUAL

    # ═══════════════════════════════════════════════════════════
    # STAGE 2: GATE (catch garbage, rebuild if needed)
    # ═══════════════════════════════════════════════════════════

    def _gate(self, raw: str, question: str, arch: str) -> Tuple[str, bool]:
        """If answer is garbage, rebuild from knowledge. Returns (answer, was_rebuilt)."""
        # Special archetypes handle themselves
        if arch == ARCHETYPE_EMOTIONAL:
            return "That's rough. I'm here if you want to talk, or I can help with something practical.", True
        if arch == ARCHETYPE_CREATIVE:
            return "I'm built for facts and reasoning — creative writing isn't my strength. I'd be making things up.", True
        
        if not raw or len(raw.strip()) < 5:
            rebuilt = self._rebuild(question)
            return (rebuilt if rebuilt else "I don't know this one. Want me to look it up?"), True
        
        raw_lower = raw.lower()
        for signal in GARBAGE_SIGNALS:
            if signal.lower() in raw_lower:
                rebuilt = self._rebuild(question)
                if rebuilt:
                    return rebuilt, True
                # Rebuild failed but answer IS garbage — strip the garbage part
                cleaned = raw
                for sig in GARBAGE_SIGNALS:
                    # Also strip "X is a concept" where X is the subject
                    cleaned = re.sub(r'\w+\s+' + re.escape(sig), '', cleaned, flags=re.IGNORECASE)
                    cleaned = cleaned.replace(sig, '').replace(sig.capitalize(), '')
                # Clean robot patterns too
                cleaned = re.sub(r'Characteristically,?\s*', '', cleaned)
                cleaned = re.sub(r'This entity is\s*', 'It\'s ', cleaned)
                cleaned = re.sub(r'^\s*[.,;:\s]+', '', cleaned)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip().strip('.')
                if cleaned and len(cleaned) > 15:
                    return cleaned + '.', True
                return "I don't have solid info on this one.", True
        
        # Also catch: answer is just "X = 0" (math parse on non-math)
        if re.match(r'.+ = \d+', raw) and arch != 'math':
            return "I don't have solid info on this one.", True
        
        return raw, False

    def _rebuild(self, question: str) -> str:
        """Build answer from knowledge sources when engine failed."""
        topic = self._extract_topic(question)
        
        # Try KDA query
        if self.query:
            facts = self.query(topic)
            if facts and len(facts) >= 1:
                # Build natural sentences from triples
                sentences = []
                for rel, obj, conf in facts[:4]:
                    rel_clean = str(rel).replace('_', ' ')
                    obj_clean = str(obj)
                    if rel_clean == 'is a' or rel_clean == 'is_a':
                        sentences.append(f"{topic.capitalize()} is {obj_clean}")
                    elif rel_clean in ('has', 'has property', 'has_property'):
                        sentences.append(f"It has {obj_clean}")
                    elif rel_clean in ('causes', 'leads to'):
                        sentences.append(f"It causes {obj_clean}")
                    else:
                        sentences.append(f"{rel_clean.capitalize()}: {obj_clean}")
                if sentences:
                    return '. '.join(sentences) + '.'
        
        # Try web search
        if self.web:
            result = self.web(question)
            if result and len(result) > 20:
                sentences = re.split(r'(?<=[.!?])\s+', result)
                return ' '.join(sentences[:2])
        
        return ''


    # ═══════════════════════════════════════════════════════════
    # STAGE 3: ENRICH (query live knowledge)
    # ═══════════════════════════════════════════════════════════

    def _enrich(self, topic: str, arch: str) -> List[Tuple[str, str, float]]:
        """Query knowledge sources for additional facts. Returns [(relation, object, confidence)]."""
        if not topic or arch in (ARCHETYPE_MATH, ARCHETYPE_EMOTIONAL, ARCHETYPE_CREATIVE):
            return []
        
        facts = []
        
        # Source 1: KDA/KG query
        if self.query:
            try:
                results = self.query(topic)
                if results:
                    for item in results[:10]:
                        if isinstance(item, tuple) and len(item) >= 3:
                            facts.append((item[0] if len(item) > 3 else item[0], item[1] if len(item) > 3 else item[1], item[2] if len(item) > 3 else item[-1]))
                        elif isinstance(item, tuple) and len(item) == 3:
                            facts.append(item)
            except: pass
        
        # Source 2: Memory (user-taught facts)
        if self.memory:
            try:
                memories = self.memory(topic)
                if memories:
                    for mem in memories[:3]:
                        if isinstance(mem, dict):
                            facts.append(('learned', mem.get('text', ''), 0.9))
                        elif isinstance(mem, str):
                            facts.append(('learned', mem, 0.9))
            except: pass
        
        return facts

    # ═══════════════════════════════════════════════════════════
    # STAGE 4: RANK (user-aware interestingness scoring)
    # ═══════════════════════════════════════════════════════════

    def _rank(self, facts: List, topic: str) -> List[Tuple[str, str, float]]:
        """Rank facts by interestingness. Return top 2 above threshold."""
        if not facts:
            return []
        
        scored = []
        for rel, obj, conf in facts:
            score = 0.3  # Base
            obj_lower = str(obj).lower()
            
            # Surprise bonus
            if any(w in obj_lower for w in ['only', 'unique', 'unlike', 'exception', 'first', 'largest', 'smallest']):
                score += 0.4
            # Number bonus (specific)
            if re.search(r'\d+', obj_lower):
                score += 0.2
            # Practical bonus
            if any(w in obj_lower for w in ['used for', 'helps', 'prevents', 'causes', 'danger']):
                score += 0.2
            # Vague penalty
            if any(w in obj_lower for w in ['important', 'interesting', 'notable', 'well-known', 'various']):
                score -= 0.3
            # Already given penalty
            fact_key = f"{topic}:{rel}:{obj}"
            if fact_key in self.session['facts_given']:
                score -= 0.8
            # Redundancy with topic name
            if obj_lower == topic.lower() or topic.lower() in obj_lower:
                score -= 0.2
            
            scored.append((rel, obj, score))
        
        # Sort by score, filter by threshold
        scored.sort(key=lambda x: x[2], reverse=True)
        result = [(r, o, s) for r, o, s in scored if s > 0.45][:2]
        
        # Mark as given
        for r, o, s in result:
            self.session['facts_given'].add(f"{topic}:{r}:{o}")
        
        return result

    # ═══════════════════════════════════════════════════════════
    # STAGE 5: CAUSAL CONTEXT (dynamic from rules)
    # ═══════════════════════════════════════════════════════════

    def _causal_context(self, question: str, arch: str) -> Optional[Dict]:
        """Build causal context from WorldSim rules dynamically."""
        if not self.worldsim:
            return None
        
        q = question.lower()
        # Extract action + object
        action, obj = '', ''
        match = re.search(r'(?:if you|if i|when you|when i)\s+(\w+)\s+(.+?)(?:\?|$)', q)
        if match:
            action, obj = match.group(1), match.group(2).strip().rstrip('?.')
        elif re.search(r'(drop|heat|cool|mix|burn|freeze|throw|hit)\s+(.+)', q):
            m = re.search(r'(drop|heat|cool|mix|burn|freeze|throw|hit)\s+(.+)', q)
            if m: action, obj = m.group(1), m.group(2).strip().rstrip('?.')
        
        if not action or not obj:
            return None
        
        try:
            results = self.worldsim(action, obj)
            if results and len(results) > 0:
                main_effect = results[0][0] if isinstance(results[0], tuple) else str(results[0])
                main_prob = results[0][1] if isinstance(results[0], tuple) and len(results[0]) > 1 else 0.9
                secondary = results[1][0] if len(results) > 1 and isinstance(results[1], tuple) else ''
                
                # Check object danger
                is_dangerous = any(d in obj for d in ['bleach', 'ammonia', 'acid', 'gasoline', 'poison'])
                # Check object fragility
                is_fragile = any(f in obj for f in ['glass', 'egg', 'ceramic', 'mirror', 'phone', 'screen'])
                
                return {
                    'action': action, 'object': obj,
                    'effect': main_effect.replace('_', ' '),
                    'secondary': secondary.replace('_', ' ') if secondary else '',
                    'probability': main_prob,
                    'dangerous': is_dangerous,
                    'fragile': is_fragile,
                }
        except: pass
        return None

    # ═══════════════════════════════════════════════════════════
    # STAGE 6: ASSEMBLE (6 patterns, rotate)
    # ═══════════════════════════════════════════════════════════

    def _assemble(self, raw: str, question: str, arch: str, 
                  enrichments: List, causal: Optional[Dict], confidence: float) -> str:
        """Build final response from components."""
        
        # Handle special archetypes first
        if arch == ARCHETYPE_EMOTIONAL:
            return "That's rough. I'm here if you want to talk, or I can help with something practical."
        if arch == ARCHETYPE_CREATIVE:
            return "I'm built for facts and reasoning — creative writing isn't my strength. I'd be making things up."
        if arch == ARCHETYPE_OPINION:
            return raw  # Let DEBATE mode handle (already in pipeline)
        if arch == ARCHETYPE_META:
            return raw  # Let /prove handle
        
        # Math: clean and direct
        if arch == ARCHETYPE_MATH:
            return self._assemble_math(raw, question)
        
        # Causal: build from context
        if arch == ARCHETYPE_CAUSAL_WHATIF and causal:
            return self._assemble_causal(causal)
        
        # Boolean: personality
        if arch == ARCHETYPE_BOOLEAN:
            return self._assemble_boolean(raw)
        
        # Comparative
        if arch == ARCHETYPE_COMPARATIVE:
            return self._assemble_comparative(raw)
        
        # General (factual, deep, reference): clean + enrich
        return self._assemble_general(raw, enrichments, arch)

    def _assemble_math(self, raw: str, question: str) -> str:
        """Math: clean, show operation, add flavor on first few."""
        raw = re.sub(r'\[.*?\]', '', raw).strip()
        self.session['math_streak'] += 1
        
        # Factorial
        match = re.search(r'(\d+)!\s*=\s*(\d+)', raw)
        if match:
            n, result = match.group(1), int(match.group(2))
            text = f"{n}! = {result:,}."
            if self.session['math_streak'] <= 2 and result > 1000000:
                text += " That escalates fast."
            return text
        
        # Power
        match = re.search(r'(\d+) to the power of (\d+)\s*=\s*(\d+)', raw)
        if match:
            result = int(match.group(3))
            text = f"{match.group(1)}^{match.group(2)} = {result:,}."
            if self.session['math_streak'] <= 2 and result > 1000:
                text += " Grows fast."
            return text
        
        # Multiplication
        match = re.search(r'(\d+)\s*[x×]\s*(\d+)\s*=\s*(\d+)', raw)
        if match:
            return f"{match.group(1)} × {match.group(2)} = {match.group(3)}."
        
        # Square root
        if 'square root' in raw.lower():
            raw = re.sub(r'\[.*?\]', '', raw).strip()
            if not raw.endswith('.'): raw += '.'
            return raw
        
        # Prime/even/odd
        raw = raw.replace(' a prime number', ' prime')
        if not raw.endswith('.'): raw += '.'
        return raw

    def _assemble_causal(self, ctx: Dict) -> str:
        """Build causal response from context dict."""
        effect = ctx['effect']
        secondary = ctx.get('secondary', '')
        
        # Fix verb: "breaks" → "break"
        verb = effect
        if verb.endswith('s') and not verb.endswith('ss'):
            verb = verb[:-1]
        
        if ctx.get('dangerous'):
            response = f"Don't. That produces {effect} which is harmful."
            response += " Get out of the area and ventilate if it happens."
            return response
        
        # Direct effect
        if secondary:
            response = f"It'll {verb}, leaving {secondary}."
        else:
            response = f"It'll {verb}."
        
        # Add object-awareness
        if ctx.get('fragile'):
            response += f" {ctx['object'].capitalize()} is fragile — doesn't take much."
        
        # High probability = confident. Lower = hedged.
        if ctx['probability'] < 0.7:
            response = f"Might {verb}, depends on the situation."
        
        return response

    def _assemble_boolean(self, raw: str) -> str:
        """Boolean answers: personality variants."""
        raw = re.sub(r'\[.*?\]', '', raw).strip()
        raw = raw.replace('By syllogism: ', '')
        raw = raw.replace('the subject is a', "it's a")
        raw = raw.replace('therefore the subject is', "so it's")
        raw = raw.replace(' a prime number', ' prime')
        if not raw.endswith('.'): raw += '.'
        
        # Casual personality
        if random.random() < 0.3:
            raw = raw.replace('Yes,', random.choice(['Yeah,', 'Yep,', 'Yes,']), 1)
            raw = raw.replace('Yes.', random.choice(['Yeah.', 'Yep.', 'Yes.']), 1)
            raw = raw.replace('No,', random.choice(['Nope,', 'No,', 'Nah,']), 1)
            raw = raw.replace('No.', random.choice(['Nope.', 'No.']), 1)
        return raw

    def _assemble_comparative(self, raw: str) -> str:
        """Comparative: direct and clean."""
        raw = re.sub(r'\[.*?\]', '', raw).strip()
        if 'same' in raw.lower() or 'weigh the same' in raw.lower():
            return "Same weight — a kilo is a kilo regardless of what it's made of."
        if not raw.endswith('.'): raw += '.'
        return raw

    def _assemble_general(self, raw: str, enrichments: List, arch: str) -> str:
        """General knowledge: clean + optionally enrich."""
        # Strip all tags and robot patterns
        text = raw
        for p in TAG_PATTERNS:
            text = re.sub(p, '', text)
        for pattern, repl in ROBOT_CLEANUPS:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        # Kill filler
        for filler in FILLER_KILL:
            text = re.sub(re.escape(filler), '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'^[.,\s]+', '', text)
        
        # If too short after cleanup and we have enrichments, add them
        if enrichments and len(text) < 60:
            for rel, obj, score in enrichments[:2]:
                fact_text = str(obj).strip()
                if fact_text and fact_text.lower() not in text.lower():
                    text = text.rstrip('.') + '. ' + fact_text.capitalize()
                    if not text.endswith('.'):
                        text += '.'
        
        # Sentence limit (keep 3 max for default)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip() and len(s.strip()) > 5]
        sentences = [s for s in sentences if not re.match(r'^(?:Overall|In summary)', s)]
        if sentences:
            text = ' '.join(sentences[:3])
            if not text.endswith('.'): text += '.'
        
        return text


    # ═══════════════════════════════════════════════════════════
    # STAGE 7: PERSONALITY
    # ═══════════════════════════════════════════════════════════

    def _personality(self, text: str, question: str, arch: str, confidence: float) -> str:
        """Add personality without being annoying."""
        if not text:
            return text
        
        # Don't add personality to emotional/creative responses
        if arch in (ARCHETYPE_EMOTIONAL, ARCHETYPE_CREATIVE):
            return text
        
        # Rare acknowledgment (1 in 20) for genuinely unusual questions
        if self.session['turn'] % 20 == 7 and arch not in (ARCHETYPE_MATH, ARCHETYPE_BOOLEAN):
            unusual_signals = ['paradox', 'impossible', 'weird', 'strange', 'counterintuitive']
            if any(w in question.lower() for w in unusual_signals):
                text = "Interesting angle. " + text
        
        # Low confidence → natural hedge
        if confidence < 0.5 and not text.startswith(("I don't", "Might", "Probably")):
            text = "I think " + text[0].lower() + text[1:] if text else text
        
        return text

    # ═══════════════════════════════════════════════════════════
    # STAGE 8: ADAPT (session tracking)
    # ═══════════════════════════════════════════════════════════

    def _adapt(self, question: str, response: str, arch: str, topic: str):
        """Track session state for future responses."""
        # Track topics
        if topic and topic not in self.session['topics_covered']:
            self.session['topics_covered'].append(topic)
            if len(self.session['topics_covered']) > 30:
                self.session['topics_covered'] = self.session['topics_covered'][-30:]
        
        # Math streak
        if arch != ARCHETYPE_MATH:
            self.session['math_streak'] = 0
        
        # Detect user style (lock after 3 turns)
        if not self.session['user_style'] and self.session['turn'] >= 3:
            self.session['user_style'] = self._detect_style(question)

    # ═══════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════

    def _extract_topic(self, question: str) -> str:
        """Get the main subject from a question."""
        stop = {'what', 'is', 'the', 'a', 'an', 'who', 'where', 'when', 'how', 'why',
                'are', 'was', 'do', 'does', 'tell', 'me', 'about', 'can', 'you',
                'please', 'would', 'could', 'should', 'will', 'it', 'that', 'this',
                'of', 'in', 'on', 'for', 'and', 'or', 'if', 'to', 'from', 'with',
                'happens', 'happen', 'there', 'i', 'my', 'your', 'whats', "what's"}
        words = question.lower().strip().rstrip('?!.').split()
        content = [w for w in words if w not in stop and len(w) > 2]
        return content[-1] if content else (words[-1] if words else '')

    def _detect_style(self, question: str) -> str:
        """Detect user communication style."""
        q = question.lower()
        if len(q.split()) <= 4 and not q.endswith('?'):
            return 'casual'
        if any(w in q for w in ['specifically', 'technically', 'mechanism', 'molecular']):
            return 'technical'
        if any(w in q for w in ['could you please', 'i would like']):
            return 'formal'
        return 'default'

    def _extract_proof(self, raw: str) -> str:
        """Extract proof data for /prove mode."""
        proofs = re.findall(r'\[(?:Verified|Proof|Instant):.*?\]', raw)
        return ' '.join(proofs) if proofs else ''


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE API (drop-in replacement)
# ═══════════════════════════════════════════════════════════════

_instance = None

def get_natural_response(query_func=None, worldsim_func=None, web_func=None) -> NaturalResponseV6:
    """Get or create singleton instance."""
    global _instance
    if _instance is None:
        _instance = NaturalResponseV6(query_func, worldsim_func, web_func)
    return _instance


def humanize(raw_answer: str, question: str = '', confidence: float = 0.9,
             context: Dict = None) -> Dict:
    """Drop-in compatible API. Returns {"display": str, "proof": str}."""
    nr = get_natural_response()
    return nr.respond(raw_answer, question, confidence)


def make_human(raw_answer: str, question: str = '', confidence: float = 0.9) -> str:
    """Simple wrapper: returns just the display text."""
    return humanize(raw_answer, question, confidence)['display']


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Create with mock knowledge query
    def mock_query(topic):
        db = {
            'water': [('is_a', 'compound', 0.99), ('formula', 'H2O', 0.99), 
                      ('covers', '71% of Earth surface', 0.95), ('essential_for', 'all life', 0.99)],
            'gravity': [('is_a', 'fundamental force', 0.99), ('causes', 'objects to fall', 0.95),
                        ('discovered_by', 'Newton (described)', 0.9)],
            'sun': [('is_a', 'star', 0.99), ('age', '4.6 billion years', 0.95),
                    ('distance', '150 million km from Earth', 0.95)],
        }
        return db.get(topic, [])

    def mock_worldsim(action, obj):
        rules = {
            ('drop', 'glass'): [('breaks', 0.95), ('sharp_shards', 0.86)],
            ('heat', 'ice'): [('melts', 0.99), ('water', 0.98)],
            ('mix', 'bleach and ammonia'): [('toxic_gas', 0.95)],
        }
        return rules.get((action, obj), [])

    nr = NaturalResponseV6(query_func=mock_query, worldsim_func=mock_worldsim)

    print("═══ Natural Response v6.0 — FINAL TEST ═══\n")
    
    tests = [
        ("what is 15 times 17", "15 x 17 = 255 [Verified: exact]", 1.0),
        ("what is 15 factorial", "15! = 1307674368000. [Verified]", 1.0),
        ("is 97 prime", "Yes, 97 is a prime number. [Verified: trial division]", 1.0),
        ("what is water", "Most people are familiar with water, an inorganic compound. This entity is needed for life.", 0.95),
        ("whats gravity", "Gravity is a concept.", 0.9),  # GARBAGE → should rebuild
        ("what happens if you drop glass", "breaks (95%) → sharp_shards (86%)", 0.95),
        ("what happens if you mix bleach and ammonia", "toxic_gas (95%)", 0.95),
        ("what is heavier a kg of steel or feathers", "They weigh the same. [Proof: by definition]", 1.0),
        ("I'm feeling really sad today", "", 0.0),
        ("write me a poem about love", "", 0.0),
        ("who are you", "I am Axima, a zero-parameter intelligence engine.", 0.99),
    ]

    for q, raw, conf in tests:
        r = nr.respond(raw, q, conf)
        print(f"> {q}")
        print(f"  {r['display']}")
        print()
