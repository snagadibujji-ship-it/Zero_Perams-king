#!/usr/bin/env python3
"""
AXIMA v3.1 — FRESH BENCHMARK (All New Questions)
Tests all 10 upgrades + core capabilities with ZERO overlap from previous benchmarks.
"""

import sys, os, time, json, tracemalloc, re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

AI_BIN = os.path.join(os.path.dirname(__file__), '..', 'ai')

# ═══════════════════════════════════════════════════════════════
# MATH (50 new questions)
# ═══════════════════════════════════════════════════════════════

MATH = [
    ("what is 23 times 19", "437"), ("what is 16 times 16", "256"),
    ("what is 225 divided by 15", "15"), ("what is 33 plus 44", "77"),
    ("what is 80 minus 53", "27"), ("what is 3 to the power of 7", "2187"),
    ("what is 6 to the power of 4", "1296"), ("what is the square root of 196", "14"),
    ("what is the square root of 289", "17"), ("what is 8 factorial", "40320"),
    ("what is 9 factorial", "362880"), ("is 83 a prime number", "yes"),
    ("is 87 a prime number", "no"), ("is 64 even", "yes"),
    ("is 45 odd", "yes"), ("what is 77 times 77", "5929"),
    ("what is 360 divided by 12", "30"), ("what is 2 to the power of 15", "32768"),
    ("what is the square root of 529", "23"), ("is 71 a prime number", "yes"),
    ("what is 18 times 22", "396"), ("what is 11 times 13", "143"),
    ("what is 144 divided by 12", "12"), ("what is 27 plus 38", "65"),
    ("what is 200 minus 67", "133"), ("what is 7 to the power of 3", "343"),
    ("what is 9 to the power of 3", "729"), ("what is the square root of 324", "18"),
    ("what is the square root of 441", "21"), ("what is 11 factorial", "39916800"),
    ("what is 5 factorial", "120"), ("is 67 a prime number", "yes"),
    ("is 63 a prime number", "no"), ("is 102 even", "yes"),
    ("is 57 odd", "yes"), ("what is 88 times 12", "1056"),
    ("what is 750 divided by 25", "30"), ("what is 4 to the power of 5", "1024"),
    ("what is the square root of 576", "24"), ("is 41 a prime number", "yes"),
    ("what is 21 times 21", "441"), ("what is 13 times 17", "221"),
    ("what is 840 divided by 7", "120"), ("what is 56 plus 78", "134"),
    ("what is 500 minus 237", "263"), ("what is 2 to the power of 12", "4096"),
    ("what is 13 factorial", "6227020800"), ("is 79 a prime number", "yes"),
    ("is 81 a prime number", "no"), ("what is 19 times 23", "437"),
]

# ═══════════════════════════════════════════════════════════════
# KNOWLEDGE (50 new questions)
# ═══════════════════════════════════════════════════════════════

KNOWLEDGE = [
    ("what is aluminum", ["metal", "element", "light"]),
    ("what is helium", ["element", "gas", "noble"]),
    ("what is a tsunami", ["wave", "ocean", "water"]),
    ("what is a glacier", ["ice", "frozen", "mass"]),
    ("what is mercury", ["element", "metal", "liquid", "planet"]),
    ("what is calcium", ["element", "metal", "bone"]),
    ("what is a tornado", ["wind", "storm", "rotating"]),
    ("what is coal", ["carbon", "fuel", "rock", "fossil"]),
    ("what is a bacteria", ["organism", "cell", "micro"]),
    ("what is a diamond", ["carbon", "hard", "crystal", "gem"]),
    ("what is lead", ["metal", "element", "heavy"]),
    ("what is marble", ["rock", "stone", "calcium"]),
    ("what is uranium", ["element", "radioactive", "metal"]),
    ("what is a hurricane", ["storm", "wind", "tropical"]),
    ("what is a rainbow", ["light", "color", "refract", "spectrum"]),
    ("what is steel", ["alloy", "iron", "metal"]),
    ("what is concrete", ["cement", "material", "construction", "building"]),
    ("what is granite", ["rock", "stone", "igneous"]),
    ("what is methane", ["gas", "carbon", "ch4"]),
    ("what is a protein", ["molecule", "amino", "cell"]),
    ("what is titanium", ["metal", "element", "strong"]),
    ("what is a neuron", ["cell", "nerve", "brain"]),
    ("what is limestone", ["rock", "calcium", "sediment"]),
    ("what is neon", ["element", "gas", "noble"]),
    ("what is chlorine", ["element", "gas", "halogen"]),
    ("what is a crystal", ["solid", "atom", "structure"]),
    ("what is bronze", ["alloy", "copper", "tin", "metal"]),
    ("what is a comet", ["ice", "orbit", "tail", "space"]),
    ("what is an earthquake", ["seismic", "tectonic", "ground"]),
    ("what is a fungus", ["organism", "spore", "mushroom"]),
    ("what is argon", ["element", "gas", "noble"]),
    ("what is sulfur", ["element", "yellow"]),
    ("what is a satellite", ["orbit", "space", "earth"]),
    ("what is a fossil", ["ancient", "remains", "rock"]),
    ("what is cotton", ["plant", "fiber", "fabric", "cloth"]),
    ("what is silk", ["fiber", "fabric", "insect", "worm"]),
    ("what is a lens", ["glass", "light", "focus"]),
    ("what is a semiconductor", ["silicon", "conduct", "electronic"]),
    ("what is tin", ["metal", "element"]),
    ("what is a nebula", ["gas", "cloud", "star", "space"]),
    ("what is petroleum", ["oil", "fossil", "fuel"]),
    ("what is a chromosome", ["dna", "gene", "cell"]),
    ("what is sandstone", ["rock", "sand", "sediment"]),
    ("what is platinum", ["metal", "element", "precious"]),
    ("what is a vaccine", ["immune", "virus", "protect"]),
    ("what is coral", ["ocean", "marine", "reef", "organism"]),
    ("what is ammonia", ["nitrogen", "hydrogen", "chemical", "gas"]),
    ("what is a prism", ["glass", "light", "spectrum", "refract"]),
    ("what is zinc", ["metal", "element"]),
    ("what is a transistor", ["electronic", "switch", "semiconductor"]),
]

# ═══════════════════════════════════════════════════════════════
# CAUSAL (40 new questions)
# ═══════════════════════════════════════════════════════════════

CAUSAL = [
    ("what happens if you heat lead", ["melt", "liquid"]),
    ("what happens if you drop a lightbulb", ["break", "shatter"]),
    ("what happens if you freeze orange juice", ["solid", "ice"]),
    ("what happens if you heat aluminum", ["melt", "expand"]),
    ("what happens if you drop a vase", ["break", "shatter"]),
    ("what happens if you heat honey", ["liquid", "thin", "melt"]),
    ("what happens if you cool lava", ["solid", "rock", "harden"]),
    ("what happens if you heat candle wax", ["melt", "liquid"]),
    ("what happens if you drop a watermelon", ["break", "crack", "splat"]),
    ("what happens if you heat sand", ["glass", "melt"]),
    ("what happens if you freeze soup", ["solid", "ice"]),
    ("what happens if you heat copper", ["expand", "melt"]),
    ("what happens if you drop a television", ["break", "crack", "damage"]),
    ("what happens if you heat stone", ["crack", "expand", "hot"]),
    ("what happens if you cool steam", ["condense", "water", "liquid"]),
    ("what happens if you heat tin", ["melt"]),
    ("what happens if you drop crystal", ["break", "shatter"]),
    ("what happens if you heat cheese", ["melt"]),
    ("what happens if you freeze coffee", ["solid", "ice"]),
    ("what happens if you heat clay", ["hard", "fire", "ceramic"]),
    ("what happens if you drop porcelain", ["break", "shatter"]),
    ("what happens if you heat silver", ["melt", "expand"]),
    ("what happens if you cool vapor", ["condense", "liquid"]),
    ("what happens if you heat tar", ["soft", "melt", "liquid"]),
    ("what happens if you drop a laptop", ["break", "crack", "damage"]),
    ("what happens if you heat soap", ["melt"]),
    ("what happens if you freeze beer", ["solid", "ice", "expand"]),
    ("what happens if you heat steel", ["expand", "glow", "red"]),
    ("what happens if you drop a jar", ["break", "shatter"]),
    ("what happens if you heat coconut oil", ["melt", "liquid"]),
    ("what happens if you cool hot metal", ["contract", "shrink", "solid"]),
    ("what happens if you heat paint", ["bubble", "dry", "peel"]),
    ("what happens if you drop a tablet", ["break", "crack"]),
    ("what happens if you heat resin", ["melt", "soft", "liquid"]),
    ("what happens if you freeze blood", ["solid", "ice"]),
    ("what happens if you heat cement", ["dry", "hard", "crack"]),
    ("what happens if you drop a bowl", ["break", "shatter", "crack"]),
    ("what happens if you heat gelatin", ["melt", "liquid"]),
    ("what happens if you cool molten glass", ["solid", "hard"]),
    ("what happens if you heat gasoline", ["vapor", "ignite", "explode", "evaporate"]),
]

# ═══════════════════════════════════════════════════════════════
# LOGIC + BOOLEAN (30 new questions)
# ═══════════════════════════════════════════════════════════════

LOGIC = [
    ("all metals conduct electricity. copper is a metal. does copper conduct electricity", ["yes"]),
    ("all planets orbit a star. mars is a planet. does mars orbit a star", ["yes"]),
    ("all insects have six legs. a bee is an insect. does a bee have six legs", ["yes"]),
    ("no mammals lay eggs. a wolf is a mammal. does a wolf lay eggs", ["no"]),
    ("all squares are rectangles. a tile is a square. is a tile a rectangle", ["yes"]),
    ("is the moon a planet", ["no"]),
    ("is iron a metal", ["yes"]),
    ("is helium a liquid", ["no"]),
    ("is diamond hard", ["yes"]),
    ("is wood a metal", ["no"]),
    ("is copper a conductor", ["yes"]),
    ("is glass transparent", ["yes"]),
    ("is ice a gas", ["no"]),
    ("can penguins fly", ["no"]),
    ("can whales breathe underwater", ["no"]),
    ("is 3 greater than 7", ["no"]),
    ("is 10 less than 100", ["yes"]),
    ("is 50 greater than 49", ["yes"]),
    ("is 2 even", ["yes"]),
    ("is 13 odd", ["yes"]),
    ("is 9 a prime number", ["no"]),
    ("is 19 a prime number", ["yes"]),
    ("is 29 a prime number", ["yes"]),
    ("is 25 a prime number", ["no"]),
    ("is 43 a prime number", ["yes"]),
    ("is 33 a prime number", ["no"]),
    ("is 59 a prime number", ["yes"]),
    ("is 57 a prime number", ["no"]),
    ("is 73 a prime number", ["yes"]),
    ("is 95 a prime number", ["no"]),
]

# ═══════════════════════════════════════════════════════════════
# COMPARATIVE + IDENTITY (3 questions)
# ═══════════════════════════════════════════════════════════════

COMPARATIVE = [
    ("which is harder diamond or glass", ["diamond"]),
    ("who are you", ["axima", "intelligence", "engine"]),
    ("what can you do", ["answer", "math", "reason", "fact"]),
]

# ═══════════════════════════════════════════════════════════════
# ONLINE (30 new questions - needs internet)
# ═══════════════════════════════════════════════════════════════

ONLINE = [
    ("what is the capital of south korea", ["seoul"]),
    ("who invented the radio", ["marconi", "tesla"]),
    ("what is the largest desert", ["sahara", "antarctic"]),
    ("what is the smallest country", ["vatican"]),
    ("who discovered electricity", ["franklin", "faraday"]),
    ("what is the deepest ocean", ["pacific", "mariana"]),
    ("what is the tallest building", ["burj", "khalifa"]),
    ("what is the capital of canada", ["ottawa"]),
    ("what is evolution", ["change", "species", "adapt", "natural selection"]),
    ("who invented the airplane", ["wright"]),
    ("what is the speed of sound", ["343", "340", "meter"]),
    ("what is the capital of egypt", ["cairo"]),
    ("who wrote the odyssey", ["homer"]),
    ("what is the largest animal", ["blue whale", "whale"]),
    ("what is the capital of russia", ["moscow"]),
    ("what is the capital of mexico", ["mexico city"]),
    ("who invented the telescope", ["galileo", "lippershey", "lippershay"]),
    ("what is the highest mountain", ["everest"]),
    ("what is the capital of argentina", ["buenos aires"]),
    ("what is the human body temperature", ["37", "98.6"]),
    ("who invented dynamite", ["nobel"]),
    ("what is the capital of turkey", ["ankara"]),
    ("what is the fastest animal", ["cheetah", "falcon"]),
    ("who discovered oxygen", ["lavoisier", "priestley", "scheele"]),
    ("what is the capital of japan", ["tokyo"]),
    ("what is the great barrier reef", ["coral", "australia", "ocean"]),
    ("who invented the steam engine", ["watt", "newcomen"]),
    ("what is the capital of poland", ["warsaw"]),
    ("what is the largest continent", ["asia"]),
    ("who discovered america", ["columbus", "viking", "leif"]),
]

# ═══════════════════════════════════════════════════════════════
# TEST RUNNER — Uses full Python pipeline (hybrid_ai.py)
# ═══════════════════════════════════════════════════════════════

import subprocess

def query_c_engine(question):
    """Query C engine directly."""
    try:
        result = subprocess.run(
            [AI_BIN], input=f"{question}\n/quit\n",
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith('>') and len(line) > 5:
                answer = line[1:].strip()
                if answer and 'How can I' not in answer and 'Goodbye' not in answer:
                    return answer
    except:
        pass
    return None


def query_python_pipeline(question):
    """Query through full Python pipeline (QIR + CSE + Self-Learning + all upgrades)."""
    try:
        from hybrid_ai import Axima
        global _axima
        if '_axima' not in globals():
            _axima = Axima()
        result = _axima.ask(question)
        return result.get('response', '')
    except Exception as e:
        return None

_axima = None


def query_worldsim(question):
    """Query WorldSim for causal questions."""
    try:
        from world_sim import WorldSimulator
        ws = WorldSimulator()
        match = re.search(r'(?:if you|if i|if)\s+(\w+)\s+(.+?)(?:\?|$)', question.lower())
        if match:
            action, obj = match.group(1), match.group(2).strip().rstrip('?.')
            result = ws.simulate(action, obj)
            if result:
                return str(result[0][0]) if isinstance(result[0], tuple) else str(result[0])
        match2 = re.search(r'(?:if|when)\s+(.+?)\s+(?:meets|touches|hits)\s+(.+?)(?:\?|$)', question.lower())
        if match2:
            action = 'contact'
            obj = f"{match2.group(1)} {match2.group(2)}".strip().rstrip('?.')
            result = ws.simulate(action, obj)
            if result:
                return str(result[0][0]) if isinstance(result[0], tuple) else str(result[0])
    except:
        pass
    return None


def query_causal_full(question):
    """Causal: try Python pipeline first (has CAE), fall back to WorldSim."""
    answer = query_python_pipeline(question)
    if answer and len(answer) > 10:
        return answer
    return query_worldsim(question)


def query_online(question):
    """Query online search engine directly (not through hybrid_ai pipeline)."""
    try:
        from online_search import get_engine
        engine = get_engine()
        return engine.search(question)
    except Exception:
        return None


def check_answer(response, expected):
    """Check if response matches expected (with stem/partial matching)."""
    if not response:
        return False
    resp_lower = response.lower()
    if isinstance(expected, str):
        return expected.lower() in resp_lower
    elif isinstance(expected, list):
        for kw in expected:
            kw_lower = kw.lower()
            # Direct match
            if kw_lower in resp_lower:
                return True
            # Stem match: 'ice' matches 'icy', 'immune' matches 'immunity'
            if len(kw_lower) >= 3:
                if kw_lower + 'y' in resp_lower or kw_lower + 'ity' in resp_lower or \
                   kw_lower + 'tion' in resp_lower or kw_lower + 'al' in resp_lower or \
                   kw_lower + 'ous' in resp_lower or kw_lower + 'ive' in resp_lower or \
                   kw_lower + 'ing' in resp_lower or kw_lower + 'ed' in resp_lower or \
                   kw_lower + 'er' in resp_lower or kw_lower + 's' in resp_lower:
                    return True
                # Also check if expected is a stem of a word in response
                # e.g., 'tectonic' matches 'tectonic', 'space' matches 'interstellar space'
                if any(kw_lower in word for word in resp_lower.split()):
                    return True
    return False


def run_category(name, questions, query_func):
    """Run a category of questions."""
    stats = {'pass': 0, 'fail': 0, 'no_answer': 0, 'times': [], 'errors': []}
    total = len(questions)

    for i, item in enumerate(questions):
        q = item[0]
        expected = item[1]

        start = time.time()
        answer = query_func(q)
        elapsed = time.time() - start
        stats['times'].append(elapsed)

        if not answer:
            stats['no_answer'] += 1
        elif check_answer(answer, expected):
            stats['pass'] += 1
        else:
            stats['fail'] += 1
            stats['errors'].append((q, answer[:80] if answer else 'None', expected))

        if (i + 1) % 10 == 0:
            print(f"    [{i+1}/{total}] ✓{stats['pass']} ✗{stats['fail']} gap:{stats['no_answer']}", flush=True)

    return stats


def main():
    print("═" * 70)
    print("  AXIMA v3.1 — FRESH 203-QUESTION BENCHMARK (ALL NEW)")
    print("  Includes: 10 Upgrades (QIR, CSE, Self-Learning, Hot Cache)")
    print("═" * 70)
    print()

    tracemalloc.start()
    total_start = time.time()
    all_results = {}

    # Initialize Python pipeline once
    print("  Initializing Python pipeline...")
    global _axima
    from hybrid_ai import Axima
    _axima = Axima()
    print("  ✓ Ready\n")

    # ─── OFFLINE TESTS ───
    print("━━━ PHASE 1: OFFLINE (C Engine + Python Pipeline) ━━━\n")

    print(f"  [MATH] {len(MATH)} questions...")
    all_results['math'] = run_category('math', MATH, query_c_engine)
    m = all_results['math']
    print(f"    RESULT: ✓{m['pass']}/{len(MATH)} | ✗{m['fail']} | gap:{m['no_answer']} | avg:{sum(m['times'])/len(m['times'])*1000:.0f}ms\n")

    print(f"  [KNOWLEDGE] {len(KNOWLEDGE)} questions (Python pipeline)...")
    all_results['knowledge'] = run_category('knowledge', KNOWLEDGE, query_python_pipeline)
    k = all_results['knowledge']
    print(f"    RESULT: ✓{k['pass']}/{len(KNOWLEDGE)} | ✗{k['fail']} | gap:{k['no_answer']} | avg:{sum(k['times'])/len(k['times'])*1000:.0f}ms\n")

    print(f"  [CAUSAL] {len(CAUSAL)} questions (CAE + WorldSim)...")
    all_results['causal'] = run_category('causal', CAUSAL, query_causal_full)
    c = all_results['causal']
    print(f"    RESULT: ✓{c['pass']}/{len(CAUSAL)} | ✗{c['fail']} | gap:{c['no_answer']} | avg:{sum(c['times'])/len(c['times'])*1000:.0f}ms\n")

    print(f"  [LOGIC] {len(LOGIC)} questions (Python Pipeline — Boolean + Syllogisms)...")
    all_results['logic'] = run_category('logic', LOGIC, query_python_pipeline)
    l = all_results['logic']
    print(f"    RESULT: ✓{l['pass']}/{len(LOGIC)} | ✗{l['fail']} | gap:{l['no_answer']} | avg:{sum(l['times'])/len(l['times'])*1000:.0f}ms\n")

    print(f"  [COMPARATIVE] {len(COMPARATIVE)} questions...")
    all_results['comparative'] = run_category('comparative', COMPARATIVE, query_python_pipeline)
    v = all_results['comparative']
    print(f"    RESULT: ✓{v['pass']}/{len(COMPARATIVE)} | ✗{v['fail']} | gap:{v['no_answer']} | avg:{sum(v['times'])/len(v['times'])*1000:.0f}ms\n")

    # ─── ONLINE TESTS ───
    print("━━━ PHASE 2: ONLINE (Web Search) ━━━\n")
    print(f"  [ONLINE] {len(ONLINE)} questions...")
    all_results['online'] = run_category('online', ONLINE, query_online)
    o = all_results['online']
    print(f"    RESULT: ✓{o['pass']}/{len(ONLINE)} | ✗{o['fail']} | gap:{o['no_answer']} | avg:{sum(o['times'])/len(o['times'])*1000:.0f}ms\n")

    # ─── FINAL RESULTS ───
    total_time = time.time() - total_start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_q = sum(len(x) for x in [MATH, KNOWLEDGE, CAUSAL, LOGIC, COMPARATIVE, ONLINE])
    total_pass = sum(r['pass'] for r in all_results.values())
    total_fail = sum(r['fail'] for r in all_results.values())
    total_gap = sum(r['no_answer'] for r in all_results.values())

    offline_pass = sum(all_results[k]['pass'] for k in ['math', 'knowledge', 'causal', 'logic', 'comparative'])
    offline_total = len(MATH) + len(KNOWLEDGE) + len(CAUSAL) + len(LOGIC) + len(COMPARATIVE)

    print("━" * 70)
    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║    AXIMA v3.1 — FRESH BENCHMARK RESULTS (203 NEW Qs)        ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"  OFFLINE: {offline_pass}/{offline_total} ({offline_pass/max(1,offline_total)*100:.0f}%)")
    print(f"    Math:           {all_results['math']['pass']}/{len(MATH)} ({all_results['math']['pass']/len(MATH)*100:.0f}%)")
    print(f"    Knowledge:      {all_results['knowledge']['pass']}/{len(KNOWLEDGE)} ({all_results['knowledge']['pass']/len(KNOWLEDGE)*100:.0f}%)")
    print(f"    Causal:         {all_results['causal']['pass']}/{len(CAUSAL)} ({all_results['causal']['pass']/len(CAUSAL)*100:.0f}%)")
    print(f"    Logic/Boolean:  {all_results['logic']['pass']}/{len(LOGIC)} ({all_results['logic']['pass']/len(LOGIC)*100:.0f}%)")
    print(f"    Comparative:    {all_results['comparative']['pass']}/{len(COMPARATIVE)} ({all_results['comparative']['pass']/len(COMPARATIVE)*100:.0f}%)")
    print()
    print(f"  ONLINE: {all_results['online']['pass']}/{len(ONLINE)} ({all_results['online']['pass']/len(ONLINE)*100:.0f}%)")
    print()
    print(f"  ─────────────────────────────────────────────")
    print(f"  TOTAL: {total_pass}/{total_q} ({total_pass/max(1,total_q)*100:.0f}%)")
    print(f"  Wrong answers: {total_fail}")
    print(f"  Honest gaps:   {total_gap}")
    print()
    print(f"  Speed: {total_time:.0f}s total | Peak RAM: {peak/1024/1024:.1f} MB")
    print()

    # Show errors
    total_errors = []
    for cat, stats in all_results.items():
        for err in stats.get('errors', []):
            total_errors.append((cat, err))
    if total_errors:
        print(f"  ═══ ERRORS ({len(total_errors)} total) ═══")
        for cat, (q, got, expected) in total_errors[:15]:
            print(f"    [{cat}] {q}")
            print(f"      Got: {got}")
            print(f"      Want: {expected}")
        if len(total_errors) > 15:
            print(f"    ... and {len(total_errors)-15} more")
        print()

    print("━" * 70)


if __name__ == '__main__':
    main()
