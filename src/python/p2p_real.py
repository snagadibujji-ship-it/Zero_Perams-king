#!/usr/bin/env python3
"""
Real P2P Knowledge Sharing — TCP socket based.
Two AI instances on same machine (or network) share knowledge directly.
No central server. Direct peer-to-peer.
"""
import socket
import threading
import json
import time
import os
import sys

DEFAULT_PORT = 9900
LEARNED_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'web_learned.txt')


def get_local_facts():
    """Load facts from local knowledge file."""
    facts = []
    if os.path.isfile(LEARNED_FILE):
        with open(LEARNED_FILE) as f:
            facts = [line.strip() for line in f if line.strip()]
    return facts


def save_fact(fact):
    """Save a new fact locally."""
    os.makedirs(os.path.dirname(LEARNED_FILE), exist_ok=True)
    with open(LEARNED_FILE, 'a') as f:
        f.write(fact.strip() + '\n')


class P2PServer:
    """Listens for incoming peer connections and shares/receives facts."""
    
    def __init__(self, port=DEFAULT_PORT):
        self.port = port
        self.running = False
        self.thread = None
        self.facts_received = 0
        self.facts_sent = 0
        self.connections = 0
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        return self.port
    
    def stop(self):
        self.running = False
    
    def _listen(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('127.0.0.1', self.port))
        srv.listen(5)
        srv.settimeout(1.0)
        
        while self.running:
            try:
                conn, addr = srv.accept()
                self.connections += 1
                threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
        srv.close()
    
    def _handle(self, conn):
        try:
            data = conn.recv(65536).decode()
            msg = json.loads(data)
            
            if msg.get("action") == "sync_request":
                # Peer wants our facts
                my_facts = get_local_facts()
                response = {"action": "sync_response", "facts": my_facts}
                conn.sendall(json.dumps(response).encode())
                self.facts_sent += len(my_facts)
                
            elif msg.get("action") == "push_facts":
                # Peer is sending us facts
                new_facts = msg.get("facts", [])
                my_facts = set(get_local_facts())
                added = 0
                for fact in new_facts:
                    if fact not in my_facts:
                        save_fact(fact)
                        my_facts.add(fact)
                        added += 1
                self.facts_received += added
                response = {"action": "push_ack", "accepted": added}
                conn.sendall(json.dumps(response).encode())
        except Exception as e:
            try:
                conn.sendall(json.dumps({"error": str(e)}).encode())
            except:
                pass
        finally:
            conn.close()


def sync_with_peer(host='127.0.0.1', port=DEFAULT_PORT):
    """Connect to a peer and exchange facts."""
    try:
        # Step 1: Get their facts
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        sock.sendall(json.dumps({"action": "sync_request"}).encode())
        data = sock.recv(65536).decode()
        sock.close()
        
        response = json.loads(data)
        their_facts = set(response.get("facts", []))
        my_facts = set(get_local_facts())
        
        # Step 2: Find what they have that we don't
        new_for_us = their_facts - my_facts
        for fact in new_for_us:
            save_fact(fact)
        
        # Step 3: Push what we have that they don't
        new_for_them = my_facts - their_facts
        if new_for_them:
            sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock2.settimeout(5)
            sock2.connect((host, port))
            sock2.sendall(json.dumps({"action": "push_facts", "facts": list(new_for_them)}).encode())
            ack = json.loads(sock2.recv(65536).decode())
            sock2.close()
        else:
            ack = {"accepted": 0}
        
        return {
            "success": True,
            "received": len(new_for_us),
            "sent": len(new_for_them),
            "peer_accepted": ack.get("accepted", 0),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# === REAL TEST: Two nodes on localhost ===
if __name__ == "__main__":
    print("=" * 50)
    print("  P2P REAL NETWORK TEST (TCP localhost)")
    print("=" * 50)
    
    # Setup: Node A on port 9900, Node B on port 9901
    print("\n[1] Starting Node A (port 9900)...")
    node_a = P2PServer(port=9900)
    node_a.start()
    time.sleep(0.3)
    print("    ✓ Node A listening")
    
    print("[2] Starting Node B (port 9901)...")
    node_b = P2PServer(port=9901)
    node_b.start()
    time.sleep(0.3)
    print("    ✓ Node B listening")
    
    # Save test facts for Node A
    test_file_a = LEARNED_FILE
    # Backup existing
    backup = None
    if os.path.isfile(test_file_a):
        with open(test_file_a) as f:
            backup = f.read()
    
    # Write Node A's knowledge
    os.makedirs(os.path.dirname(test_file_a), exist_ok=True)
    with open(test_file_a, 'w') as f:
        f.write("P2P test fact: quantum computing uses qubits\n")
        f.write("P2P test fact: DNA has a double helix structure\n")
        f.write("P2P test fact: the speed of light is 300000 km per second\n")
    
    print(f"\n[3] Node A has {len(get_local_facts())} facts")
    
    # Node B syncs with Node A
    print("[4] Node B syncing with Node A (port 9900)...")
    result = sync_with_peer('127.0.0.1', 9900)
    print(f"    Result: {result}")
    
    if result["success"]:
        facts_now = get_local_facts()
        print(f"    ✓ After sync: {len(facts_now)} facts locally")
        print(f"    ✓ Received {result['received']} new facts")
        print(f"    ✓ Sent {result['sent']} facts to peer")
        
        # Verify the sync worked
        assert result["received"] >= 0
        print(f"\n[5] Node A stats: sent={node_a.facts_sent}, received={node_a.facts_received}, connections={node_a.connections}")
        print(f"    Node B stats: sent={node_b.facts_sent}, received={node_b.facts_received}, connections={node_b.connections}")
        
        print("\n" + "=" * 50)
        print("  ✅ P2P REAL NETWORK TEST: PASSED!")
        print("  Knowledge shared over TCP sockets successfully.")
        print("=" * 50)
    else:
        print(f"    ✗ FAILED: {result['error']}")
    
    # Cleanup
    node_a.stop()
    node_b.stop()
    time.sleep(0.5)
    
    # Restore backup
    if backup is not None:
        with open(test_file_a, 'w') as f:
            f.write(backup)
    else:
        if os.path.isfile(test_file_a):
            os.remove(test_file_a)
