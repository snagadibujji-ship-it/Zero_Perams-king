#!/usr/bin/env python3
"""
Auto-Learn Module — When AI doesn't know, searches web and offers to save.
Integrates with web_search.py and the concept_build system.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from web_search import search_web, extract_facts


LEARNED_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'web_learned.txt')


def offer_search(query):
    """Search web for a query. Returns answer dict or None."""
    result = search_web(query)
    if result:
        return {
            "answer": result["text"],
            "source": result["source"],
            "facts": extract_facts(result["text"], query.split()[-1] if query.split() else query),
        }
    return None


def save_facts(facts):
    """Save facts to web_learned.txt for future concept_build inclusion."""
    os.makedirs(os.path.dirname(LEARNED_FILE), exist_ok=True)
    with open(LEARNED_FILE, 'a') as f:
        for fact in facts:
            # Clean and write one fact per line
            clean = fact.strip().rstrip('.')
            if len(clean) > 10:
                f.write(clean + '\n')
    return len(facts)


def get_learned_count():
    """How many web-learned facts do we have?"""
    if os.path.isfile(LEARNED_FILE):
        with open(LEARNED_FILE) as f:
            return sum(1 for line in f if line.strip())
    return 0


if __name__ == "__main__":
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "quantum computing"
    print(f"Query: {query}")
    result = offer_search(query)
    if result:
        print(f"\n[{result['source']}] {result['answer'][:200]}...")
        print(f"\nSave {len(result['facts'])} facts? (y/n)")
        if input("> ").strip().lower() == 'y':
            n = save_facts(result['facts'])
            print(f"Saved {n} facts to {LEARNED_FILE}")
    else:
        print("Couldn't find anything online either.")
