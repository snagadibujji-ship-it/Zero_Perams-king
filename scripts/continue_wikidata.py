#!/usr/bin/env python3
"""Continue Wikidata import - remaining batches after timeout."""
import urllib.request, urllib.parse, json, time, os, sys

RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw')
OUTPUT = os.path.join(RAW_DIR, 'all_batches_throttled.txt')
SPARQL_URL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "Axima/3.0 Knowledge-Builder (bot; batch-import)",
           "Accept": "application/json"}
DELAY = 62
facts = 0
qnum = 0


def sparql(query):
    global qnum
    for attempt in range(3):
        try:
            url = f"{SPARQL_URL}?query={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=120)
            data = json.loads(resp.read().decode())
            qnum += 1
            print(f"  [Q{qnum}] OK, waiting {DELAY}s...", flush=True)
            time.sleep(DELAY)
            return data
        except Exception as e:
            print(f"  Attempt {attempt+1} fail: {e}", flush=True)
            time.sleep(DELAY * 2)
    return None

def val(row, key):
    v = row.get(key, {}).get('value', '')
    if v.startswith('http://www.wikidata.org/entity/'): return None
    return v.strip() if v and len(v) > 0 else None

def write(f, subj, rel, obj, conf=90):
    global facts
    if subj and obj and len(subj) > 1:
        s, o = subj.lower().strip(), obj.lower().strip()
        if not s.startswith('q') and not o.startswith('q'):
            f.write(f"{s}|{rel}|{o}|{conf}\n")
            facts += 1

if __name__ == '__main__':
    batch = sys.argv[1] if len(sys.argv) > 1 else 'people2'
    print(f"Running batch: {batch}", flush=True)
    f = open(OUTPUT, 'a')  # APPEND mode

    if batch == 'people2':
        # Remaining people categories
        cats = [('Q36180','writer',5000),('Q639669','musician',5000),
                ('Q82955','politician',5000),('Q2066131','athlete',5000),
                ('Q205375','inventor',3000),('Q33999','actor',5000)]
        for qid, name, limit in cats:
            print(f"  {name}...", flush=True)
            q = f"""SELECT ?pL ?bL ?cL ?wL WHERE {{
              ?p wdt:P31 wd:Q5. ?p wdt:P106 wd:{qid}.
              OPTIONAL {{ ?p wdt:P19 ?b. }}
              OPTIONAL {{ ?p wdt:P27 ?c. }}
              OPTIONAL {{ ?p wdt:P800 ?w. }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en".
                ?p rdfs:label ?pL. ?b rdfs:label ?bL. ?c rdfs:label ?cL. ?w rdfs:label ?wL. }}
            }} LIMIT {limit}"""
            data = sparql(q)
            if data:
                for row in data['results']['bindings']:
                    p = val(row, 'pL')
                    if not p or len(p) < 3: continue
                    write(f, p, 'is_a', name, 95)
                    bp = val(row, 'bL')
                    if bp: write(f, p, 'born_in', bp, 90)
                    c = val(row, 'cL')
                    if c: write(f, p, 'nationality', c, 90)
                    w = val(row, 'wL')
                    if w: write(f, p, 'known_for', w, 85)

    elif batch == 'geo':
        # Cities
        q = """SELECT ?cityLabel ?countryLabel ?population WHERE {
          ?city wdt:P31/wdt:P279* wd:Q515.
          ?city wdt:P17 ?country. ?city wdt:P1082 ?population.
          FILTER(?population > 100000)
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } ORDER BY DESC(?population) LIMIT 5000"""
        data = sparql(q)
        if data:
            for row in data['results']['bindings']:
                city = val(row, 'cityLabel')
                if not city: continue
                write(f, city, 'is_a', 'city', 95)
                co = val(row, 'countryLabel')
                if co: write(f, city, 'located_in', co, 95)
                pop = val(row, 'population')
                if pop: write(f, city, 'population', pop, 90)
        # Rivers
        q2 = """SELECT ?riverLabel ?length ?countryLabel WHERE {
          ?river wdt:P31 wd:Q4022.
          OPTIONAL { ?river wdt:P2043 ?length. }
          OPTIONAL { ?river wdt:P17 ?country. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 3000"""
        data = sparql(q2)
        if data:
            for row in data['results']['bindings']:
                r = val(row, 'riverLabel')
                if not r: continue
                write(f, r, 'is_a', 'river', 95)
                l = val(row, 'length')
                if l: write(f, r, 'length_km', l, 90)
                c = val(row, 'countryLabel')
                if c: write(f, r, 'located_in', c, 90)
        # Mountains
        q3 = """SELECT ?mLabel ?elevation ?cLabel WHERE {
          ?m wdt:P31 wd:Q8502.
          OPTIONAL { ?m wdt:P2044 ?elevation. }
          OPTIONAL { ?m wdt:P17 ?c. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 3000"""
        data = sparql(q3)
        if data:
            for row in data['results']['bindings']:
                m = val(row, 'mLabel')
                if not m: continue
                write(f, m, 'is_a', 'mountain', 95)
                e = val(row, 'elevation')
                if e: write(f, m, 'elevation_m', e, 95)
                c = val(row, 'cLabel')
                if c: write(f, m, 'located_in', c, 90)

    elif batch == 'culture':
        # Films
        q = """SELECT ?filmLabel ?dirLabel ?year ?gLabel WHERE {
          ?film wdt:P31 wd:Q11424.
          OPTIONAL { ?film wdt:P57 ?dir. }
          OPTIONAL { ?film wdt:P577 ?year. }
          OPTIONAL { ?film wdt:P136 ?g. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 10000"""
        data = sparql(q)
        if data:
            for row in data['results']['bindings']:
                film = val(row, 'filmLabel')
                if not film: continue
                write(f, film, 'is_a', 'film', 90)
                d = val(row, 'dirLabel')
                if d: write(f, film, 'directed_by', d, 90)
                y = val(row, 'year')
                if y: write(f, film, 'release_year', y[:4], 90)
                g = val(row, 'gLabel')
                if g: write(f, film, 'genre', g, 85)
        # Books
        q2 = """SELECT ?bLabel ?aLabel ?year WHERE {
          ?b wdt:P31 wd:Q7725634.
          OPTIONAL { ?b wdt:P50 ?a. }
          OPTIONAL { ?b wdt:P577 ?year. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 10000"""
        data = sparql(q2)
        if data:
            for row in data['results']['bindings']:
                b = val(row, 'bLabel')
                if not b: continue
                write(f, b, 'is_a', 'book', 90)
                a = val(row, 'aLabel')
                if a: write(f, b, 'written_by', a, 90)
                y = val(row, 'year')
                if y: write(f, b, 'published_year', y[:4], 85)

    elif batch == 'tech':
        q = """SELECT ?lLabel ?dLabel ?year WHERE {
          ?l wdt:P31 wd:Q9143.
          OPTIONAL { ?l wdt:P287 ?d. }
          OPTIONAL { ?l wdt:P571 ?year. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 500"""
        data = sparql(q)
        if data:
            for row in data['results']['bindings']:
                l = val(row, 'lLabel')
                if not l: continue
                write(f, l, 'is_a', 'programming language', 99)
                d = val(row, 'dLabel')
                if d: write(f, l, 'designed_by', d, 95)
                y = val(row, 'year')
                if y: write(f, l, 'created_year', y[:4], 95)
        # Companies
        q2 = """SELECT ?coLabel ?fLabel ?year ?hqLabel WHERE {
          ?co wdt:P31 wd:Q4830453.
          ?co wdt:P2139 ?rev. FILTER(?rev > 1000000000)
          OPTIONAL { ?co wdt:P112 ?f. }
          OPTIONAL { ?co wdt:P571 ?year. }
          OPTIONAL { ?co wdt:P159 ?hq. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 5000"""
        data = sparql(q2)
        if data:
            for row in data['results']['bindings']:
                co = val(row, 'coLabel')
                if not co: continue
                write(f, co, 'is_a', 'company', 95)
                founder = val(row, 'fLabel')
                if founder: write(f, co, 'founded_by', founder, 90)
                y = val(row, 'year')
                if y: write(f, co, 'founded_year', y[:4], 90)
                hq = val(row, 'hqLabel')
                if hq: write(f, co, 'headquarters', hq, 90)

    elif batch == 'taxonomy':
        q = """SELECT ?cityLabel ?stateLabel ?countryLabel WHERE {
          ?city wdt:P31/wdt:P279* wd:Q515.
          ?city wdt:P131 ?state. ?state wdt:P17 ?country.
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        } LIMIT 10000"""
        data = sparql(q)
        if data:
            for row in data['results']['bindings']:
                city = val(row, 'cityLabel')
                state = val(row, 'stateLabel')
                country = val(row, 'countryLabel')
                if city and state: write(f, city, 'located_in', state, 90)
                if state and country: write(f, state, 'located_in', country, 90)

    f.close()
    print(f"\nDone! Added {facts:,} facts. Queries: {qnum}", flush=True)
    total = sum(1 for _ in open(OUTPUT))
    print(f"Total in file: {total:,} facts", flush=True)
