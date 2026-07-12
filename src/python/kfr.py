#!/usr/bin/env python3
"""
KFR — Knowledge Fusion Reactor
5 fuel rods for growing knowledge from 7K to millions:
  Rod A: Self-inference (transitive closure, inverses)
  Rod B: Wikidata structured import
  Rod C: LLM distillation (triple-validated)
  Rod D: User teaching (already built in C engine)
  Rod E: Cross-fact arithmetic synthesis

Target: 7,834 → 100K (day 1) → 500K (day 7) → 2M (day 30)
"""

import os, json, time, hashlib, re, subprocess
from typing import Dict, List, Tuple, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
USER_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data')
AI_BIN = os.path.join(os.path.dirname(__file__), '..', '..', 'ai')


class KnowledgeFusionReactor:
    """Grow knowledge continuously from multiple sources."""

    def __init__(self, output_dir=None):
        self.output_dir = output_dir or DATA_DIR
        self.stats = {'imported': 0, 'rejected': 0, 'derived': 0, 'conflicts': 0}
        self.seen_hashes = set()
        os.makedirs(self.output_dir, exist_ok=True)

    def _fact_hash(self, subj: str, rel: str, obj: str) -> str:
        return hashlib.md5(f"{subj.lower()}|{rel.lower()}|{obj.lower()}".encode()).hexdigest()[:12]

    def _is_duplicate(self, subj: str, rel: str, obj: str) -> bool:
        h = self._fact_hash(subj, rel, obj)
        if h in self.seen_hashes:
            return True
        self.seen_hashes.add(h)
        return False

    # ═══════════════════════════════════════════════════════════════
    # ROD A: Self-Inference (transitive closure + inverses)
    # ═══════════════════════════════════════════════════════════════

    INVERSE_RELATIONS = {
        'capital_of': 'has_capital',
        'parent_of': 'child_of',
        'part_of': 'has_part',
        'created_by': 'created',
        'located_in': 'contains',
        'member_of': 'has_member',
        'owned_by': 'owns',
        'borders': 'borders',
        'causes': 'caused_by',
        'invented_by': 'invented',
        'written_by': 'wrote',
        'discovered_by': 'discovered',
        'employed_by': 'employs',
    }

    TRANSITIVE_RELATIONS = {'located_in', 'part_of', 'is_a', 'subclass_of', 'contained_in'}

    def rod_a_self_inference(self, facts: List[Dict]) -> List[Dict]:
        """Generate new facts via inverse relations and transitive closure."""
        derived = []

        # Pass 1: Inverse relations
        for fact in facts:
            rel = fact.get('relation', '')
            if rel in self.INVERSE_RELATIONS:
                inv_rel = self.INVERSE_RELATIONS[rel]
                new_fact = {
                    'subject': fact['object'],
                    'relation': inv_rel,
                    'object': fact['subject'],
                    'confidence': round(fact.get('confidence', 0.9) * 0.95, 3),
                    'source': 'self_inference_inverse',
                }
                if not self._is_duplicate(new_fact['subject'], new_fact['relation'], new_fact['object']):
                    derived.append(new_fact)

        # Pass 2: Transitive closure (1 hop)
        by_subject = {}
        for fact in facts:
            by_subject.setdefault(fact.get('subject', ''), []).append(fact)

        for fact in facts:
            rel = fact.get('relation', '')
            if rel in self.TRANSITIVE_RELATIONS:
                # A rel B, B rel C → A rel C
                obj = fact.get('object', '')
                if obj in by_subject:
                    for next_fact in by_subject[obj]:
                        if next_fact.get('relation') == rel:
                            new_fact = {
                                'subject': fact['subject'],
                                'relation': rel,
                                'object': next_fact['object'],
                                'confidence': round(fact.get('confidence', 0.9) * next_fact.get('confidence', 0.9) * 0.9, 3),
                                'source': 'self_inference_transitive',
                            }
                            if not self._is_duplicate(new_fact['subject'], new_fact['relation'], new_fact['object']):
                                derived.append(new_fact)

        self.stats['derived'] += len(derived)
        return derived

    # ═══════════════════════════════════════════════════════════════
    # ROD B: Wikidata Structured Import
    # ═══════════════════════════════════════════════════════════════

    WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

    WIKIDATA_QUERIES = {
        'countries': """
            SELECT ?country ?countryLabel ?capital ?capitalLabel ?population WHERE {
              ?country wdt:P31 wd:Q6256.
              OPTIONAL { ?country wdt:P36 ?capital. }
              OPTIONAL { ?country wdt:P1082 ?population. }
              SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
            } LIMIT 300
        """,
        'elements': """
            SELECT ?element ?elementLabel ?symbol ?atomicNumber WHERE {
              ?element wdt:P31 wd:Q11344.
              ?element wdt:P246 ?symbol.
              ?element wdt:P1086 ?atomicNumber.
              SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
            } LIMIT 200
        """,
        'planets': """
            SELECT ?planet ?planetLabel ?mass ?radius WHERE {
              ?planet wdt:P31 wd:Q634.
              OPTIONAL { ?planet wdt:P2067 ?mass. }
              OPTIONAL { ?planet wdt:P2120 ?radius. }
              SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
            } LIMIT 20
        """,
        'programming_languages': """
            SELECT ?lang ?langLabel ?designer ?designerLabel ?year WHERE {
              ?lang wdt:P31 wd:Q9143.
              OPTIONAL { ?lang wdt:P287 ?designer. }
              OPTIONAL { ?lang wdt:P571 ?year. }
              SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
            } LIMIT 200
        """,
    }

    def rod_b_wikidata_import(self, category: str = 'countries') -> List[Dict]:
        """Import structured facts from Wikidata SPARQL endpoint."""
        try:
            import urllib.request, urllib.parse
            query = self.WIKIDATA_QUERIES.get(category, '')
            if not query:
                return []

            url = f"{self.WIKIDATA_SPARQL}?query={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'Axima/3.0'})

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())

            facts = []
            for row in data.get('results', {}).get('bindings', []):
                facts.extend(self._parse_wikidata_row(row, category))

            self.stats['imported'] += len(facts)
            return facts

        except Exception as e:
            return []

    def _parse_wikidata_row(self, row: Dict, category: str) -> List[Dict]:
        """Convert a Wikidata SPARQL row to triples."""
        facts = []

        if category == 'countries':
            country = row.get('countryLabel', {}).get('value', '')
            capital = row.get('capitalLabel', {}).get('value', '')
            pop = row.get('population', {}).get('value', '')
            if country and capital:
                facts.append({'subject': country.lower(), 'relation': 'capital', 'object': capital.lower(), 'confidence': 0.99, 'source': 'wikidata'})
            if country and pop:
                facts.append({'subject': country.lower(), 'relation': 'population', 'object': pop, 'confidence': 0.95, 'source': 'wikidata'})

        elif category == 'elements':
            elem = row.get('elementLabel', {}).get('value', '')
            symbol = row.get('symbol', {}).get('value', '')
            number = row.get('atomicNumber', {}).get('value', '')
            if elem and symbol:
                facts.append({'subject': elem.lower(), 'relation': 'symbol', 'object': symbol, 'confidence': 0.99, 'source': 'wikidata'})
            if elem and number:
                facts.append({'subject': elem.lower(), 'relation': 'atomic_number', 'object': number, 'confidence': 0.99, 'source': 'wikidata'})

        elif category == 'programming_languages':
            lang = row.get('langLabel', {}).get('value', '')
            designer = row.get('designerLabel', {}).get('value', '')
            year = row.get('year', {}).get('value', '')
            if lang and designer:
                facts.append({'subject': lang.lower(), 'relation': 'designed_by', 'object': designer.lower(), 'confidence': 0.95, 'source': 'wikidata'})
            if lang and year:
                facts.append({'subject': lang.lower(), 'relation': 'created_year', 'object': year[:4], 'confidence': 0.95, 'source': 'wikidata'})

        return facts

    # ═══════════════════════════════════════════════════════════════
    # ROD C: LLM Distillation (triple-validated)
    # ═══════════════════════════════════════════════════════════════

    def rod_c_llm_distillation(self, concepts: List[str], ask_func=None) -> List[Dict]:
        """
        Extract structured knowledge from an LLM.
        ask_func(prompt) -> str response. If None, returns templates only.
        Triple validation: ask 3 different ways, keep only consistent answers.
        """
        if ask_func is None:
            return []

        facts = []
        for concept in concepts:
            # Ask 3 different ways
            prompts = [
                f"List 5 factual properties of {concept}. Format: property: value",
                f"What are the key attributes of {concept}? List as 'attribute = value'",
                f"Give me 5 true facts about {concept} in 'fact: answer' format",
            ]

            responses = []
            for p in prompts:
                try:
                    resp = ask_func(p)
                    responses.append(self._parse_llm_response(concept, resp))
                except:
                    responses.append({})

            # Triple validation: keep only facts that appear in 2+ responses
            all_facts = {}
            for resp_facts in responses:
                for key, val in resp_facts.items():
                    all_facts.setdefault(key, []).append(val)

            for key, values in all_facts.items():
                if len(values) >= 2:
                    # Use most common value
                    most_common = max(set(values), key=values.count)
                    facts.append({
                        'subject': concept.lower(),
                        'relation': key.lower(),
                        'object': most_common.lower(),
                        'confidence': 0.85,
                        'source': 'llm_distillation_validated',
                    })

        self.stats['imported'] += len(facts)
        return facts

    def _parse_llm_response(self, concept: str, response: str) -> Dict:
        """Parse LLM response into key-value pairs."""
        result = {}
        if not response:
            return result
        for line in response.split('\n'):
            line = line.strip().lstrip('0123456789.-) ')
            for sep in [':', '=', ' is ', ' are ']:
                if sep in line:
                    parts = line.split(sep, 1)
                    if len(parts) == 2 and len(parts[0]) < 50 and len(parts[1]) < 200:
                        key = re.sub(r'[^a-z0-9_]', '_', parts[0].strip().lower())
                        val = parts[1].strip().rstrip('.')
                        if key and val:
                            result[key] = val
                    break
        return result

    # ═══════════════════════════════════════════════════════════════
    # ROD E: Cross-fact Arithmetic Synthesis
    # ═══════════════════════════════════════════════════════════════

    def rod_e_arithmetic_synthesis(self, facts: List[Dict]) -> List[Dict]:
        """Derive new facts through arithmetic on existing numeric facts."""
        derived = []
        numeric_facts = {}

        # Collect numeric facts by subject
        for fact in facts:
            try:
                val = float(re.sub(r'[^\d.\-]', '', str(fact.get('object', ''))))
                key = (fact['subject'], fact['relation'])
                numeric_facts[key] = val
            except (ValueError, TypeError):
                continue

        # Find pairs for the same subject → compute ratios, sums, differences
        by_subject = {}
        for (subj, rel), val in numeric_facts.items():
            by_subject.setdefault(subj, []).append((rel, val))

        for subj, rels in by_subject.items():
            if len(rels) >= 2:
                # For birthdate + deathdate → lifespan
                birth = next((v for r, v in rels if 'birth' in r or 'born' in r), None)
                death = next((v for r, v in rels if 'death' in r or 'died' in r), None)
                if birth and death and death > birth:
                    lifespan = int(death - birth)
                    new_fact = {
                        'subject': subj,
                        'relation': 'lifespan_years',
                        'object': str(lifespan),
                        'confidence': 0.95,
                        'source': 'arithmetic_synthesis',
                    }
                    if not self._is_duplicate(subj, 'lifespan_years', str(lifespan)):
                        derived.append(new_fact)

        # Cross-subject comparison (find superlatives)
        by_relation = {}
        for (subj, rel), val in numeric_facts.items():
            by_relation.setdefault(rel, []).append((subj, val))

        for rel, entries in by_relation.items():
            if len(entries) >= 3:
                sorted_entries = sorted(entries, key=lambda x: x[1], reverse=True)
                # Record the max
                max_subj, max_val = sorted_entries[0]
                new_fact = {
                    'subject': max_subj,
                    'relation': f'highest_{rel}',
                    'object': f'{max_val} (rank 1 of {len(entries)})',
                    'confidence': 0.90,
                    'source': 'arithmetic_synthesis',
                }
                if not self._is_duplicate(max_subj, f'highest_{rel}', str(max_val)):
                    derived.append(new_fact)

        self.stats['derived'] += len(derived)
        return derived

    # ═══════════════════════════════════════════════════════════════
    # REACTOR CONTROL
    # ═══════════════════════════════════════════════════════════════

    def run_all_rods(self, existing_facts: List[Dict], ask_func=None) -> List[Dict]:
        """Run all fuel rods and return all new facts."""
        all_new = []

        # Rod A: Self-inference
        all_new.extend(self.rod_a_self_inference(existing_facts))

        # Rod B: Wikidata (if internet available)
        for category in self.WIKIDATA_QUERIES:
            all_new.extend(self.rod_b_wikidata_import(category))

        # Rod C: LLM distillation (if function provided)
        if ask_func:
            # Extract concepts from existing facts for expansion
            concepts = list(set(f.get('subject', '') for f in existing_facts[:100]))[:20]
            all_new.extend(self.rod_c_llm_distillation(concepts, ask_func))

        # Rod E: Arithmetic synthesis
        all_new.extend(self.rod_e_arithmetic_synthesis(existing_facts + all_new))

        return all_new

    def export_for_c_engine(self, facts: List[Dict], output_path: str = None):
        """Export facts in format consumable by C engine's learn module."""
        path = output_path or os.path.join(self.output_dir, 'kfr_import.txt')
        with open(path, 'w') as f:
            for fact in facts:
                # Format: subject|relation|object|confidence
                line = f"{fact['subject']}|{fact['relation']}|{fact['object']}|{int(fact.get('confidence', 0.8) * 100)}\n"
                f.write(line)
        return path

    def get_stats(self) -> Dict:
        return {**self.stats, 'total_new': self.stats['imported'] + self.stats['derived']}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    reactor = KnowledgeFusionReactor()

    if len(sys.argv) > 1 and sys.argv[1] == 'wikidata':
        category = sys.argv[2] if len(sys.argv) > 2 else 'countries'
        facts = reactor.rod_b_wikidata_import(category)
        print(f"Imported {len(facts)} facts from Wikidata ({category})")
        if facts:
            path = reactor.export_for_c_engine(facts)
            print(f"Exported to: {path}")
    else:
        print("Usage: python kfr.py wikidata [countries|elements|planets|programming_languages]")
        print("       Imports structured knowledge from Wikidata into Axima.")
