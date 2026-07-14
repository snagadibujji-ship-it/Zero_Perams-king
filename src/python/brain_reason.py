"""
AXIMA BRAIN — Module 7: Reasoning Engine
Built by: Ghias + Kiro

The missing piece: CONSTRUCT answers from multiple chunks.
Multi-hop reasoning: chain facts together to answer complex questions.
Context tracking: remember what user was talking about.

Without this, Brain is just search. WITH this, it THINKS.
"""

import re
from typing import Dict, List, Optional, Tuple
from brain_ingest import DocumentBrain, Chunk


class ReasoningEngine:
    """Construct answers by chaining knowledge. Multi-hop reasoning."""

    def __init__(self, brain: DocumentBrain):
        self.brain = brain
        self.context: List[str] = []  # recent topics discussed (for "the other one")
        self.last_chunks: List[Chunk] = []  # last retrieved chunks

    def answer(self, question: str) -> Dict:
        """Answer a question by reasoning over knowledge chunks.
        
        Returns: {
            answer: constructed answer text,
            sources: [(source, section)],
            confidence: 0-1,
            reasoning_chain: [step1, step2, ...],
            related: [follow-up topics]
        }
        """
        q_lower = question.lower()

        # Handle context references ("the other one", "it", "that")
        question = self._resolve_context(question)

        # Classify question type to determine reasoning strategy
        q_type = self._classify_question(question)

        # Execute appropriate reasoning strategy
        if q_type == "what":
            return self._answer_what(question)
        elif q_type == "why":
            return self._answer_why(question)
        elif q_type == "how":
            return self._answer_how(question)
        elif q_type == "compare":
            return self._answer_compare(question)
        elif q_type == "consequence":
            return self._answer_consequence(question)
        elif q_type == "compute":
            return self._answer_compute(question)
        else:
            return self._answer_general(question)

    def _classify_question(self, q: str) -> str:
        """Determine what type of reasoning this question needs."""
        ql = q.lower()
        if re.search(r'\bif\b.*\bwhat\b|\bwhat\s+happens?\s+(?:if|when)\b', ql):
            return "consequence"
        if re.search(r'\bwhy\b|\breason\b|\bcause\b', ql):
            return "why"
        if re.search(r'\bhow\b(?!\s+many|\s+much)', ql):
            return "how"
        if re.search(r'\bcompare\b|\bdifference\b|\bvs\b|\bversus\b|\bbetter\b', ql):
            return "compare"
        if re.search(r'\bcalculate\b|\bcompute\b|\bfind\b.*\b\d|\bhow\s+(?:many|much)\b', ql):
            return "compute"
        if re.search(r'\bwhat\b|\bdefine\b|\bwho\b|\bwhere\b|\bwhich\b', ql):
            return "what"
        return "general"

    def _resolve_context(self, question: str) -> str:
        """Replace pronouns/references with actual topics from context."""
        ql = question.lower()
        # "the other one" / "the first one" / "it" / "that"
        if self.context:
            if 'the other one' in ql or 'the second' in ql:
                if len(self.context) >= 2:
                    question = question.replace('the other one', self.context[-2])
                    question = question.replace('the second', self.context[-2])
            if re.search(r'\bit\b|\bthat\b|\bthis\b', ql) and not re.search(r'\bwhat\s+is\s+it\b', ql):
                # "it"/"that" likely refers to last topic
                last = self.context[-1] if self.context else ""
                if last and len(question.split()) <= 8:
                    question = re.sub(r'\bit\b', last, question, count=1)
        return question

    def _answer_what(self, question: str) -> Dict:
        """Answer definitional/factual questions."""
        chunks = self.brain.search(question, top_k=3)
        self.last_chunks = chunks

        if not chunks:
            return self._no_answer(question)

        # Extract the best answer from top chunk
        top = chunks[0]
        answer_text = ""

        # If it's a definition chunk, use the relationship
        if top.chunk_type == "definition":
            for subj, rel, obj in top.relationships:
                if rel == "is":
                    answer_text = f"{subj} is {obj}"
                    break

        # Otherwise use the most relevant sentence
        if not answer_text:
            # Find sentence with most query term overlap
            query_terms = set(re.findall(r'\b\w{4,}\b', question.lower()))
            best_sent = ""
            best_score = 0
            for sent in re.split(r'[.!?\n]', top.text):
                sent = sent.strip()
                if len(sent) < 10:
                    continue
                sent_terms = set(re.findall(r'\b\w{4,}\b', sent.lower()))
                overlap = len(query_terms & sent_terms)
                if overlap > best_score:
                    best_score = overlap
                    best_sent = sent
            answer_text = best_sent

        # Update context
        topic = self._extract_topic(question)
        if topic:
            self.context.append(topic)
            self.context = self.context[-10:]  # keep last 10

        return {
            "answer": answer_text,
            "sources": [(top.source, top.section)],
            "confidence": min(1.0, len(chunks) * 0.3),
            "reasoning_chain": [f"Found in: {top.source} ({top.section})"],
            "related": [c.topic for c in chunks[1:3] if c.topic],
        }

    def _answer_why(self, question: str) -> Dict:
        """Answer causal questions by finding the reason chain."""
        chunks = self.brain.search(question, top_k=5)
        self.last_chunks = chunks

        if not chunks:
            return self._no_answer(question)

        # Look for causal relationships
        reasons = []
        sources = []
        for chunk in chunks:
            for subj, rel, obj in chunk.relationships:
                if rel in ("causes", "enables", "depends_on"):
                    reasons.append(f"{subj} → {obj}")
                    sources.append((chunk.source, chunk.section))

            # Also look for "because" in text
            for m in re.finditer(r'because\s+(.+?)(?:[.\n]|$)', chunk.text, re.IGNORECASE):
                reasons.append(m.group(1).strip())
                sources.append((chunk.source, chunk.section))

            # "important because" / "this is because"
            for m in re.finditer(r'(?:important|necessary|needed)\s+because\s+(.+?)(?:[.\n])', chunk.text, re.IGNORECASE):
                reasons.append(m.group(1).strip())

        if reasons:
            answer = "Because: " + "; and ".join(reasons[:3])
        else:
            # Fallback: return most relevant sentence
            answer = chunks[0].text.split('.')[0]

        topic = self._extract_topic(question)
        if topic:
            self.context.append(topic)

        return {
            "answer": answer,
            "sources": sources[:3],
            "confidence": min(1.0, len(reasons) * 0.4),
            "reasoning_chain": [f"Reason {i+1}: {r}" for i, r in enumerate(reasons[:5])],
            "related": [],
        }

    def _answer_how(self, question: str) -> Dict:
        """Answer process/mechanism questions."""
        chunks = self.brain.search(question, top_k=5)
        self.last_chunks = chunks

        # Prefer procedure-type chunks
        procedures = [c for c in chunks if c.chunk_type == "procedure"]
        if procedures:
            chunk = procedures[0]
        elif chunks:
            chunk = chunks[0]
        else:
            return self._no_answer(question)

        # Extract steps from the text
        steps = []
        lines = chunk.text.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(r'^[\d]+[\.\)]\s|^[•\-\*]\s|^(?:first|then|next|finally)', line, re.IGNORECASE):
                steps.append(re.sub(r'^[\d\.\)\•\-\*\s]+', '', line).strip())

        if not steps:
            # No explicit steps — use sentences
            steps = [s.strip() for s in chunk.text.split('.') if len(s.strip()) > 15][:5]

        answer = '\n'.join(f"  {i+1}. {step}" for i, step in enumerate(steps))

        return {
            "answer": answer,
            "sources": [(chunk.source, chunk.section)],
            "confidence": 0.7 if steps else 0.3,
            "reasoning_chain": steps,
            "related": [],
        }

    def _answer_compare(self, question: str) -> Dict:
        """Answer comparison questions by finding both concepts."""
        # Extract the two things being compared
        m = re.search(r'(?:between|compare)\s+(.+?)\s+(?:and|vs|versus)\s+(.+?)(?:\?|$)', question, re.IGNORECASE)
        if not m:
            m = re.search(r'(.+?)\s+(?:vs|versus|or)\s+(.+?)(?:\?|$)', question, re.IGNORECASE)

        if m:
            thing1, thing2 = m.group(1).strip(), m.group(2).strip()
        else:
            return self._answer_general(question)

        # Search for each
        chunks1 = self.brain.search(thing1, top_k=3)
        chunks2 = self.brain.search(thing2, top_k=3)

        info1 = chunks1[0].text[:150] if chunks1 else "No information found"
        info2 = chunks2[0].text[:150] if chunks2 else "No information found"

        answer = f"{thing1}:\n  {info1}\n\n{thing2}:\n  {info2}"

        # Find explicit contrast relationships
        contrasts = []
        for chunk in self.brain.chunks.values():
            for subj, rel, obj in chunk.relationships:
                if rel == "opposite" and (thing1.lower() in subj.lower() or thing2.lower() in subj.lower()):
                    contrasts.append(f"{subj} is opposite to {obj}")

        if contrasts:
            answer += f"\n\nKey difference: {contrasts[0]}"

        return {
            "answer": answer,
            "sources": [(c.source, c.section) for c in (chunks1[:1] + chunks2[:1])],
            "confidence": 0.6,
            "reasoning_chain": [f"Found info on {thing1}", f"Found info on {thing2}", "Compared"],
            "related": [thing1, thing2],
        }

    def _answer_consequence(self, question: str) -> Dict:
        """Answer 'what happens if X' by chaining causal relationships.
        
        THIS IS MULTI-HOP REASONING:
        Q: "If photosynthesis stops, what happens to animals?"
        Chain: photosynthesis→produces oxygen, animals→need oxygen, no oxygen→animals die
        """
        # Extract the condition
        m = re.search(r'(?:if|when)\s+(.+?)(?:,|\s+what|\s+then|\s+how)', question, re.IGNORECASE)
        condition = m.group(1).strip() if m else question

        # Find what this condition CAUSES (hop 1)
        chunks = self.brain.search(condition, top_k=5)
        self.last_chunks = chunks

        chain = []
        current_effects = set()

        # Hop 1: direct effects of the condition
        for chunk in chunks:
            for subj, rel, obj in chunk.relationships:
                if rel in ("causes", "enables", "purpose"):
                    chain.append(f"{subj} → {obj}")
                    current_effects.add(obj.lower()[:30])

        # Hop 2: effects OF the effects (follow the chain)
        for effect in list(current_effects)[:3]:
            effect_chunks = self.brain.search(effect, top_k=2)
            for chunk in effect_chunks:
                for subj, rel, obj in chunk.relationships:
                    if rel in ("causes", "enables", "depends_on"):
                        chain.append(f"  → therefore: {subj} → {obj}")

        if chain:
            answer = f"If {condition}:\n" + '\n'.join(f"  {step}" for step in chain[:6])
        else:
            # Fallback
            answer = f"Based on available information, if {condition} then related processes would be affected."
            if chunks:
                answer += f"\n\nRelated: {chunks[0].text[:100]}"

        return {
            "answer": answer,
            "sources": [(c.source, c.section) for c in chunks[:3]],
            "confidence": min(1.0, len(chain) * 0.25),
            "reasoning_chain": chain,
            "related": list(current_effects)[:5],
        }

    def _answer_compute(self, question: str) -> Dict:
        """Route to computation engine."""
        # This would integrate with brain_compute.py
        return {
            "answer": "[Route to BrainCompute for numerical answer]",
            "sources": [],
            "confidence": 0,
            "reasoning_chain": ["Computation required — route to BrainCompute"],
            "related": [],
        }

    def _answer_general(self, question: str) -> Dict:
        """General fallback — return most relevant chunks."""
        chunks = self.brain.search(question, top_k=3)
        self.last_chunks = chunks

        if not chunks:
            return self._no_answer(question)

        # Combine top sentences from multiple chunks
        sentences = []
        sources = []
        for chunk in chunks[:3]:
            best = self._best_sentence(chunk.text, question)
            if best:
                sentences.append(best)
                sources.append((chunk.source, chunk.section))

        answer = ' '.join(sentences) if sentences else chunks[0].text[:200]

        topic = self._extract_topic(question)
        if topic:
            self.context.append(topic)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": 0.4,
            "reasoning_chain": ["General search — no specific reasoning strategy matched"],
            "related": [c.topic for c in chunks if c.topic],
        }

    def _no_answer(self, question: str) -> Dict:
        """When we have no relevant knowledge."""
        return {
            "answer": f"I don't have information about this in your sources. Try adding more material about '{self._extract_topic(question)}'.",
            "sources": [],
            "confidence": 0,
            "reasoning_chain": ["No relevant chunks found"],
            "related": [],
        }

    def _best_sentence(self, text: str, question: str) -> str:
        """Find the sentence in text most relevant to the question."""
        query_terms = set(re.findall(r'\b\w{4,}\b', question.lower()))
        best = ""
        best_score = 0
        for sent in re.split(r'[.!?\n]', text):
            sent = sent.strip()
            if len(sent) < 15:
                continue
            terms = set(re.findall(r'\b\w{4,}\b', sent.lower()))
            score = len(query_terms & terms)
            if score > best_score:
                best_score = score
                best = sent
        return best

    def _extract_topic(self, question: str) -> str:
        """Extract main topic from question."""
        q = re.sub(r'^(what|how|why|when|where|who|is|are|does|do|can|will|the|a|an)\s+', '',
                   question.lower(), flags=re.IGNORECASE).strip()
        return q.rstrip('?').strip()[:50]
