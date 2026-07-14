#!/usr/bin/env python3
"""
COSMIC EXPANSION PART 2 — Keep going, more domains, more depth.
"""
import urllib.request, urllib.parse, json, time, os, sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPTS_DIR, '..', 'data', 'raw')
OUTPUT = os.path.join(RAW_DIR, 'batch_cosmic2.txt')
os.makedirs(RAW_DIR, exist_ok=True)

DBPEDIA_URL = "https://dbpedia.org/sparql"
facts_added = 0
queries_done = 0

def dbpedia_query(query, retries=3):
    global queries_done
    for attempt in range(retries):
        try:
            params = urllib.parse.urlencode({
                'default-graph-uri': 'http://dbpedia.org',
                'query': query, 'format': 'application/json'
            })
            url = f"{DBPEDIA_URL}?{params}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Axima/3.0'})
            resp = urllib.request.urlopen(req, timeout=120)
            data = json.loads(resp.read().decode())
            queries_done += 1
            time.sleep(1.2)
            return data
        except Exception as e:
            if attempt < retries-1: time.sleep(5*(attempt+1))
            else: print(f"    FAIL: {e}", flush=True)
    return None

def n(uri):
    if not uri: return None
    nm = uri.split('/')[-1].replace('_', ' ')
    if '(' in nm: nm = nm.split('(')[0].strip()
    return nm if 1 < len(nm) < 128 else None

def w(f, subj, rel, obj, conf=90):
    global facts_added
    if subj and obj and len(subj) > 1 and len(obj) > 0:
        s = subj.lower().strip()[:127]
        o = obj.lower().strip()[:127]
        if s and o and len(s) > 1:
            f.write(f"{s}|{rel}|{o}|{conf}\n")
            facts_added += 1


def relationships(f):
    """Pull relationship-heavy queries from DBpedia."""
    print("\n[RELATIONSHIPS] Pulling complex relations...", flush=True)

    # People → occupation, birthPlace, deathPlace, almaMater
    for offset in range(0, 200000, 10000):
        q = f"""SELECT ?p ?alma ?deathPlace ?deathDate WHERE {{
          ?p a dbo:Person .
          OPTIONAL {{ ?p dbo:almaMater ?alma }}
          OPTIONAL {{ ?p dbo:deathPlace ?deathPlace }}
          OPTIONAL {{ ?p dbo:deathDate ?deathDate }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            p = n(row.get('p',{}).get('value',''))
            if not p: continue
            alma = n(row.get('alma',{}).get('value',''))
            if alma: w(f, p, 'studied_at', alma, 85)
            dp = n(row.get('deathPlace',{}).get('value',''))
            if dp: w(f, p, 'died_in', dp, 80)
            dd = row.get('deathDate',{}).get('value','')
            if dd and len(dd)>=4: w(f, p, 'died_year', dd[:4], 80)

    # Films → cast, country, budget
    print("  Films with cast...", flush=True)
    for offset in range(0, 50000, 10000):
        q = f"""SELECT ?film ?actor ?country WHERE {{
          ?film a dbo:Film .
          OPTIONAL {{ ?film dbo:starring ?actor }}
          OPTIONAL {{ ?film dbo:country ?country }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            film = n(row.get('film',{}).get('value',''))
            if not film: continue
            actor = n(row.get('actor',{}).get('value',''))
            if actor: w(f, film, 'stars', actor, 85)
            co = n(row.get('country',{}).get('value',''))
            if co: w(f, film, 'country', co, 80)

    # Songs → artist, album, genre
    print("  Songs with artists...", flush=True)
    for offset in range(0, 100000, 10000):
        q = f"""SELECT ?song ?artist ?album ?genre WHERE {{
          ?song a dbo:Song .
          OPTIONAL {{ ?song dbo:artist ?artist }}
          OPTIONAL {{ ?song dbo:album ?album }}
          OPTIONAL {{ ?song dbo:genre ?genre }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            s = n(row.get('song',{}).get('value',''))
            if not s: continue
            ar = n(row.get('artist',{}).get('value',''))
            if ar: w(f, s, 'performed_by', ar, 85)
            al = n(row.get('album',{}).get('value',''))
            if al: w(f, s, 'from_album', al, 80)
            ge = n(row.get('genre',{}).get('value',''))
            if ge: w(f, s, 'genre', ge, 80)

    # Athletes → team, sport, position
    print("  Athletes with teams...", flush=True)
    for offset in range(0, 100000, 10000):
        q = f"""SELECT ?athlete ?team ?sport ?pos WHERE {{
          ?athlete a dbo:Athlete .
          OPTIONAL {{ ?athlete dbo:team ?team }}
          OPTIONAL {{ ?athlete dbo:sport ?sport }}
          OPTIONAL {{ ?athlete dbo:position ?pos }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            a = n(row.get('athlete',{}).get('value',''))
            if not a: continue
            t = n(row.get('team',{}).get('value',''))
            if t: w(f, a, 'plays_for', t, 85)
            sp = n(row.get('sport',{}).get('value',''))
            if sp: w(f, a, 'plays_sport', sp, 85)

    # Albums → artist, genre, label
    print("  Albums with details...", flush=True)
    for offset in range(0, 100000, 10000):
        q = f"""SELECT ?album ?artist ?genre ?label WHERE {{
          ?album a dbo:Album .
          OPTIONAL {{ ?album dbo:artist ?artist }}
          OPTIONAL {{ ?album dbo:genre ?genre }}
          OPTIONAL {{ ?album dbo:recordLabel ?label }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            al = n(row.get('album',{}).get('value',''))
            if not al: continue
            ar = n(row.get('artist',{}).get('value',''))
            if ar: w(f, al, 'by_artist', ar, 85)
            ge = n(row.get('genre',{}).get('value',''))
            if ge: w(f, al, 'genre', ge, 80)
            lb = n(row.get('label',{}).get('value',''))
            if lb: w(f, al, 'record_label', lb, 80)

    # Companies → products, revenue, employees
    print("  Companies with details...", flush=True)
    for offset in range(0, 50000, 10000):
        q = f"""SELECT ?co ?product ?numEmp ?rev WHERE {{
          ?co a dbo:Company .
          OPTIONAL {{ ?co dbo:product ?product }}
          OPTIONAL {{ ?co dbo:numberOfEmployees ?numEmp }}
          OPTIONAL {{ ?co dbo:revenue ?rev }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            co = n(row.get('co',{}).get('value',''))
            if not co: continue
            pr = n(row.get('product',{}).get('value',''))
            if pr: w(f, co, 'produces', pr, 80)
            emp = row.get('numEmp',{}).get('value','')
            if emp: w(f, co, 'employees', emp, 75)


def more_types(f):
    """Even more types from DBpedia."""
    print("\n[MORE TYPES] Additional entity types...", flush=True)
    types = [
        ("dbo:ComicStrip", "comic strip", 10000),
        ("dbo:Anime", "anime", 10000),
        ("dbo:Manga", "manga", 10000),
        ("dbo:Musical", "musical", 10000),
        ("dbo:Play", "play", 10000),
        ("dbo:Poem", "poem", 5000),
        ("dbo:Opera", "opera", 5000),
        ("dbo:Ballet", "ballet", 3000),
        ("dbo:MartialArt", "martial art", 1000),
        ("dbo:Sport", "sport", 3000),
        ("dbo:Grape", "grape variety", 3000),
        ("dbo:Cheese", "cheese", 3000),
        ("dbo:Wine", "wine", 5000),
        ("dbo:Beer", "beer", 5000),
        ("dbo:Cocktail", "cocktail", 1000),
        ("dbo:Gemstone", "gemstone", 1000),
        ("dbo:Colour", "color", 500),
        ("dbo:ChemicalSubstance", "chemical substance", 10000),
        ("dbo:Enzyme", "enzyme", 10000),
        ("dbo:Hormone", "hormone", 1000),
        ("dbo:Vitamin", "vitamin", 200),
        ("dbo:Bacteria", "bacteria", 10000),
        ("dbo:Virus", "virus", 5000),
        ("dbo:Protein", "protein", 20000),
        ("dbo:Gene", "gene", 20000),
        ("dbo:Chromosome", "chromosome", 1000),
        ("dbo:Fossil", "fossil", 5000),
        ("dbo:Dinosaur", "dinosaur", 5000),
        ("dbo:CelestialBody", "celestial body", 20000),
        ("dbo:Comet", "comet", 3000),
        ("dbo:Planet", "planet", 3000),
        ("dbo:Moon", "moon", 3000),
    ]
    for cls, label, limit in types:
        for offset in range(0, limit, 10000):
            q = f"""SELECT ?item WHERE {{
              ?item a {cls} .
            }} LIMIT 10000 OFFSET {offset}"""
            data = dbpedia_query(q)
            if not data or not data['results']['bindings']: break
            for row in data['results']['bindings']:
                item = n(row.get('item',{}).get('value',''))
                if item: w(f, item, 'is_a', label, 80)


if __name__ == '__main__':
    start = time.time()
    print("=" * 60)
    print("  COSMIC EXPANSION PART 2 — More depth, more relations")
    print("=" * 60, flush=True)

    with open(OUTPUT, 'w') as f:
        relationships(f)
        more_types(f)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  PART 2 COMPLETE!")
    print(f"  Facts: {facts_added:,}")
    print(f"  Queries: {queries_done}")
    print(f"  Time: {elapsed/60:.1f} min")
    print(f"  Size: {os.path.getsize(OUTPUT)/1e6:.1f} MB")
    print(f"{'=' * 60}", flush=True)
