#!/usr/bin/env python3
"""
Validate and Deduplicate — Quality control before CSE build.
Reads all batch outputs, removes duplicates, validates, merges into one file.
"""
import os, hashlib, re

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'all_triples_clean.txt')


def run():
    seen = set()
    valid = 0
    duplicates = 0
    invalid = 0
    total_read = 0

    # Find all batch files
    batch_files = sorted([f for f in os.listdir(RAW_DIR) if f.startswith('batch_') and f.endswith('.txt')])
    print(f"  Found {len(batch_files)} batch files in {RAW_DIR}")

    out = open(OUTPUT_FILE, 'w')

    for batch_file in batch_files:
        path = os.path.join(RAW_DIR, batch_file)
        batch_count = 0

        with open(path) as f:
            for line in f:
                total_read += 1
                line = line.strip()
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) < 3:
                    invalid += 1
                    continue

                subj = parts[0].strip().lower()
                rel = parts[1].strip().lower()
                obj = parts[2].strip().lower()
                conf = parts[3].strip() if len(parts) > 3 else '80'

                # Validate
                if len(subj) < 2 or len(obj) < 1 or len(rel) < 2:
                    invalid += 1
                    continue
                if len(subj) > 127 or len(obj) > 127:
                    invalid += 1
                    continue
                # Skip if subject or object is just a number
                if subj.isdigit() or obj.isdigit():
                    invalid += 1
                    continue
                # Skip Wikidata Q-IDs that leaked through
                if re.match(r'^q\d+$', subj) or re.match(r'^q\d+$', obj):
                    invalid += 1
                    continue

                # Deduplicate
                h = hashlib.md5(f"{subj}|{rel}|{obj}".encode()).hexdigest()[:12]
                if h in seen:
                    duplicates += 1
                    continue
                seen.add(h)

                # Normalize confidence
                try:
                    c = int(conf)
                    c = max(10, min(99, c))
                except:
                    c = 80

                out.write(f"{subj}|{rel}|{obj}|{c}\n")
                valid += 1
                batch_count += 1

        print(f"    {batch_file}: {batch_count:,} valid facts")

    out.close()

    print(f"\n  Summary:")
    print(f"    Total read:   {total_read:,}")
    print(f"    Valid:         {valid:,}")
    print(f"    Duplicates:    {duplicates:,}")
    print(f"    Invalid:       {invalid:,}")
    print(f"    Output:        {OUTPUT_FILE}")
    print(f"    File size:     {os.path.getsize(OUTPUT_FILE) / 1_000_000:.1f} MB")
    return valid


if __name__ == '__main__':
    print("Validate & Deduplicate")
    run()
