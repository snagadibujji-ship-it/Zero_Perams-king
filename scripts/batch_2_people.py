#!/usr/bin/env python3
"""
Batch 2: Famous People — 500K facts from Wikidata
Scientists, authors, musicians, leaders, athletes, inventors.
"""

import urllib.request
import urllib.parse
import json
import time
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'batch_2_people.txt')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SPARQL_URL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "Axima/3.0 Knowledge Builder", "Accept": "application/json"}


def sparql_query(query, retries=3):
    for attempt in range(retries):
        try:
            url = f"{SPARQL_URL}?query={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                print(f"  FAILED: {e}")
                return None


def write_triples(triples, f):
    for subj, rel, obj, conf in triples:
        if subj and rel and obj and len(subj) > 1 and len(obj) > 0:
            f.write(f"{subj.lower()}|{rel}|{obj.lower()}|{conf}\n")


def query_people(f, category_qid, category_name, limit=5000):
    """Generic query for a category of notable people."""
    print(f"  Querying {category_name} (limit {limit})...")
    q = f"""
    SELECT ?personLabel ?birthDate ?deathDate ?birthPlaceLabel ?citizenshipLabel ?occupationLabel ?notableWorkLabel WHERE {{
      ?person wdt:P31 wd:Q5.
      ?person wdt:P106 wd:{category_qid}.
      OPTIONAL {{ ?person wdt:P569 ?birthDate. }}
      OPTIONAL {{ ?person wdt:P570 ?deathDate. }}
      OPTIONAL {{ ?person wdt:P19 ?birthPlace. }}
      OPTIONAL {{ ?person wdt:P27 ?citizenship. }}
      OPTIONAL {{ ?person wdt:P106 ?occupation. }}
      OPTIONAL {{ ?person wdt:P800 ?notableWork. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} LIMIT {limit}
    """
    data = sparql_query(q)
    count = 0
    if data:
        for row in data.get('results', {}).get('bindings', []):
            person = row.get('personLabel', {}).get('value', '')
            if not person or person.startswith('Q') or len(person) < 3:
                continue
            triples = [(person, 'is_a', category_name, 95)]

            birth = row.get('birthDate', {}).get('value', '')
            if birth and len(birth) >= 4:
                triples.append((person, 'born_year', birth[:4], 95))

            death = row.get('deathDate', {}).get('value', '')
            if death and len(death) >= 4:
                triples.append((person, 'died_year', death[:4], 95))

            place = row.get('birthPlaceLabel', {}).get('value', '')
            if place and not place.startswith('Q'):
                triples.append((person, 'born_in', place, 90))

            citizen = row.get('citizenshipLabel', {}).get('value', '')
            if citizen and not citizen.startswith('Q'):
                triples.append((person, 'nationality', citizen, 90))

            work = row.get('notableWorkLabel', {}).get('value', '')
            if work and not work.startswith('Q'):
                triples.append((person, 'known_for', work, 85))

            write_triples(triples, f)
            count += len(triples)
    time.sleep(3)
    return count


def run():
    facts_total = 0
    f = open(OUTPUT_FILE, 'w')

    # Categories: (Wikidata QID for occupation, label, limit)
    categories = [
        ('Q901', 'scientist', 10000),
        ('Q36180', 'writer', 8000),
        ('Q639669', 'musician', 8000),
        ('Q82955', 'politician', 8000),
        ('Q2066131', 'athlete', 8000),
        ('Q205375', 'inventor', 5000),
        ('Q3455803', 'director', 5000),
        ('Q33999', 'actor', 8000),
        ('Q4964182', 'philosopher', 3000),
        ('Q169470', 'physicist', 5000),
        ('Q593644', 'chemist', 3000),
        ('Q864503', 'biologist', 3000),
        ('Q11774202', 'mathematician', 3000),
        ('Q15981151', 'artist', 5000),
        ('Q3387717', 'military_leader', 3000),
    ]

    for qid, name, limit in categories:
        count = query_people(f, qid, name, limit)
        facts_total += count
        print(f"    → {count} facts")

    f.close()
    print(f"\n  Batch 2 complete: {facts_total} facts → {OUTPUT_FILE}")
    return facts_total


if __name__ == '__main__':
    print("Batch 2: Famous People")
    run()
