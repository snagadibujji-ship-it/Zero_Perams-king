#!/usr/bin/env python3
"""
Batch 5: Culture — Movies, books, music (300K facts)
"""
import urllib.request, urllib.parse, json, time, os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'batch_5_culture.txt')
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

    # Movies
    print("  Movies...")
    q = """
    SELECT ?filmLabel ?directorLabel ?year ?genreLabel WHERE {
      ?film wdt:P31 wd:Q11424.
      OPTIONAL { ?film wdt:P57 ?director. }
      OPTIONAL { ?film wdt:P577 ?year. }
      OPTIONAL { ?film wdt:P136 ?genre. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 10000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            film = row.get('filmLabel',{}).get('value','')
            if not film or film.startswith('Q'): continue
            triples = [(film, 'is_a', 'film', 90)]
            d = row.get('directorLabel',{}).get('value','')
            if d and not d.startswith('Q'): triples.append((film, 'directed_by', d, 90))
            y = row.get('year',{}).get('value','')
            if y: triples.append((film, 'release_year', y[:4], 90))
            g = row.get('genreLabel',{}).get('value','')
            if g and not g.startswith('Q'): triples.append((film, 'genre', g, 85))
            write_triples(triples, f)
            facts += len(triples)
    time.sleep(3)

    # Books
    print("  Books...")
    q = """
    SELECT ?bookLabel ?authorLabel ?year ?genreLabel WHERE {
      ?book wdt:P31 wd:Q7725634.
      OPTIONAL { ?book wdt:P50 ?author. }
      OPTIONAL { ?book wdt:P577 ?year. }
      OPTIONAL { ?book wdt:P136 ?genre. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 10000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            book = row.get('bookLabel',{}).get('value','')
            if not book or book.startswith('Q'): continue
            triples = [(book, 'is_a', 'book', 90)]
            a = row.get('authorLabel',{}).get('value','')
            if a and not a.startswith('Q'): triples.append((book, 'written_by', a, 90))
            y = row.get('year',{}).get('value','')
            if y: triples.append((book, 'published_year', y[:4], 85))
            write_triples(triples, f)
            facts += len(triples)
    time.sleep(3)

    # Music artists
    print("  Musicians...")
    q = """
    SELECT ?artistLabel ?genreLabel ?countryLabel WHERE {
      ?artist wdt:P31 wd:Q5.
      ?artist wdt:P106 wd:Q177220.
      OPTIONAL { ?artist wdt:P136 ?genre. }
      OPTIONAL { ?artist wdt:P27 ?country. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 8000
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results',{}).get('bindings',[]):
            artist = row.get('artistLabel',{}).get('value','')
            if not artist or artist.startswith('Q'): continue
            triples = [(artist, 'is_a', 'singer', 90)]
            g = row.get('genreLabel',{}).get('value','')
            if g and not g.startswith('Q'): triples.append((artist, 'genre', g, 85))
            c = row.get('countryLabel',{}).get('value','')
            if c and not c.startswith('Q'): triples.append((artist, 'nationality', c, 90))
            write_triples(triples, f)
            facts += len(triples)

    f.close()
    print(f"\n  Batch 5 complete: {facts} facts → {OUTPUT_FILE}")
    return facts

if __name__ == '__main__':
    print("Batch 5: Culture")
    run()
