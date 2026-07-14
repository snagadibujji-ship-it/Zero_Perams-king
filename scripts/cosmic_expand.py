#!/usr/bin/env python3
"""
COSMIC-LEVEL Knowledge Expansion — MAX EVERYTHING.
Run for as long as possible, extract EVERY fact available.
"""
import urllib.request, urllib.parse, json, time, os, sys, gzip, csv

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPTS_DIR, '..', 'data', 'raw')
OUTPUT = os.path.join(RAW_DIR, 'batch_cosmic.txt')
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
            print(f"    [Q{queries_done+1}] fail: {e}", flush=True)
            time.sleep(5 * (attempt + 1))
    return None

def n(uri):
    if not uri: return None
    nm = uri.split('/')[-1].replace('_', ' ')
    if '(' in nm: nm = nm.split('(')[0].strip()
    return nm if len(nm) > 1 and len(nm) < 128 else None

def w(f, subj, rel, obj, conf=90):
    global facts_added
    if subj and obj and len(subj) > 1 and len(obj) > 0:
        s = subj.lower().strip()[:127]
        o = obj.lower().strip()[:127]
        if s and o and len(s) > 1:
            f.write(f"{s}|{rel}|{o}|{conf}\n")
            facts_added += 1


# ═══════════════════════════════════════════════════════════
# EDUCATION — Schools, Degrees, Subjects, Learning
# ═══════════════════════════════════════════════════════════
def education(f):
    print("\n[EDUCATION] Schools, subjects, degrees, theories...", flush=True)

    # Universities with details
    for offset in range(0, 50000, 10000):
        q = f"""SELECT ?uni ?city ?country ?students ?established WHERE {{
          ?uni a dbo:University .
          OPTIONAL {{ ?uni dbo:city ?city }}
          OPTIONAL {{ ?uni dbo:country ?country }}
          OPTIONAL {{ ?uni dbo:numberOfStudents ?students }}
          OPTIONAL {{ ?uni dbo:established ?established }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            u = n(row.get('uni',{}).get('value',''))
            if not u: continue
            w(f, u, 'is_a', 'university', 90)
            c = n(row.get('city',{}).get('value',''))
            if c: w(f, u, 'located_in', c, 90)
            co = n(row.get('country',{}).get('value',''))
            if co: w(f, u, 'country', co, 90)
            st = row.get('students',{}).get('value','')
            if st: w(f, u, 'students', st, 80)
            est = row.get('established',{}).get('value','')
            if est and len(est)>=4: w(f, u, 'established', est[:4], 85)

    # Schools
    for offset in range(0, 30000, 10000):
        q = f"""SELECT ?school ?city ?country WHERE {{
          ?school a dbo:School .
          OPTIONAL {{ ?school dbo:city ?city }}
          OPTIONAL {{ ?school dbo:country ?country }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            s = n(row.get('school',{}).get('value',''))
            if not s: continue
            w(f, s, 'is_a', 'school', 85)
            c = n(row.get('city',{}).get('value',''))
            if c: w(f, s, 'located_in', c, 85)
            co = n(row.get('country',{}).get('value',''))
            if co: w(f, s, 'country', co, 85)

    # Academic subjects & fields
    print("  Academic disciplines...", flush=True)
    q = """SELECT ?field ?broader WHERE {
      ?field a dbo:AcademicSubject .
      OPTIONAL { ?field dbo:academicDiscipline ?broader }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            field = n(row.get('field',{}).get('value',''))
            if not field: continue
            w(f, field, 'is_a', 'academic subject', 90)
            b = n(row.get('broader',{}).get('value',''))
            if b: w(f, field, 'subfield_of', b, 85)

    # Programmatic: education hierarchy
    subjects = {
        "mathematics": ["algebra", "calculus", "geometry", "statistics", "number theory", "topology", "linear algebra", "differential equations", "discrete mathematics", "combinatorics", "graph theory", "probability theory", "mathematical logic", "abstract algebra", "real analysis", "complex analysis", "numerical analysis"],
        "physics": ["mechanics", "thermodynamics", "electromagnetism", "optics", "quantum mechanics", "relativity", "nuclear physics", "particle physics", "astrophysics", "condensed matter physics", "plasma physics", "fluid dynamics", "acoustics", "statistical mechanics"],
        "chemistry": ["organic chemistry", "inorganic chemistry", "physical chemistry", "analytical chemistry", "biochemistry", "electrochemistry", "polymer chemistry", "materials science", "photochemistry", "computational chemistry", "nuclear chemistry", "geochemistry"],
        "biology": ["molecular biology", "cell biology", "genetics", "ecology", "evolution", "microbiology", "zoology", "botany", "anatomy", "physiology", "neuroscience", "immunology", "bioinformatics", "marine biology", "paleontology"],
        "computer science": ["algorithms", "data structures", "artificial intelligence", "machine learning", "computer networks", "databases", "operating systems", "software engineering", "computer graphics", "cryptography", "distributed systems", "compiler design", "computer vision", "natural language processing", "robotics", "cybersecurity", "cloud computing", "quantum computing"],
        "engineering": ["mechanical engineering", "electrical engineering", "civil engineering", "chemical engineering", "aerospace engineering", "biomedical engineering", "environmental engineering", "industrial engineering", "materials engineering", "nuclear engineering", "software engineering"],
        "medicine": ["anatomy", "pharmacology", "pathology", "surgery", "internal medicine", "pediatrics", "psychiatry", "radiology", "anesthesiology", "emergency medicine", "obstetrics", "ophthalmology", "cardiology", "neurology", "oncology", "dermatology"],
        "social sciences": ["psychology", "sociology", "anthropology", "economics", "political science", "linguistics", "geography", "archaeology", "criminology", "demography", "education theory", "social work"],
        "humanities": ["philosophy", "history", "literature", "art history", "music theory", "theology", "ethics", "aesthetics", "logic", "metaphysics", "epistemology", "classics"],
        "earth sciences": ["geology", "meteorology", "oceanography", "seismology", "volcanology", "mineralogy", "petrology", "hydrology", "glaciology", "paleoclimatology"],
        "business": ["accounting", "finance", "marketing", "management", "entrepreneurship", "supply chain", "human resources", "business analytics", "international business", "organizational behavior"],
        "law": ["criminal law", "civil law", "constitutional law", "international law", "corporate law", "environmental law", "intellectual property law", "human rights law", "tax law", "family law"],
    }
    for field, subs in subjects.items():
        w(f, field, 'is_a', 'academic field', 99)
        for sub in subs:
            w(f, sub, 'is_a', 'academic subject', 95)
            w(f, sub, 'subfield_of', field, 95)
            w(f, sub, 'studied_in', 'university', 80)

    # Degrees
    degrees = ["bachelor of science", "bachelor of arts", "master of science", "master of arts",
               "master of business administration", "doctor of philosophy", "doctor of medicine",
               "juris doctor", "master of engineering", "bachelor of engineering",
               "master of education", "doctor of education", "master of fine arts",
               "master of public health", "master of social work", "bachelor of music"]
    for d in degrees:
        w(f, d, 'is_a', 'academic degree', 95)

    # Learning theories
    theories = [
        ("behaviorism", "pioneer", "b.f. skinner"),
        ("constructivism", "pioneer", "jean piaget"),
        ("social learning theory", "pioneer", "albert bandura"),
        ("cognitive load theory", "pioneer", "john sweller"),
        ("zone of proximal development", "pioneer", "lev vygotsky"),
        ("multiple intelligences", "pioneer", "howard gardner"),
        ("bloom taxonomy", "pioneer", "benjamin bloom"),
        ("maslow hierarchy of needs", "pioneer", "abraham maslow"),
        ("montessori method", "pioneer", "maria montessori"),
        ("experiential learning", "pioneer", "david kolb"),
    ]
    for theory, rel, person in theories:
        w(f, theory, 'is_a', 'learning theory', 95)
        w(f, theory, rel, person, 90)


# ═══════════════════════════════════════════════════════════
# COSMIC / SPACE / ASTRONOMY — MAX
# ═══════════════════════════════════════════════════════════
def cosmic(f):
    print("\n[COSMIC] Stars, galaxies, nebulae, missions, cosmology...", flush=True)

    # Stars
    for offset in range(0, 30000, 10000):
        q = f"""SELECT ?star ?constellation ?spectral ?dist WHERE {{
          ?star a dbo:Star .
          OPTIONAL {{ ?star dbo:constellation ?constellation }}
          OPTIONAL {{ ?star dbp:class ?spectral }}
          OPTIONAL {{ ?star dbo:distance ?dist }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            s = n(row.get('star',{}).get('value',''))
            if not s: continue
            w(f, s, 'is_a', 'star', 90)
            c = n(row.get('constellation',{}).get('value',''))
            if c: w(f, s, 'constellation', c, 85)

    # Galaxies
    for offset in range(0, 20000, 10000):
        q = f"""SELECT ?galaxy ?type ?constellation WHERE {{
          ?galaxy a dbo:Galaxy .
          OPTIONAL {{ ?galaxy dbo:type ?type }}
          OPTIONAL {{ ?galaxy dbo:constellation ?constellation }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            g = n(row.get('galaxy',{}).get('value',''))
            if not g: continue
            w(f, g, 'is_a', 'galaxy', 90)
            t = row.get('type',{}).get('value','')
            if t and not t.startswith('http'): w(f, g, 'galaxy_type', t.lower()[:60], 80)

    # Nebulae
    q = """SELECT ?nebula ?constellation ?type WHERE {
      ?nebula a dbo:Nebula .
      OPTIONAL { ?nebula dbo:constellation ?constellation }
      OPTIONAL { ?nebula dbo:type ?type }
    } LIMIT 5000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            nb = n(row.get('nebula',{}).get('value',''))
            if not nb: continue
            w(f, nb, 'is_a', 'nebula', 90)
            c = n(row.get('constellation',{}).get('value',''))
            if c: w(f, nb, 'constellation', c, 85)

    # Constellations
    q = """SELECT ?const WHERE { ?const a dbo:Constellation . } LIMIT 500"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            c = n(row.get('const',{}).get('value',''))
            if c: w(f, c, 'is_a', 'constellation', 95)

    # Asteroids
    for offset in range(0, 30000, 10000):
        q = f"""SELECT ?asteroid ?discoverer ?epoch WHERE {{
          ?asteroid a dbo:Asteroid .
          OPTIONAL {{ ?asteroid dbo:discoverer ?discoverer }}
          OPTIONAL {{ ?asteroid dbo:epoch ?epoch }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            a = n(row.get('asteroid',{}).get('value',''))
            if not a: continue
            w(f, a, 'is_a', 'asteroid', 85)
            d = n(row.get('discoverer',{}).get('value',''))
            if d: w(f, a, 'discovered_by', d, 80)

    # Exoplanets
    q = """SELECT ?planet ?star ?method WHERE {
      ?planet a dbo:Exoplanet .
      OPTIONAL { ?planet dbo:parentStar ?star }
      OPTIONAL { ?planet dbo:detectionMethod ?method }
    } LIMIT 10000"""
    data = dbpedia_query(q)
    if data:
        for row in data['results']['bindings']:
            p = n(row.get('planet',{}).get('value',''))
            if not p: continue
            w(f, p, 'is_a', 'exoplanet', 90)
            s = n(row.get('star',{}).get('value',''))
            if s: w(f, p, 'orbits', s, 85)

    # Space missions (max)
    for offset in range(0, 20000, 10000):
        q = f"""SELECT ?mission ?operator ?launch ?destination WHERE {{
          ?mission a dbo:SpaceMission .
          OPTIONAL {{ ?mission dbo:operator ?operator }}
          OPTIONAL {{ ?mission dbo:launchDate ?launch }}
          OPTIONAL {{ ?mission dbo:destination ?destination }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            m = n(row.get('mission',{}).get('value',''))
            if not m: continue
            w(f, m, 'is_a', 'space mission', 90)
            op = n(row.get('operator',{}).get('value',''))
            if op: w(f, m, 'operated_by', op, 85)
            dest = n(row.get('destination',{}).get('value',''))
            if dest: w(f, m, 'destination', dest, 85)

    # Programmatic cosmology
    print("  Cosmology constants & facts...", flush=True)
    cosmic_facts = [
        ("universe", "age", "13.8 billion years"),
        ("universe", "observable_diameter", "93 billion light years"),
        ("universe", "temperature", "2.725 kelvin"),
        ("universe", "composition", "68% dark energy 27% dark matter 5% ordinary matter"),
        ("milky way", "is_a", "spiral galaxy"),
        ("milky way", "diameter", "100000 light years"),
        ("milky way", "stars", "100-400 billion"),
        ("milky way", "age", "13.6 billion years"),
        ("milky way", "center", "sagittarius a star"),
        ("andromeda galaxy", "is_a", "spiral galaxy"),
        ("andromeda galaxy", "distance", "2.537 million light years"),
        ("andromeda galaxy", "diameter", "220000 light years"),
        ("black hole", "is_a", "astronomical object"),
        ("black hole", "property", "gravity so strong nothing can escape"),
        ("black hole", "event_horizon", "boundary beyond which nothing returns"),
        ("schwarzschild radius", "formula", "2gm/c^2"),
        ("neutron star", "is_a", "stellar remnant"),
        ("neutron star", "density", "10^17 kg/m^3"),
        ("white dwarf", "is_a", "stellar remnant"),
        ("red giant", "is_a", "stellar evolution stage"),
        ("supernova", "is_a", "stellar explosion"),
        ("pulsar", "is_a", "rotating neutron star"),
        ("quasar", "is_a", "active galactic nucleus"),
        ("dark matter", "is_a", "hypothetical form of matter"),
        ("dark matter", "percentage_of_universe", "27%"),
        ("dark energy", "is_a", "hypothetical form of energy"),
        ("dark energy", "percentage_of_universe", "68%"),
        ("cosmic microwave background", "is_a", "relic radiation from big bang"),
        ("cosmic microwave background", "temperature", "2.725 kelvin"),
        ("big bang", "is_a", "origin event of universe"),
        ("big bang", "occurred", "13.8 billion years ago"),
        ("hubble constant", "measures", "rate of expansion of universe"),
        ("hubble constant", "value", "approximately 70 km/s/mpc"),
        ("redshift", "indicates", "object moving away from observer"),
        ("blueshift", "indicates", "object moving toward observer"),
        ("light year", "equals", "9.461 trillion kilometers"),
        ("parsec", "equals", "3.26 light years"),
        ("astronomical unit", "equals", "149.6 million kilometers"),
        ("solar mass", "equals", "1.989 x 10^30 kg"),
        ("chandrasekhar limit", "value", "1.4 solar masses"),
        ("planck length", "value", "1.616 x 10^-35 meters"),
        ("planck time", "value", "5.391 x 10^-44 seconds"),
        ("cosmic inflation", "is_a", "rapid expansion of early universe"),
        ("stellar nucleosynthesis", "is_a", "creation of elements in stars"),
        ("gravitational wave", "first_detected", "2015 by ligo"),
        ("gravitational wave", "predicted_by", "albert einstein 1916"),
        ("hawking radiation", "is_a", "theoretical radiation from black holes"),
        ("hawking radiation", "proposed_by", "stephen hawking 1974"),
        ("multiverse", "is_a", "hypothetical set of multiple universes"),
        ("string theory", "is_a", "theoretical physics framework"),
        ("string theory", "dimensions", "10 or 11"),
        ("general relativity", "proposed_by", "albert einstein 1915"),
        ("general relativity", "describes", "gravity as curvature of spacetime"),
        ("special relativity", "proposed_by", "albert einstein 1905"),
        ("special relativity", "key_result", "e equals mc squared"),
        ("quantum field theory", "is_a", "theoretical framework combining qm and relativity"),
        ("standard model", "is_a", "theory of fundamental particles and forces"),
        ("higgs boson", "discovered", "2012 at cern"),
        ("higgs boson", "mass", "125.1 gev"),
        ("cern", "is_a", "particle physics laboratory"),
        ("cern", "located_in", "geneva switzerland"),
        ("large hadron collider", "is_a", "particle accelerator"),
        ("large hadron collider", "circumference", "27 kilometers"),
    ]
    for s, r, o in cosmic_facts:
        w(f, s, r, o, 99)

    # Space agencies
    agencies = [
        ("nasa", "united states", "1958"),
        ("esa", "europe", "1975"),
        ("roscosmos", "russia", "1992"),
        ("cnsa", "china", "1993"),
        ("isro", "india", "1969"),
        ("jaxa", "japan", "2003"),
        ("csa", "canada", "1989"),
        ("dlr", "germany", "1969"),
        ("cnes", "france", "1961"),
        ("uksa", "united kingdom", "2010"),
        ("asi", "italy", "1988"),
        ("kari", "south korea", "1989"),
        ("spacex", "united states", "2002"),
        ("blue origin", "united states", "2000"),
    ]
    for agency, country, year in agencies:
        w(f, agency, 'is_a', 'space agency', 95)
        w(f, agency, 'country', country, 95)
        w(f, agency, 'founded_year', year, 90)


# ═══════════════════════════════════════════════════════════
# DBPEDIA MAX — ALL REMAINING CATEGORIES WITH PROPERTIES
# ═══════════════════════════════════════════════════════════
def dbpedia_max_with_props(f):
    print("\n[DBPEDIA MAX+] All categories with properties...", flush=True)

    # Persons with MORE details
    print("  Persons (detailed)...", flush=True)
    for offset in range(0, 100000, 10000):
        q = f"""SELECT ?p ?bp ?bd ?occ ?nat WHERE {{
          ?p a dbo:Person .
          OPTIONAL {{ ?p dbo:birthPlace ?bp }}
          OPTIONAL {{ ?p dbo:birthDate ?bd }}
          OPTIONAL {{ ?p dbo:occupation ?occ }}
          OPTIONAL {{ ?p dbo:nationality ?nat }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            p = n(row.get('p',{}).get('value',''))
            if not p: continue
            w(f, p, 'is_a', 'person', 85)
            bp = n(row.get('bp',{}).get('value',''))
            if bp: w(f, p, 'born_in', bp, 85)
            bd = row.get('bd',{}).get('value','')
            if bd and len(bd)>=4: w(f, p, 'born_year', bd[:4], 80)
            occ = n(row.get('occ',{}).get('value',''))
            if occ: w(f, p, 'occupation', occ, 85)
            nat = n(row.get('nat',{}).get('value',''))
            if nat: w(f, p, 'nationality', nat, 85)

    # Places with details
    print("  Places (detailed)...", flush=True)
    for offset in range(0, 100000, 10000):
        q = f"""SELECT ?place ?country ?pop ?elev WHERE {{
          ?place a dbo:Place .
          OPTIONAL {{ ?place dbo:country ?country }}
          OPTIONAL {{ ?place dbo:populationTotal ?pop }}
          OPTIONAL {{ ?place dbo:elevation ?elev }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            pl = n(row.get('place',{}).get('value',''))
            if not pl: continue
            w(f, pl, 'is_a', 'place', 80)
            co = n(row.get('country',{}).get('value',''))
            if co: w(f, pl, 'country', co, 85)
            pop = row.get('pop',{}).get('value','')
            if pop: w(f, pl, 'population', pop, 80)

    # Organizations with details
    print("  Organizations (detailed)...", flush=True)
    for offset in range(0, 50000, 10000):
        q = f"""SELECT ?org ?founder ?hq ?industry WHERE {{
          ?org a dbo:Organisation .
          OPTIONAL {{ ?org dbo:foundedBy ?founder }}
          OPTIONAL {{ ?org dbo:headquarter ?hq }}
          OPTIONAL {{ ?org dbo:industry ?industry }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            org = n(row.get('org',{}).get('value',''))
            if not org: continue
            w(f, org, 'is_a', 'organization', 85)
            fo = n(row.get('founder',{}).get('value',''))
            if fo: w(f, org, 'founded_by', fo, 85)
            hq = n(row.get('hq',{}).get('value',''))
            if hq: w(f, org, 'headquarters', hq, 85)
            ind = n(row.get('industry',{}).get('value',''))
            if ind: w(f, org, 'industry', ind, 80)

    # Works (books, films, songs, albums) with details
    print("  Creative works...", flush=True)
    for offset in range(0, 100000, 10000):
        q = f"""SELECT ?work ?author ?genre WHERE {{
          ?work a dbo:Work .
          OPTIONAL {{ ?work dbo:author ?author }}
          OPTIONAL {{ ?work dbo:genre ?genre }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            wk = n(row.get('work',{}).get('value',''))
            if not wk: continue
            w(f, wk, 'is_a', 'creative work', 80)
            au = n(row.get('author',{}).get('value',''))
            if au: w(f, wk, 'created_by', au, 85)
            ge = n(row.get('genre',{}).get('value',''))
            if ge: w(f, wk, 'genre', ge, 80)

    # Species with classification
    print("  Species (taxonomy)...", flush=True)
    for offset in range(0, 100000, 10000):
        q = f"""SELECT ?species ?kingdom ?family ?order WHERE {{
          ?species a dbo:Species .
          OPTIONAL {{ ?species dbo:kingdom ?kingdom }}
          OPTIONAL {{ ?species dbo:family ?family }}
          OPTIONAL {{ ?species dbo:order ?order }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            sp = n(row.get('species',{}).get('value',''))
            if not sp: continue
            w(f, sp, 'is_a', 'species', 85)
            k = n(row.get('kingdom',{}).get('value',''))
            if k: w(f, sp, 'kingdom', k, 85)
            fam = n(row.get('family',{}).get('value',''))
            if fam: w(f, sp, 'family', fam, 80)
            o = n(row.get('order',{}).get('value',''))
            if o: w(f, sp, 'order', o, 80)

    # Settlements with country & population
    print("  Settlements...", flush=True)
    for offset in range(0, 100000, 10000):
        q = f"""SELECT ?s ?country ?pop WHERE {{
          ?s a dbo:Settlement .
          OPTIONAL {{ ?s dbo:country ?country }}
          OPTIONAL {{ ?s dbo:populationTotal ?pop }}
        }} LIMIT 10000 OFFSET {offset}"""
        data = dbpedia_query(q)
        if not data or not data['results']['bindings']: break
        for row in data['results']['bindings']:
            s = n(row.get('s',{}).get('value',''))
            if not s: continue
            w(f, s, 'is_a', 'settlement', 80)
            co = n(row.get('country',{}).get('value',''))
            if co: w(f, s, 'country', co, 85)


# ═══════════════════════════════════════════════════════════
# MORE DBPEDIA CATEGORIES
# ═══════════════════════════════════════════════════════════
def more_categories(f):
    print("\n[MORE] Additional DBpedia categories...", flush=True)

    cats = [
        ("dbo:MilitaryConflict", "military conflict", 30000),
        ("dbo:Politician", "politician", 50000),
        ("dbo:Athlete", "athlete", 50000),
        ("dbo:Scientist", "scientist", 30000),
        ("dbo:Writer", "writer", 30000),
        ("dbo:MusicalArtist", "musical artist", 50000),
        ("dbo:Band", "band", 30000),
        ("dbo:Film", "film", 50000),
        ("dbo:TelevisionShow", "tv show", 30000),
        ("dbo:VideoGame", "video game", 20000),
        ("dbo:Song", "song", 50000),
        ("dbo:Album", "album", 50000),
        ("dbo:Book", "book", 30000),
        ("dbo:Magazine", "magazine", 10000),
        ("dbo:Newspaper", "newspaper", 10000),
        ("dbo:RadioStation", "radio station", 10000),
        ("dbo:TelevisionStation", "tv station", 10000),
        ("dbo:SportsSeason", "sports season", 30000),
        ("dbo:SportsTeam", "sports team", 30000),
        ("dbo:Stadium", "stadium", 10000),
        ("dbo:Bridge", "bridge", 10000),
        ("dbo:Dam", "dam", 5000),
        ("dbo:Canal", "canal", 5000),
        ("dbo:Tunnel", "tunnel", 5000),
        ("dbo:Lake", "lake", 10000),
        ("dbo:Island", "island", 10000),
        ("dbo:Mountain", "mountain", 20000),
        ("dbo:Volcano", "volcano", 5000),
        ("dbo:River", "river", 20000),
        ("dbo:Desert", "desert", 3000),
        ("dbo:Forest", "forest", 5000),
        ("dbo:Park", "park", 10000),
        ("dbo:ProtectedArea", "protected area", 10000),
        ("dbo:WorldHeritageSite", "world heritage site", 5000),
        ("dbo:Monument", "monument", 10000),
        ("dbo:HistoricBuilding", "historic building", 10000),
        ("dbo:Castle", "castle", 10000),
        ("dbo:Church", "church", 10000),
        ("dbo:Mosque", "mosque", 5000),
        ("dbo:Temple", "temple", 5000),
        ("dbo:Museum", "museum", 10000),
        ("dbo:Library", "library", 5000),
        ("dbo:Theatre", "theatre", 5000),
        ("dbo:Hotel", "hotel", 10000),
        ("dbo:Restaurant", "restaurant", 5000),
        ("dbo:ShoppingMall", "shopping mall", 5000),
        ("dbo:Airport", "airport", 10000),
        ("dbo:RailwayStation", "railway station", 20000),
        ("dbo:Ship", "ship", 20000),
        ("dbo:Aircraft", "aircraft", 10000),
        ("dbo:Automobile", "automobile", 20000),
        ("dbo:Motorcycle", "motorcycle", 5000),
        ("dbo:Locomotive", "locomotive", 5000),
        ("dbo:Satellite", "satellite", 5000),
        ("dbo:Rocket", "rocket", 3000),
        ("dbo:MilitaryUnit", "military unit", 10000),
        ("dbo:Language", "language", 10000),
        ("dbo:Currency", "currency", 3000),
        ("dbo:Award", "award", 10000),
        ("dbo:Holiday", "holiday", 3000),
        ("dbo:Plant", "plant", 30000),
        ("dbo:Fungus", "fungus", 10000),
        ("dbo:Reptile", "reptile", 10000),
        ("dbo:Amphibian", "amphibian", 10000),
        ("dbo:Bird", "bird", 30000),
        ("dbo:Mammal", "mammal", 30000),
        ("dbo:Fish", "fish", 20000),
        ("dbo:Insect", "insect", 20000),
        ("dbo:Arachnid", "arachnid", 5000),
        ("dbo:Crustacean", "crustacean", 5000),
        ("dbo:Mollusca", "mollusc", 10000),
    ]
    for cls, label, limit in cats:
        print(f"    {label}...", flush=True)
        for offset in range(0, limit, 10000):
            q = f"""SELECT ?item WHERE {{
              ?item a {cls} .
            }} LIMIT 10000 OFFSET {offset}"""
            data = dbpedia_query(q)
            if not data or not data['results']['bindings']: break
            for row in data['results']['bindings']:
                item = n(row.get('item',{}).get('value',''))
                if item: w(f, item, 'is_a', label, 80)


# ═══════════════════════════════════════════════════════════
# MASSIVE PROGRAMMATIC — History, Culture, Science, Geography
# ═══════════════════════════════════════════════════════════
def mega_programmatic(f):
    print("\n[PROGRAMMATIC] History, inventions, geography, culture...", flush=True)

    # Historical periods
    periods = [
        ("stone age", "2500000 bce - 3300 bce", "prehistoric"),
        ("bronze age", "3300 bce - 1200 bce", "ancient"),
        ("iron age", "1200 bce - 600 bce", "ancient"),
        ("classical antiquity", "800 bce - 600 ce", "ancient"),
        ("middle ages", "500 - 1500", "medieval"),
        ("renaissance", "1300 - 1600", "early modern"),
        ("age of discovery", "1400 - 1600", "early modern"),
        ("scientific revolution", "1543 - 1687", "early modern"),
        ("enlightenment", "1685 - 1815", "modern"),
        ("industrial revolution", "1760 - 1840", "modern"),
        ("victorian era", "1837 - 1901", "modern"),
        ("world war i", "1914 - 1918", "contemporary"),
        ("interwar period", "1918 - 1939", "contemporary"),
        ("world war ii", "1939 - 1945", "contemporary"),
        ("cold war", "1947 - 1991", "contemporary"),
        ("space age", "1957 - present", "contemporary"),
        ("information age", "1970 - present", "contemporary"),
    ]
    for period, dates, era in periods:
        w(f, period, 'is_a', 'historical period', 99)
        w(f, period, 'time_span', dates, 95)
        w(f, period, 'era', era, 90)

    # Major inventions with dates & inventors
    print("  Major inventions...", flush=True)
    inventions = [
        ("wheel", "3500 bce", "mesopotamia"), ("writing", "3200 bce", "sumer"),
        ("paper", "105 ce", "cai lun"), ("compass", "200 bce", "china"),
        ("gunpowder", "850 ce", "china"), ("printing press", "1440", "johannes gutenberg"),
        ("telescope", "1608", "hans lippershey"), ("microscope", "1590", "zacharias janssen"),
        ("steam engine", "1712", "thomas newcomen"), ("spinning jenny", "1764", "james hargreaves"),
        ("cotton gin", "1793", "eli whitney"), ("battery", "1800", "alessandro volta"),
        ("locomotive", "1804", "richard trevithick"), ("photography", "1826", "joseph niepce"),
        ("telegraph", "1837", "samuel morse"), ("telephone", "1876", "alexander graham bell"),
        ("light bulb", "1879", "thomas edison"), ("automobile", "1886", "karl benz"),
        ("radio", "1895", "guglielmo marconi"), ("airplane", "1903", "wright brothers"),
        ("television", "1927", "philo farnsworth"), ("penicillin", "1928", "alexander fleming"),
        ("computer", "1936", "alan turing"), ("nuclear energy", "1942", "enrico fermi"),
        ("transistor", "1947", "bell labs"), ("internet", "1969", "arpanet"),
        ("personal computer", "1975", "altair 8800"), ("world wide web", "1989", "tim berners-lee"),
        ("smartphone", "2007", "apple iphone"), ("crispr", "2012", "jennifer doudna"),
    ]
    for inv, year, inventor in inventions:
        w(f, inv, 'is_a', 'invention', 99)
        w(f, inv, 'invented_year', year, 95)
        w(f, inv, 'invented_by', inventor, 95)
        w(f, inventor, 'invented', inv, 95)

    # Programming languages with paradigms
    print("  Programming languages...", flush=True)
    langs = [
        ("python", "1991", "guido van rossum", "interpreted multi-paradigm"),
        ("javascript", "1995", "brendan eich", "interpreted multi-paradigm"),
        ("java", "1995", "james gosling", "compiled object-oriented"),
        ("c", "1972", "dennis ritchie", "compiled procedural"),
        ("c++", "1979", "bjarne stroustrup", "compiled multi-paradigm"),
        ("c#", "2000", "anders hejlsberg", "compiled object-oriented"),
        ("rust", "2010", "graydon hoare", "compiled systems"),
        ("go", "2009", "robert griesemer", "compiled concurrent"),
        ("swift", "2014", "chris lattner", "compiled multi-paradigm"),
        ("kotlin", "2011", "jetbrains", "compiled multi-paradigm"),
        ("typescript", "2012", "anders hejlsberg", "compiled superset of javascript"),
        ("ruby", "1995", "yukihiro matsumoto", "interpreted object-oriented"),
        ("php", "1995", "rasmus lerdorf", "interpreted web scripting"),
        ("scala", "2004", "martin odersky", "compiled functional object-oriented"),
        ("haskell", "1990", "committee", "compiled purely functional"),
        ("lua", "1993", "roberto ierusalimschy", "interpreted lightweight scripting"),
        ("perl", "1987", "larry wall", "interpreted text processing"),
        ("r", "1993", "ross ihaka", "interpreted statistical computing"),
        ("matlab", "1984", "cleve moler", "interpreted numerical computing"),
        ("fortran", "1957", "john backus", "compiled scientific"),
        ("cobol", "1959", "grace hopper", "compiled business"),
        ("lisp", "1958", "john mccarthy", "interpreted functional"),
        ("sql", "1974", "donald chamberlin", "declarative database query"),
        ("assembly", "1949", "various", "low level machine code"),
        ("dart", "2011", "lars bak", "compiled client-side"),
        ("elixir", "2011", "jose valim", "functional concurrent"),
        ("clojure", "2007", "rich hickey", "functional lisp dialect"),
        ("zig", "2016", "andrew kelley", "systems programming"),
        ("solidity", "2015", "gavin wood", "smart contract language"),
    ]
    for lang, year, creator, paradigm in langs:
        w(f, lang, 'is_a', 'programming language', 99)
        w(f, lang, 'created_year', year, 95)
        w(f, lang, 'created_by', creator, 95)
        w(f, lang, 'paradigm', paradigm, 90)

    # World religions
    print("  World religions...", flush=True)
    religions = [
        ("christianity", "2.4 billion", "jesus christ", "bible"),
        ("islam", "1.9 billion", "prophet muhammad", "quran"),
        ("hinduism", "1.2 billion", "no single founder", "vedas"),
        ("buddhism", "500 million", "siddhartha gautama", "tripitaka"),
        ("sikhism", "30 million", "guru nanak", "guru granth sahib"),
        ("judaism", "15 million", "abraham", "torah"),
        ("taoism", "12 million", "laozi", "tao te ching"),
        ("shintoism", "4 million", "indigenous", "kojiki"),
        ("confucianism", "6 million", "confucius", "analects"),
        ("zoroastrianism", "200000", "zoroaster", "avesta"),
        ("jainism", "4 million", "mahavira", "agamas"),
        ("bahai", "8 million", "bahaullah", "kitab-i-aqdas"),
    ]
    for religion, followers, founder, text in religions:
        w(f, religion, 'is_a', 'world religion', 99)
        w(f, religion, 'followers', followers, 90)
        w(f, religion, 'founder', founder, 95)
        w(f, religion, 'sacred_text', text, 95)

    # Wonders of the world
    ancient_wonders = ["great pyramid of giza", "hanging gardens of babylon",
        "statue of zeus at olympia", "temple of artemis at ephesus",
        "mausoleum at halicarnassus", "colossus of rhodes", "lighthouse of alexandria"]
    for wonder in ancient_wonders:
        w(f, wonder, 'is_a', 'ancient wonder of the world', 99)

    modern_wonders = ["great wall of china", "petra", "colosseum", "chichen itza",
        "machu picchu", "taj mahal", "christ the redeemer"]
    for wonder in modern_wonders:
        w(f, wonder, 'is_a', 'new wonder of the world', 99)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == '__main__':
    start = time.time()
    print("=" * 60)
    print("  COSMIC-LEVEL KNOWLEDGE EXPANSION")
    print("  No stopping. Maximum extraction.")
    print("=" * 60, flush=True)

    with open(OUTPUT, 'w') as f:
        education(f)
        cosmic(f)
        dbpedia_max_with_props(f)
        more_categories(f)
        mega_programmatic(f)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  COSMIC EXPANSION COMPLETE!")
    print(f"  Facts added: {facts_added:,}")
    print(f"  DBpedia queries: {queries_done}")
    print(f"  Time: {elapsed/60:.1f} min")
    print(f"  File: {OUTPUT}")
    print(f"  Size: {os.path.getsize(OUTPUT)/1e6:.1f} MB")
    print(f"{'=' * 60}", flush=True)
