#!/usr/bin/env python3
"""
Batch 4: Geography — Cities, rivers, mountains, oceans
"""
import urllib.request, urllib.parse, json, time, os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'batch_4_geography.txt')
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
            if attempt < retries - 1: time.sleep(5*(attempt+1))
            else: print(f"  FAILED: {e}"); return None

def write_triples(triples, f):
    for subj, rel, obj, conf in triples:
        if subj and obj and len(subj)>1:
            f.write(f"{subj.lower()}|{rel}|{obj.lower()}|{conf}\n")

def run():
    facts_total = 0
    f = open(OUTPUT_FILE, 'w')

    # Cities (top 5000 by population)
    print("  Cities...")
    q = """
    SELECT ?cityLabel ?countryLabel ?population WHERE {
      ?city wdt:P31/wdt:P279* wd:Q515.
      ?city wdt:P17 ?country.
      ?city wdt:P1082 ?population.
      FILTER(?population > 100000)
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } ORDER BY DESC(?population) LIMIT 5000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            city = row.get('cityLabel',{}).get('value','')
            country = row.get('countryLabel',{}).get('value','')
            pop = row.get('population',{}).get('value','')
            if not city or city.startswith('Q'): continue
            triples = [(city, 'is_a', 'city', 95)]
            if country and not country.startswith('Q'):
                triples.append((city, 'located_in', country, 95))
            if pop:
                triples.append((city, 'population', pop, 90))
            write_triples(triples, f)
            facts_total += len(triples)
    time.sleep(3)

    # Rivers
    print("  Rivers...")
    q = """
    SELECT ?riverLabel ?length ?countryLabel WHERE {
      ?river wdt:P31 wd:Q4022.
      OPTIONAL { ?river wdt:P2043 ?length. }
      OPTIONAL { ?river wdt:P17 ?country. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 3000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            river = row.get('riverLabel',{}).get('value','')
            if not river or river.startswith('Q'): continue
            triples = [(river, 'is_a', 'river', 95)]
            length = row.get('length',{}).get('value','')
            if length: triples.append((river, 'length_km', length, 90))
            country = row.get('countryLabel',{}).get('value','')
            if country and not country.startswith('Q'):
                triples.append((river, 'located_in', country, 90))
            write_triples(triples, f)
            facts_total += len(triples)
    time.sleep(3)

    # Mountains
    print("  Mountains...")
    q = """
    SELECT ?mountainLabel ?elevation ?rangeLabel ?countryLabel WHERE {
      ?mountain wdt:P31 wd:Q8502.
      OPTIONAL { ?mountain wdt:P2044 ?elevation. }
      OPTIONAL { ?mountain wdt:P4552 ?range. }
      OPTIONAL { ?mountain wdt:P17 ?country. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 3000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            mountain = row.get('mountainLabel',{}).get('value','')
            if not mountain or mountain.startswith('Q'): continue
            triples = [(mountain, 'is_a', 'mountain', 95)]
            elev = row.get('elevation',{}).get('value','')
            if elev: triples.append((mountain, 'elevation_m', elev, 95))
            rng = row.get('rangeLabel',{}).get('value','')
            if rng and not rng.startswith('Q'):
                triples.append((mountain, 'part_of', rng, 90))
            country = row.get('countryLabel',{}).get('value','')
            if country and not country.startswith('Q'):
                triples.append((mountain, 'located_in', country, 90))
            write_triples(triples, f)
            facts_total += len(triples)

    f.close()
    print(f"\n  Batch 4 complete: {facts_total} facts → {OUTPUT_FILE}")
    return facts_total

if __name__ == '__main__':
    print("Batch 4: Geography")
    run()
