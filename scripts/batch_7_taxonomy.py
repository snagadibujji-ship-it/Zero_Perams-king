#!/usr/bin/env python3
"""
Batch 7: Taxonomy — is_a hierarchy chains (500K facts)
Species → genus → family → order → class
City → country → continent
Part_of relationships
"""
import urllib.request, urllib.parse, json, time, os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'batch_7_taxonomy.txt')
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
        except:
            if attempt < retries-1: time.sleep(5*(attempt+1))
            else: return None

def write_triples(triples, f):
    for subj, rel, obj, conf in triples:
        if subj and obj and len(subj)>1 and not subj.startswith('q') and not obj.startswith('q'):
            f.write(f"{subj.lower()}|{rel}|{obj.lower()}|{conf}\n")

def run():
    facts = 0
    f = open(OUTPUT_FILE, 'w')

    # Biological taxonomy (animal classes)
    print("  Biological taxonomy...")
    taxa = [
        ('Q7377', 'mammal', 'Q5113', 'bird'),
        ('Q10811', 'reptile', 'Q10908', 'amphibian'),
        ('Q152', 'fish', 'Q1390', 'insect'),
    ]
    for qid, name, _, _ in taxa:
        q = f"""
        SELECT ?speciesLabel ?familyLabel ?orderLabel WHERE {{
          ?species wdt:P31 wd:{qid}.
          OPTIONAL {{ ?species wdt:P171 ?family. }}
          OPTIONAL {{ ?family wdt:P171 ?order. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT 5000
        """
        data = sparql_query(q)
        if data:
            for row in data.get('results',{}).get('bindings',[]):
                species = row.get('speciesLabel',{}).get('value','')
                family = row.get('familyLabel',{}).get('value','')
                order = row.get('orderLabel',{}).get('value','')
                if species:
                    write_triples([(species, 'is_a', name, 95)], f)
                    facts += 1
                if species and family and not family.startswith('Q'):
                    write_triples([(species, 'family', family, 90)], f)
                    facts += 1
                if family and order and not family.startswith('Q') and not order.startswith('Q'):
                    write_triples([(family, 'order', order, 90)], f)
                    facts += 1
        time.sleep(3)

    # Geographic hierarchy
    print("  Geographic hierarchy...")
    q = """
    SELECT ?cityLabel ?stateLabel ?countryLabel WHERE {
      ?city wdt:P31/wdt:P279* wd:Q515.
      ?city wdt:P131 ?state.
      ?state wdt:P17 ?country.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 10000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            city = row.get('cityLabel',{}).get('value','')
            state = row.get('stateLabel',{}).get('value','')
            country = row.get('countryLabel',{}).get('value','')
            if city and state and not state.startswith('Q'):
                write_triples([(city, 'located_in', state, 90)], f)
                facts += 1
            if state and country and not state.startswith('Q') and not country.startswith('Q'):
                write_triples([(state, 'located_in', country, 90)], f)
                facts += 1

    f.close()
    print(f"\n  Batch 7 complete: {facts} facts → {OUTPUT_FILE}")
    return facts

if __name__ == '__main__':
    print("Batch 7: Taxonomy")
    run()
