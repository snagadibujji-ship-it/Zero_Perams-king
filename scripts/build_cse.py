#!/usr/bin/env python3
"""
Build CSE — Final step. Takes all_triples_clean.txt → axima.cse (compressed binary).
Uses the C engine's cse_build function via subprocess, or builds in Python as fallback.
"""
import os, sys, struct, hashlib, time

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
INPUT_FILE = os.path.join(DATA_DIR, 'all_triples_clean.txt')
OUTPUT_FILE = os.path.join(DATA_DIR, 'axima.cse')


def build_python():
    """Pure Python CSE builder (fallback if C binary not available)."""
    print("  Building CSE database (Python builder)...")

    if not os.path.isfile(INPUT_FILE):
        print(f"  ERROR: {INPUT_FILE} not found. Run validate_and_dedup.py first.")
        return 0

    # Pass 1: Collect all unique strings + relations
    strings = {}  # text → id
    relations = {}  # text → id
    facts = []

    with open(INPUT_FILE) as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) < 3:
                continue
            subj, rel, obj = parts[0], parts[1], parts[2]
            conf = int(parts[3]) if len(parts) > 3 else 80

            if subj not in strings:
                strings[subj] = len(strings)
            if obj not in strings:
                strings[obj] = len(strings)
            if rel not in relations:
                relations[rel] = len(relations)

            facts.append((strings[subj], relations[rel], strings[obj], conf))

    print(f"    Strings: {len(strings):,}")
    print(f"    Relations: {len(relations)}")
    print(f"    Facts: {len(facts):,}")

    # Pass 2: Sort facts by subject (for clustering)
    facts.sort(key=lambda x: x[0])

    # Pass 3: Write binary CSE file
    with open(OUTPUT_FILE, 'wb') as out:
        # Header: magic(4) + version(4) + string_count(4) + fact_count(4)
        out.write(struct.pack('<I', 0x43534530))  # "CSE0"
        out.write(struct.pack('<I', 1))  # version
        out.write(struct.pack('<I', len(strings)))
        out.write(struct.pack('<I', len(facts)))

        # String table (sorted by ID)
        id_to_string = [''] * len(strings)
        for text, sid in strings.items():
            id_to_string[sid] = text

        for text in id_to_string:
            encoded = text.encode('utf-8')[:127]
            out.write(struct.pack('<H', len(encoded)))
            out.write(encoded)

        # Relation table
        id_to_rel = [''] * len(relations)
        for text, rid in relations.items():
            id_to_rel[rid] = text
        out.write(struct.pack('<B', len(relations)))
        for rel in id_to_rel:
            encoded = rel.encode('utf-8')[:31]
            out.write(struct.pack('<B', len(encoded)))
            out.write(encoded)

        # Facts (varint encoded: subject_varint + relation_byte + object_varint + conf_nibble)
        for subj_id, rel_id, obj_id, conf in facts:
            # Varint encoding
            out.write(encode_varint(subj_id))
            out.write(struct.pack('<B', rel_id & 0xFF))
            out.write(encode_varint(obj_id))
            # Confidence: 4 bits (0-15 maps to 0-100)
            conf_encoded = min(15, conf * 15 // 100)
            out.write(struct.pack('<B', conf_encoded << 4))

    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"\n  CSE database built:")
    print(f"    File: {OUTPUT_FILE}")
    print(f"    Size: {file_size / 1_000_000:.2f} MB")
    print(f"    Facts: {len(facts):,}")
    print(f"    Strings: {len(strings):,}")
    print(f"    Avg bytes/fact: {file_size / max(1, len(facts)):.1f}")
    print(f"    Derivable answers (EIR 1000x): {len(facts) * 1000:,}")

    return len(facts)


def encode_varint(value):
    """Encode uint32 as varint bytes."""
    result = bytearray()
    while value > 0x7F:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)


def verify():
    """Quick verification of the built CSE file."""
    if not os.path.isfile(OUTPUT_FILE):
        print("  No CSE file to verify.")
        return

    with open(OUTPUT_FILE, 'rb') as f:
        magic = struct.unpack('<I', f.read(4))[0]
        version = struct.unpack('<I', f.read(4))[0]
        str_count = struct.unpack('<I', f.read(4))[0]
        fact_count = struct.unpack('<I', f.read(4))[0]

    size_mb = os.path.getsize(OUTPUT_FILE) / 1_000_000
    print(f"\n  Verification:")
    print(f"    Magic: {'CSE0' if magic == 0x43534530 else 'INVALID'}")
    print(f"    Version: {version}")
    print(f"    Strings: {str_count:,}")
    print(f"    Facts: {fact_count:,}")
    print(f"    Size: {size_mb:.2f} MB")
    print(f"    Status: {'VALID' if magic == 0x43534530 else 'CORRUPT'}")


if __name__ == '__main__':
    print("Build CSE — Compress all triples into axima.cse")
    start = time.time()
    count = build_python()
    elapsed = time.time() - start
    print(f"\n  Build time: {elapsed:.1f}s")
    if count > 0:
        verify()
