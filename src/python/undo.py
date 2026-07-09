#!/usr/bin/env python3
"""Undo/time-travel system for AI knowledge base."""
import json, hashlib, os, sys, shutil
from datetime import datetime

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "user_data")
FACTS_FILE = os.path.join(BASE, "web_learned.txt")
CHECKPOINTS_FILE = os.path.join(BASE, "checkpoints.json")
BACKUPS_DIR = os.path.join(BASE, "backups")

def _ensure(): os.makedirs(BACKUPS_DIR, exist_ok=True)

def _load_cps():
    if os.path.exists(CHECKPOINTS_FILE):
        with open(CHECKPOINTS_FILE, "r") as f: return json.load(f)
    return []

def _save_cps(cps):
    with open(CHECKPOINTS_FILE, "w") as f: json.dump(cps, f, indent=2)

def _file_hash():
    if not os.path.exists(FACTS_FILE): return "empty"
    with open(FACTS_FILE, "rb") as f: return hashlib.sha256(f.read()).hexdigest()[:16]

def _facts_count():
    if not os.path.exists(FACTS_FILE): return 0
    with open(FACTS_FILE, "r") as f: return sum(1 for l in f if l.strip())

def checkpoint(label="auto"):
    """Save current state snapshot."""
    _ensure()
    cps = _load_cps()
    cp_id = len(cps) + 1
    backup_path = os.path.join(BACKUPS_DIR, f"backup_{cp_id}.txt")
    if os.path.exists(FACTS_FILE): shutil.copy2(FACTS_FILE, backup_path)
    cp = {"id": cp_id, "timestamp": datetime.now().isoformat(), "label": label,
          "facts_file_hash": _file_hash(), "facts_count": _facts_count(), "backup": backup_path}
    cps.append(cp)
    _save_cps(cps)
    print(f"[checkpoint] #{cp_id} '{label}' — {cp['facts_count']} facts, hash={cp['facts_file_hash']}")
    return cp

def list_checkpoints():
    """Show all saved checkpoints."""
    cps = _load_cps()
    if not cps:
        print("[undo] No checkpoints saved."); return []
    print(f"{'ID':<4} {'Label':<20} {'Facts':<6} {'Hash':<18} {'Timestamp'}")
    print("-" * 72)
    for cp in cps:
        print(f"{cp['id']:<4} {cp['label']:<20} {cp['facts_count']:<6} {cp['facts_file_hash']:<18} {cp['timestamp']}")
    return cps

def undo_last():
    """Remove last learned fact from web_learned.txt."""
    if not os.path.exists(FACTS_FILE):
        print("[undo] No facts file found."); return False
    with open(FACTS_FILE, "r") as f: lines = f.readlines()
    if not lines:
        print("[undo] Facts file is empty."); return False
    removed = lines.pop().strip()
    with open(FACTS_FILE, "w") as f: f.writelines(lines)
    print(f"[undo] Removed: {removed[:60]}{'...' if len(removed) > 60 else ''}")
    return True

def rollback(checkpoint_id):
    """Restore web_learned.txt from checkpoint backup."""
    cps = _load_cps()
    cp = next((c for c in cps if c["id"] == checkpoint_id), None)
    if not cp:
        print(f"[undo] Checkpoint #{checkpoint_id} not found."); return False
    if not os.path.exists(cp["backup"]):
        print(f"[undo] Backup file missing for checkpoint #{checkpoint_id}."); return False
    shutil.copy2(cp["backup"], FACTS_FILE)
    print(f"[undo] Rolled back to #{checkpoint_id} '{cp['label']}' ({cp['facts_count']} facts)")
    return True

def diff(cp1_id, cp2_id):
    """Show what changed between two checkpoints."""
    cps = _load_cps()
    c1 = next((c for c in cps if c["id"] == cp1_id), None)
    c2 = next((c for c in cps if c["id"] == cp2_id), None)
    if not c1 or not c2:
        print("[undo] One or both checkpoints not found."); return
    delta = c2["facts_count"] - c1["facts_count"]
    print(f"[diff] #{cp1_id} → #{cp2_id}: {'+' if delta >= 0 else ''}{delta} facts")
    print(f"  Hash: {c1['facts_file_hash']} → {c2['facts_file_hash']}")
    if os.path.exists(c1["backup"]) and os.path.exists(c2["backup"]):
        with open(c1["backup"]) as f: s1 = set(f.read().splitlines())
        with open(c2["backup"]) as f: s2 = set(f.read().splitlines())
        for line in (s2 - s1): print(f"  + {line[:70]}")
        for line in (s1 - s2): print(f"  - {line[:70]}")

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "list"
    if arg == "checkpoint":
        checkpoint(sys.argv[2] if len(sys.argv) > 2 else "manual")
    elif arg == "rollback" and len(sys.argv) > 2:
        rollback(int(sys.argv[2]))
    elif arg == "diff" and len(sys.argv) > 3:
        diff(int(sys.argv[2]), int(sys.argv[3]))
    elif arg == "undo": undo_last()
    elif arg == "list": list_checkpoints()
    else: print("Usage: python3 undo.py [list|checkpoint LABEL|undo|rollback ID|diff ID1 ID2]")
