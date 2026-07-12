#!/usr/bin/env python3
"""
DEBATE Mode — Adversarial argumentation on contested topics.
Presents BOTH sides with evidence. Never picks a side on opinion questions.
Lets the user decide based on evidence, not AI's bias.
"""

import re
from typing import Dict, List, Optional


# Topics with known multiple valid positions
CONTESTED_TOPICS = {
    'nuclear energy': {
        'positions': ['beneficial', 'risky'],
        'for': ['zero carbon emissions in operation', 'highest energy density', 'France 70% nuclear with lowest carbon grid',
                'modern Gen IV designs have passive safety', 'reliable baseload power'],
        'against': ['Chernobyl and Fukushima catastrophic failures', 'waste radioactive for 10000+ years',
                    'weapons proliferation risk', 'decommissioning costs underestimated', 'high upfront capital cost'],
        'verdict': 'Genuinely contested. Scientific consensus slightly favors on climate grounds, but safety and waste concerns are legitimate.',
    },
    'artificial intelligence': {
        'positions': ['transformative good', 'existential risk'],
        'for': ['accelerates scientific discovery', 'democratizes access to knowledge', 'automates dangerous work',
                'assists medical diagnosis', 'increases productivity'],
        'against': ['job displacement at scale', 'concentration of power', 'surveillance capabilities',
                    'alignment problem unsolved', 'deepfakes and misinformation'],
        'verdict': 'Both positions have strong evidence. Risk depends on governance and alignment research pace.',
    },
    'social media': {
        'positions': ['empowering', 'harmful'],
        'for': ['connects communities globally', 'gives voice to marginalized', 'rapid information sharing',
                'small business growth', 'political organizing tool'],
        'against': ['mental health impact on youth', 'addiction by design', 'misinformation amplification',
                    'polarization of discourse', 'privacy erosion'],
        'verdict': 'Platform design matters more than the technology itself. Same tool, different outcomes depending on incentives.',
    },
    'remote work': {
        'positions': ['superior', 'inferior to office'],
        'for': ['eliminates commute time', 'better work-life balance', 'access to global talent',
                'reduced office costs', 'higher reported satisfaction'],
        'against': ['reduced collaboration', 'harder to build culture', 'blurred work-life boundaries',
                    'isolation and loneliness', 'harder to mentor juniors'],
        'verdict': 'Depends heavily on role type, personality, and company culture. Hybrid appears optimal for many.',
    },
    'veganism': {
        'positions': ['ethical imperative', 'personal choice'],
        'for': ['reduces animal suffering', 'lower carbon footprint per calorie', 'health benefits documented',
                'more efficient land use', 'reduces pandemic risk from factory farming'],
        'against': ['nutritional challenges (B12, iron, protein)', 'cultural and economic barriers',
                    'not accessible everywhere', 'personal autonomy over diet', 'some ecosystems require grazing'],
        'verdict': 'Strong environmental and ethical arguments exist. Practical implementation varies by context.',
    },
    'capitalism': {
        'positions': ['best system available', 'fundamentally flawed'],
        'for': ['lifted billions from poverty', 'drives innovation', 'allocates resources efficiently',
                'personal freedom of enterprise', 'historical GDP growth'],
        'against': ['wealth inequality growing', 'climate externalities ignored', 'boom-bust cycles',
                    'exploitation of labor', 'short-term thinking over long-term sustainability'],
        'verdict': 'Most economists favor regulated market economies. Pure forms of either extreme have failed historically.',
    },
}

# Detection keywords for controversial/opinion topics
OPINION_SIGNALS = [
    'good or bad', 'should we', 'is it right', 'is it wrong',
    'pros and cons', 'advantages and disadvantages', 'debate',
    'controversial', 'both sides', 'what do you think',
    'is it better', 'is it worse', 'ethical', 'moral',
]


class DebateEngine:
    """Presents both sides of contested questions with evidence."""

    def is_debate_topic(self, question: str) -> bool:
        """Detect if question is opinion/contested."""
        q_lower = question.lower()
        # Check explicit signals
        if any(signal in q_lower for signal in OPINION_SIGNALS):
            return True
        # Check known topics
        for topic in CONTESTED_TOPICS:
            if topic in q_lower:
                return True
        return False

    def find_topic(self, question: str) -> Optional[str]:
        """Find which known topic matches."""
        q_lower = question.lower()
        for topic in CONTESTED_TOPICS:
            if topic in q_lower or any(w in q_lower for w in topic.split()):
                return topic
        return None

    def debate(self, question: str, knowledge_func=None) -> Optional[Dict]:
        """Generate a balanced debate on the topic."""
        topic_key = self.find_topic(question)

        if topic_key and topic_key in CONTESTED_TOPICS:
            return self._debate_from_known(topic_key)

        # Unknown topic — generate generic balanced response
        return self._debate_generic(question, knowledge_func)

    def _debate_from_known(self, topic_key: str) -> Dict:
        """Generate debate from known topic database."""
        topic = CONTESTED_TOPICS[topic_key]
        return {
            'topic': topic_key,
            'position_a': {
                'label': topic['positions'][0],
                'evidence': topic['for'],
                'strength': len(topic['for']),
            },
            'position_b': {
                'label': topic['positions'][1],
                'evidence': topic['against'],
                'strength': len(topic['against']),
            },
            'verdict': topic['verdict'],
            'recommendation': 'This is genuinely contested. I present evidence for both sides — you decide.',
        }

    def _debate_generic(self, question: str, knowledge_func=None) -> Dict:
        """Generate debate for unknown topic using general reasoning."""
        return {
            'topic': question,
            'position_a': {
                'label': 'In favor',
                'evidence': ['Arguments would depend on the specific context and evidence available.'],
                'strength': 0,
            },
            'position_b': {
                'label': 'Against',
                'evidence': ['Counter-arguments would depend on the specific context and evidence available.'],
                'strength': 0,
            },
            'verdict': 'I need more context to present both sides fairly. Could you be more specific?',
            'recommendation': 'Try asking about a specific aspect of this topic.',
        }

    def format_debate(self, debate_result: Dict) -> str:
        """Format debate result for display."""
        r = debate_result
        lines = []
        lines.append(f"\n  DEBATE: {r['topic']}")
        lines.append(f"  {'═' * 50}")

        lines.append(f"\n  POSITION A: {r['position_a']['label'].upper()}")
        for e in r['position_a']['evidence'][:5]:
            lines.append(f"    • {e}")

        lines.append(f"\n  POSITION B: {r['position_b']['label'].upper()}")
        for e in r['position_b']['evidence'][:5]:
            lines.append(f"    • {e}")

        lines.append(f"\n  VERDICT: {r['verdict']}")
        lines.append(f"  {r['recommendation']}")
        lines.append("")

        return '\n'.join(lines)


# Singleton
_debate_engine = None

def get_debate_engine() -> DebateEngine:
    global _debate_engine
    if _debate_engine is None:
        _debate_engine = DebateEngine()
    return _debate_engine


if __name__ == '__main__':
    import sys
    engine = DebateEngine()
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "Is nuclear energy good or bad?"
    print(f"Query: {query}")
    print(f"Is debate topic: {engine.is_debate_topic(query)}")
    result = engine.debate(query)
    if result:
        print(engine.format_debate(result))
