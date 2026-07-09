#!/usr/bin/env python3
"""
Web Knowledge Fetcher — searches the web when AI doesn't know something.
No API keys. Uses DuckDuckGo + Wikipedia. Free forever.
"""
import urllib.request
import urllib.parse
import json
import re
import html


def search_wikipedia(query, sentences=3):
    """Search Wikipedia API — completely free, no key."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "HybridAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if "extract" in data:
                text = data["extract"]
                # Return first N sentences
                sents = re.split(r'(?<=[.!?])\s+', text)
                return ' '.join(sents[:sentences])
    except Exception:
        pass
    return None


def search_duckduckgo(query):
    """Search DuckDuckGo instant answer — free, no key."""
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
        req = urllib.request.Request(url, headers={"User-Agent": "HybridAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            # Try abstract first
            if data.get("AbstractText"):
                return data["AbstractText"]
            # Try answer
            if data.get("Answer"):
                return data["Answer"]
            # Try first related topic
            if data.get("RelatedTopics") and len(data["RelatedTopics"]) > 0:
                topic = data["RelatedTopics"][0]
                if isinstance(topic, dict) and "Text" in topic:
                    return topic["Text"]
    except Exception:
        pass
    return None


def search_web(query):
    """Try multiple sources, return first result found."""
    # Clean query — strip question words
    query = query.strip().rstrip('?').strip()
    for prefix in ['what is ', 'what are ', 'who is ', 'who are ', 'where is ',
                   'when is ', 'when was ', 'how does ', 'how do ', 'why does ',
                   'why do ', 'what does ', 'tell me about ', 'explain ',
                   'define ', 'what is a ', 'what is an ', 'what is the ']:
        if query.lower().startswith(prefix):
            query = query[len(prefix):]
            break
    
    query = query.strip()
    
    # Try Wikipedia first (best quality)
    result = search_wikipedia(query)
    if result and len(result) > 20:
        return {"source": "Wikipedia", "text": result}
    
    # Try DuckDuckGo
    result = search_duckduckgo(query)
    if result and len(result) > 20:
        return {"source": "DuckDuckGo", "text": result}
    
    # Try Wikipedia with simplified query (first 3 words)
    words = query.split()[:3]
    simple = ' '.join(words)
    if simple != query:
        result = search_wikipedia(simple)
        if result and len(result) > 20:
            return {"source": "Wikipedia", "text": result}
    
    return None


def extract_facts(text, topic):
    """Extract simple facts from text for storage."""
    facts = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sent in sentences[:5]:  # Max 5 facts
        sent = sent.strip()
        if len(sent) > 10 and topic.lower() in sent.lower():
            facts.append(sent)
    if not facts and sentences:
        facts = [sentences[0]]  # At least keep the first sentence
    return facts


if __name__ == "__main__":
    import sys
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "What is a black hole"
    print(f"Searching: '{query}'")
    result = search_web(query)
    if result:
        print(f"Source: {result['source']}")
        print(f"Answer: {result['text']}")
        print(f"\nExtracted facts:")
        for f in extract_facts(result['text'], query.split()[-1]):
            print(f"  - {f}")
    else:
        print("No results found.")
