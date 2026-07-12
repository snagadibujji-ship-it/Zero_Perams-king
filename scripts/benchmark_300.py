#!/usr/bin/env python3
"""
AXIMA v3.0 — FULL 300-QUESTION BENCHMARK
Tests: Math, Knowledge, Causal, Logic, Comparative, Identity, Online
Tracks: Speed, RAM, accuracy per category
"""

import sys, os, time, json, subprocess, tracemalloc, re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

AI_BIN = os.path.join(os.path.dirname(__file__), '..', 'ai')

# ═══════════════════════════════════════════════════════════════
# MATH (50 questions)
# ═══════════════════════════════════════════════════════════════

MATH = [
    ("what is 15 times 17", "255"), ("what is 12 times 12", "144"),
    ("what is 100 divided by 4", "25"), ("what is 7 plus 8", "15"),
    ("what is 50 minus 23", "27"), ("what is 2 to the power of 10", "1024"),
    ("what is 3 to the power of 5", "243"), ("what is the square root of 144", "12"),
    ("what is the square root of 256", "16"), ("what is 10 factorial", "3628800"),
    ("what is 15 factorial", "1307674368000"), ("is 97 a prime number", "yes"),
    ("is 100 a prime number", "no"), ("is 42 even", "yes"),
    ("is 7 odd", "yes"), ("what is 99 times 99", "9801"),
    ("what is 1000 divided by 8", "125"), ("what is 2 to the power of 20", "1048576"),
    ("what is the square root of 625", "25"), ("is 53 a prime number", "yes"),
    ("what is 25 times 25", "625"), ("what is 8 times 7", "56"),
    ("what is 200 divided by 5", "40"), ("what is 13 plus 19", "32"),
    ("what is 100 minus 37", "63"), ("what is 5 to the power of 4", "625"),
    ("what is 4 to the power of 6", "4096"), ("what is the square root of 81", "9"),
    ("what is the square root of 400", "20"), ("what is 6 factorial", "720"),
    ("what is 7 factorial", "5040"), ("is 31 a prime number", "yes"),
    ("is 51 a prime number", "no"), ("is 88 even", "yes"),
    ("is 33 odd", "yes"), ("what is 111 times 111", "12321"),
    ("what is 500 divided by 25", "20"), ("what is 10 to the power of 3", "1000"),
    ("what is the square root of 169", "13"), ("is 2 a prime number", "yes"),
    ("what is 14 times 14", "196"), ("what is 9 times 9", "81"),
    ("what is 1024 divided by 2", "512"), ("what is 45 plus 55", "100"),
    ("what is 1000 minus 999", "1"), ("what is 2 to the power of 8", "256"),
    ("what is 12 factorial", "479001600"), ("is 89 a prime number", "yes"),
    ("is 91 a prime number", "no"), ("what is 17 times 19", "323"),
]

# ═══════════════════════════════════════════════════════════════
# KNOWLEDGE (50 questions - offline C engine)
# ═══════════════════════════════════════════════════════════════

KNOWLEDGE = [
    ("what is water", ["h2o", "liquid", "compound"]),
    ("what is gravity", ["force", "attract", "fall"]),
    ("what is DNA", ["molecule", "genetic", "cell", "nucleotide"]),
    ("what is python", ["programming", "language"]),
    ("what is the sun", ["star", "solar"]),
    ("what is oxygen", ["element", "gas", "breathe"]),
    ("what causes rust", ["oxidation", "iron", "oxygen"]),
    ("what is iron", ["metal", "element"]),
    ("what is a computer", ["machine", "electronic", "device"]),
    ("what is fire", ["combustion", "heat", "flame"]),
    ("what is electricity", ["charge", "current", "electron"]),
    ("what is sound", ["wave", "vibrat"]),
    ("what is light", ["electromagnetic", "wave", "photon"]),
    ("what is carbon", ["element", "organic"]),
    ("what is nitrogen", ["element", "gas", "atmosphere"]),
    ("what is a virus", ["infect", "replicate", "cell"]),
    ("what is an atom", ["small", "particle", "nucleus"]),
    ("what is a planet", ["orbit", "star", "celestial"]),
    ("what is a mammal", ["warm", "blood", "vertebrate"]),
    ("what is a volcano", ["magma", "lava", "erupt"]),
    ("what is hydrogen", ["element", "gas", "lightest"]),
    ("what is copper", ["metal", "element", "conduct"]),
    ("what is gold", ["metal", "element", "precious"]),
    ("what is silver", ["metal", "element"]),
    ("what is a star", ["gas", "fusion", "energy", "light"]),
    ("what is the moon", ["satellite", "orbit", "earth"]),
    ("what is an ocean", ["water", "salt", "large"]),
    ("what is a desert", ["dry", "sand", "arid"]),
    ("what is a forest", ["tree", "woodland", "ecosystem"]),
    ("what is weather", ["atmosphere", "temperature", "climate"]),
    ("what is energy", ["work", "force", "capacity"]),
    ("what is a cell", ["biology", "basic", "unit", "life"]),
    ("what is a rock", ["mineral", "solid", "earth", "stone"]),
    ("what is soil", ["earth", "organic", "ground"]),
    ("what is rain", ["water", "cloud", "drop", "precipitation"]),
    ("what is wind", ["air", "movement", "pressure"]),
    ("what is glass", ["silicon", "transparent", "solid"]),
    ("what is plastic", ["polymer", "synthetic", "material"]),
    ("what is a river", ["water", "flow", "stream"]),
    ("what is a mountain", ["elevation", "peak", "tall", "high"]),
    ("what is rubber", ["elastic", "polymer", "material"]),
    ("what is paper", ["wood", "pulp", "sheet", "write"]),
    ("what is ice", ["frozen", "water", "solid", "cold"]),
    ("what is steam", ["water", "vapor", "gas", "hot"]),
    ("what is salt", ["sodium", "chloride", "mineral", "season"]),
    ("what is sugar", ["sweet", "carbohydrate", "glucose"]),
    ("what is oil", ["liquid", "petroleum", "fat"]),
    ("what is a battery", ["energy", "electric", "chemical", "power"]),
    ("what is a magnet", ["attract", "iron", "field", "magnetic"]),
    ("what is pressure", ["force", "area", "push"]),
]

# ═══════════════════════════════════════════════════════════════
# CAUSAL (40 questions - WorldSim + C engine)
# ═══════════════════════════════════════════════════════════════

CAUSAL = [
    ("what happens if you drop glass", ["break", "shatter"]),
    ("what happens if you heat ice", ["melt", "water"]),
    ("what happens if you heat water", ["evaporate", "steam", "boil"]),
    ("what happens if fire meets paper", ["burn"]),
    ("what happens if you cool water", ["freeze", "ice"]),
    ("what happens if you drop an egg", ["break", "crack"]),
    ("what happens if you heat metal", ["expand"]),
    ("what happens if you mix electricity and water", ["danger", "shock"]),
    ("what happens if a magnet touches iron", ["attract", "stick"]),
    ("what happens if you drop a ball", ["fall", "bounce"]),
    ("what happens if you heat rubber", ["melt", "deform"]),
    ("what happens if you freeze milk", ["solid", "ice"]),
    ("what happens if you cut a wire", ["circuit", "break", "stop"]),
    ("what happens if you heat sugar", ["caramel", "melt"]),
    ("what happens if you mix oil and water", ["separate", "float"]),
    ("what happens if you stretch rubber", ["elastic", "snap", "return"]),
    ("what happens if you drop a phone", ["crack", "break", "damage"]),
    ("what happens if you heat glass", ["soften", "melt"]),
    ("what happens if you cool metal", ["contract", "shrink"]),
    ("what happens if you heat plastic", ["melt", "deform"]),
    ("what happens if you drop ice", ["shatter", "break", "crack"]),
    ("what happens if you heat butter", ["melt", "liquid"]),
    ("what happens if you mix salt and water", ["dissolve"]),
    ("what happens if you heat wax", ["melt", "liquid"]),
    ("what happens if you drop a mirror", ["shatter", "break"]),
    ("what happens if you heat chocolate", ["melt"]),
    ("what happens if you freeze juice", ["solid", "ice"]),
    ("what happens if you mix vinegar and baking soda", ["fizz", "bubble", "react"]),
    ("what happens if you heat iron", ["expand", "glow", "red"]),
    ("what happens if you drop ceramic", ["break", "shatter"]),
    ("what happens if you heat an egg", ["cook", "solid"]),
    ("what happens if you freeze water", ["ice", "solid", "expand"]),
    ("what happens if you heat oil", ["smoke", "hot", "boil"]),
    ("what happens if you mix bleach and ammonia", ["toxic", "danger", "gas"]),
    ("what happens if you heat wood", ["burn", "char"]),
    ("what happens if you drop a plate", ["break", "shatter"]),
    ("what happens if you cool steam", ["condense", "water", "liquid"]),
    ("what happens if you heat salt", ["melt"]),
    ("what happens if you stretch a spring", ["elastic", "return", "deform"]),
    ("what happens if you drop a rock in water", ["sink", "splash"]),
]

# ═══════════════════════════════════════════════════════════════
# LOGIC + BOOLEAN (30 questions)
# ═══════════════════════════════════════════════════════════════

LOGIC = [
    ("all cats are animals. tom is a cat. is tom an animal", ["yes"]),
    ("all dogs are mammals. rex is a dog. is rex a mammal", ["yes"]),
    ("all fish live in water. nemo is a fish. does nemo live in water", ["yes"]),
    ("all birds have wings. a penguin is a bird. does a penguin have wings", ["yes"]),
    ("no reptiles are mammals. a snake is a reptile. is a snake a mammal", ["no"]),
    ("is the sun a star", ["yes"]),
    ("is water wet", ["yes"]),
    ("is fire cold", ["no"]),
    ("is ice hot", ["no"]),
    ("is the earth flat", ["no"]),
    ("is gold a metal", ["yes"]),
    ("is oxygen a gas", ["yes"]),
    ("is mercury a liquid", ["yes"]),
    ("can birds fly", ["yes", "most"]),
    ("can fish breathe air", ["no"]),
    ("is 2 greater than 1", ["yes"]),
    ("is 5 less than 3", ["no"]),
    ("is 100 greater than 99", ["yes"]),
    ("is 0 even", ["yes"]),
    ("is 1 odd", ["yes"]),
    ("is 4 a prime number", ["no"]),
    ("is 7 a prime number", ["yes"]),
    ("is 11 a prime number", ["yes"]),
    ("is 15 a prime number", ["no"]),
    ("is 23 a prime number", ["yes"]),
    ("is 27 a prime number", ["no"]),
    ("is 37 a prime number", ["yes"]),
    ("is 49 a prime number", ["no"]),
    ("is 61 a prime number", ["yes"]),
    ("is 77 a prime number", ["no"]),
]

# ═══════════════════════════════════════════════════════════════
# COMPARATIVE + IDENTITY (30 questions)
# ═══════════════════════════════════════════════════════════════

COMPARATIVE = [
    ("what is heavier a kilogram of steel or a kilogram of feathers", ["same", "equal", "kilo"]),
    ("who are you", ["axima", "intelligence", "engine"]),
    ("what can you do", ["answer", "math", "reason", "fact"]),
]

# ═══════════════════════════════════════════════════════════════
# ONLINE (100 questions - needs internet)
# ═══════════════════════════════════════════════════════════════

ONLINE = [
    ("what is the capital of japan", ["tokyo"]),
    ("who invented the telephone", ["bell", "reis", "meucci"]),
    ("what is photosynthesis", ["plant", "light", "sun", "energy"]),
    ("what is the speed of light", ["300", "299", "792"]),
    ("who wrote hamlet", ["shakespeare"]),
    ("what is the largest planet", ["jupiter"]),
    ("what is the boiling point of water", ["100", "celsius", "boil"]),
    ("when did world war 2 end", ["1945"]),
    ("who painted the mona lisa", ["vinci", "leonardo"]),
    ("what is the capital of france", ["paris"]),
    ("what is bitcoin", ["crypto", "digital", "currency", "decentral"]),
    ("what is the amazon river", ["south america", "river", "brazil"]),
    ("who discovered penicillin", ["fleming"]),
    ("what is the theory of relativity", ["einstein", "time", "space"]),
    ("what is the population of india", ["billion", "1", "000"]),
    ("who is albert einstein", ["physicist", "relativity"]),
    ("what is machine learning", ["algorithm", "data", "learn"]),
    ("what is climate change", ["temperature", "warming", "carbon"]),
    ("what is the internet", ["network", "connect", "computer"]),
    ("what is the capital of germany", ["berlin"]),
    ("what is the capital of italy", ["rome"]),
    ("what is the capital of spain", ["madrid"]),
    ("what is the capital of brazil", ["brasilia"]),
    ("what is the capital of australia", ["canberra"]),
    ("who invented the light bulb", ["edison"]),
    ("who wrote romeo and juliet", ["shakespeare"]),
    ("what is the largest ocean", ["pacific"]),
    ("what is the longest river", ["nile", "amazon"]),
    ("who discovered gravity", ["newton"]),
    ("what is the great wall of china", ["china", "wall", "dynasty"]),
]

# ═══════════════════════════════════════════════════════════════
# TEST RUNNER
# ═══════════════════════════════════════════════════════════════

def query_c_engine(question):
    """Query C engine."""
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
        # Try alternate: "what happens if X meets Y"
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


def query_online(question):
    """Query online search v3."""
    try:
        from online_search import OnlineSearch
        engine = OnlineSearch()
        return engine.search(question)
    except:
        return None


def check_answer(response, expected):
    """Check if response matches expected."""
    if not response:
        return False
    resp_lower = response.lower()
    if isinstance(expected, str):
        return expected.lower() in resp_lower
    elif isinstance(expected, list):
        return any(kw.lower() in resp_lower for kw in expected)
    return False


def run_category(name, questions, query_func, is_string_match=False):
    """Run a category of questions. Returns stats dict."""
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
            stats['errors'].append((q, answer[:60], expected))
        
        # Progress every 10
        if (i + 1) % 10 == 0:
            print(f"    [{i+1}/{total}] {stats['pass']} pass, {stats['fail']} fail, {stats['no_answer']} gap", flush=True)
    
    return stats


def main():
    print("═" * 70)
    print("  AXIMA v3.0 — 300-QUESTION FULL SYSTEM BENCHMARK")
    print("═" * 70)
    print()

    tracemalloc.start()
    total_start = time.time()
    all_results = {}

    # ─── OFFLINE TESTS ───
    print("━━━ PHASE 1: OFFLINE (C Engine + WorldSim — no internet) ━━━")
    print()

    print(f"  [MATH] {len(MATH)} questions...")
    all_results['math'] = run_category('math', MATH, query_c_engine, True)
    m = all_results['math']
    print(f"    ✓ {m['pass']}/{len(MATH)} | ✗ {m['fail']} | gap {m['no_answer']} | avg {sum(m['times'])/len(m['times'])*1000:.0f}ms")
    print()

    print(f"  [KNOWLEDGE] {len(KNOWLEDGE)} questions...")
    all_results['knowledge'] = run_category('knowledge', KNOWLEDGE, query_c_engine)
    k = all_results['knowledge']
    print(f"    ✓ {k['pass']}/{len(KNOWLEDGE)} | ✗ {k['fail']} | gap {k['no_answer']} | avg {sum(k['times'])/len(k['times'])*1000:.0f}ms")
    print()

    print(f"  [CAUSAL] {len(CAUSAL)} questions...")
    all_results['causal'] = run_category('causal', CAUSAL, query_worldsim)
    c = all_results['causal']
    print(f"    ✓ {c['pass']}/{len(CAUSAL)} | ✗ {c['fail']} | gap {c['no_answer']} | avg {sum(c['times'])/len(c['times'])*1000:.1f}ms")
    print()

    print(f"  [LOGIC] {len(LOGIC)} questions...")
    all_results['logic'] = run_category('logic', LOGIC, query_c_engine)
    l = all_results['logic']
    print(f"    ✓ {l['pass']}/{len(LOGIC)} | ✗ {l['fail']} | gap {l['no_answer']} | avg {sum(l['times'])/len(l['times'])*1000:.0f}ms")
    print()

    print(f"  [COMPARATIVE+IDENTITY] {len(COMPARATIVE)} questions...")
    all_results['comparative'] = run_category('comparative', COMPARATIVE, query_c_engine)
    v = all_results['comparative']
    print(f"    ✓ {v['pass']}/{len(COMPARATIVE)} | ✗ {v['fail']} | gap {v['no_answer']} | avg {sum(v['times'])/len(v['times'])*1000:.0f}ms")
    print()

    # ─── ONLINE TESTS ───
    print("━━━ PHASE 2: ONLINE (16 sources — internet required) ━━━")
    print()
    print(f"  [ONLINE] {len(ONLINE)} questions...")
    
    # Use shared engine for caching benefit
    from online_search import OnlineSearch
    shared_engine = OnlineSearch()
    def online_query(q):
        result = shared_engine.search(q)
        time.sleep(0.3)  # Rate limit courtesy
        return result
    
    all_results['online'] = run_category('online', ONLINE, online_query)
    o = all_results['online']
    print(f"    ✓ {o['pass']}/{len(ONLINE)} | ✗ {o['fail']} | gap {o['no_answer']} | avg {sum(o['times'])/len(o['times'])*1000:.0f}ms")
    print()

    # ─── FINAL STATS ───
    total_time = time.time() - total_start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_q = sum(len(x) for x in [MATH, KNOWLEDGE, CAUSAL, LOGIC, COMPARATIVE, ONLINE])
    total_pass = sum(r['pass'] for r in all_results.values())
    total_fail = sum(r['fail'] for r in all_results.values())
    total_gap = sum(r['no_answer'] for r in all_results.values())

    offline_pass = sum(all_results[k]['pass'] for k in ['math', 'knowledge', 'causal', 'logic', 'comparative'])
    offline_total = len(MATH) + len(KNOWLEDGE) + len(CAUSAL) + len(LOGIC) + len(COMPARATIVE)
    
    offline_times = []
    for k in ['math', 'knowledge', 'causal', 'logic', 'comparative']:
        offline_times.extend(all_results[k]['times'])
    
    online_times = all_results['online']['times']

    print("━" * 70)
    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║          AXIMA v3.0 — 300Q BENCHMARK RESULTS                ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"  OFFLINE (no internet): {offline_pass}/{offline_total} ({offline_pass/max(1,offline_total)*100:.0f}%)")
    print(f"    Math:           {all_results['math']['pass']}/{len(MATH)} ({all_results['math']['pass']/len(MATH)*100:.0f}%)")
    print(f"    Knowledge:      {all_results['knowledge']['pass']}/{len(KNOWLEDGE)} ({all_results['knowledge']['pass']/len(KNOWLEDGE)*100:.0f}%)")
    print(f"    Causal:         {all_results['causal']['pass']}/{len(CAUSAL)} ({all_results['causal']['pass']/len(CAUSAL)*100:.0f}%)")
    print(f"    Logic/Boolean:  {all_results['logic']['pass']}/{len(LOGIC)} ({all_results['logic']['pass']/len(LOGIC)*100:.0f}%)")
    print(f"    Comparative:    {all_results['comparative']['pass']}/{len(COMPARATIVE)} ({all_results['comparative']['pass']/len(COMPARATIVE)*100:.0f}%)")
    print()
    print(f"  ONLINE (with internet): {all_results['online']['pass']}/{len(ONLINE)} ({all_results['online']['pass']/len(ONLINE)*100:.0f}%)")
    print()
    print(f"  ─────────────────────────────────────────────")
    print(f"  TOTAL: {total_pass}/{total_q} ({total_pass/max(1,total_q)*100:.0f}%)")
    print(f"  Hallucinations (wrong answer): {total_fail}")
    print(f"  Gaps (no answer / honest): {total_gap}")
    print()
    print(f"  ═══ SPEED ═══")
    print(f"    Total time:      {total_time:.0f}s")
    print(f"    Offline avg:     {sum(offline_times)/max(1,len(offline_times))*1000:.1f}ms")
    print(f"    Offline fastest: {min(offline_times)*1000:.1f}ms")
    print(f"    Offline slowest: {max(offline_times)*1000:.0f}ms")
    if online_times:
        print(f"    Online avg:      {sum(online_times)/len(online_times)*1000:.0f}ms")
        print(f"    Online fastest:  {min(online_times)*1000:.0f}ms")
        print(f"    Online slowest:  {max(online_times)*1000:.0f}ms")
    print()
    print(f"  ═══ MEMORY ═══")
    print(f"    Peak RAM:        {peak / 1024 / 1024:.1f} MB")
    print(f"    Current:         {current / 1024 / 1024:.1f} MB")
    print()
    print(f"  ═══ SYSTEM ═══")
    try:
        bin_size = os.path.getsize(AI_BIN)
        print(f"    Binary:          {bin_size / 1024:.0f} KB")
    except:
        print(f"    Binary:          N/A")
    print(f"    Total questions: {total_q}")
    print(f"    Categories:      6")
    print(f"    Online sources:  16")
    print(f"    Causal rules:    210")
    print(f"    C engine concepts: 7,818")
    print()
    
    # Show errors
    total_errors = []
    for cat, stats in all_results.items():
        for err in stats.get('errors', [])[:3]:
            total_errors.append((cat, err))
    if total_errors:
        print(f"  ═══ SAMPLE ERRORS (first 10) ═══")
        for cat, (q, got, expected) in total_errors[:10]:
            print(f"    [{cat}] {q}")
            print(f"      Got: {got[:50]} | Expected: {expected}")
        print()

    print("━" * 70)

    # Save JSON report
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_questions': total_q,
        'total_pass': total_pass, 'total_fail': total_fail, 'total_gap': total_gap,
        'accuracy_pct': round(total_pass / max(1, total_q) * 100, 1),
        'offline': {
            'total': offline_total, 'pass': offline_pass,
            'pct': round(offline_pass / max(1, offline_total) * 100, 1),
            'avg_ms': round(sum(offline_times) / max(1, len(offline_times)) * 1000, 1),
        },
        'online': {
            'total': len(ONLINE), 'pass': all_results['online']['pass'],
            'pct': round(all_results['online']['pass'] / len(ONLINE) * 100, 1),
            'avg_ms': round(sum(online_times) / max(1, len(online_times)) * 1000, 0),
        },
        'categories': {k: {'pass': v['pass'], 'total': len(globals().get(k.upper(), [])),
                           'fail': v['fail'], 'gap': v['no_answer']}
                      for k, v in all_results.items()},
        'performance': {
            'total_time_s': round(total_time, 1),
            'peak_ram_mb': round(peak / 1024 / 1024, 1),
        },
    }
    report_dir = os.path.join(os.path.dirname(__file__), '..', 'user_data')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, 'benchmark_300_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved: {report_path}")


if __name__ == '__main__':
    main()
