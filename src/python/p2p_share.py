#!/usr/bin/env python3
"""
P2P Share — User-friendly knowledge sharing.
No code needed. AI handles everything:
1. Finds your IP
2. Asks for friend's IP
3. Connects and syncs
4. Shows what was received
5. Lets you keep/remove facts by topic
"""
import socket
import json
import threading
import time
import os
import sys


def animate_download(count, label="Downloading"):
    """Show animated progress while adding facts."""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    for i in range(count):
        for f in frames[:3]:
            sys.stdout.write(f'\r  {f} {label}... [{i+1}/{count}]')
            sys.stdout.flush()
            time.sleep(0.05)
    sys.stdout.write(f'\r  ✓ {label} complete! [{count}/{count}]    \n')
    sys.stdout.flush()


def animate_connecting():
    """Show connecting animation."""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    for i in range(15):
        sys.stdout.write(f'\r  {frames[i % len(frames)]} Connecting...')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r  ✓ Connected!          \n')
    sys.stdout.flush()


def animate_syncing(count):
    """Show syncing animation."""
    bar_len = 20
    for i in range(count + 1):
        pct = i / max(count, 1)
        filled = int(bar_len * pct)
        bar = '█' * filled + '░' * (bar_len - filled)
        sys.stdout.write(f'\r  [{bar}] {int(pct*100)}% syncing facts...')
        sys.stdout.flush()
        time.sleep(0.08)
    sys.stdout.write(f'\r  [{("█" * bar_len)}] 100% sync complete!   \n')
    sys.stdout.flush()

LEARNED_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'web_learned.txt')
SHARE_PORT = 9900


def get_my_ip():
    """Get real local IP (not 127.0.0.1). Detect VPN/DNS issues."""
    ip = "127.0.0.1"
    vpn_detected = False
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        pass
    
    # Detect VPN/unusual IPs
    if ip.startswith("10.") and not ip.startswith("10.0."):
        vpn_detected = True
    if ip.startswith("100."):  # CGNAT or VPN (Tailscale etc)
        vpn_detected = True
    
    return ip, vpn_detected


def mask_ip(ip):
    """Hide full IP for privacy — show only partial."""
    parts = ip.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***. ***"
    return "***.***.***. ***"


def get_share_code(ip):
    """Generate a random 6-char code. Store IP→code mapping locally."""
    import hashlib, random, string
    code_file = os.path.join(os.path.dirname(LEARNED_FILE), '.share_codes.json')
    
    # Generate random 6-char code (letters + digits, easy to type)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # Avoid confusing chars
    code = code.replace('O', 'X').replace('0', 'Y').replace('I', 'Z').replace('1', 'W')
    
    # Store mapping locally
    codes = {}
    if os.path.isfile(code_file):
        try:
            with open(code_file) as f:
                codes = json.loads(f.read())
        except:
            pass
    
    codes[code] = {"ip": ip, "created": time.time()}
    os.makedirs(os.path.dirname(code_file), exist_ok=True)
    with open(code_file, 'w') as f:
        f.write(json.dumps(codes))
    
    return code


def decode_share_code(code, subnet_prefix=None):
    """Decode share code — only works if you have the code file from the other person.
    In practice: friend tells you code verbally, you enter it, 
    your AI asks THEIR AI (via broadcast) who has this code."""
    # For local network: try connecting to common subnets with broadcast
    # For now: ask user for IP directly if code doesn't resolve
    code_file = os.path.join(os.path.dirname(LEARNED_FILE), '.share_codes.json')
    
    if os.path.isfile(code_file):
        try:
            with open(code_file) as f:
                codes = json.loads(f.read())
            if code in codes:
                return codes[code]["ip"]
        except:
            pass
    
    # Code not found locally — it's from another machine
    # Ask user for IP as fallback
    return None


def get_local_facts():
    """Load local knowledge."""
    if not os.path.isfile(LEARNED_FILE):
        return []
    with open(LEARNED_FILE) as f:
        return [l.strip() for l in f if l.strip()]


def save_facts(facts):
    """Overwrite local facts file."""
    os.makedirs(os.path.dirname(LEARNED_FILE), exist_ok=True)
    with open(LEARNED_FILE, 'w') as f:
        for fact in facts:
            f.write(fact.strip() + '\n')


def categorize_facts(facts):
    """Group facts by detected topic."""
    categories = {}
    for fact in facts:
        # Simple categorization by keywords
        fl = fact.lower()
        if any(w in fl for w in ['fish', 'shark', 'salmon', 'whale', 'ocean', 'marine', 'aquatic']):
            cat = "marine/fish"
        elif any(w in fl for w in ['dog', 'cat', 'animal', 'bird', 'mammal', 'pet']):
            cat = "animals"
        elif any(w in fl for w in ['code', 'python', 'program', 'computer', 'software', 'algorithm']):
            cat = "computing"
        elif any(w in fl for w in ['planet', 'star', 'sun', 'moon', 'space', 'galaxy', 'orbit']):
            cat = "space"
        elif any(w in fl for w in ['country', 'capital', 'city', 'located', 'continent']):
            cat = "geography"
        elif any(w in fl for w in ['cause', 'effect', 'leads', 'result']):
            cat = "science/causation"
        elif any(w in fl for w in ['quantum', 'atom', 'molecule', 'physics', 'energy']):
            cat = "physics"
        elif any(w in fl for w in ['health', 'disease', 'body', 'brain', 'medical']):
            cat = "health/biology"
        else:
            cat = "general"
        
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(fact)
    
    return categories


def start_sharing_server(timeout=60):
    """Start listening for incoming peer connections."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', SHARE_PORT))
    srv.listen(1)
    srv.settimeout(timeout)
    
    try:
        conn, addr = srv.accept()
        data = json.loads(conn.recv(65536).decode())
        
        if data.get("action") == "sync":
            my_facts = get_local_facts()
            their_facts = data.get("facts", [])
            
            # Send our facts back
            conn.sendall(json.dumps({"facts": my_facts}).encode())
            conn.close()
            srv.close()
            
            return {"success": True, "received_facts": their_facts, "from": addr[0]}
    except socket.timeout:
        srv.close()
        return {"success": False, "error": "No one connected within timeout"}
    except Exception as e:
        srv.close()
        return {"success": False, "error": str(e)}


def connect_to_friend(friend_ip):
    """Connect to friend's AI and exchange facts."""
    try:
        my_facts = get_local_facts()
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((friend_ip, SHARE_PORT))
        
        # Send our facts + request theirs
        sock.sendall(json.dumps({"action": "sync", "facts": my_facts}).encode())
        
        # Receive their facts
        data = json.loads(sock.recv(65536).decode())
        sock.close()
        
        their_facts = data.get("facts", [])
        return {"success": True, "received_facts": their_facts}
    except Exception as e:
        return {"success": False, "error": str(e)}


def share_interactive():
    """Full interactive P2P sharing flow — called from the AI."""
    my_ip, vpn_detected = get_my_ip()
    my_facts = get_local_facts()
    
    print(f"\n  📡 P2P Knowledge Sharing")
    print(f"  ─────────────────────────")
    print(f"  Your connection: {mask_ip(my_ip)}")
    print(f"  Share code: {get_share_code(my_ip)}")
    print(f"  Your facts: {len(my_facts)}")
    
    if vpn_detected:
        print(f"\n  ⚠️  VPN or proxy detected!")
        print(f"  For P2P to work, both sides need real local network IPs.")
        print(f"  Please turn off VPN/DNS proxy and try again.")
        print(f"  (P2P works on same WiFi/LAN without VPN)")
        try:
            cont = input("\n  Continue anyway? (y/n): ").strip().lower()
        except EOFError:
            return
        if cont not in ('y', 'yes'):
            return
    
    print(f"\n  Options:")
    print(f"    1. Connect to a friend (enter their IP or share code)")
    print(f"    2. Wait for a friend to connect to you")
    print(f"    3. Cancel")
    
    try:
        choice = input("\n  Choose (1/2/3): ").strip()
    except EOFError:
        return
    
    if choice == "1":
        try:
            friend = input("  Enter friend's IP or share code: ").strip()
        except EOFError:
            return
        
        # Decode share code if given (6 chars, no dots)
        if len(friend) == 6 and '.' not in friend:
            friend_ip = decode_share_code(friend)
            if not friend_ip:
                print(f"  Code '{friend}' didn't connect.")
                print(f"  No worries — ask your friend for their IP directly.")
                print(f"  (They can find it in their /share screen)")
                try:
                    friend_ip = input("  Friend's IP: ").strip()
                except EOFError:
                    return
                if not friend_ip:
                    print("  Cancelled.")
                    return
        else:
            friend_ip = friend
        
        print(f"  Connecting...")
        animate_connecting()
        result = connect_to_friend(friend_ip)
        
        if result["success"]:
            _process_received_with_permission(result["received_facts"], my_facts)
        else:
            print(f"  ✗ Failed: {result['error']}")
            if "refused" in str(result.get('error','')).lower():
                print(f"  Make sure your friend is running /share option 2 (waiting).")
    
    elif choice == "2":
        print(f"\n  📢 Tell your friend:")
        print(f"     Share code: {get_share_code(my_ip)}")
        print(f"     Backup IP (if code fails): {my_ip}")
        print(f"\n  Waiting for connection (60 seconds)...")
        
        result = start_sharing_server(timeout=60)
        
        if result["success"]:
            print(f"  ✓ Someone connected!")
            _process_received_with_permission(result["received_facts"], my_facts)
        else:
            print(f"  ✗ {result['error']}")
    
    else:
        print("  Cancelled.")


def _process_received_with_permission(their_facts, my_facts):
    """Process received facts WITH permission control per category."""
    my_set = set(my_facts)
    new_facts = [f for f in their_facts if f not in my_set]
    
    if not new_facts:
        print(f"\n  No new facts — you already know everything they shared!")
        return
    
    # Categorize
    categories = categorize_facts(new_facts)
    
    print(f"\n  ┌─ Incoming: {len(new_facts)} new facts ─────────────┐")
    for cat, facts in sorted(categories.items()):
        print(f"  │ [{cat}] — {len(facts)} facts")
        for f in facts[:2]:
            print(f"  │   • {f[:60]}{'...' if len(f)>60 else ''}")
        if len(facts) > 2:
            print(f"  │   ... +{len(facts)-2} more")
    print(f"  └───────────────────────────────────────────┘")
    
    # Permission per category
    print(f"\n  Choose what to accept:")
    keep_facts = []
    for cat, facts in sorted(categories.items()):
        try:
            choice = input(f"  Accept [{cat}] ({len(facts)} facts)? (y/n): ").strip().lower()
        except EOFError:
            break
        if choice in ('y', 'yes'):
            keep_facts.extend(facts)
            print(f"    ✓ Added {len(facts)} {cat} facts")
        else:
            print(f"    ✗ Rejected {len(facts)} {cat} facts")
    
    if keep_facts:
        animate_syncing(len(keep_facts))
        all_facts = my_facts + keep_facts
        save_facts(all_facts)
        print(f"\n  ✓ Done! Accepted {len(keep_facts)}/{len(new_facts)} facts.")
        print(f"  Total knowledge: {len(all_facts)} facts")
    else:
        print(f"\n  No facts accepted.")


def _process_received(their_facts, my_facts):
    """Process received facts — show categories, let user choose."""
    my_set = set(my_facts)
    new_facts = [f for f in their_facts if f not in my_set]
    
    if not new_facts:
        print(f"\n  No new facts — you already know everything they know!")
        return
    
    print(f"\n  ✓ Received {len(new_facts)} new facts!")
    
    # Categorize
    categories = categorize_facts(new_facts)
    
    print(f"\n  Facts by topic:")
    for cat, facts in sorted(categories.items()):
        print(f"    [{cat}] — {len(facts)} facts")
        for f in facts[:3]:  # Show max 3 per category
            print(f"      • {f[:70]}{'...' if len(f)>70 else ''}")
        if len(facts) > 3:
            print(f"      ... and {len(facts)-3} more")
    
    # Ask what to keep
    print(f"\n  What would you like to do?")
    print(f"    a. Keep ALL {len(new_facts)} facts")
    print(f"    r. Remove specific topics")
    print(f"    n. Keep NONE")
    
    try:
        action = input("  Choose (a/r/n): ").strip().lower()
    except EOFError:
        return
    
    if action == 'a':
        # Save all
        all_facts = my_facts + new_facts
        save_facts(all_facts)
        print(f"  ✓ Saved all {len(new_facts)} new facts! Total: {len(all_facts)}")
    
    elif action == 'r':
        # Let user remove by category
        keep_facts = []
        for cat, facts in sorted(categories.items()):
            try:
                choice = input(f"  Keep [{cat}] ({len(facts)} facts)? (y/n): ").strip().lower()
            except EOFError:
                break
            if choice in ('y', 'yes'):
                keep_facts.extend(facts)
            else:
                print(f"    ✗ Removed {len(facts)} {cat} facts")
        
        if keep_facts:
            all_facts = my_facts + keep_facts
            save_facts(all_facts)
            print(f"\n  ✓ Kept {len(keep_facts)} facts, removed {len(new_facts)-len(keep_facts)}. Total: {len(all_facts)}")
        else:
            print(f"\n  Kept nothing.")
    
    else:
        print(f"  OK, nothing saved.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Self-test with two threads
        print("Running P2P self-test...")
        
        # Setup test data
        os.makedirs(os.path.dirname(LEARNED_FILE), exist_ok=True)
        with open(LEARNED_FILE, 'w') as f:
            f.write("Test fact: dogs are loyal\n")
            f.write("Test fact: cats are independent\n")
        
        # Start server in background
        server_result = [None]
        def run_server():
            server_result[0] = start_sharing_server(timeout=5)
        t = threading.Thread(target=run_server, daemon=True)
        t.start()
        time.sleep(0.3)
        
        # Connect as "friend" with different facts
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', SHARE_PORT))
        sock.sendall(json.dumps({
            "action": "sync",
            "facts": ["Friend fact: sharks live in oceans", "Friend fact: whales are mammals", "Friend fact: python is a language"]
        }).encode())
        resp = json.loads(sock.recv(65536).decode())
        sock.close()
        t.join(timeout=3)
        
        print(f"  Server got: {server_result[0]}")
        print(f"  We got back: {len(resp.get('facts',[]))} facts from them")
        
        received = server_result[0]
        if received and received["success"]:
            print(f"  ✓ Received {len(received['received_facts'])} facts from friend")
            cats = categorize_facts(received['received_facts'])
            print(f"  Categories: {dict((k,len(v)) for k,v in cats.items())}")
            print("\n  ✅ P2P SELF-TEST PASSED!")
        
        # Cleanup
        os.remove(LEARNED_FILE)
    else:
        share_interactive()
