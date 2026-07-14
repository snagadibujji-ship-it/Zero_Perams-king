#!/usr/bin/env python3
"""
Throttled batch runner - respects Wikidata rate limits.
Adds 65-second delay between SPARQL queries to avoid 429.
"""
import urllib.request, urllib.parse, json, time, os, sys, csv, gzip

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPTS_DIR, '..', 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
os.makedirs(RAW_DIR, exist_ok=True)

SPARQL_URL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "Axima/3.0 Knowledge-Builder (bot; batch-import)",
           "Accept": "application/json"}
DELAY = 62  # seconds between queries (Wikidata enforces 1/min)

total_facts = 0
query_count = 0



def sparql(query, retries=3):
    """SPARQL query with proper throttling."""
    global query_count
    for attempt in range(retries):
        try:
            url = f"{SPARQL_URL}?query={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=120)
            data = json.loads(resp.read().decode())
            query_count += 1
            print(f"    [Query #{query_count}] OK - waiting {DELAY}s...")
            time.sleep(DELAY)
            return data
        except Exception as e:
            print(f"    Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                wait = DELAY * (attempt + 2)
                print(f"    Waiting {wait}s before retry...")
                time.sleep(wait)
    return None


def val(row, key):
    """Extract value from SPARQL binding, skip Q-IDs."""
    v = row.get(key, {}).get('value', '')
    if v.startswith('http://www.wikidata.org/entity/'):
        return None
    if v and len(v) < 3 and v.startswith('Q'):
        return None
    return v.strip() if v else None



def write(f, subj, rel, obj, conf=90):
    """Write a single triple."""
    global total_facts
    if subj and rel and obj and len(subj) > 1 and len(obj) > 0:
        s = subj.lower().strip()
        o = obj.lower().strip()
        if not s.startswith('q') and not o.startswith('q'):
            f.write(f"{s}|{rel}|{o}|{conf}\n")
            total_facts += 1


# ═══════════════════════════════════════════════════════════
# BATCH 1: Countries
# ═══════════════════════════════════════════════════════════
def batch_1(f):
    print("\n[BATCH 1] Countries...")
    q = """SELECT ?countryLabel ?capitalLabel ?population ?area ?continentLabel WHERE {
      ?country wdt:P31 wd:Q6256.
      OPTIONAL { ?country wdt:P36 ?capital. }
      OPTIONAL { ?country wdt:P1082 ?population. }
      OPTIONAL { ?country wdt:P2046 ?area. }
      OPTIONAL { ?country wdt:P30 ?continent. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }"""
    data = sparql(q)
    if data:
        for row in data['results']['bindings']:
            c = val(row, 'countryLabel')
            if not c: continue
            write(f, c, 'is_a', 'country', 99)
            cap = val(row, 'capitalLabel')
            if cap:
                write(f, c, 'capital', cap, 99)
                write(f, cap, 'capital_of', c, 99)
            pop = val(row, 'population')
            if pop: write(f, c, 'population', pop, 95)
            area = val(row, 'area')
            if area: write(f, c, 'area_km2', area, 95)
            cont = val(row, 'continentLabel')
            if cont:
                write(f, c, 'continent', cont, 99)
                write(f, c, 'located_in', cont, 99)


    # Languages
    q2 = """SELECT ?countryLabel ?languageLabel WHERE {
      ?country wdt:P31 wd:Q6256. ?country wdt:P37 ?language.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }"""
    data = sparql(q2)
    if data:
        for row in data['results']['bindings']:
            c = val(row, 'countryLabel')
            l = val(row, 'languageLabel')
            if c and l: write(f, c, 'official_language', l, 95)

    # Currencies
    q3 = """SELECT ?countryLabel ?currencyLabel WHERE {
      ?country wdt:P31 wd:Q6256. ?country wdt:P38 ?currency.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }"""
    data = sparql(q3)
    if data:
        for row in data['results']['bindings']:
            c = val(row, 'countryLabel')
            cur = val(row, 'currencyLabel')
            if c and cur: write(f, c, 'currency', cur, 95)

    # Borders
    q4 = """SELECT ?countryLabel ?borderLabel WHERE {
      ?country wdt:P31 wd:Q6256. ?country wdt:P47 ?border.
      ?border wdt:P31 wd:Q6256.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }"""
    data = sparql(q4)
    if data:
        for row in data['results']['bindings']:
            c = val(row, 'countryLabel')
            b = val(row, 'borderLabel')
            if c and b: write(f, c, 'borders', b, 95)



# ═══════════════════════════════════════════════════════════
# BATCH 2: People (top categories)
# ═══════════════════════════════════════════════════════════
def batch_2(f):
    print("\n[BATCH 2] Famous People...")
    categories = [
        ('Q901', 'scientist', 5000),
        ('Q36180', 'writer', 5000),
        ('Q639669', 'musician', 5000),
        ('Q82955', 'politician', 5000),
        ('Q2066131', 'athlete', 5000),
        ('Q205375', 'inventor', 3000),
        ('Q33999', 'actor', 5000),
        ('Q169470', 'physicist', 3000),
    ]
    for qid, name, limit in categories:
        print(f"    {name} (limit {limit})...")
        q = f"""SELECT ?personLabel ?birthPlaceLabel ?citizenshipLabel ?notableWorkLabel WHERE {{
          ?person wdt:P31 wd:Q5. ?person wdt:P106 wd:{qid}.
          OPTIONAL {{ ?person wdt:P19 ?birthPlace. }}
          OPTIONAL {{ ?person wdt:P27 ?citizenship. }}
          OPTIONAL {{ ?person wdt:P800 ?notableWork. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT {limit}"""
        data = sparql(q)
        if data:
            for row in data['results']['bindings']:
                p = val(row, 'personLabel')
                if not p or len(p) < 3: continue
                write(f, p, 'is_a', name, 95)
                bp = val(row, 'birthPlaceLabel')
                if bp: write(f, p, 'born_in', bp, 90)
                cit = val(row, 'citizenshipLabel')
                if cit: write(f, p, 'nationality', cit, 90)
                work = val(row, 'notableWorkLabel')
                if work: write(f, p, 'known_for', work, 85)



# ═══════════════════════════════════════════════════════════
# BATCH 3: Science
# ═══════════════════════════════════════════════════════════
def batch_3(f):
    print("\n[BATCH 3] Science...")
    # Elements
    q = """SELECT ?elementLabel ?symbol ?atomicNumber ?mass ?boilingPoint ?meltingPoint WHERE {
      ?element wdt:P31 wd:Q11344.
      OPTIONAL { ?element wdt:P246 ?symbol. }
      OPTIONAL { ?element wdt:P1086 ?atomicNumber. }
      OPTIONAL { ?element wdt:P2067 ?mass. }
      OPTIONAL { ?element wdt:P2102 ?boilingPoint. }
      OPTIONAL { ?element wdt:P2101 ?meltingPoint. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }"""
    data = sparql(q)
    if data:
        for row in data['results']['bindings']:
            e = val(row, 'elementLabel')
            if not e: continue
            write(f, e, 'is_a', 'chemical element', 99)
            s = val(row, 'symbol')
            if s: write(f, e, 'symbol', s, 99)
            an = val(row, 'atomicNumber')
            if an: write(f, e, 'atomic_number', an, 99)
            m = val(row, 'mass')
            if m: write(f, e, 'atomic_mass', m, 99)
            bp = val(row, 'boilingPoint')
            if bp: write(f, e, 'boiling_point', bp, 95)
            mp = val(row, 'meltingPoint')
            if mp: write(f, e, 'melting_point', mp, 95)

    # Planets
    q2 = """SELECT ?planetLabel ?mass ?radius WHERE {
      ?planet wdt:P31 wd:Q634.
      OPTIONAL { ?planet wdt:P2067 ?mass. }
      OPTIONAL { ?planet wdt:P2120 ?radius. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }"""
    data = sparql(q2)
    if data:
        for row in data['results']['bindings']:
            p = val(row, 'planetLabel')
            if not p: continue
            write(f, p, 'is_a', 'planet', 99)
            write(f, p, 'located_in', 'solar system', 99)


    # Animals
    animals = [('Q7377','mammal',3000),('Q5113','bird',3000),
               ('Q10811','reptile',2000),('Q152','fish',2000)]
    for qid, cls, limit in animals:
        q = f"""SELECT ?animalLabel WHERE {{
          ?animal wdt:P31 wd:{qid}.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} LIMIT {limit}"""
        data = sparql(q)
        if data:
            for row in data['results']['bindings']:
                a = val(row, 'animalLabel')
                if a: write(f, a, 'is_a', cls, 95)


# ═══════════════════════════════════════════════════════════
# BATCH 4: Geography
# ═══════════════════════════════════════════════════════════
def batch_4(f):
    print("\n[BATCH 4] Geography...")
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
            country = val(row, 'countryLabel')
            if country: write(f, city, 'located_in', country, 95)
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
    q3 = """SELECT ?mountainLabel ?elevation ?countryLabel WHERE {
      ?mountain wdt:P31 wd:Q8502.
      OPTIONAL { ?mountain wdt:P2044 ?elevation. }
      OPTIONAL { ?mountain wdt:P17 ?country. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 3000"""
    data = sparql(q3)
    if data:
        for row in data['results']['bindings']:
            m = val(row, 'mountainLabel')
            if not m: continue
            write(f, m, 'is_a', 'mountain', 95)
            e = val(row, 'elevation')
            if e: write(f, m, 'elevation_m', e, 95)
            c = val(row, 'countryLabel')
            if c: write(f, m, 'located_in', c, 90)



# ═══════════════════════════════════════════════════════════
# BATCH 5: Culture
# ═══════════════════════════════════════════════════════════
def batch_5(f):
    print("\n[BATCH 5] Culture...")
    # Movies
    q = """SELECT ?filmLabel ?directorLabel ?year ?genreLabel WHERE {
      ?film wdt:P31 wd:Q11424.
      OPTIONAL { ?film wdt:P57 ?director. }
      OPTIONAL { ?film wdt:P577 ?year. }
      OPTIONAL { ?film wdt:P136 ?genre. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 10000"""
    data = sparql(q)
    if data:
        for row in data['results']['bindings']:
            film = val(row, 'filmLabel')
            if not film: continue
            write(f, film, 'is_a', 'film', 90)
            d = val(row, 'directorLabel')
            if d: write(f, film, 'directed_by', d, 90)
            y = val(row, 'year')
            if y: write(f, film, 'release_year', y[:4], 90)
            g = val(row, 'genreLabel')
            if g: write(f, film, 'genre', g, 85)

    # Books
    q2 = """SELECT ?bookLabel ?authorLabel ?year WHERE {
      ?book wdt:P31 wd:Q7725634.
      OPTIONAL { ?book wdt:P50 ?author. }
      OPTIONAL { ?book wdt:P577 ?year. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 10000"""
    data = sparql(q2)
    if data:
        for row in data['results']['bindings']:
            b = val(row, 'bookLabel')
            if not b: continue
            write(f, b, 'is_a', 'book', 90)
            a = val(row, 'authorLabel')
            if a: write(f, b, 'written_by', a, 90)
            y = val(row, 'year')
            if y: write(f, b, 'published_year', y[:4], 85)


# ═══════════════════════════════════════════════════════════
# BATCH 6: Technology
# ═══════════════════════════════════════════════════════════
def batch_6(f):
    print("\n[BATCH 6] Technology...")
    # Programming Languages
    q = """SELECT ?langLabel ?designerLabel ?year WHERE {
      ?lang wdt:P31 wd:Q9143.
      OPTIONAL { ?lang wdt:P287 ?designer. }
      OPTIONAL { ?lang wdt:P571 ?year. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 500"""
    data = sparql(q)
    if data:
        for row in data['results']['bindings']:
            l = val(row, 'langLabel')
            if not l: continue
            write(f, l, 'is_a', 'programming language', 99)
            d = val(row, 'designerLabel')
            if d: write(f, l, 'designed_by', d, 95)
            y = val(row, 'year')
            if y: write(f, l, 'created_year', y[:4], 95)

    # Companies
    q2 = """SELECT ?companyLabel ?founderLabel ?year ?hqLabel WHERE {
      ?company wdt:P31 wd:Q4830453.
      ?company wdt:P2139 ?revenue. FILTER(?revenue > 1000000000)
      OPTIONAL { ?company wdt:P112 ?founder. }
      OPTIONAL { ?company wdt:P571 ?year. }
      OPTIONAL { ?company wdt:P159 ?hq. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 5000"""
    data = sparql(q2)
    if data:
        for row in data['results']['bindings']:
            co = val(row, 'companyLabel')
            if not co: continue
            write(f, co, 'is_a', 'company', 95)
            founder = val(row, 'founderLabel')
            if founder: write(f, co, 'founded_by', founder, 90)
            y = val(row, 'year')
            if y: write(f, co, 'founded_year', y[:4], 90)
            hq = val(row, 'hqLabel')
            if hq: write(f, co, 'headquarters', hq, 90)



# ═══════════════════════════════════════════════════════════
# BATCH 7: Taxonomy
# ═══════════════════════════════════════════════════════════
def batch_7(f):
    print("\n[BATCH 7] Taxonomy...")
    # Geographic hierarchy
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

    # Biological subclass chains
    q2 = """SELECT ?childLabel ?parentLabel WHERE {
      ?child wdt:P279 ?parent.
      ?child wdt:P31 wd:Q16521.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 10000"""
    data = sparql(q2)
    if data:
        for row in data['results']['bindings']:
            child = val(row, 'childLabel')
            parent = val(row, 'parentLabel')
            if child and parent: write(f, child, 'subclass_of', parent, 90)


# ═══════════════════════════════════════════════════════════
# BATCH 8: ConceptNet (direct download, no rate limit)
# ═══════════════════════════════════════════════════════════
def batch_8_conceptnet(f):
    print("\n[BATCH 8] ConceptNet (downloading ~2GB)...")
    DL_URL = "https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz"
    DL_FILE = os.path.join(RAW_DIR, 'conceptnet.csv.gz')

    RELATION_MAP = {
        '/r/IsA': 'is_a', '/r/HasA': 'has_part', '/r/PartOf': 'part_of',
        '/r/UsedFor': 'used_for', '/r/CapableOf': 'capable_of',
        '/r/Causes': 'causes', '/r/HasProperty': 'has_property',
        '/r/MadeOf': 'made_of', '/r/AtLocation': 'found_at',
        '/r/HasPrerequisite': 'requires', '/r/MotivatedByGoal': 'purpose',
        '/r/CreatedBy': 'created_by', '/r/DefinedAs': 'defined_as',
    }

    if not os.path.isfile(DL_FILE):
        print("    Downloading ConceptNet...")
        urllib.request.urlretrieve(DL_URL, DL_FILE)
        print(f"    Downloaded: {os.path.getsize(DL_FILE)/1e6:.0f} MB")
    else:
        print(f"    Already have: {os.path.getsize(DL_FILE)/1e6:.0f} MB")

    print("    Parsing (English, weight > 1.0)...")
    count = 0
    with gzip.open(DL_FILE, 'rt', encoding='utf-8', errors='ignore') as gz:
        reader = csv.reader(gz, delimiter='\t')
        for row in reader:
            if len(row) < 5: continue
            relation, source, target, info = row[1], row[2], row[3], row[4]
            if not source.startswith('/c/en/') or not target.startswith('/c/en/'):
                continue
            if relation not in RELATION_MAP:
                continue
            try:
                meta = json.loads(info)
                if meta.get('weight', 0) < 1.0: continue
            except: continue

            subj = source[6:].split('/')[0].replace('_', ' ')
            obj = target[6:].split('/')[0].replace('_', ' ')
            rel = RELATION_MAP[relation]
            if subj and obj and len(subj) > 1 and len(obj) > 1:
                weight = meta.get('weight', 1.0)
                conf = min(95, int(50 + weight * 10))
                write(f, subj, rel, obj, conf)
                count += 1
                if count % 100000 == 0:
                    print(f"      {count:,} facts...")
    print(f"    ConceptNet done: {count:,} facts")



# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    start = time.time()
    output_file = os.path.join(RAW_DIR, 'all_batches_throttled.txt')

    print("=" * 60)
    print("  AXIMA KNOWLEDGE EXPANSION (Throttled)")
    print(f"  Rate limit: 1 query per {DELAY}s")
    print("  Output:", output_file)
    print("=" * 60)

    with open(output_file, 'w') as f:
        # ConceptNet first (no rate limit, biggest source)
        batch_8_conceptnet(f)

        # Then Wikidata batches (throttled)
        batch_1(f)
        batch_2(f)
        batch_3(f)
        batch_4(f)
        batch_5(f)
        batch_6(f)
        batch_7(f)

    elapsed = time.time() - start
    hours = int(elapsed // 3600)
    mins = int((elapsed % 3600) // 60)

    print("\n" + "=" * 60)
    print(f"  COMPLETE!")
    print(f"  Total facts: {total_facts:,}")
    print(f"  SPARQL queries: {query_count}")
    print(f"  Time: {hours}h {mins}m")
    print(f"  Output: {output_file}")
    size_mb = os.path.getsize(output_file) / 1e6
    print(f"  File size: {size_mb:.1f} MB")
    print("=" * 60)
