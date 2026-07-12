#!/usr/bin/env python3
"""
Import ConceptNet — 500K common-sense facts (English only, high confidence)
Downloads ConceptNet assertions CSV, filters English, exports triples.
"""
import os, csv, gzip, time
import urllib.request

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'batch_8_conceptnet.txt')
DOWNLOAD_URL = "https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz"
DOWNLOAD_FILE = os.path.join(OUTPUT_DIR, 'conceptnet.csv.gz')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Relations to import (ConceptNet → our relation names)
RELATION_MAP = {
    '/r/IsA': 'is_a',
    '/r/HasA': 'has_part',
    '/r/PartOf': 'part_of',
    '/r/UsedFor': 'used_for',
    '/r/CapableOf': 'capable_of',
    '/r/Causes': 'causes',
    '/r/HasProperty': 'has_property',
    '/r/MadeOf': 'made_of',
    '/r/AtLocation': 'found_at',
    '/r/HasPrerequisite': 'requires',
    '/r/MotivatedByGoal': 'purpose',
    '/r/CreatedBy': 'created_by',
    '/r/DefinedAs': 'defined_as',
    '/r/SymbolOf': 'symbolizes',
}

MIN_WEIGHT = 1.0  # Only high-confidence facts


def download_conceptnet():
    """Download ConceptNet (2GB compressed)."""
    if os.path.isfile(DOWNLOAD_FILE):
        print(f"  Already downloaded: {DOWNLOAD_FILE}")
        return True
    print(f"  Downloading ConceptNet (~2GB)...")
    print(f"  URL: {DOWNLOAD_URL}")
    try:
        urllib.request.urlretrieve(DOWNLOAD_URL, DOWNLOAD_FILE)
        print(f"  Downloaded: {os.path.getsize(DOWNLOAD_FILE) / 1_000_000:.0f} MB")
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def extract_concept(uri):
    """Extract English concept name from ConceptNet URI."""
    # Format: /c/en/word_phrase
    if not uri.startswith('/c/en/'):
        return None
    name = uri[6:]  # Strip '/c/en/'
    # Remove suffix like /n/wn/... 
    if '/' in name:
        name = name.split('/')[0]
    return name.replace('_', ' ')


def run():
    if not download_conceptnet():
        print("  Cannot proceed without ConceptNet data.")
        print("  Alternative: download manually from")
        print(f"  {DOWNLOAD_URL}")
        return 0

    print("  Parsing ConceptNet (filtering English, weight > 1.0)...")
    facts = 0
    f = open(OUTPUT_FILE, 'w')

    with gzip.open(DOWNLOAD_FILE, 'rt', encoding='utf-8', errors='ignore') as gz:
        reader = csv.reader(gz, delimiter='\t')
        for row in reader:
            if len(row) < 5:
                continue

            relation = row[1]
            source = row[2]
            target = row[3]
            info = row[4] if len(row) > 4 else '{}'

            # Filter: only English
            if not source.startswith('/c/en/') or not target.startswith('/c/en/'):
                continue

            # Filter: only relations we want
            if relation not in RELATION_MAP:
                continue

            # Filter: weight > threshold
            try:
                import json as _json
                meta = _json.loads(info)
                weight = meta.get('weight', 0)
                if weight < MIN_WEIGHT:
                    continue
            except:
                continue

            subj = extract_concept(source)
            obj = extract_concept(target)
            rel = RELATION_MAP[relation]

            if subj and obj and len(subj) > 1 and len(obj) > 1:
                conf = min(95, int(50 + weight * 10))
                f.write(f"{subj}|{rel}|{obj}|{conf}\n")
                facts += 1

            if facts % 100000 == 0 and facts > 0:
                print(f"    {facts:,} facts extracted...")

    f.close()
    print(f"\n  ConceptNet complete: {facts:,} facts → {OUTPUT_FILE}")
    return facts


if __name__ == '__main__':
    print("Batch 8: ConceptNet Common Sense")
    run()
