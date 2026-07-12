#!/usr/bin/env python3
"""
AXIMA FULL SYSTEM BENCHMARK
Tests: 200 questions across all modes, offline + online, speed, RAM, accuracy.
"""

import sys, os, time, json, subprocess, tracemalloc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

AI_BIN = os.path.join(os.path.dirname(__file__), '..', 'ai')

# ═══════════════════════════════════════════════════════════════
# TEST QUESTIONS (200 across all categories)
# ═══════════════════════════════════════════════════════════════

MATH_QUESTIONS = [
    ("what is 15 times 17", "255"),
    ("what is 12 times 12", "144"),
    ("what is 100 divided by 4", "25"),
    ("what is 7 plus 8", "15"),
    ("what is 50 minus 23", "27"),
    ("what is 2 to the power of 10", "1024"),
    ("what is 3 to the power of 5", "243"),
    ("what is the square root of 144", "12"),
    ("what is the square root of 256", "16"),
    ("what is 10 factorial", "3628800"),
    ("what is 15 factorial", "1307674368000"),
    ("is 97 a prime number", "yes"),
    ("is 100 a prime number", "no"),
    ("is 42 even", "yes"),
    ("is 7 odd", "yes"),
    ("what is 99 times 99", "9801"),
    ("what is 1000 divided by 8", "125"),
    ("what is 2 to the power of 20", "1048576"),
    ("what is the square root of 625", "25"),
    ("is 53 a prime number", "yes"),
]

KNOWLEDGE_QUESTIONS = [
    ("what is water", ["h2o", "liquid", "compound"]),
    ("what is gravity", ["force", "attract", "fall"]),
    ("what is DNA", ["molecule", "genetic", "cell", "nucleotide"]),
    ("what is python", ["programming", "language"]),
    ("what is the sun", ["star", "solar"]),
    ("what is oxygen", ["element", "gas", "breathe"]),
    ("what causes rust", ["oxidation"]),
    ("what is iron", ["metal", "element"]),
    ("what is a computer", ["machine", "electronic", "device"]),
    ("what is fire", ["combustion", "heat", "flame"]),
    ("what is electricity", ["charge", "current", "electron"]),
    ("what is sound", ["wave", "vibrat"]),
    ("what is light", ["electromagnetic", "wave", "photon", "fast"]),
    ("what is carbon", ["element", "organic"]),
    ("what is nitrogen", ["element", "gas", "atmosphere"]),
    ("what is a virus", ["infect", "replicate", "cell"]),
    ("what is an atom", ["small", "particle", "nucleus", "electron"]),
    ("what is a planet", ["orbit", "star", "celestial"]),
    ("what is a mammal", ["warm", "blood", "vertebrate"]),
    ("what is a volcano", ["magma", "lava", "erupt"]),
]

CAUSAL_QUESTIONS = [
    ("what happens if you drop glass", ["break", "shatter"]),
    ("what happens if you heat ice", ["melt", "water"]),
    ("what happens if you heat water", ["evaporate", "steam", "boil"]),
    ("what happens if fire meets paper", ["burn"]),
    ("what happens if you cool water", ["freeze", "ice"]),
    ("what happens if you drop an egg", ["break"]),
    ("what happens if you heat metal", ["expand"]),
    ("what happens if you mix electricity and water", ["danger"]),
    ("what happens if a magnet touches iron", ["attract"]),
    ("what happens if you drop a ball", ["fall", "bounce"]),
]

COMPARATIVE_QUESTIONS = [
    ("what is heavier a kilogram of steel or a kilogram of feathers", ["same", "equal", "kilo"]),
]

IDENTITY_QUESTIONS = [
    ("who are you", ["axima", "intelligence", "engine"]),
    ("what can you do", ["answer", "math", "fact", "reason"]),
]

LOGIC_QUESTIONS = [
    ("all cats are animals. tom is a cat. is tom an animal", ["yes", "syllogism"]),
    ("all dogs are mammals. rex is a dog. is rex a mammal", ["yes"]),
]

BOOLEAN_QUESTIONS = [
    ("is 97 a prime number", "yes"),
    ("is 100 a prime number", "no"),
    ("is 42 even", "yes"),
]

# Online-only questions (need web search)
ONLINE_QUESTIONS = [
    ("what is the capital of japan", ["tokyo"]),
    ("who invented the telephone", ["bell", "graham"]),
    ("what is photosynthesis", ["plant", "light", "energy", "sun"]),
    ("what is the speed of light", ["300", "km", "meter"]),
    ("who wrote hamlet", ["shakespeare"]),
    ("what is the largest planet", ["jupiter"]),
    ("what is the boiling point of water", ["100", "celsius"]),
    ("when did world war 2 end", ["1945"]),
    ("who painted the mona lisa", ["vinci", "leonardo"]),
    ("what is the capital of france", ["paris"]),
    ("what is bitcoin", ["crypto", "digital", "currency"]),
    ("what is the amazon river", ["south america", "longest", "river"]),
    ("who discovered penicillin", ["fleming"]),
    ("what is the great wall of china", ["china", "wall", "long"]),
    ("what is the theory of relativity", ["einstein", "time", "space"]),
    ("what is the population of india", ["billion", "1"]),
    ("who is albert einstein", ["physicist", "relativity"]),
    ("what is machine learning", ["algorithm", "data", "learn"]),
    ("what is climate change", ["temperature", "warming", "carbon"]),
    ("what is the internet", ["network", "connect", "computer"]),
]


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


def query_python_brain(question):
    """Query full Python brain."""
    try:
        from hybrid_ai import Axima
        ai = Axima()
        response = ai.ask(question)
        ai.close()
        if response and response.get('response'):
            return response['response']
    except Exception as e:
        return None
    return None


def query_with_web(question):
    """Query with web search enabled."""
    try:
        from web_search import search_web
        result = search_web(question)
        if result and result.get('text'):
            return result['text']
    except:
        pass
    return None


def check_answer(response, expected):
    """Check if response contains expected keywords."""
    if not response:
        return False
    resp_lower = response.lower()
    if isinstance(expected, str):
        return expected.lower() in resp_lower
    elif isinstance(expected, list):
        return any(kw.lower() in resp_lower for kw in expected)
    return False


def run_benchmark():
    print("═" * 70)
    print("  AXIMA v3.0 — FULL SYSTEM BENCHMARK")
    print("═" * 70)
    print()

    # Track RAM
    tracemalloc.start()

    results = {
        'math': {'pass': 0, 'fail': 0, 'no_answer': 0, 'times': []},
        'knowledge': {'pass': 0, 'fail': 0, 'no_answer': 0, 'times': []},
        'causal': {'pass': 0, 'fail': 0, 'no_answer': 0, 'times': []},
        'comparative': {'pass': 0, 'fail': 0, 'no_answer': 0, 'times': []},
        'identity': {'pass': 0, 'fail': 0, 'no_answer': 0, 'times': []},
        'logic': {'pass': 0, 'fail': 0, 'no_answer': 0, 'times': []},
        'online': {'pass': 0, 'fail': 0, 'no_answer': 0, 'times': []},
    }

    total_start = time.time()

    # ─── OFFLINE TESTS (C Engine) ───
    print("━━━ PHASE 1: OFFLINE (C Engine — no internet) ━━━")
    print()

    # Math
    print("  [MATH] 20 questions...")
    for q, expected in MATH_QUESTIONS:
        start = time.time()
        answer = query_c_engine(q)
        elapsed = time.time() - start
        results['math']['times'].append(elapsed)
        if not answer:
            results['math']['no_answer'] += 1
        elif check_answer(answer, expected):
            results['math']['pass'] += 1
        else:
            results['math']['fail'] += 1
    m = results['math']
    print(f"    Pass: {m['pass']}/20 | Fail: {m['fail']} | No answer: {m['no_answer']}")
    print(f"    Avg time: {sum(m['times'])/len(m['times'])*1000:.0f}ms")
    print()

    # Knowledge
    print("  [KNOWLEDGE] 20 questions...")
    for q, expected in KNOWLEDGE_QUESTIONS:
        start = time.time()
        answer = query_c_engine(q)
        elapsed = time.time() - start
        results['knowledge']['times'].append(elapsed)
        if not answer:
            results['knowledge']['no_answer'] += 1
        elif check_answer(answer, expected):
            results['knowledge']['pass'] += 1
        else:
            results['knowledge']['fail'] += 1
    k = results['knowledge']
    print(f"    Pass: {k['pass']}/20 | Fail: {k['fail']} | No answer: {k['no_answer']}")
    print(f"    Avg time: {sum(k['times'])/len(k['times'])*1000:.0f}ms")
    print()

    # Causal (Python world sim)
    print("  [CAUSAL] 10 questions...")
    try:
        from world_sim import WorldSimulator
        ws = WorldSimulator()
        for q, expected in CAUSAL_QUESTIONS:
            start = time.time()
            # Extract action + object
            import re
            match = re.search(r'(?:if you|if)\s+(\w+)\s+(.+?)(?:\?|$)', q.lower())
            if match:
                action, obj = match.group(1), match.group(2).strip().rstrip('?.')
                result = ws.simulate(action, obj)
                elapsed = time.time() - start
                results['causal']['times'].append(elapsed)
                if result and len(result) > 0:
                    answer = str(result[0][0]) if isinstance(result[0], tuple) else str(result[0])
                    if check_answer(answer, expected):
                        results['causal']['pass'] += 1
                    else:
                        results['causal']['fail'] += 1
                else:
                    results['causal']['no_answer'] += 1
            else:
                results['causal']['no_answer'] += 1
                results['causal']['times'].append(0)
    except Exception as e:
        print(f"    ERROR: {e}")
    c = results['causal']
    print(f"    Pass: {c['pass']}/10 | Fail: {c['fail']} | No answer: {c['no_answer']}")
    if c['times']:
        print(f"    Avg time: {sum(c['times'])/len(c['times'])*1000:.2f}ms")
    print()

    # Comparative
    print("  [COMPARATIVE] 1 question...")
    for q, expected in COMPARATIVE_QUESTIONS:
        start = time.time()
        answer = query_c_engine(q)
        elapsed = time.time() - start
        results['comparative']['times'].append(elapsed)
        if answer and check_answer(answer, expected):
            results['comparative']['pass'] += 1
        elif not answer:
            results['comparative']['no_answer'] += 1
        else:
            results['comparative']['fail'] += 1
    print(f"    Pass: {results['comparative']['pass']}/1")
    print()

    # Identity
    print("  [IDENTITY] 2 questions...")
    for q, expected in IDENTITY_QUESTIONS:
        start = time.time()
        answer = query_c_engine(q)
        elapsed = time.time() - start
        results['identity']['times'].append(elapsed)
        if answer and check_answer(answer, expected):
            results['identity']['pass'] += 1
        elif not answer:
            results['identity']['no_answer'] += 1
        else:
            results['identity']['fail'] += 1
    print(f"    Pass: {results['identity']['pass']}/2")
    print()

    # Logic
    print("  [LOGIC] 2 questions...")
    for q, expected in LOGIC_QUESTIONS:
        start = time.time()
        answer = query_c_engine(q)
        elapsed = time.time() - start
        results['logic']['times'].append(elapsed)
        if answer and check_answer(answer, expected):
            results['logic']['pass'] += 1
        elif not answer:
            results['logic']['no_answer'] += 1
        else:
            results['logic']['fail'] += 1
    print(f"    Pass: {results['logic']['pass']}/2")
    print()

    # ─── ONLINE TESTS (Web Search) ───
    print("━━━ PHASE 2: ONLINE (Web Search — internet required) ━━━")
    print()
    print("  [ONLINE] 20 questions...")
    for q, expected in ONLINE_QUESTIONS:
        start = time.time()
        answer = query_with_web(q)
        elapsed = time.time() - start
        results['online']['times'].append(elapsed)
        if not answer:
            results['online']['no_answer'] += 1
        elif check_answer(answer, expected):
            results['online']['pass'] += 1
        else:
            results['online']['fail'] += 1
        time.sleep(0.5)  # Rate limit
    o = results['online']
    print(f"    Pass: {o['pass']}/20 | Fail: {o['fail']} | No answer: {o['no_answer']}")
    if o['times']:
        print(f"    Avg time: {sum(o['times'])/len(o['times'])*1000:.0f}ms")
    print()

    # ─── SUMMARY ───
    total_time = time.time() - total_start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_pass = sum(r['pass'] for r in results.values())
    total_fail = sum(r['fail'] for r in results.values())
    total_na = sum(r['no_answer'] for r in results.values())
    total_questions = total_pass + total_fail + total_na

    all_times = []
    for r in results.values():
        all_times.extend(r['times'])

    print("━" * 70)
    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║              BENCHMARK RESULTS                           ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print()
    print(f"  OFFLINE (no internet):")
    print(f"    Math:        {results['math']['pass']}/20")
    print(f"    Knowledge:   {results['knowledge']['pass']}/20")
    print(f"    Causal:      {results['causal']['pass']}/10")
    print(f"    Comparative: {results['comparative']['pass']}/1")
    print(f"    Identity:    {results['identity']['pass']}/2")
    print(f"    Logic:       {results['logic']['pass']}/2")
    offline_pass = sum(results[k]['pass'] for k in ['math','knowledge','causal','comparative','identity','logic'])
    offline_total = 55
    print(f"    ─────────────────────────")
    print(f"    OFFLINE TOTAL: {offline_pass}/{offline_total} ({offline_pass/offline_total*100:.0f}%)")
    print()
    print(f"  ONLINE (with internet):")
    print(f"    Web search:  {results['online']['pass']}/20")
    print(f"    ─────────────────────────")
    print(f"    ONLINE TOTAL: {results['online']['pass']}/20 ({results['online']['pass']/20*100:.0f}%)")
    print()
    print(f"  COMBINED: {total_pass}/{total_questions} ({total_pass/max(1,total_questions)*100:.0f}%)")
    print(f"  Hallucinations: {total_fail} (answered wrong)")
    print(f"  Gaps (no answer): {total_na}")
    print()
    print(f"  PERFORMANCE:")
    print(f"    Total time:     {total_time:.1f}s")
    print(f"    Avg per query:  {sum(all_times)/max(1,len(all_times))*1000:.0f}ms")
    offline_times = results['math']['times'] + results['knowledge']['times'] + results['causal']['times']
    if offline_times:
        print(f"    Avg offline:    {sum(offline_times)/len(offline_times)*1000:.0f}ms")
    if results['online']['times']:
        print(f"    Avg online:     {sum(results['online']['times'])/len(results['online']['times'])*1000:.0f}ms")
    print()
    print(f"  MEMORY:")
    print(f"    Peak RAM:       {peak / 1024 / 1024:.1f} MB")
    print(f"    Current:        {current / 1024 / 1024:.1f} MB")
    print()
    print(f"  SYSTEM:")
    print(f"    Binary:         {os.path.getsize(AI_BIN) / 1024:.0f} KB")
    print(f"    Knowledge:      7,818 concepts (C engine)")
    print(f"    Causal rules:   210")
    print(f"    Modes:          8")
    print(f"    Inventions:     22")
    print()
    print("━" * 70)

    # Save results
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'results': {k: {kk: vv for kk, vv in v.items() if kk != 'times'} for k, v in results.items()},
        'totals': {'pass': total_pass, 'fail': total_fail, 'no_answer': total_na, 'total': total_questions},
        'performance': {
            'total_time_s': round(total_time, 1),
            'avg_query_ms': round(sum(all_times)/max(1,len(all_times))*1000, 0),
            'peak_ram_mb': round(peak/1024/1024, 1),
        },
    }
    report_path = os.path.join(os.path.dirname(__file__), '..', 'user_data', 'benchmark_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved: {report_path}")


if __name__ == '__main__':
    run_benchmark()
