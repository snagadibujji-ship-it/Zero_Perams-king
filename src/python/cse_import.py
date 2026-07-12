#!/usr/bin/env python3
"""
CSE Import Pipeline — Convert raw data sources into CSE compressed format.

Sources → Normalize → Deduplicate → Sort → Export (pipe-delimited for cse_build)

Usage:
  python cse_import.py from-kfr           Import from KFR output
  python cse_import.py from-learned       Import from web_learned.txt
  python cse_import.py from-triples       Import from learned_triples.jsonl
  python cse_import.py stats              Show current CSE database stats
  python cse_import.py build              Build final .cse binary
"""

import os, sys, json, re, hashlib
from typing import Dict, List, Tuple, Set

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
USER_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data')
CSE_TRIPLES_FILE = os.path.join(DATA_DIR, 'cse_triples.txt')  # subject|relation|object|confidence
CSE_DB_FILE = os.path.join(DATA_DIR, 'axima.cse')


class CSEImporter:
    """Converts various data sources into CSE pipe-delimited format."""

    def __init__(self):
        self.seen_hashes: Set[str] = set()
        self.triples: List[Tuple[str, str, str, int]] = []
        self.stats = {'imported': 0, 'duplicates': 0, 'invalid': 0}

    def _normalize(self, text: str) -> str:
        """Normalize string for consistent storage."""
        text = text.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        text = text.rstrip('.,;:')
        return text[:127]  # CSE_MAX_STRING_LEN - 1

    def _hash_triple(self, subj: str, rel: str, obj: str) -> str:
        return hashlib.md5(f"{subj}|{rel}|{obj}".encode()).hexdigest()[:12]

    def _add_triple(self, subj: str, rel: str, obj: str, confidence: int = 80):
        """Add a triple if not duplicate."""
        subj = self._normalize(subj)
        rel = self._normalize(rel)
        obj = self._normalize(obj)

        if not subj or not rel or not obj:
            self.stats['invalid'] += 1
            return False
        if len(subj) < 2 or len(obj) < 1:
            self.stats['invalid'] += 1
            return False

        h = self._hash_triple(subj, rel, obj)
        if h in self.seen_hashes:
            self.stats['duplicates'] += 1
            return False
        self.seen_hashes.add(h)

        confidence = max(10, min(99, confidence))
        self.triples.append((subj, rel, obj, confidence))
        self.stats['imported'] += 1
        return True

    # ═══════════════════════════════════════════════════════════
    # SOURCE: KFR output (kfr_import.txt)
    # ═══════════════════════════════════════════════════════════

    def from_kfr(self, path: str = None):
        """Import from KFR pipe-delimited file."""
        path = path or os.path.join(DATA_DIR, 'kfr_import.txt')
        if not os.path.isfile(path):
            print(f"  KFR file not found: {path}")
            return 0

        count = 0
        with open(path) as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    subj, rel, obj = parts[0], parts[1], parts[2]
                    conf = int(parts[3]) if len(parts) > 3 else 80
                    if self._add_triple(subj, rel, obj, conf):
                        count += 1
        return count

    # ═══════════════════════════════════════════════════════════
    # SOURCE: learned_triples.jsonl
    # ═══════════════════════════════════════════════════════════

    def from_triples_jsonl(self, path: str = None):
        """Import from JSONL triples file."""
        path = path or os.path.join(USER_DIR, 'learned_triples.jsonl')
        if not os.path.isfile(path):
            return 0

        count = 0
        with open(path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    subj = entry.get('subject', '')
                    rel = entry.get('relation', '')
                    obj = entry.get('object', '')
                    conf = int(entry.get('confidence', 0.8) * 100)
                    if self._add_triple(subj, rel, obj, conf):
                        count += 1
                except: pass
        return count

    # ═══════════════════════════════════════════════════════════
    # SOURCE: web_learned.txt (text sentences → extract triples)
    # ═══════════════════════════════════════════════════════════

    EXTRACT_PATTERNS = [
        (r'^(.+?)\s+is\s+(?:a|an|the)\s+(.+)$', 'is_a'),
        (r'^(.+?)\s+is\s+located\s+in\s+(.+)$', 'located_in'),
        (r'^(.+?)\s+is\s+(?:the\s+)?capital\s+of\s+(.+)$', 'capital_of'),
        (r'^(.+?)\s+was\s+(?:born|created|founded)\s+in\s+(\d{4})$', 'born_year'),
        (r'^(.+?)\s+was\s+(?:invented|created|designed)\s+by\s+(.+)$', 'created_by'),
        (r'^(.+?)\s+is\s+made\s+(?:of|from)\s+(.+)$', 'made_of'),
        (r'^(.+?)\s+has\s+(?:a\s+)?population\s+of\s+(.+)$', 'population'),
        (r'^(.+?)\s+(?:borders|is\s+bordered\s+by)\s+(.+)$', 'borders'),
        (r'^(.+?)\s+is\s+known\s+for\s+(.+)$', 'known_for'),
    ]

    def from_learned_text(self, path: str = None):
        """Import from text file by extracting triples via patterns."""
        path = path or os.path.join(USER_DIR, 'web_learned.txt')
        if not os.path.isfile(path):
            return 0

        count = 0
        with open(path) as f:
            for line in f:
                line = line.strip()
                if len(line) < 10:
                    continue
                # Try each extraction pattern
                for pattern, relation in self.EXTRACT_PATTERNS:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        subj = match.group(1).strip()
                        obj = match.group(2).strip()
                        if self._add_triple(subj, relation, obj, 85):
                            count += 1
                        break
        return count

    # ═══════════════════════════════════════════════════════════
    # SOURCE: Seed knowledge (existing knowledge base)
    # ═══════════════════════════════════════════════════════════

    def from_seed_knowledge(self, path: str = None):
        """Import from seed_knowledge.txt (format: 'A dog is a mammal')."""
        path = path or os.path.join(DATA_DIR, 'seed_knowledge.txt')
        if not os.path.isfile(path):
            return 0

        count = 0
        with open(path) as f:
            for line in f:
                line = line.strip()
                # "A/An X is a/an Y" → (X, is_a, Y)
                match = re.match(r'^(?:A|An)\s+(.+?)\s+is\s+(?:a|an)\s+(.+)$', line, re.IGNORECASE)
                if match:
                    if self._add_triple(match.group(1), 'is_a', match.group(2), 95):
                        count += 1
                    continue
                # "X has Y" → (X, has_property, Y)
                match = re.match(r'^(.+?)\s+has\s+(.+)$', line, re.IGNORECASE)
                if match:
                    if self._add_triple(match.group(1), 'has_property', match.group(2), 90):
                        count += 1
        return count

    # ═══════════════════════════════════════════════════════════
    # EXPORT + BUILD
    # ═══════════════════════════════════════════════════════════

    def export(self, path: str = None):
        """Export all collected triples to pipe-delimited file for cse_build."""
        path = path or CSE_TRIPLES_FILE
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Sort by subject for clustering efficiency
        self.triples.sort(key=lambda t: t[0])

        with open(path, 'w') as f:
            for subj, rel, obj, conf in self.triples:
                f.write(f"{subj}|{rel}|{obj}|{conf}\n")

        return len(self.triples)

    def import_all(self) -> Dict:
        """Import from ALL available sources."""
        results = {}
        results['seed'] = self.from_seed_knowledge()
        results['kfr'] = self.from_kfr()
        results['triples'] = self.from_triples_jsonl()
        results['learned'] = self.from_learned_text()
        results['total'] = len(self.triples)
        results['stats'] = self.stats
        return results

    def estimate_cse_size(self) -> Dict:
        """Estimate final compressed database size."""
        n = len(self.triples)
        unique_strings = set()
        for subj, rel, obj, _ in self.triples:
            unique_strings.add(subj)
            unique_strings.add(obj)

        avg_str_len = sum(len(s) for s in unique_strings) / max(1, len(unique_strings))
        string_table_bytes = int(len(unique_strings) * avg_str_len * 0.7)  # Prefix compression
        facts_bytes = int(n * 3.5)  # With clustering
        total = string_table_bytes + facts_bytes

        return {
            'facts': n,
            'unique_strings': len(unique_strings),
            'string_table_mb': round(string_table_bytes / 1_000_000, 2),
            'facts_mb': round(facts_bytes / 1_000_000, 2),
            'total_mb': round(total / 1_000_000, 2),
            'derivable_answers': f"{n * 1000:,}",  # 1000x EIR amplification
        }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    importer = CSEImporter()

    if len(sys.argv) < 2:
        print("CSE Import Pipeline")
        print("  python cse_import.py all        Import from all sources + export")
        print("  python cse_import.py stats      Show estimated size")
        print("  python cse_import.py from-kfr   Import KFR output only")
        print("  python cse_import.py from-seed  Import seed knowledge only")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'all':
        print("Importing from all sources...")
        results = importer.import_all()
        for src, count in results.items():
            if src not in ('total', 'stats'):
                print(f"  {src}: {count} triples")
        n = importer.export()
        print(f"\nExported {n} triples to {CSE_TRIPLES_FILE}")
        est = importer.estimate_cse_size()
        print(f"Estimated CSE size: {est['total_mb']} MB")
        print(f"Derivable answers: {est['derivable_answers']}")

    elif cmd == 'stats':
        importer.import_all()
        est = importer.estimate_cse_size()
        print(f"Facts: {est['facts']}")
        print(f"Unique strings: {est['unique_strings']}")
        print(f"String table: {est['string_table_mb']} MB")
        print(f"Facts storage: {est['facts_mb']} MB")
        print(f"Total CSE: {est['total_mb']} MB")
        print(f"Derivable answers: {est['derivable_answers']}")

    elif cmd == 'from-kfr':
        n = importer.from_kfr()
        print(f"Imported {n} triples from KFR")
        importer.export()

    elif cmd == 'from-seed':
        n = importer.from_seed_knowledge()
        print(f"Imported {n} triples from seed knowledge")
        importer.export()

    else:
        print(f"Unknown command: {cmd}")
