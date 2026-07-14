#!/usr/bin/env python3
"""
Expand knowledge with MORE topics beyond the initial 462K.
Adds: historical events, wars, languages, religions, foods, sports teams,
awards, inventions, architecture, music genres, currencies, astronomical objects,
chemical compounds, mathematical concepts, legal systems, and more.
"""
import urllib.request, urllib.parse, json, time, os, sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPTS_DIR, '..', 'data', 'raw')
OUTPUT = os.path.join(RAW_DIR, 'batch_more_topics.txt')
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
            resp = urllib.request.urlopen(req, timeout=90)
            data = json.loads(resp.read().decode())
            queries_done += 1
            time.sleep(2)
            return data
        except Exception as e:
            print(f"    [Q{queries_done+1}] attempt {attempt+1} fail: {e}", flush=True)
            time.sleep(10 * (attempt + 1))
    return None

def name(uri):
    if not uri: return None
    n = uri.split('/')[-1].replace('_', ' ')
    if '(' in n: n = n.split('(')[0].strip()
    return n if len(n) > 1 else None

def write(f, subj, rel, obj, conf=90):
    global facts_added
    if subj and obj and len(subj) > 1 and len(obj) > 0:
        s = subj.lower().strip()[:127]
        o = obj.lower().strip()[:127]
        if s and o:
            f.write(f"{s}|{rel}|{o}|{conf}\n")
            facts_added += 1


# ═══════════════════════════════════════════════════════════
# TOPIC 1: Historical Events & Wars
# ═══════════════════════════════════════════════════════════
def historical_events(f):
    print("  [1] Historical Events & Battles...", flush=True)
    q = """SELECT ?event ?date ?place WHERE {
      ?event a dbo:MilitaryConflict .
      OPTIONAL { ?event dbo:date ?date }
      OPTIONAL { ?event dbo:place ?place }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            e = name(row.get('event',{}).get('value',''))
            if not e: continue
            write(f, e, 'is_a', 'military conflict', 90)
            p = name(row.get('place',{}).get('value',''))
            if p: write(f, e, 'location', p, 85)
            d = row.get('date',{}).get('value','')
            if d and len(d) >= 4: write(f, e, 'year', d[:4], 85)

    # Historical events (non-military)
    q2 = """SELECT ?event ?date WHERE {
      ?event a dbo:Event .
      ?event dbo:date ?date .
    } LIMIT 10000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            e = name(row.get('event',{}).get('value',''))
            if not e: continue
            write(f, e, 'is_a', 'historical event', 85)
            d = row.get('date',{}).get('value','')
            if d and len(d) >= 4: write(f, e, 'year', d[:4], 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 2: Languages of the World
# ═══════════════════════════════════════════════════════════
def languages(f):
    print("  [2] Languages...", flush=True)
    q = """SELECT ?lang ?family ?speakers WHERE {
      ?lang a dbo:Language .
      OPTIONAL { ?lang dbo:languageFamily ?family }
      OPTIONAL { ?lang dbo:numberOfSpeakers ?speakers }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            l = name(row.get('lang',{}).get('value',''))
            if not l: continue
            write(f, l, 'is_a', 'language', 95)
            fam = name(row.get('family',{}).get('value',''))
            if fam: write(f, l, 'language_family', fam, 90)
            sp = row.get('speakers',{}).get('value','')
            if sp: write(f, l, 'speakers', sp, 85)


# ═══════════════════════════════════════════════════════════
# TOPIC 3: Food & Cuisine
# ═══════════════════════════════════════════════════════════
def food(f):
    print("  [3] Food & Cuisine...", flush=True)
    q = """SELECT ?food ?country ?ingredient WHERE {
      ?food a dbo:Food .
      OPTIONAL { ?food dbo:country ?country }
      OPTIONAL { ?food dbo:ingredient ?ingredient }
    } LIMIT 8000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            fd = name(row.get('food',{}).get('value',''))
            if not fd: continue
            write(f, fd, 'is_a', 'food', 90)
            co = name(row.get('country',{}).get('value',''))
            if co: write(f, fd, 'origin_country', co, 85)
            ing = name(row.get('ingredient',{}).get('value',''))
            if ing: write(f, fd, 'ingredient', ing, 80)

# ═══════════════════════════════════════════════════════════
# TOPIC 4: Awards & Prizes
# ═══════════════════════════════════════════════════════════
def awards(f):
    print("  [4] Awards & Nobel Prizes...", flush=True)
    # Nobel laureates
    q = """SELECT ?person ?award ?year WHERE {
      ?person dbo:award ?award .
      ?award dbo:wikiPageWikiLink <http://dbpedia.org/resource/Nobel_Prize> .
      OPTIONAL { ?person dbo:birthDate ?year }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            p = name(row.get('person',{}).get('value',''))
            a = name(row.get('award',{}).get('value',''))
            if p and a:
                write(f, p, 'won_award', a, 90)
                write(f, p, 'is_a', 'award winner', 85)

    # General awards
    q2 = """SELECT ?award ?country WHERE {
      ?award a dbo:Award .
      OPTIONAL { ?award dbo:country ?country }
    } LIMIT 5000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            a = name(row.get('award',{}).get('value',''))
            if not a: continue
            write(f, a, 'is_a', 'award', 90)
            co = name(row.get('country',{}).get('value',''))
            if co: write(f, a, 'country', co, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 5: Inventions & Discoveries
# ═══════════════════════════════════════════════════════════
def inventions(f):
    print("  [5] Inventions...", flush=True)
    q = """SELECT ?inv ?inventor WHERE {
      ?inv dbo:inventor ?inventor .
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            i = name(row.get('inv',{}).get('value',''))
            p = name(row.get('inventor',{}).get('value',''))
            if i and p:
                write(f, i, 'invented_by', p, 90)
                write(f, i, 'is_a', 'invention', 85)
                write(f, p, 'invented', i, 90)


# ═══════════════════════════════════════════════════════════
# TOPIC 6: Architecture & Buildings
# ═══════════════════════════════════════════════════════════
def architecture(f):
    print("  [6] Architecture & Buildings...", flush=True)
    q = """SELECT ?building ?city ?architect ?year WHERE {
      ?building a dbo:Building .
      OPTIONAL { ?building dbo:location ?city }
      OPTIONAL { ?building dbo:architect ?architect }
      OPTIONAL { ?building dbo:openingDate ?year }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            b = name(row.get('building',{}).get('value',''))
            if not b: continue
            write(f, b, 'is_a', 'building', 90)
            c = name(row.get('city',{}).get('value',''))
            if c: write(f, b, 'located_in', c, 90)
            a = name(row.get('architect',{}).get('value',''))
            if a: write(f, b, 'designed_by', a, 85)

    # Bridges
    q2 = """SELECT ?bridge ?crosses ?length WHERE {
      ?bridge a dbo:Bridge .
      OPTIONAL { ?bridge dbo:crosses ?crosses }
      OPTIONAL { ?bridge dbo:length ?length }
    } LIMIT 5000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            b = name(row.get('bridge',{}).get('value',''))
            if not b: continue
            write(f, b, 'is_a', 'bridge', 90)
            cr = name(row.get('crosses',{}).get('value',''))
            if cr: write(f, b, 'crosses', cr, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 7: Sports Teams & Leagues
# ═══════════════════════════════════════════════════════════
def sports_teams(f):
    print("  [7] Sports Teams...", flush=True)
    # Football clubs
    q = """SELECT ?team ?city ?league ?stadium WHERE {
      ?team a dbo:SoccerClub .
      OPTIONAL { ?team dbo:ground ?stadium }
      OPTIONAL { ?team dbo:league ?league }
      OPTIONAL { ?team dbo:city ?city }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            t = name(row.get('team',{}).get('value',''))
            if not t: continue
            write(f, t, 'is_a', 'football club', 90)
            c = name(row.get('city',{}).get('value',''))
            if c: write(f, t, 'located_in', c, 90)
            lg = name(row.get('league',{}).get('value',''))
            if lg: write(f, t, 'plays_in', lg, 85)
            st = name(row.get('stadium',{}).get('value',''))
            if st: write(f, t, 'stadium', st, 85)

    # Basketball teams
    q2 = """SELECT ?team ?city ?arena WHERE {
      ?team a dbo:BasketballTeam .
      OPTIONAL { ?team dbo:city ?city }
      OPTIONAL { ?team dbo:arena ?arena }
    } LIMIT 5000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            t = name(row.get('team',{}).get('value',''))
            if not t: continue
            write(f, t, 'is_a', 'basketball team', 90)
            c = name(row.get('city',{}).get('value',''))
            if c: write(f, t, 'located_in', c, 90)


# ═══════════════════════════════════════════════════════════
# TOPIC 8: Astronomical Objects
# ═══════════════════════════════════════════════════════════
def astronomy(f):
    print("  [8] Astronomy...", flush=True)
    # Stars
    q = """SELECT ?star ?constellation ?dist WHERE {
      ?star a dbo:Star .
      OPTIONAL { ?star dbo:constellation ?constellation }
      OPTIONAL { ?star dbo:distance ?dist }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            s = name(row.get('star',{}).get('value',''))
            if not s: continue
            write(f, s, 'is_a', 'star', 90)
            c = name(row.get('constellation',{}).get('value',''))
            if c: write(f, s, 'constellation', c, 85)

    # Galaxies
    q2 = """SELECT ?galaxy ?type WHERE {
      ?galaxy a dbo:Galaxy .
      OPTIONAL { ?galaxy dbo:type ?type }
    } LIMIT 3000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            g = name(row.get('galaxy',{}).get('value',''))
            if not g: continue
            write(f, g, 'is_a', 'galaxy', 90)

    # Constellations
    q3 = """SELECT ?const WHERE {
      ?const a dbo:Constellation .
    } LIMIT 200"""
    data = dbpedia_query(q3)
    if data:
        for row in data['results']['bindings']:
            c = name(row.get('const',{}).get('value',''))
            if c: write(f, c, 'is_a', 'constellation', 95)

# ═══════════════════════════════════════════════════════════
# TOPIC 9: Chemical Compounds
# ═══════════════════════════════════════════════════════════
def chemicals(f):
    print("  [9] Chemical Compounds...", flush=True)
    q = """SELECT ?compound ?formula ?mass WHERE {
      ?compound a dbo:ChemicalCompound .
      OPTIONAL { ?compound dbo:iupacName ?formula }
      OPTIONAL { ?compound dbo:molecularWeight ?mass }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            c = name(row.get('compound',{}).get('value',''))
            if not c: continue
            write(f, c, 'is_a', 'chemical compound', 90)
            fm = row.get('formula',{}).get('value','')
            if fm and len(fm) < 100: write(f, c, 'iupac_name', fm, 85)
            m = row.get('mass',{}).get('value','')
            if m: write(f, c, 'molecular_weight', m, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 10: Religions & Philosophies
# ═══════════════════════════════════════════════════════════
def religions(f):
    print("  [10] Religions...", flush=True)
    q = """SELECT ?religion ?founder ?origin WHERE {
      { ?religion a dbo:ReligiousOrganisation } UNION { ?religion a yago:Religion108081668 }
      OPTIONAL { ?religion dbo:foundedBy ?founder }
      OPTIONAL { ?religion dbo:country ?origin }
    } LIMIT 3000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            r = name(row.get('religion',{}).get('value',''))
            if not r: continue
            write(f, r, 'is_a', 'religious organization', 85)
            fo = name(row.get('founder',{}).get('value',''))
            if fo: write(f, r, 'founded_by', fo, 85)


# ═══════════════════════════════════════════════════════════
# TOPIC 11: TV Shows & Series
# ═══════════════════════════════════════════════════════════
def tv_shows(f):
    print("  [11] TV Shows...", flush=True)
    q = """SELECT ?show ?creator ?network ?genre WHERE {
      ?show a dbo:TelevisionShow .
      OPTIONAL { ?show dbo:creator ?creator }
      OPTIONAL { ?show dbo:network ?network }
      OPTIONAL { ?show dbo:genre ?genre }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            s = name(row.get('show',{}).get('value',''))
            if not s: continue
            write(f, s, 'is_a', 'tv show', 90)
            cr = name(row.get('creator',{}).get('value',''))
            if cr: write(f, s, 'created_by', cr, 85)
            n = name(row.get('network',{}).get('value',''))
            if n: write(f, s, 'network', n, 85)
            g = name(row.get('genre',{}).get('value',''))
            if g: write(f, s, 'genre', g, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 12: Video Games
# ═══════════════════════════════════════════════════════════
def video_games(f):
    print("  [12] Video Games...", flush=True)
    q = """SELECT ?game ?developer ?publisher ?genre WHERE {
      ?game a dbo:VideoGame .
      OPTIONAL { ?game dbo:developer ?developer }
      OPTIONAL { ?game dbo:publisher ?publisher }
      OPTIONAL { ?game dbo:genre ?genre }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            g = name(row.get('game',{}).get('value',''))
            if not g: continue
            write(f, g, 'is_a', 'video game', 90)
            d = name(row.get('developer',{}).get('value',''))
            if d: write(f, g, 'developed_by', d, 90)
            p = name(row.get('publisher',{}).get('value',''))
            if p: write(f, g, 'published_by', p, 85)
            gen = name(row.get('genre',{}).get('value',''))
            if gen: write(f, g, 'genre', gen, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 13: Airports & Airlines
# ═══════════════════════════════════════════════════════════
def aviation(f):
    print("  [13] Airports & Airlines...", flush=True)
    q = """SELECT ?airport ?city ?country ?iata WHERE {
      ?airport a dbo:Airport .
      OPTIONAL { ?airport dbo:city ?city }
      OPTIONAL { ?airport dbo:country ?country }
      OPTIONAL { ?airport dbo:iataLocationIdentifier ?iata }
    } LIMIT 8000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            a = name(row.get('airport',{}).get('value',''))
            if not a: continue
            write(f, a, 'is_a', 'airport', 90)
            c = name(row.get('city',{}).get('value',''))
            if c: write(f, a, 'located_in', c, 90)
            co = name(row.get('country',{}).get('value',''))
            if co: write(f, a, 'country', co, 85)
            iata = row.get('iata',{}).get('value','')
            if iata: write(f, a, 'iata_code', iata, 95)

    # Airlines
    q2 = """SELECT ?airline ?hub ?country WHERE {
      ?airline a dbo:Airline .
      OPTIONAL { ?airline dbo:hubAirport ?hub }
      OPTIONAL { ?airline dbo:country ?country }
    } LIMIT 3000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            al = name(row.get('airline',{}).get('value',''))
            if not al: continue
            write(f, al, 'is_a', 'airline', 90)
            h = name(row.get('hub',{}).get('value',''))
            if h: write(f, al, 'hub', h, 85)
            co = name(row.get('country',{}).get('value',''))
            if co: write(f, al, 'country', co, 90)


# ═══════════════════════════════════════════════════════════
# TOPIC 14: Musical Instruments & Genres
# ═══════════════════════════════════════════════════════════
def music(f):
    print("  [14] Music (instruments & genres)...", flush=True)
    q = """SELECT ?instrument ?family WHERE {
      ?instrument a dbo:Instrument .
      OPTIONAL { ?instrument dbo:instrumentFamily ?family }
    } LIMIT 2000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            i = name(row.get('instrument',{}).get('value',''))
            if not i: continue
            write(f, i, 'is_a', 'musical instrument', 90)
            fam = name(row.get('family',{}).get('value',''))
            if fam: write(f, i, 'instrument_family', fam, 85)

    # Music genres
    q2 = """SELECT ?genre ?origin WHERE {
      ?genre a dbo:MusicGenre .
      OPTIONAL { ?genre dbo:stylisticOrigin ?origin }
    } LIMIT 3000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            g = name(row.get('genre',{}).get('value',''))
            if not g: continue
            write(f, g, 'is_a', 'music genre', 90)
            o = name(row.get('origin',{}).get('value',''))
            if o: write(f, g, 'derived_from', o, 80)

# ═══════════════════════════════════════════════════════════
# TOPIC 15: Medications & Drugs
# ═══════════════════════════════════════════════════════════
def medications(f):
    print("  [15] Medications...", flush=True)
    q = """SELECT ?drug ?use WHERE {
      ?drug a dbo:Drug .
      OPTIONAL { ?drug dbo:medicalUse ?use }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            d = name(row.get('drug',{}).get('value',''))
            if not d: continue
            write(f, d, 'is_a', 'medication', 90)

# ═══════════════════════════════════════════════════════════
# TOPIC 16: Plants & Trees
# ═══════════════════════════════════════════════════════════
def plants(f):
    print("  [16] Plants...", flush=True)
    q = """SELECT ?plant ?family WHERE {
      ?plant a dbo:Plant .
      OPTIONAL { ?plant dbo:family ?family }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            p = name(row.get('plant',{}).get('value',''))
            if not p: continue
            write(f, p, 'is_a', 'plant', 90)
            fam = name(row.get('family',{}).get('value',''))
            if fam: write(f, p, 'family', fam, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 17: Holidays & Festivals
# ═══════════════════════════════════════════════════════════
def holidays(f):
    print("  [17] Holidays & Festivals...", flush=True)
    q = """SELECT ?holiday ?country ?date WHERE {
      ?holiday a dbo:Holiday .
      OPTIONAL { ?holiday dbo:country ?country }
      OPTIONAL { ?holiday dbo:date ?date }
    } LIMIT 3000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            h = name(row.get('holiday',{}).get('value',''))
            if not h: continue
            write(f, h, 'is_a', 'holiday', 90)
            co = name(row.get('country',{}).get('value',''))
            if co: write(f, h, 'celebrated_in', co, 85)


# ═══════════════════════════════════════════════════════════
# TOPIC 18: Museums & Art
# ═══════════════════════════════════════════════════════════
def museums(f):
    print("  [18] Museums & Artworks...", flush=True)
    q = """SELECT ?museum ?city ?country WHERE {
      ?museum a dbo:Museum .
      OPTIONAL { ?museum dbo:city ?city }
      OPTIONAL { ?museum dbo:country ?country }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            m = name(row.get('museum',{}).get('value',''))
            if not m: continue
            write(f, m, 'is_a', 'museum', 90)
            c = name(row.get('city',{}).get('value',''))
            if c: write(f, m, 'located_in', c, 90)

    # Artworks / Paintings
    q2 = """SELECT ?artwork ?artist ?museum WHERE {
      ?artwork a dbo:Artwork .
      OPTIONAL { ?artwork dbo:author ?artist }
      OPTIONAL { ?artwork dbo:museum ?museum }
    } LIMIT 5000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            a = name(row.get('artwork',{}).get('value',''))
            if not a: continue
            write(f, a, 'is_a', 'artwork', 85)
            ar = name(row.get('artist',{}).get('value',''))
            if ar: write(f, a, 'created_by', ar, 90)
            m = name(row.get('museum',{}).get('value',''))
            if m: write(f, a, 'displayed_in', m, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 19: Currencies & Economics
# ═══════════════════════════════════════════════════════════
def economics(f):
    print("  [19] Currencies & Economics...", flush=True)
    q = """SELECT ?currency ?country ?symbol WHERE {
      ?currency a dbo:Currency .
      OPTIONAL { ?currency dbo:usingCountry ?country }
      OPTIONAL { ?currency dbp:symbol ?symbol }
    } LIMIT 1000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            c = name(row.get('currency',{}).get('value',''))
            if not c: continue
            write(f, c, 'is_a', 'currency', 90)
            co = name(row.get('country',{}).get('value',''))
            if co: write(f, c, 'used_in', co, 90)

# ═══════════════════════════════════════════════════════════
# TOPIC 20: Spacecraft & Space Missions
# ═══════════════════════════════════════════════════════════
def space_missions(f):
    print("  [20] Space Missions...", flush=True)
    q = """SELECT ?mission ?operator ?launchDate WHERE {
      ?mission a dbo:SpaceMission .
      OPTIONAL { ?mission dbo:operator ?operator }
      OPTIONAL { ?mission dbo:launchDate ?launchDate }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            m = name(row.get('mission',{}).get('value',''))
            if not m: continue
            write(f, m, 'is_a', 'space mission', 90)
            op = name(row.get('operator',{}).get('value',''))
            if op: write(f, m, 'operated_by', op, 85)
            ld = row.get('launchDate',{}).get('value','')
            if ld and len(ld) >= 4: write(f, m, 'launch_year', ld[:4], 85)

    # Spacecraft
    q2 = """SELECT ?craft ?manufacturer WHERE {
      ?craft a dbo:Spacecraft .
      OPTIONAL { ?craft dbo:manufacturer ?manufacturer }
    } LIMIT 3000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            c = name(row.get('craft',{}).get('value',''))
            if not c: continue
            write(f, c, 'is_a', 'spacecraft', 90)
            m = name(row.get('manufacturer',{}).get('value',''))
            if m: write(f, c, 'manufactured_by', m, 85)


# ═══════════════════════════════════════════════════════════
# TOPIC 21: Philosophers & Theories
# ═══════════════════════════════════════════════════════════
def philosophy(f):
    print("  [21] Philosophy & Theories...", flush=True)
    q = """SELECT ?person ?nationality ?era WHERE {
      ?person a dbo:Philosopher .
      OPTIONAL { ?person dbo:nationality ?nationality }
      OPTIONAL { ?person dbo:era ?era }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            p = name(row.get('person',{}).get('value',''))
            if not p: continue
            write(f, p, 'is_a', 'philosopher', 95)
            n = name(row.get('nationality',{}).get('value',''))
            if n: write(f, p, 'nationality', n, 90)
            e = name(row.get('era',{}).get('value',''))
            if e: write(f, p, 'era', e, 80)

# ═══════════════════════════════════════════════════════════
# TOPIC 22: Insects & Marine Life
# ═══════════════════════════════════════════════════════════
def marine_life(f):
    print("  [22] Marine Life & Insects...", flush=True)
    q = """SELECT ?creature ?family WHERE {
      ?creature a dbo:Fish .
      OPTIONAL { ?creature dbo:family ?family }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            c = name(row.get('creature',{}).get('value',''))
            if not c: continue
            write(f, c, 'is_a', 'fish', 90)
            fam = name(row.get('family',{}).get('value',''))
            if fam: write(f, c, 'family', fam, 85)

    q2 = """SELECT ?insect ?order WHERE {
      ?insect a dbo:Insect .
      OPTIONAL { ?insect dbo:order ?order }
    } LIMIT 5000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            i = name(row.get('insect',{}).get('value',''))
            if not i: continue
            write(f, i, 'is_a', 'insect', 90)
            o = name(row.get('order',{}).get('value',''))
            if o: write(f, i, 'order', o, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 23: Newspapers & Media
# ═══════════════════════════════════════════════════════════
def media(f):
    print("  [23] Newspapers & Media...", flush=True)
    q = """SELECT ?paper ?city ?language WHERE {
      ?paper a dbo:Newspaper .
      OPTIONAL { ?paper dbo:city ?city }
      OPTIONAL { ?paper dbo:language ?language }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            p = name(row.get('paper',{}).get('value',''))
            if not p: continue
            write(f, p, 'is_a', 'newspaper', 85)
            c = name(row.get('city',{}).get('value',''))
            if c: write(f, p, 'published_in', c, 85)
            l = name(row.get('language',{}).get('value',''))
            if l: write(f, p, 'language', l, 85)

    # Radio stations
    q2 = """SELECT ?station ?city ?freq WHERE {
      ?station a dbo:RadioStation .
      OPTIONAL { ?station dbo:city ?city }
      OPTIONAL { ?station dbo:frequency ?freq }
    } LIMIT 5000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            s = name(row.get('station',{}).get('value',''))
            if not s: continue
            write(f, s, 'is_a', 'radio station', 85)
            c = name(row.get('city',{}).get('value',''))
            if c: write(f, s, 'located_in', c, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 24: Wines & Beverages
# ═══════════════════════════════════════════════════════════
def beverages(f):
    print("  [24] Beverages & Wine...", flush=True)
    q = """SELECT ?beverage ?country ?type WHERE {
      ?beverage a dbo:Beverage .
      OPTIONAL { ?beverage dbo:country ?country }
      OPTIONAL { ?beverage dbo:type ?type }
    } LIMIT 3000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            b = name(row.get('beverage',{}).get('value',''))
            if not b: continue
            write(f, b, 'is_a', 'beverage', 85)
            co = name(row.get('country',{}).get('value',''))
            if co: write(f, b, 'origin_country', co, 80)

    # Wine regions
    q2 = """SELECT ?region ?country WHERE {
      ?region a dbo:WineRegion .
      OPTIONAL { ?region dbo:country ?country }
    } LIMIT 2000"""
    data = dbpedia_query(q2)
    if data:
        for row in data['results']['bindings']:
            r = name(row.get('region',{}).get('value',''))
            if not r: continue
            write(f, r, 'is_a', 'wine region', 80)
            co = name(row.get('country',{}).get('value',''))
            if co: write(f, r, 'located_in', co, 80)


# ═══════════════════════════════════════════════════════════
# TOPIC 25: Motorsport & Racing
# ═══════════════════════════════════════════════════════════
def motorsport(f):
    print("  [25] Motorsport...", flush=True)
    q = """SELECT ?race ?circuit ?country WHERE {
      ?race a dbo:Race .
      OPTIONAL { ?race dbo:circuit ?circuit }
      OPTIONAL { ?race dbo:country ?country }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            r = name(row.get('race',{}).get('value',''))
            if not r: continue
            write(f, r, 'is_a', 'race', 85)
            ci = name(row.get('circuit',{}).get('value',''))
            if ci: write(f, r, 'held_at', ci, 85)
            co = name(row.get('country',{}).get('value',''))
            if co: write(f, r, 'country', co, 85)

# ═══════════════════════════════════════════════════════════
# TOPIC 26: Ships & Naval
# ═══════════════════════════════════════════════════════════
def ships(f):
    print("  [26] Ships...", flush=True)
    q = """SELECT ?ship ?type ?operator WHERE {
      ?ship a dbo:Ship .
      OPTIONAL { ?ship dbo:type ?type }
      OPTIONAL { ?ship dbo:operator ?operator }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            s = name(row.get('ship',{}).get('value',''))
            if not s: continue
            write(f, s, 'is_a', 'ship', 85)
            t = name(row.get('type',{}).get('value',''))
            if t: write(f, s, 'ship_type', t, 80)
            op = name(row.get('operator',{}).get('value',''))
            if op: write(f, s, 'operated_by', op, 80)

# ═══════════════════════════════════════════════════════════
# TOPIC 27: Software & Operating Systems
# ═══════════════════════════════════════════════════════════
def software(f):
    print("  [27] Software...", flush=True)
    q = """SELECT ?sw ?developer ?license WHERE {
      ?sw a dbo:Software .
      OPTIONAL { ?sw dbo:developer ?developer }
      OPTIONAL { ?sw dbo:license ?license }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            s = name(row.get('sw',{}).get('value',''))
            if not s: continue
            write(f, s, 'is_a', 'software', 90)
            d = name(row.get('developer',{}).get('value',''))
            if d: write(f, s, 'developed_by', d, 90)
            l = name(row.get('license',{}).get('value',''))
            if l: write(f, s, 'license', l, 80)

# ═══════════════════════════════════════════════════════════
# TOPIC 28: Minerals & Rocks
# ═══════════════════════════════════════════════════════════
def minerals(f):
    print("  [28] Minerals...", flush=True)
    q = """SELECT ?mineral ?formula ?color WHERE {
      ?mineral a dbo:Mineral .
      OPTIONAL { ?mineral dbo:chemicalFormula ?formula }
      OPTIONAL { ?mineral dbo:color ?color }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            m = name(row.get('mineral',{}).get('value',''))
            if not m: continue
            write(f, m, 'is_a', 'mineral', 90)
            fm = row.get('formula',{}).get('value','')
            if fm: write(f, m, 'chemical_formula', fm, 85)
            co = name(row.get('color',{}).get('value',''))
            if co: write(f, m, 'color', co, 80)


# ═══════════════════════════════════════════════════════════
# TOPIC 29: Automobiles
# ═══════════════════════════════════════════════════════════
def automobiles(f):
    print("  [29] Automobiles...", flush=True)
    q = """SELECT ?car ?manufacturer ?class WHERE {
      ?car a dbo:Automobile .
      OPTIONAL { ?car dbo:manufacturer ?manufacturer }
      OPTIONAL { ?car dbo:class ?class }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            c = name(row.get('car',{}).get('value',''))
            if not c: continue
            write(f, c, 'is_a', 'automobile', 85)
            m = name(row.get('manufacturer',{}).get('value',''))
            if m: write(f, c, 'manufactured_by', m, 90)
            cl = name(row.get('class',{}).get('value',''))
            if cl: write(f, c, 'vehicle_class', cl, 80)

# ═══════════════════════════════════════════════════════════
# TOPIC 30: Dinosaurs & Fossils
# ═══════════════════════════════════════════════════════════
def dinosaurs(f):
    print("  [30] Dinosaurs & Prehistoric...", flush=True)
    q = """SELECT ?dino ?period ?family WHERE {
      ?dino a dbo:Dinosaur .
      OPTIONAL { ?dino dbp:period ?period }
      OPTIONAL { ?dino dbo:family ?family }
    } LIMIT 3000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            d = name(row.get('dino',{}).get('value',''))
            if not d: continue
            write(f, d, 'is_a', 'dinosaur', 90)
            p = row.get('period',{}).get('value','')
            if p and not p.startswith('http'): write(f, d, 'period', p.lower(), 80)
            fam = name(row.get('family',{}).get('value',''))
            if fam: write(f, d, 'family', fam, 85)

# ═══════════════════════════════════════════════════════════
# PROGRAMMATIC: Math, Physics, Geography, Commonsense
# ═══════════════════════════════════════════════════════════
def extra_programmatic(f):
    print("  [BONUS] Extra programmatic facts...", flush=True)

    # World capitals (comprehensive, not dependent on API)
    capitals = [
        ("afghanistan","kabul"),("albania","tirana"),("algeria","algiers"),
        ("andorra","andorra la vella"),("angola","luanda"),("argentina","buenos aires"),
        ("armenia","yerevan"),("australia","canberra"),("austria","vienna"),
        ("azerbaijan","baku"),("bahamas","nassau"),("bahrain","manama"),
        ("bangladesh","dhaka"),("barbados","bridgetown"),("belarus","minsk"),
        ("belgium","brussels"),("belize","belmopan"),("benin","porto-novo"),
        ("bhutan","thimphu"),("bolivia","sucre"),("brazil","brasilia"),
        ("brunei","bandar seri begawan"),("bulgaria","sofia"),("cambodia","phnom penh"),
        ("cameroon","yaounde"),("canada","ottawa"),("chad","ndjamena"),
        ("chile","santiago"),("china","beijing"),("colombia","bogota"),
        ("costa rica","san jose"),("croatia","zagreb"),("cuba","havana"),
        ("cyprus","nicosia"),("czech republic","prague"),("denmark","copenhagen"),
        ("dominican republic","santo domingo"),("ecuador","quito"),("egypt","cairo"),
        ("el salvador","san salvador"),("estonia","tallinn"),("ethiopia","addis ababa"),
        ("fiji","suva"),("finland","helsinki"),("france","paris"),
        ("gabon","libreville"),("georgia","tbilisi"),("germany","berlin"),
        ("ghana","accra"),("greece","athens"),("guatemala","guatemala city"),
        ("haiti","port-au-prince"),("honduras","tegucigalpa"),("hungary","budapest"),
        ("iceland","reykjavik"),("india","new delhi"),("indonesia","jakarta"),
        ("iran","tehran"),("iraq","baghdad"),("ireland","dublin"),
        ("israel","jerusalem"),("italy","rome"),("jamaica","kingston"),
        ("japan","tokyo"),("jordan","amman"),("kazakhstan","astana"),
        ("kenya","nairobi"),("north korea","pyongyang"),("south korea","seoul"),
        ("kuwait","kuwait city"),("laos","vientiane"),("latvia","riga"),
        ("lebanon","beirut"),("libya","tripoli"),("lithuania","vilnius"),
        ("luxembourg","luxembourg city"),("madagascar","antananarivo"),
        ("malaysia","kuala lumpur"),("mali","bamako"),("malta","valletta"),
        ("mexico","mexico city"),("mongolia","ulaanbaatar"),("morocco","rabat"),
        ("mozambique","maputo"),("myanmar","naypyidaw"),("nepal","kathmandu"),
        ("netherlands","amsterdam"),("new zealand","wellington"),
        ("nicaragua","managua"),("niger","niamey"),("nigeria","abuja"),
        ("norway","oslo"),("oman","muscat"),("pakistan","islamabad"),
        ("panama","panama city"),("paraguay","asuncion"),("peru","lima"),
        ("philippines","manila"),("poland","warsaw"),("portugal","lisbon"),
        ("qatar","doha"),("romania","bucharest"),("russia","moscow"),
        ("saudi arabia","riyadh"),("senegal","dakar"),("serbia","belgrade"),
        ("singapore","singapore"),("slovakia","bratislava"),("slovenia","ljubljana"),
        ("somalia","mogadishu"),("south africa","pretoria"),("spain","madrid"),
        ("sri lanka","colombo"),("sudan","khartoum"),("sweden","stockholm"),
        ("switzerland","bern"),("syria","damascus"),("taiwan","taipei"),
        ("tanzania","dodoma"),("thailand","bangkok"),("tunisia","tunis"),
        ("turkey","ankara"),("uganda","kampala"),("ukraine","kyiv"),
        ("united arab emirates","abu dhabi"),("united kingdom","london"),
        ("united states","washington d.c."),("uruguay","montevideo"),
        ("uzbekistan","tashkent"),("venezuela","caracas"),("vietnam","hanoi"),
        ("yemen","sanaa"),("zambia","lusaka"),("zimbabwe","harare"),
    ]
    for country, capital in capitals:
        write(f, country, 'capital', capital, 99)
        write(f, capital, 'capital_of', country, 99)
        write(f, country, 'is_a', 'country', 99)
        write(f, capital, 'is_a', 'capital city', 95)

    # Math concepts
    math_concepts = [
        ("circle", "has_property", "360 degrees"),
        ("triangle", "has_property", "3 sides"),
        ("triangle", "angle_sum", "180 degrees"),
        ("square", "has_property", "4 equal sides"),
        ("pentagon", "has_property", "5 sides"),
        ("hexagon", "has_property", "6 sides"),
        ("sphere", "surface_area_formula", "4*pi*r^2"),
        ("sphere", "volume_formula", "4/3*pi*r^3"),
        ("cylinder", "volume_formula", "pi*r^2*h"),
        ("cone", "volume_formula", "1/3*pi*r^2*h"),
        ("pythagorean theorem", "formula", "a^2 + b^2 = c^2"),
        ("quadratic formula", "formula", "(-b ± sqrt(b^2-4ac)) / 2a"),
        ("euler identity", "formula", "e^(i*pi) + 1 = 0"),
        ("fibonacci sequence", "starts_with", "0 1 1 2 3 5 8 13 21"),
        ("prime numbers", "first_ten", "2 3 5 7 11 13 17 19 23 29"),
    ]
    for s, r, o in math_concepts:
        write(f, s, r, o, 99)

    # Famous equations / laws
    laws = [
        ("newton first law", "states", "an object at rest stays at rest unless acted on by a force"),
        ("newton second law", "formula", "f = m * a"),
        ("newton third law", "states", "every action has an equal and opposite reaction"),
        ("einstein mass-energy", "formula", "e = m * c^2"),
        ("ohm law", "formula", "v = i * r"),
        ("coulomb law", "describes", "force between electric charges"),
        ("boyle law", "formula", "p1*v1 = p2*v2"),
        ("ideal gas law", "formula", "pv = nrt"),
        ("archimedes principle", "states", "buoyant force equals weight of displaced fluid"),
        ("heisenberg uncertainty", "states", "cannot know both position and momentum exactly"),
        ("schrodinger equation", "describes", "quantum state of a system"),
        ("maxwell equations", "describes", "electromagnetism"),
        ("thermodynamics first law", "states", "energy cannot be created or destroyed"),
        ("thermodynamics second law", "states", "entropy of isolated system always increases"),
        ("thermodynamics third law", "states", "entropy approaches zero as temperature approaches absolute zero"),
    ]
    for s, r, o in laws:
        write(f, s, r, o, 99)

    # Body parts & organs
    body = [
        ("heart", "function", "pumps blood"),
        ("lungs", "function", "gas exchange"),
        ("brain", "function", "controls nervous system"),
        ("liver", "function", "detoxification and metabolism"),
        ("kidney", "function", "filters blood"),
        ("stomach", "function", "digests food"),
        ("pancreas", "function", "produces insulin"),
        ("skin", "is_a", "largest organ"),
        ("femur", "is_a", "longest bone"),
        ("human body", "has_bones", "206"),
        ("human body", "has_muscles", "over 600"),
        ("human body", "blood_volume", "about 5 liters"),
        ("dna", "stands_for", "deoxyribonucleic acid"),
        ("rna", "stands_for", "ribonucleic acid"),
    ]
    for s, r, o in body:
        write(f, s, r, o, 99)

    # Colors and wavelengths
    colors = [
        ("red", "wavelength_nm", "620-750"), ("orange", "wavelength_nm", "590-620"),
        ("yellow", "wavelength_nm", "570-590"), ("green", "wavelength_nm", "495-570"),
        ("blue", "wavelength_nm", "450-495"), ("violet", "wavelength_nm", "380-450"),
    ]
    for s, r, o in colors:
        write(f, s, r, o, 95)
        write(f, s, 'is_a', 'color', 99)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    start = time.time()
    print("=" * 60)
    print("  AXIMA Knowledge Expansion — MORE TOPICS")
    print("  30 new topic areas via DBpedia + Programmatic")
    print("=" * 60, flush=True)

    with open(OUTPUT, 'w') as f:
        historical_events(f)
        languages(f)
        food(f)
        awards(f)
        inventions(f)
        architecture(f)
        sports_teams(f)
        astronomy(f)
        chemicals(f)
        religions(f)
        tv_shows(f)
        video_games(f)
        aviation(f)
        music(f)
        medications(f)
        plants(f)
        holidays(f)
        museums(f)
        economics(f)
        space_missions(f)
        philosophy(f)
        marine_life(f)
        media(f)
        beverages(f)
        motorsport(f)
        ships(f)
        software(f)
        minerals(f)
        automobiles(f)
        dinosaurs(f)
        extra_programmatic(f)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  New facts: {facts_added:,}")
    print(f"  DBpedia queries: {queries_done}")
    print(f"  Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"  File: {OUTPUT}")
    print(f"  Size: {os.path.getsize(OUTPUT)/1e6:.1f} MB")
    print(f"{'=' * 60}", flush=True)
