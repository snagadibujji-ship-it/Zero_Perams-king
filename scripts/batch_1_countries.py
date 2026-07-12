#!/usr/bin/env python3
"""
Batch 1: Countries — 200K facts from Wikidata
Capitals, populations, area, continent, language, currency, borders, leaders.
"""

import urllib.request
import urllib.parse
import json
import time
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'batch_1_countries.txt')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SPARQL_URL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "Axima/3.0 Knowledge Builder", "Accept": "application/json"}


def sparql_query(query, retries=3):
    """Execute SPARQL query against Wikidata."""
    for attempt in range(retries):
        try:
            url = f"{SPARQL_URL}?query={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                print(f"  FAILED: {e}")
                return None


def extract_value(binding, key):
    """Extract value from SPARQL binding."""
    if key in binding:
        val = binding[key].get('value', '')
        # Strip Wikidata URI prefix
        if val.startswith('http://www.wikidata.org/entity/'):
            return None  # Skip raw entity IDs
        return val.strip()
    return None


def write_triples(triples, f):
    """Write triples to file."""
    for subj, rel, obj, conf in triples:
        if subj and rel and obj and len(subj) > 1 and len(obj) > 0:
            f.write(f"{subj.lower()}|{rel}|{obj.lower()}|{conf}\n")


def run():
    facts_total = 0
    f = open(OUTPUT_FILE, 'w')

    # ─── Query 1: Countries + Capitals + Population + Area ───
    print("  Query 1: Countries basic info...")
    q = """
    SELECT ?countryLabel ?capitalLabel ?population ?area ?continentLabel WHERE {
      ?country wdt:P31 wd:Q6256.
      OPTIONAL { ?country wdt:P36 ?capital. }
      OPTIONAL { ?country wdt:P1082 ?population. }
      OPTIONAL { ?country wdt:P2046 ?area. }
      OPTIONAL { ?country wdt:P30 ?continent. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            country = extract_value(row, 'countryLabel')
            capital = extract_value(row, 'capitalLabel')
            pop = extract_value(row, 'population')
            area = extract_value(row, 'area')
            continent = extract_value(row, 'continentLabel')
            if not country:
                continue
            triples = []
            if capital:
                triples.append((country, 'capital', capital, 99))
                triples.append((capital, 'capital_of', country, 99))
            if pop:
                triples.append((country, 'population', pop, 95))
            if area:
                triples.append((country, 'area_km2', area, 95))
            if continent:
                triples.append((country, 'continent', continent, 99))
                triples.append((country, 'located_in', continent, 99))
            triples.append((country, 'is_a', 'country', 99))
            write_triples(triples, f)
            facts_total += len(triples)
    time.sleep(2)

    # ─── Query 2: Official Languages ───
    print("  Query 2: Languages...")
    q = """
    SELECT ?countryLabel ?languageLabel WHERE {
      ?country wdt:P31 wd:Q6256.
      ?country wdt:P37 ?language.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            country = extract_value(row, 'countryLabel')
            language = extract_value(row, 'languageLabel')
            if country and language:
                write_triples([(country, 'official_language', language, 95)], f)
                facts_total += 1
    time.sleep(2)

    # ─── Query 3: Currencies ───
    print("  Query 3: Currencies...")
    q = """
    SELECT ?countryLabel ?currencyLabel WHERE {
      ?country wdt:P31 wd:Q6256.
      ?country wdt:P38 ?currency.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            country = extract_value(row, 'countryLabel')
            currency = extract_value(row, 'currencyLabel')
            if country and currency:
                write_triples([(country, 'currency', currency, 95)], f)
                facts_total += 1
    time.sleep(2)

    # ─── Query 4: Borders ───
    print("  Query 4: Borders...")
    q = """
    SELECT ?countryLabel ?borderLabel WHERE {
      ?country wdt:P31 wd:Q6256.
      ?country wdt:P47 ?border.
      ?border wdt:P31 wd:Q6256.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            country = extract_value(row, 'countryLabel')
            border = extract_value(row, 'borderLabel')
            if country and border:
                write_triples([(country, 'borders', border, 95)], f)
                facts_total += 1
    time.sleep(2)

    # ─── Query 5: Heads of State ───
    print("  Query 5: Heads of state...")
    q = """
    SELECT ?countryLabel ?leaderLabel WHERE {
      ?country wdt:P31 wd:Q6256.
      ?country wdt:P35 ?leader.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            country = extract_value(row, 'countryLabel')
            leader = extract_value(row, 'leaderLabel')
            if country and leader:
                write_triples([(country, 'head_of_state', leader, 85)], f)
                facts_total += 1
    time.sleep(2)

    # ─── Query 6: Independence Dates ───
    print("  Query 6: Independence dates...")
    q = """
    SELECT ?countryLabel ?date WHERE {
      ?country wdt:P31 wd:Q6256.
      ?country wdt:P571 ?date.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            country = extract_value(row, 'countryLabel')
            date = extract_value(row, 'date')
            if country and date:
                year = date[:4] if date else None
                if year and year.isdigit():
                    write_triples([(country, 'founded_year', year, 90)], f)
                    facts_total += 1
    time.sleep(2)

    # ─── Query 7: GDP ───
    print("  Query 7: GDP...")
    q = """
    SELECT ?countryLabel ?gdp WHERE {
      ?country wdt:P31 wd:Q6256.
      ?country wdt:P2131 ?gdp.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    data = sparql_query(q)
    if data:
        for row in data.get('results', {}).get('bindings', []):
            country = extract_value(row, 'countryLabel')
            gdp = extract_value(row, 'gdp')
            if country and gdp:
                write_triples([(country, 'gdp_usd', gdp, 85)], f)
                facts_total += 1

    f.close()
    print(f"\n  Batch 1 complete: {facts_total} facts → {OUTPUT_FILE}")
    return facts_total


if __name__ == '__main__':
    print("Batch 1: Countries")
    run()
