#!/usr/bin/env python3
"""
Batch 3: Science — 200K facts from Wikidata
Chemical elements, planets, animals, diseases.
"""

import urllib.request, urllib.parse, json, time, os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'batch_3_science.txt')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SPARQL_URL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "Axima/3.0", "Accept": "application/json"}


def sparql_query(query, retries=3):
    for attempt in range(retries):
        try:
            url = f"{SPARQL_URL}?query={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < retries - 1: time.sleep(5 * (attempt + 1))
            else: print(f"  FAILED: {e}"); return None


def write_triples(triples, f):
    for subj, rel, obj, conf in triples:
        if subj and obj and len(subj) > 1:
            f.write(f"{subj.lower()}|{rel}|{obj.lower()}|{conf}\n")


def run():
    facts_total = 0
    f = open(OUTPUT_FILE, 'w')

    # ─── Chemical Elements ───
    print("  Elements...")
    q = """
    SELECT ?elementLabel ?symbol ?atomicNumber ?mass ?boilingPoint ?meltingPoint ?discovererLabel WHERE {
      ?element wdt:P31 wd:Q11344.
      OPTIONAL { ?element wdt:P246 ?symbol. }
      OPTIONAL { ?element wdt:P1086 ?atomicNumber. }
      OPTIONAL { ?element wdt:P2067 ?mass. }
      OPTIONAL { ?element wdt:P2102 ?boilingPoint. }
      OPTIONAL { ?element wdt:P2101 ?meltingPoint. }
      OPTIONAL { ?element wdt:P61 ?discoverer. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            elem = row.get('elementLabel', {}).get('value', '')
            if not elem or elem.startswith('Q'): continue
            triples = [(elem, 'is_a', 'chemical element', 99)]
            for key, rel in [('symbol','symbol'),('atomicNumber','atomic_number'),
                             ('mass','atomic_mass'),('boilingPoint','boiling_point'),
                             ('meltingPoint','melting_point')]:
                val = row.get(key, {}).get('value', '')
                if val: triples.append((elem, rel, val, 99))
            disc = row.get('discovererLabel', {}).get('value', '')
            if disc and not disc.startswith('Q'):
                triples.append((elem, 'discovered_by', disc, 90))
            write_triples(triples, f)
            facts_total += len(triples)
    time.sleep(2)

    # ─── Planets ───
    print("  Planets...")
    q = """
    SELECT ?planetLabel ?mass ?radius ?orbitalPeriod ?moons WHERE {
      ?planet wdt:P31 wd:Q634.
      OPTIONAL { ?planet wdt:P2067 ?mass. }
      OPTIONAL { ?planet wdt:P2120 ?radius. }
      OPTIONAL { ?planet wdt:P2146 ?orbitalPeriod. }
      OPTIONAL { ?planet wdt:P397 ?moons. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            planet = row.get('planetLabel', {}).get('value', '')
            if not planet or planet.startswith('Q'): continue
            triples = [(planet, 'is_a', 'planet', 99), (planet, 'located_in', 'solar system', 99)]
            for key, rel in [('mass','mass_kg'),('radius','radius_km'),('orbitalPeriod','orbital_period')]:
                val = row.get(key, {}).get('value', '')
                if val: triples.append((planet, rel, val, 95))
            write_triples(triples, f)
            facts_total += len(triples)
    time.sleep(2)

    # ─── Animals (mammals, birds, reptiles, fish) ───
    print("  Animals...")
    animal_classes = [
        ('Q7377', 'mammal', 3000),
        ('Q5113', 'bird', 3000),
        ('Q10811', 'reptile', 2000),
        ('Q152', 'fish', 2000),
        ('Q1390', 'insect', 2000),
    ]
    for qid, class_name, limit in animal_classes:
        print(f"    {class_name}...")
        q = f"""
        SELECT ?animalLabel ?habitatLabel ?dietLabel WHERE {{
          ?animal wdt:P31 wd:{qid}.
          OPTIONAL {{ ?animal wdt:P2974 ?habitat. }}
          OPTIONAL {{ ?animal wdt:P1034 ?diet. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT {limit}
        """
        data = sparql_query(q)
        if data:
            for row in data.get('results', {}).get('bindings', []):
                animal = row.get('animalLabel', {}).get('value', '')
                if not animal or animal.startswith('Q'): continue
                triples = [(animal, 'is_a', class_name, 95)]
                habitat = row.get('habitatLabel', {}).get('value', '')
                if habitat and not habitat.startswith('Q'):
                    triples.append((animal, 'habitat', habitat, 85))
                write_triples(triples, f)
                facts_total += len(triples)
        time.sleep(3)

    # ─── Diseases ───
    print("  Diseases...")
    q = """
    SELECT ?diseaseLabel ?causeLabel ?symptomLabel WHERE {
      ?disease wdt:P31 wd:Q112193867.
      OPTIONAL { ?disease wdt:P828 ?cause. }
      OPTIONAL { ?disease wdt:P780 ?symptom. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 5000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            disease = row.get('diseaseLabel', {}).get('value', '')
            if not disease or disease.startswith('Q'): continue
            triples = [(disease, 'is_a', 'disease', 95)]
            cause = row.get('causeLabel', {}).get('value', '')
            if cause and not cause.startswith('Q'):
                triples.append((disease, 'caused_by', cause, 85))
            symptom = row.get('symptomLabel', {}).get('value', '')
            if symptom and not symptom.startswith('Q'):
                triples.append((disease, 'has_symptom', symptom, 85))
            write_triples(triples, f)
            facts_total += len(triples)

    f.close()
    print(f"\n  Batch 3 complete: {facts_total} facts → {OUTPUT_FILE}")
    return facts_total


if __name__ == '__main__':
    print("Batch 3: Science")
    run()
