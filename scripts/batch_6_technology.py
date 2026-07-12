#!/usr/bin/env python3
"""
Batch 6: Technology — Programming languages, companies, inventions (200K facts)
"""
import urllib.request, urllib.parse, json, time, os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'batch_6_technology.txt')
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
        if subj and obj and len(subj)>1:
            f.write(f"{subj.lower()}|{rel}|{obj.lower()}|{conf}\n")

def run():
    facts = 0
    f = open(OUTPUT_FILE, 'w')

    # Programming Languages
    print("  Programming languages...")
    q = """
    SELECT ?langLabel ?designerLabel ?year ?paradigmLabel WHERE {
      ?lang wdt:P31 wd:Q9143.
      OPTIONAL { ?lang wdt:P287 ?designer. }
      OPTIONAL { ?lang wdt:P571 ?year. }
      OPTIONAL { ?lang wdt:P3966 ?paradigm. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 500
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            lang = row.get('langLabel',{}).get('value','')
            if not lang or lang.startswith('Q'): continue
            triples = [(lang, 'is_a', 'programming language', 99)]
            d = row.get('designerLabel',{}).get('value','')
            if d and not d.startswith('Q'): triples.append((lang, 'designed_by', d, 95))
            y = row.get('year',{}).get('value','')
            if y: triples.append((lang, 'created_year', y[:4], 95))
            p = row.get('paradigmLabel',{}).get('value','')
            if p and not p.startswith('Q'): triples.append((lang, 'paradigm', p, 90))
            write_triples(triples, f)
            facts += len(triples)
    time.sleep(3)

    # Companies
    print("  Companies...")
    q = """
    SELECT ?companyLabel ?founderLabel ?year ?hqLabel ?industryLabel WHERE {
      ?company wdt:P31 wd:Q4830453.
      ?company wdt:P2139 ?revenue. FILTER(?revenue > 1000000000)
      OPTIONAL { ?company wdt:P112 ?founder. }
      OPTIONAL { ?company wdt:P571 ?year. }
      OPTIONAL { ?company wdt:P159 ?hq. }
      OPTIONAL { ?company wdt:P452 ?industry. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 5000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            company = row.get('companyLabel',{}).get('value','')
            if not company or company.startswith('Q'): continue
            triples = [(company, 'is_a', 'company', 95)]
            founder = row.get('founderLabel',{}).get('value','')
            if founder and not founder.startswith('Q'):
                triples.append((company, 'founded_by', founder, 90))
            y = row.get('year',{}).get('value','')
            if y: triples.append((company, 'founded_year', y[:4], 90))
            hq = row.get('hqLabel',{}).get('value','')
            if hq and not hq.startswith('Q'):
                triples.append((company, 'headquarters', hq, 90))
            ind = row.get('industryLabel',{}).get('value','')
            if ind and not ind.startswith('Q'):
                triples.append((company, 'industry', ind, 85))
            write_triples(triples, f)
            facts += len(triples)
    time.sleep(3)

    # Inventions
    print("  Inventions...")
    q = """
    SELECT ?inventionLabel ?inventorLabel ?year WHERE {
      ?invention wdt:P31 wd:Q39546.
      OPTIONAL { ?invention wdt:P61 ?inventor. }
      OPTIONAL { ?invention wdt:P575 ?year. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 5000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            inv = row.get('inventionLabel',{}).get('value','')
            if not inv or inv.startswith('Q'): continue
            triples = [(inv, 'is_a', 'invention', 90)]
            person = row.get('inventorLabel',{}).get('value','')
            if person and not person.startswith('Q'):
                triples.append((inv, 'invented_by', person, 90))
            y = row.get('year',{}).get('value','')
            if y: triples.append((inv, 'invented_year', y[:4], 85))
            write_triples(triples, f)
            facts += len(triples)

    f.close()
    print(f"\n  Batch 6 complete: {facts} facts → {OUTPUT_FILE}")
    return facts

if __name__ == '__main__':
    print("Batch 6: Technology")
    run()
