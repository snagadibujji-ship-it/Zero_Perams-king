"""
AXIMA BRAIN — Module 3: Study Engine
Built by: Ghias + Kiro

Generates flashcards, quizzes, summaries, mind maps, formula sheets
from ingested documents. No LLM — pure pattern extraction.
"""

import re
import random
from typing import Dict, List, Tuple, Optional
from brain_ingest import DocumentBrain, Chunk


class StudyEngine:
    """Generate study materials from ingested knowledge."""

    def __init__(self, brain: DocumentBrain):
        self.brain = brain

    # ──────────────────────────────────────────────────────────────
    # FLASHCARDS
    # ──────────────────────────────────────────────────────────────

    def generate_flashcards(self, topic: str = None, limit: int = 20) -> List[Dict[str, str]]:
        """Generate Q/A flashcards from knowledge chunks."""
        cards = []

        if topic:
            chunks = [self.brain.chunks[cid] for cid in self.brain.topic_index.get(topic.lower(), [])]
        else:
            chunks = list(self.brain.chunks.values())

        for chunk in chunks:
            # From definitions: "What is X?" → "X is Y"
            if chunk.chunk_type in ("definition", "key_fact"):
                for subj, rel, obj in chunk.relationships:
                    if rel == "is" and len(subj.split()) <= 4:
                        # Clean subject: remove filler words
                        clean_subj = re.sub(r'^(also|basically|essentially|so|ok|and)\s+\w+\s+that\s+', '', subj, flags=re.IGNORECASE).strip()
                        if len(clean_subj) >= 3 and len(obj) >= 5:
                            cards.append({"front": f"What is {clean_subj}?", "back": obj[:100], "source": chunk.source})

            # From formulas: "What is the formula for X?" → equation
            for formula in chunk.formulas:
                # For chemical equations, use as-is
                if '→' in formula:
                    cards.append({"front": "What is the chemical equation for this reaction?", "back": formula, "source": chunk.source})
                else:
                    lhs = formula.split('=')[0].strip()
                    if len(lhs) <= 5:  # Short variable names like F, KE, PE
                        cards.append({"front": f"What is the formula for {lhs}?", "back": formula, "source": chunk.source})

            # From causal relationships: "What does X cause?" → Y
            for subj, rel, obj in chunk.relationships:
                if rel == "causes" and len(subj.split()) <= 5 and len(obj.split()) <= 10:
                    cards.append({"front": f"What does {subj} produce/cause?", "back": obj, "source": chunk.source})
                elif rel == "purpose" and len(subj.split()) <= 4:
                    cards.append({"front": f"What is {subj} used for?", "back": obj[:80], "source": chunk.source})
                elif rel == "opposite" and len(subj.split()) <= 3:
                    cards.append({"front": f"What is the opposite of {subj}?", "back": obj, "source": chunk.source})
                elif rel == "enables" and len(obj.split()) <= 10:
                    cards.append({"front": f"Why is {subj} important?", "back": f"Without it: {obj}", "source": chunk.source})

        # Deduplicate and limit
        seen = set()
        unique = []
        for card in cards:
            key = card["front"]
            if key not in seen and len(card["back"]) >= 5:
                seen.add(key)
                unique.append(card)
        return unique[:limit]

    # ──────────────────────────────────────────────────────────────
    # QUIZZES
    # ──────────────────────────────────────────────────────────────

    def generate_quiz(self, topic: str = None, num_questions: int = 10) -> List[Dict]:
        """Generate quiz questions: MCQ, fill-blank, true/false."""
        questions = []

        if topic:
            chunks = [self.brain.chunks[cid] for cid in self.brain.topic_index.get(topic.lower(), [])]
        else:
            chunks = list(self.brain.chunks.values())

        for chunk in chunks:
            # MCQ from definitions
            if chunk.chunk_type == "definition" and chunk.relationships:
                for subj, rel, obj in chunk.relationships:
                    if rel == "is" and len(obj.split()) <= 15:
                        # Get distractors from other definitions
                        distractors = self._get_distractors(obj, chunks)
                        if len(distractors) >= 2:
                            options = [obj] + distractors[:3]
                            random.shuffle(options)
                            questions.append({
                                "type": "mcq",
                                "question": f"What is {subj}?",
                                "options": options,
                                "correct": obj,
                                "source": chunk.source,
                            })

            # Fill-in-blank from key sentences
            if chunk.key_terms and len(chunk.text) < 200:
                term = random.choice(chunk.key_terms)
                if term.lower() in chunk.text.lower():
                    blanked = re.sub(re.escape(term), "________", chunk.text, count=1, flags=re.IGNORECASE)
                    if blanked != chunk.text:
                        questions.append({
                            "type": "fill_blank",
                            "question": blanked[:150],
                            "correct": term,
                            "source": chunk.source,
                        })

            # True/False from relationships
            for subj, rel, obj in chunk.relationships:
                if rel == "is":
                    questions.append({
                        "type": "true_false",
                        "question": f"{subj} is {obj}",
                        "correct": True,
                        "source": chunk.source,
                    })
                    # Also generate a FALSE version (swap with different object)
                    fake = self._get_distractors(obj, chunks)
                    if fake:
                        questions.append({
                            "type": "true_false",
                            "question": f"{subj} is {fake[0]}",
                            "correct": False,
                            "source": chunk.source,
                        })

        random.shuffle(questions)
        return questions[:num_questions]

    def _get_distractors(self, correct: str, chunks: List[Chunk]) -> List[str]:
        """Find plausible wrong answers from other chunks."""
        distractors = []
        for chunk in chunks:
            for _, rel, obj in chunk.relationships:
                if rel == "is" and obj != correct and len(obj.split()) <= 15:
                    distractors.append(obj)
        return list(set(distractors))[:5]

    # ──────────────────────────────────────────────────────────────
    # SUMMARIES
    # ──────────────────────────────────────────────────────────────

    def generate_summary(self, source: str = None, topic: str = None) -> str:
        """Generate bullet-point summary from chunks."""
        if source:
            chunks = [c for c in self.brain.chunks.values() if c.source == source]
        elif topic:
            chunks = [self.brain.chunks[cid] for cid in self.brain.topic_index.get(topic.lower(), [])]
        else:
            chunks = list(self.brain.chunks.values())

        lines = []

        # Group by section
        sections: Dict[str, List[Chunk]] = {}
        for chunk in chunks:
            sec = chunk.section or "General"
            if sec not in sections:
                sections[sec] = []
            sections[sec].append(chunk)

        for section, sec_chunks in sections.items():
            lines.append(f"\n{'─'*40}")
            lines.append(f"  {section}")
            lines.append(f"{'─'*40}")

            for chunk in sec_chunks[:5]:  # max 5 per section
                # Extract first sentence as summary point
                first_sent = chunk.text.split('.')[0].strip()
                if len(first_sent) > 10:
                    lines.append(f"  • {first_sent}")

                # Show any formulas
                for f in chunk.formulas:
                    lines.append(f"    📐 {f}")

        return '\n'.join(lines)

    # ──────────────────────────────────────────────────────────────
    # MIND MAP (text-based)
    # ──────────────────────────────────────────────────────────────

    def generate_mindmap(self, topic: str = None) -> str:
        """Generate text-based mind map of concepts."""
        if topic:
            center = topic
            chunks = [self.brain.chunks[cid] for cid in self.brain.topic_index.get(topic.lower(), [])]
        else:
            # Use most common topic as center
            topics = self.brain.get_topics()
            if not topics:
                return "No knowledge ingested yet."
            center = max(topics, key=topics.get)
            chunks = list(self.brain.chunks.values())

        # Build tree: center → sections → key terms
        sections: Dict[str, Set] = {}
        for chunk in chunks:
            sec = chunk.section or chunk.topic or "misc"
            if sec not in sections:
                sections[sec] = set()
            for term in chunk.key_terms[:3]:
                sections[sec].add(term)

        # Render as text tree
        lines = [f"  ┌{'─'*50}┐"]
        lines.append(f"  │{'':^50}│")
        lines.append(f"  │{center.upper():^50}│")
        lines.append(f"  │{'':^50}│")
        lines.append(f"  └{'─'*25}┬{'─'*24}┘")
        lines.append(f"{'':25}│")

        for i, (section, terms) in enumerate(list(sections.items())[:8]):
            is_last = (i == len(sections) - 1) or (i == 7)
            connector = "└" if is_last else "├"
            lines.append(f"{'':20}{connector}── {section}")
            for j, term in enumerate(list(terms)[:4]):
                sub_conn = " " if is_last else "│"
                term_conn = "└" if j == len(list(terms)[:4])-1 else "├"
                lines.append(f"{'':20}{sub_conn}   {term_conn}── {term}")

        return '\n'.join(lines)

    # ──────────────────────────────────────────────────────────────
    # FORMULA SHEET
    # ──────────────────────────────────────────────────────────────

    def generate_formula_sheet(self, source: str = None) -> str:
        """Extract all formulas into a clean formula sheet."""
        formulas = self.brain.get_formulas()
        if source:
            formulas = [(f, s, sec) for f, s, sec in formulas if s == source]

        if not formulas:
            return "No formulas found in sources."

        lines = ["FORMULA SHEET", "═"*40]
        current_section = ""
        for formula, src, section in formulas:
            if section != current_section:
                current_section = section
                lines.append(f"\n  [{section}]")
            lines.append(f"  • {formula}")
            lines.append(f"    Source: {src}")

        return '\n'.join(lines)

    # ──────────────────────────────────────────────────────────────
    # GLOSSARY
    # ──────────────────────────────────────────────────────────────

    def generate_glossary(self) -> str:
        """Generate glossary of all defined terms."""
        definitions = self.brain.get_definitions()
        if not definitions:
            return "No definitions found."

        entries = []
        for chunk in definitions:
            for subj, rel, obj in chunk.relationships:
                if rel == "is":
                    entries.append((subj, obj, chunk.source))

        entries.sort(key=lambda x: x[0].lower())

        lines = ["GLOSSARY", "═"*40]
        for term, definition, source in entries:
            lines.append(f"\n  {term}")
            lines.append(f"    {definition}")
            lines.append(f"    [Source: {source}]")

        return '\n'.join(lines)


    # ──────────────────────────────────────────────────────────────
    # ADAPTIVE QUIZ — gets harder as user improves
    # ──────────────────────────────────────────────────────────────

    def adaptive_quiz(self, tracker, num_questions: int = 10) -> List[Dict]:
        """Generate quiz that adapts to user's level.
        
        - Weak concepts → easier questions (definition recall)
        - Medium concepts → moderate (application, fill-blank)  
        - Strong concepts → hard (multi-hop, computation, tricky false)
        """
        from brain_tracker import KnowledgeTracker

        questions = []
        chunks = list(self.brain.chunks.values())
        if not chunks:
            return []

        # Get user's weak/strong areas
        weak = [c for c, s in tracker.get_weak_concepts(0.3)]
        due = tracker.get_due_for_review()

        # PRIORITY 1: Due for review (about to forget)
        for concept in due[:3]:
            relevant = self.brain.search(concept, top_k=1)
            if relevant:
                chunk = relevant[0]
                # Easy question — just recall
                for subj, rel, obj in chunk.relationships:
                    if rel == "is":
                        questions.append({
                            "type": "recall",
                            "question": f"Quick recall: What is {subj}?",
                            "correct": obj[:50],
                            "difficulty": "review",
                            "concept": concept,
                        })
                        break

        # PRIORITY 2: Weak concepts — moderate difficulty
        for concept in weak[:4]:
            relevant = self.brain.search(concept, top_k=2)
            if relevant:
                chunk = relevant[0]
                # Fill-blank from key sentence
                if chunk.key_terms:
                    term = chunk.key_terms[0]
                    if term.lower() in chunk.text.lower():
                        blanked = re.sub(re.escape(term), "________", chunk.text[:100], count=1, flags=re.IGNORECASE)
                        questions.append({
                            "type": "fill_blank",
                            "question": blanked,
                            "correct": term,
                            "difficulty": "medium",
                            "concept": concept,
                        })

        # PRIORITY 3: Strong concepts — hard questions
        # Multi-hop: "If X stops, what happens to Y?"
        all_rels = []
        for chunk in chunks:
            for subj, rel, obj in chunk.relationships:
                if rel in ("causes", "enables", "depends_on"):
                    all_rels.append((subj, rel, obj, chunk.source))

        for subj, rel, obj, src in all_rels[:3]:
            if tracker.get_strength(subj) > 0.5:  # only if user knows the base
                questions.append({
                    "type": "consequence",
                    "question": f"What would happen if {subj} stopped/disappeared?",
                    "correct": f"It would affect: {obj}",
                    "difficulty": "hard",
                    "concept": subj,
                })

        # FILL remaining with mixed
        remaining = num_questions - len(questions)
        if remaining > 0:
            standard = self.generate_quiz(num_questions=remaining)
            for q in standard:
                q["difficulty"] = "standard"
            questions.extend(standard)

        return questions[:num_questions]

    # ──────────────────────────────────────────────────────────────
    # EXAM GENERATOR — full mock exam in specific format
    # ──────────────────────────────────────────────────────────────

    def generate_exam(self, style: str = "standard", duration_min: int = 60) -> Dict:
        """Generate a full mock exam from sources.
        
        Styles: standard, multiple_choice, short_answer, mixed
        """
        chunks = list(self.brain.chunks.values())
        if not chunks:
            return {"error": "No material ingested"}

        # Calculate questions based on duration
        # Assume: MCQ=1min, short=2min, computation=3min
        if style == "multiple_choice":
            num_q = duration_min
            questions = self.generate_quiz(num_questions=num_q)
            questions = [q for q in questions if q["type"] in ("mcq", "true_false")]
        elif style == "short_answer":
            num_q = duration_min // 2
            questions = []
            for chunk in chunks[:num_q]:
                if chunk.relationships:
                    subj, rel, obj = chunk.relationships[0]
                    questions.append({
                        "type": "short_answer",
                        "question": f"Explain: {subj}",
                        "model_answer": obj[:100],
                        "marks": 3,
                        "source": chunk.source,
                    })
        else:  # mixed
            num_mcq = duration_min // 3
            num_short = duration_min // 6
            mcq = self.generate_quiz(num_questions=num_mcq)
            short = []
            for chunk in chunks[:num_short]:
                if chunk.key_terms:
                    short.append({
                        "type": "short_answer",
                        "question": f"Define or explain: {chunk.key_terms[0]}",
                        "model_answer": chunk.text[:80],
                        "marks": 5,
                    })
            questions = mcq + short

        # Structure as exam
        total_marks = sum(q.get("marks", 1) for q in questions)
        return {
            "title": f"Mock Exam ({style}, {duration_min} min)",
            "duration": duration_min,
            "total_marks": total_marks,
            "num_questions": len(questions),
            "questions": questions,
            "topics_covered": list(set(c.topic for c in chunks if c.topic)),
        }
