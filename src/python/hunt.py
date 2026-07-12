#!/usr/bin/env python3
"""
HUNT Mode — Cross-validated deep research.
Queries 4 sources in parallel, compares answers, flags disagreements,
scores reliability, presents VERIFIED consensus.
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from web_search import search_wikipedia, search_duckduckgo, search_wikidata, search_wikipedia_search
from web_search import extract_facts, extract_triples, _clean_query
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class HuntEngine:
    """Multi-source cross-validated research."""

    def hunt(self, query: str) -> Dict:
        """Deep research with cross-validation."""
        clean = _clean_query(query)
        if not clean:
            return {'status': 'empty_query'}

        # Phase 1: Parallel multi-source search
        sources = self._gather_sources(clean)
        if not sources:
            return {'status': 'no_results', 'query': clean}

        # Phase 2: Extract facts from each source
        all_facts = {}
        for source in sources:
            facts = extract_facts(source['text'], clean)
            for fact in facts:
                key = fact.get('fact', '')[:80].lower()
                if key not in all_facts:
                    all_facts[key] = {'text': fact.get('fact', ''), 'sources': [], 'confidence': 0}
                all_facts[key]['sources'].append(source['source'])
                all_facts[key]['confidence'] += 0.25  # Each source adds 0.25

        # Phase 3: Cross-validate (facts confirmed by 2+ sources = high confidence)
        verified = []
        single_source = []
        conflicts = []

        for key, data in all_facts.items():
            data['confidence'] = min(0.99, data['confidence'])
            if len(data['sources']) >= 2:
                verified.append(data)
            else:
                single_source.append(data)

        # Phase 4: Check for conflicts (different sources say different things)
        # Simple: if two facts about same subject contradict
        fact_texts = [f['text'].lower() for f in verified + single_source]
        for i in range(len(fact_texts)):
            for j in range(i + 1, len(fact_texts)):
                if self._are_contradictory(fact_texts[i], fact_texts[j]):
                    conflicts.append({
                        'fact_a': fact_texts[i],
                        'fact_b': fact_texts[j],
                        'resolution': 'Sources disagree on this point.'
                    })

        # Phase 5: Assemble result
        return {
            'status': 'complete',
            'query': clean,
            'sources_queried': len(sources),
            'sources_responded': [s['source'] for s in sources],
            'verified_facts': verified,  # 2+ sources agree
            'unverified_facts': single_source,  # Only 1 source
            'conflicts': conflicts,
            'total_facts': len(all_facts),
            'confidence': self._overall_confidence(verified, single_source, conflicts),
            'summary': self._build_summary(clean, verified, single_source, sources),
        }

    def _gather_sources(self, query: str) -> List[Dict]:
        """Query all sources in parallel."""
        sources = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {
                pool.submit(search_wikipedia, query): "Wikipedia",
                pool.submit(search_duckduckgo, query): "DuckDuckGo",
                pool.submit(search_wikidata, query): "Wikidata",
                pool.submit(search_wikipedia_search, query): "Wikipedia Search",
            }
            for future in as_completed(futures, timeout=15):
                try:
                    result = future.result()
                    if result and result.get('text') and len(result['text']) > 20:
                        result['source'] = result.get('source', futures[future])
                        sources.append(result)
                except:
                    pass
        return sources

    def _are_contradictory(self, fact_a: str, fact_b: str) -> bool:
        """Simple contradiction detection between two facts."""
        # "X is Y" vs "X is not Y"
        if ' not ' in fact_a and fact_a.replace(' not ', ' ') in fact_b:
            return True
        if ' not ' in fact_b and fact_b.replace(' not ', ' ') in fact_a:
            return True
        return False

    def _overall_confidence(self, verified, single, conflicts) -> float:
        """Calculate overall research confidence."""
        if not verified and not single:
            return 0.0
        v_score = len(verified) * 0.9
        s_score = len(single) * 0.5
        c_penalty = len(conflicts) * 0.3
        total = len(verified) + len(single)
        return min(0.99, max(0.1, (v_score + s_score - c_penalty) / max(1, total)))

    def _build_summary(self, query, verified, single, sources) -> str:
        """Build human-readable research summary."""
        parts = []
        parts.append(f"Research on '{query}' ({len(sources)} sources)")
        if verified:
            parts.append(f"\nVerified ({len(verified)} facts, 2+ sources agree):")
            for f in verified[:5]:
                src_str = ', '.join(f['sources'])
                parts.append(f"  • {f['text'][:100]} [{src_str}]")
        if single:
            parts.append(f"\nSingle-source ({len(single)} facts, unconfirmed):")
            for f in single[:3]:
                parts.append(f"  • {f['text'][:100]} [{f['sources'][0]}]")
        return '\n'.join(parts)

    def format_hunt(self, result: Dict) -> str:
        """Format hunt result for display."""
        if result['status'] != 'complete':
            return f"  Hunt: No results for '{result.get('query', '')}'"

        lines = []
        lines.append(f"\n  HUNT: {result['query']}")
        lines.append(f"  {'═' * 50}")
        lines.append(f"  Sources: {', '.join(result['sources_responded'])}")
        lines.append(f"  Confidence: {result['confidence']:.0%}")

        if result['verified_facts']:
            lines.append(f"\n  VERIFIED ({len(result['verified_facts'])} facts, multi-source consensus):")
            for f in result['verified_facts'][:5]:
                lines.append(f"    ✓ {f['text'][:90]}")
                lines.append(f"      Sources: {', '.join(f['sources'])}")

        if result['conflicts']:
            lines.append(f"\n  CONFLICTS ({len(result['conflicts'])} disagreements):")
            for c in result['conflicts'][:3]:
                lines.append(f"    ⚠ {c['resolution']}")

        if result['unverified_facts']:
            lines.append(f"\n  UNVERIFIED ({len(result['unverified_facts'])} single-source):")
            for f in result['unverified_facts'][:3]:
                lines.append(f"    ? {f['text'][:80]} [{f['sources'][0]}]")

        lines.append("")
        return '\n'.join(lines)


_hunt_engine = None

def get_hunt_engine() -> HuntEngine:
    global _hunt_engine
    if _hunt_engine is None:
        _hunt_engine = HuntEngine()
    return _hunt_engine


if __name__ == '__main__':
    engine = HuntEngine()
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "What is photosynthesis"
    print(f"Hunting: {query}")
    result = engine.hunt(query)
    print(engine.format_hunt(result))
