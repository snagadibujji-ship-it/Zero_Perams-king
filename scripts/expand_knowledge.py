#!/usr/bin/env python3
"""
Knowledge Expansion via DBpedia + Programmatic Generation.
Wikidata is down, so we use alternative sources.
Target: Add 500K+ additional facts to existing 375K from ConceptNet.
"""
import urllib.request, urllib.parse, json, time, os, sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPTS_DIR, '..', 'data', 'raw')
OUTPUT = os.path.join(RAW_DIR, 'all_batches_throttled.txt')
os.makedirs(RAW_DIR, exist_ok=True)

DBPEDIA_URL = "https://dbpedia.org/sparql"
facts_added = 0
queries_done = 0


def dbpedia_query(query, retries=3):
    """Query DBpedia SPARQL endpoint."""
    global queries_done
    for attempt in range(retries):
        try:
            params = urllib.parse.urlencode({
                'default-graph-uri': 'http://dbpedia.org',
                'query': query,
                'format': 'application/json'
            })
            url = f"{DBPEDIA_URL}?{params}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Axima/3.0'})
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read().decode())
            queries_done += 1
            time.sleep(2)  # Gentle throttle for DBpedia
            return data
        except Exception as e:
            print(f"    DBpedia attempt {attempt+1} fail: {e}", flush=True)
            time.sleep(10)
    return None

def extract_name(uri):
    """Extract clean name from DBpedia URI."""
    if not uri: return None
    name = uri.split('/')[-1].replace('_', ' ')
    # Skip if it looks like a redirect or disambiguation
    if '(' in name: name = name.split('(')[0].strip()
    return name if len(name) > 1 else None

def write(f, subj, rel, obj, conf=90):
    global facts_added
    if subj and obj and len(subj) > 1 and len(obj) > 0:
        s = subj.lower().strip()[:127]
        o = obj.lower().strip()[:127]
        f.write(f"{s}|{rel}|{o}|{conf}\n")
        facts_added += 1


def countries(f):
    """Countries from DBpedia."""
    print("  [1/10] Countries...", flush=True)
    q = """SELECT ?country ?capital ?pop ?area WHERE {
      ?country a dbo:Country .
      OPTIONAL { ?country dbo:capital ?capital }
      OPTIONAL { ?country dbo:populationTotal ?pop }
      OPTIONAL { ?country dbo:areaTotal ?area }
    } LIMIT 500"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            c = extract_name(row.get('country',{}).get('value',''))
            if not c: continue
            write(f, c, 'is_a', 'country', 99)
            cap = extract_name(row.get('capital',{}).get('value',''))
            if cap:
                write(f, c, 'capital', cap, 99)
                write(f, cap, 'capital_of', c, 99)
            pop = row.get('pop',{}).get('value','')
            if pop: write(f, c, 'population', pop, 95)
            area = row.get('area',{}).get('value','')
            if area: write(f, c, 'area_km2', area, 90)

    # Languages
    q2 = """SELECT ?country ?lang WHERE {
      ?country a dbo:Country .
      ?country dbo:officialLanguage ?lang .
    } LIMIT 1000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            c = extract_name(row.get('country',{}).get('value',''))
            l = extract_name(row.get('lang',{}).get('value',''))
            if c and l: write(f, c, 'official_language', l, 95)

    # Continents
    q3 = """SELECT ?country ?cont WHERE {
      ?country a dbo:Country .
      ?country dbo:continent ?cont .
    } LIMIT 500"""
    data = dbpedia_query(q3)
    if data:
        for row in data['results']['bindings']:
            c = extract_name(row.get('country',{}).get('value',''))
            cont = extract_name(row.get('cont',{}).get('value',''))
            if c and cont: write(f, c, 'continent', cont, 99)

def people(f):
    """Famous people from DBpedia."""
    print("  [2/10] People...", flush=True)
    categories = [
        ('dbo:Scientist', 'scientist', 10000),
        ('dbo:Writer', 'writer', 8000),
        ('dbo:Politician', 'politician', 8000),
        ('dbo:Athlete', 'athlete', 8000),
        ('dbo:MusicalArtist', 'musician', 8000),
        ('dbo:Actor', 'actor', 5000),
        ('dbo:Philosopher', 'philosopher', 3000),
    ]
    for cls, name, limit in categories:
        print(f"    {name}...", flush=True)
        q = f"""SELECT ?person ?birthPlace ?birthDate WHERE {{
          ?person a {cls} .
          OPTIONAL {{ ?person dbo:birthPlace ?birthPlace }}
          OPTIONAL {{ ?person dbo:birthDate ?birthDate }}
        }} LIMIT {limit}"""
        data = dbpedia_query(q)
        if data:
            for row in data['results']['bindings']:
                p = extract_name(row.get('person',{}).get('value',''))
                if not p or len(p) < 3: continue
                write(f, p, 'is_a', name, 95)
                bp = extract_name(row.get('birthPlace',{}).get('value',''))
                if bp: write(f, p, 'born_in', bp, 90)
                bd = row.get('birthDate',{}).get('value','')
                if bd and len(bd) >= 4:
                    write(f, p, 'born_year', bd[:4], 90)


def science(f):
    """Science facts from DBpedia."""
    print("  [3/10] Science...", flush=True)
    # Chemical elements
    q = """SELECT ?elem ?symbol ?atomicNum ?mass WHERE {
      ?elem a dbo:ChemicalElement .
      OPTIONAL { ?elem dbo:symbol ?symbol }
      OPTIONAL { ?elem dbp:atomicNumber ?atomicNum }
      OPTIONAL { ?elem dbo:atomicMass ?mass }
    } LIMIT 200"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            e = extract_name(row.get('elem',{}).get('value',''))
            if not e: continue
            write(f, e, 'is_a', 'chemical element', 99)
            s = row.get('symbol',{}).get('value','')
            if s: write(f, e, 'symbol', s, 99)
            an = row.get('atomicNum',{}).get('value','')
            if an: write(f, e, 'atomic_number', an, 99)
            m = row.get('mass',{}).get('value','')
            if m: write(f, e, 'atomic_mass', m, 99)

    # Planets
    q2 = """SELECT ?planet WHERE {
      ?planet a dbo:Planet .
      ?planet dbo:discoverer ?d .
    } LIMIT 100"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            p = extract_name(row.get('planet',{}).get('value',''))
            if p: write(f, p, 'is_a', 'planet', 99)

    # Animals
    q3 = """SELECT ?animal ?cls WHERE {
      ?animal a dbo:Animal .
      ?animal dbo:class ?cls .
    } LIMIT 10000"""
    data = dbpedia_query(q3)
    if data:
        for row in data['results']['bindings']:
            a = extract_name(row.get('animal',{}).get('value',''))
            cls = extract_name(row.get('cls',{}).get('value',''))
            if a:
                write(f, a, 'is_a', 'animal', 90)
                if cls: write(f, a, 'class', cls, 85)

def geography(f):
    """Geography facts from DBpedia."""
    print("  [4/10] Geography...", flush=True)
    # Cities
    q = """SELECT ?city ?country ?pop WHERE {
      ?city a dbo:City .
      OPTIONAL { ?city dbo:country ?country }
      OPTIONAL { ?city dbo:populationTotal ?pop }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            city = extract_name(row.get('city',{}).get('value',''))
            if not city: continue
            write(f, city, 'is_a', 'city', 95)
            co = extract_name(row.get('country',{}).get('value',''))
            if co: write(f, city, 'located_in', co, 95)
            pop = row.get('pop',{}).get('value','')
            if pop: write(f, city, 'population', pop, 90)

    # Rivers
    q2 = """SELECT ?river ?country ?length WHERE {
      ?river a dbo:River .
      OPTIONAL { ?river dbo:country ?country }
      OPTIONAL { ?river dbo:length ?length }
    } LIMIT 5000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            r = extract_name(row.get('river',{}).get('value',''))
            if not r: continue
            write(f, r, 'is_a', 'river', 95)
            co = extract_name(row.get('country',{}).get('value',''))
            if co: write(f, r, 'located_in', co, 90)

    # Mountains
    q3 = """SELECT ?mt ?elev ?country WHERE {
      ?mt a dbo:Mountain .
      OPTIONAL { ?mt dbo:elevation ?elev }
      OPTIONAL { ?mt dbo:country ?country }
    } LIMIT 5000"""
    data = dbpedia_query(q3)
    if data:
        for row in data['results']['bindings']:
            m = extract_name(row.get('mt',{}).get('value',''))
            if not m: continue
            write(f, m, 'is_a', 'mountain', 95)
            e = row.get('elev',{}).get('value','')
            if e: write(f, m, 'elevation_m', e, 95)
            co = extract_name(row.get('country',{}).get('value',''))
            if co: write(f, m, 'located_in', co, 90)


def culture(f):
    """Culture facts from DBpedia."""
    print("  [5/10] Culture...", flush=True)
    # Films
    q = """SELECT ?film ?director ?year WHERE {
      ?film a dbo:Film .
      OPTIONAL { ?film dbo:director ?director }
      OPTIONAL { ?film dbp:released ?year }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            film = extract_name(row.get('film',{}).get('value',''))
            if not film: continue
            write(f, film, 'is_a', 'film', 90)
            d = extract_name(row.get('director',{}).get('value',''))
            if d: write(f, film, 'directed_by', d, 90)

    # Books
    q2 = """SELECT ?book ?author WHERE {
      ?book a dbo:Book .
      OPTIONAL { ?book dbo:author ?author }
    } LIMIT 10000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            b = extract_name(row.get('book',{}).get('value',''))
            if not b: continue
            write(f, b, 'is_a', 'book', 90)
            a = extract_name(row.get('author',{}).get('value',''))
            if a: write(f, b, 'written_by', a, 90)

    # Albums
    q3 = """SELECT ?album ?artist WHERE {
      ?album a dbo:Album .
      OPTIONAL { ?album dbo:artist ?artist }
    } LIMIT 10000"""
    data = dbpedia_query(q3)
    if data:
        for row in data['results']['bindings']:
            al = extract_name(row.get('album',{}).get('value',''))
            if not al: continue
            write(f, al, 'is_a', 'album', 85)
            ar = extract_name(row.get('artist',{}).get('value',''))
            if ar: write(f, al, 'by_artist', ar, 90)

def technology(f):
    """Technology facts from DBpedia."""
    print("  [6/10] Technology...", flush=True)
    # Programming languages
    q = """SELECT ?lang ?designer ?year WHERE {
      ?lang a dbo:ProgrammingLanguage .
      OPTIONAL { ?lang dbo:designer ?designer }
      OPTIONAL { ?lang dbp:year ?year }
    } LIMIT 500"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            l = extract_name(row.get('lang',{}).get('value',''))
            if not l: continue
            write(f, l, 'is_a', 'programming language', 99)
            d = extract_name(row.get('designer',{}).get('value',''))
            if d: write(f, l, 'designed_by', d, 95)

    # Companies
    q2 = """SELECT ?co ?founder ?industry WHERE {
      ?co a dbo:Company .
      OPTIONAL { ?co dbo:foundedBy ?founder }
      OPTIONAL { ?co dbo:industry ?industry }
    } LIMIT 10000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            co = extract_name(row.get('co',{}).get('value',''))
            if not co: continue
            write(f, co, 'is_a', 'company', 90)
            fo = extract_name(row.get('founder',{}).get('value',''))
            if fo: write(f, co, 'founded_by', fo, 90)
            ind = extract_name(row.get('industry',{}).get('value',''))
            if ind: write(f, co, 'industry', ind, 85)


def universities(f):
    """Universities from DBpedia."""
    print("  [7/10] Universities...", flush=True)
    q = """SELECT ?uni ?city ?country WHERE {
      ?uni a dbo:University .
      OPTIONAL { ?uni dbo:city ?city }
      OPTIONAL { ?uni dbo:country ?country }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            u = extract_name(row.get('uni',{}).get('value',''))
            if not u: continue
            write(f, u, 'is_a', 'university', 90)
            city = extract_name(row.get('city',{}).get('value',''))
            if city: write(f, u, 'located_in', city, 90)
            co = extract_name(row.get('country',{}).get('value',''))
            if co: write(f, u, 'country', co, 90)

def sports(f):
    """Sports facts from DBpedia."""
    print("  [8/10] Sports...", flush=True)
    # Soccer players
    q = """SELECT ?player ?team ?pos WHERE {
      ?player a dbo:SoccerPlayer .
      OPTIONAL { ?player dbo:team ?team }
      OPTIONAL { ?player dbo:position ?pos }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            p = extract_name(row.get('player',{}).get('value',''))
            if not p: continue
            write(f, p, 'is_a', 'soccer player', 90)
            t = extract_name(row.get('team',{}).get('value',''))
            if t: write(f, p, 'plays_for', t, 85)

    # Olympics
    q2 = """SELECT ?event ?sport ?year WHERE {
      ?event a dbo:OlympicEvent .
      OPTIONAL { ?event dbo:sport ?sport }
    } LIMIT 5000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            e = extract_name(row.get('event',{}).get('value',''))
            if not e: continue
            write(f, e, 'is_a', 'olympic event', 85)
            s = extract_name(row.get('sport',{}).get('value',''))
            if s: write(f, e, 'sport', s, 85)

def diseases(f):
    """Medical facts from DBpedia."""
    print("  [9/10] Diseases...", flush=True)
    q = """SELECT ?disease ?symptom WHERE {
      ?disease a dbo:Disease .
      OPTIONAL { ?disease dbo:symptom ?symptom }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            d = extract_name(row.get('disease',{}).get('value',''))
            if not d: continue
            write(f, d, 'is_a', 'disease', 90)
            s = extract_name(row.get('symptom',{}).get('value',''))
            if s: write(f, d, 'has_symptom', s, 85)

def taxonomy(f):
    """Taxonomy/hierarchy from DBpedia."""
    print("  [10/10] Taxonomy (species)...", flush=True)
    q = """SELECT ?species ?family ?order WHERE {
      ?species a dbo:Species .
      OPTIONAL { ?species dbp:familia ?family }
      OPTIONAL { ?species dbp:ordo ?order }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            sp = extract_name(row.get('species',{}).get('value',''))
            if not sp: continue
            write(f, sp, 'is_a', 'species', 90)
            fam = row.get('family',{}).get('value','')
            if fam and not fam.startswith('http'):
                write(f, sp, 'family', fam.lower(), 85)


def programmatic_facts(f):
    """Generate well-known facts programmatically (no API needed)."""
    print("  [BONUS] Programmatic facts...", flush=True)

    # Physics constants
    constants = [
        ("speed of light", "value", "299792458 m/s", 99),
        ("speed of light", "symbol", "c", 99),
        ("gravitational constant", "value", "6.674e-11 N⋅m²/kg²", 99),
        ("gravitational constant", "symbol", "G", 99),
        ("planck constant", "value", "6.626e-34 J⋅s", 99),
        ("boltzmann constant", "value", "1.381e-23 J/K", 99),
        ("avogadro number", "value", "6.022e23 /mol", 99),
        ("electron mass", "value", "9.109e-31 kg", 99),
        ("proton mass", "value", "1.673e-27 kg", 99),
        ("elementary charge", "value", "1.602e-19 C", 99),
        ("pi", "value", "3.14159265358979", 99),
        ("euler number", "value", "2.71828182845905", 99),
        ("golden ratio", "value", "1.61803398874989", 99),
    ]
    for subj, rel, obj, conf in constants:
        write(f, subj, rel, obj, conf)

    # Solar system
    planets = [
        ("mercury", 1, "57.9", "4879", "0.330e24"),
        ("venus", 2, "108.2", "12104", "4.87e24"),
        ("earth", 3, "149.6", "12756", "5.97e24"),
        ("mars", 4, "227.9", "6792", "0.642e24"),
        ("jupiter", 5, "778.6", "142984", "1898e24"),
        ("saturn", 6, "1433.5", "120536", "568e24"),
        ("uranus", 7, "2872.5", "51118", "86.8e24"),
        ("neptune", 8, "4495.1", "49528", "102e24"),
    ]
    for name, pos, dist, diam, mass in planets:
        write(f, name, 'is_a', 'planet', 99)
        write(f, name, 'position_from_sun', str(pos), 99)
        write(f, name, 'distance_from_sun_million_km', dist, 99)
        write(f, name, 'diameter_km', diam, 99)
        write(f, name, 'part_of', 'solar system', 99)

    # Continents
    continents = ["africa", "antarctica", "asia", "europe",
                  "north america", "south america", "australia"]
    for c in continents:
        write(f, c, 'is_a', 'continent', 99)

    # Oceans
    oceans = ["pacific ocean", "atlantic ocean", "indian ocean",
              "arctic ocean", "southern ocean"]
    for o in oceans:
        write(f, o, 'is_a', 'ocean', 99)

    # SI Units
    units = [
        ("meter", "measures", "length"), ("kilogram", "measures", "mass"),
        ("second", "measures", "time"), ("ampere", "measures", "current"),
        ("kelvin", "measures", "temperature"), ("mole", "measures", "amount"),
        ("candela", "measures", "luminous intensity"),
    ]
    for u, r, m in units:
        write(f, u, r, m, 99)
        write(f, u, 'is_a', 'si unit', 99)

    # Common sense additions
    common = [
        ("water", "boiling_point", "100 degrees celsius", 99),
        ("water", "freezing_point", "0 degrees celsius", 99),
        ("water", "formula", "h2o", 99),
        ("earth", "has_property", "round", 99),
        ("earth", "radius_km", "6371", 99),
        ("sun", "is_a", "star", 99),
        ("sun", "surface_temperature", "5778 kelvin", 99),
        ("moon", "orbits", "earth", 99),
        ("light year", "equals", "9.461 trillion km", 99),
        ("diamond", "hardness", "10 mohs", 99),
        ("gold", "symbol", "au", 99),
        ("iron", "symbol", "fe", 99),
        ("oxygen", "symbol", "o", 99),
        ("hydrogen", "symbol", "h", 99),
        ("carbon", "symbol", "c", 99),
        ("nitrogen", "symbol", "n", 99),
    ]
    for s, r, o, c in common:
        write(f, s, r, o, c)

if __name__ == '__main__':
    start = time.time()
    print("=" * 60)
    print("  AXIMA Knowledge Expansion (DBpedia + Programmatic)")
    print("=" * 60, flush=True)

    with open(OUTPUT, 'a') as f:  # APPEND to existing
        countries(f)
        people(f)
        science(f)
        geography(f)
        culture(f)
        technology(f)
        universities(f)
        sports(f)
        diseases(f)
        taxonomy(f)
        programmatic_facts(f)

    elapsed = time.time() - start
    total_lines = sum(1 for _ in open(OUTPUT))
    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  New facts added: {facts_added:,}")
    print(f"  DBpedia queries: {queries_done}")
    print(f"  Total in file: {total_lines:,}")
    print(f"  Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"  File: {OUTPUT}")
    print(f"  Size: {os.path.getsize(OUTPUT)/1e6:.1f} MB")
    print(f"{'=' * 60}", flush=True)
