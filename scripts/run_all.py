#!/usr/bin/env python3
"""
Master Script — Run ALL batches, validate, build CSE.
One command to go from zero to 4.7M facts in axima.cse.

Usage:
  python run_all.py          Run everything (10-14 hours)
  python run_all.py quick    Run batches 1+3+6 only (~2 hours, ~500K facts)
  python run_all.py status   Check progress
"""
import os, sys, time, importlib

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

BATCHES = [
    ('batch_1_countries', 'Countries (capitals, borders, GDP)', '~200K'),
    ('batch_2_people', 'Famous People (50K+ people)', '~500K'),
    ('batch_3_science', 'Science (elements, planets, animals)', '~200K'),
    ('batch_4_geography', 'Geography (cities, rivers, mountains)', '~200K'),
    ('batch_5_culture', 'Culture (movies, books, music)', '~300K'),
    ('batch_6_technology', 'Technology (languages, companies)', '~200K'),
    ('batch_7_taxonomy', 'Taxonomy (is_a hierarchy)', '~500K'),
    ('import_conceptnet', 'ConceptNet (common sense)', '~500K'),
]

QUICK_BATCHES = ['batch_1_countries', 'batch_3_science', 'batch_6_technology']


def run_batch(module_name):
    """Import and run a batch script."""
    try:
        mod = importlib.import_module(module_name)
        return mod.run()
    except Exception as e:
        print(f"  ERROR in {module_name}: {e}")
        return 0


def run_all(quick=False):
    """Run all batches, validate, and build CSE."""
    start_time = time.time()
    results = {}
    total_facts = 0

    batches_to_run = BATCHES if not quick else [(b, d, e) for b, d, e in BATCHES if b in QUICK_BATCHES]

    print("=" * 60)
    print("  AXIMA KNOWLEDGE BUILD")
    print(f"  Mode: {'FULL (all 8 batches)' if not quick else 'QUICK (3 batches)'}")
    print(f"  Expected: {'4.7M facts, 10-14 hours' if not quick else '~500K facts, ~2 hours'}")
    print("=" * 60)
    print()

    for i, (module, desc, expected) in enumerate(batches_to_run, 1):
        print(f"\n{'─' * 60}")
        print(f"  [{i}/{len(batches_to_run)}] {desc} (expected: {expected})")
        print(f"{'─' * 60}")
        
        batch_start = time.time()
        count = run_batch(module)
        batch_time = time.time() - batch_start
        
        results[module] = count
        total_facts += count
        print(f"  Time: {batch_time:.0f}s | Facts: {count:,} | Running total: {total_facts:,}")

    # Validate + dedup
    print(f"\n{'─' * 60}")
    print(f"  VALIDATE + DEDUPLICATE")
    print(f"{'─' * 60}")
    import validate_and_dedup
    clean_count = validate_and_dedup.run()

    # Build CSE
    print(f"\n{'─' * 60}")
    print(f"  BUILD CSE (compress to binary)")
    print(f"{'─' * 60}")
    import build_cse
    final_count = build_cse.build_python()
    build_cse.verify()

    # Final report
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    mins = int((elapsed % 3600) // 60)

    print(f"\n{'═' * 60}")
    print(f"  BUILD COMPLETE")
    print(f"{'═' * 60}")
    print(f"  Time:           {hours}h {mins}m")
    print(f"  Raw facts:      {total_facts:,}")
    print(f"  After dedup:    {clean_count:,}")
    print(f"  In CSE:         {final_count:,}")
    print(f"  CSE file:       {os.path.join(SCRIPTS_DIR, '..', 'data', 'axima.cse')}")
    cse_path = os.path.join(SCRIPTS_DIR, '..', 'data', 'axima.cse')
    if os.path.isfile(cse_path):
        size_mb = os.path.getsize(cse_path) / 1_000_000
        print(f"  CSE size:       {size_mb:.2f} MB")
        print(f"  Derivable:      {final_count * 1000:,} answers (with EIR)")
    print(f"\n  Per batch:")
    for module, count in results.items():
        print(f"    {module}: {count:,}")
    print(f"{'═' * 60}")


def status():
    """Check what's been built so far."""
    raw_dir = os.path.join(SCRIPTS_DIR, '..', 'data', 'raw')
    cse_path = os.path.join(SCRIPTS_DIR, '..', 'data', 'axima.cse')
    clean_path = os.path.join(SCRIPTS_DIR, '..', 'data', 'all_triples_clean.txt')

    print("  Build Status:")
    print()
    
    if os.path.isdir(raw_dir):
        files = [f for f in os.listdir(raw_dir) if f.endswith('.txt')]
        for fname in sorted(files):
            path = os.path.join(raw_dir, fname)
            lines = sum(1 for _ in open(path))
            size = os.path.getsize(path) / 1000
            print(f"    {fname}: {lines:,} facts ({size:.0f} KB)")
    else:
        print("    No raw files yet. Run batches first.")
    
    print()
    if os.path.isfile(clean_path):
        lines = sum(1 for _ in open(clean_path))
        print(f"    all_triples_clean.txt: {lines:,} facts (deduplicated)")
    
    if os.path.isfile(cse_path):
        size = os.path.getsize(cse_path) / 1_000_000
        print(f"    axima.cse: {size:.2f} MB (final compressed)")
    else:
        print("    axima.cse: NOT BUILT YET")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'quick':
            run_all(quick=True)
        elif sys.argv[1] == 'status':
            status()
        else:
            print("Usage: python run_all.py [quick|status]")
    else:
        run_all()
