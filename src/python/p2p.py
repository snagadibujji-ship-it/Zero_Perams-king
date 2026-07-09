"""P2P Knowledge Sharing Network — Simulates AI nodes exchanging facts."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set


class TrustLevel(Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


@dataclass
class P2PNode:
    id: str
    knowledge: List[str] = field(default_factory=list)
    peers: List["P2PNode"] = field(default_factory=list)
    trust_map: dict = field(default_factory=dict)
    pending_inbox: List[str] = field(default_factory=list)
    _facts_sent: int = 0
    _facts_received: int = 0

    def _known_set(self) -> Set[str]:
        return set(self.knowledge)

    def learn(self, fact: str):
        if fact not in self._known_set():
            self.knowledge.append(fact)

    def add_peer(self, peer: "P2PNode", trust: TrustLevel = TrustLevel.TRUSTED):
        if peer not in self.peers:
            self.peers.append(peer)
            self.trust_map[peer.id] = trust
        if self not in peer.peers:
            peer.peers.append(self)
            peer.trust_map[self.id] = trust

    def diff(self, other: "P2PNode") -> List[str]:
        """Facts self has that other doesn't."""
        return [f for f in self.knowledge if f not in other._known_set()]

    def share_with(self, other: "P2PNode") -> int:
        """Send facts the other node doesn't have. Returns count sent."""
        new_facts = self.diff(other)
        if not new_facts:
            return 0
        trust = self.trust_map.get(other.id, TrustLevel.UNTRUSTED)
        if trust == TrustLevel.TRUSTED:
            other.receive(new_facts)
        else:
            other.pending_inbox.extend(new_facts)
        self._facts_sent += len(new_facts)
        return len(new_facts)

    def receive(self, facts: List[str]):
        """Accept new facts with deduplication."""
        known = self._known_set()
        for fact in facts:
            if fact not in known:
                self.knowledge.append(fact)
                known.add(fact)
                self._facts_received += 1

    def approve_pending(self):
        """Accept all pending facts from untrusted peers."""
        self.receive(self.pending_inbox)
        self.pending_inbox.clear()

    def sync_all(self) -> int:
        """Sync knowledge with all peers. Returns total facts sent."""
        total = 0
        for peer in self.peers:
            total += self.share_with(peer)
        return total

    def sync_stats(self) -> dict:
        return {"node": self.id, "facts_sent": self._facts_sent,
                "facts_received": self._facts_received,
                "peers_count": len(self.peers),
                "knowledge_count": len(self.knowledge)}


if __name__ == "__main__":
    # Create 3 nodes
    node_a = P2PNode("Alice")
    node_b = P2PNode("Bob")
    node_c = P2PNode("Carol")
    # Connect them
    node_a.add_peer(node_b)
    node_b.add_peer(node_c)
    # Alice learns something
    node_a.learn("Quantum entanglement is spooky action at distance")
    node_a.learn("Black holes have event horizons")
    # Bob learns something different
    node_b.learn("CRISPR can edit genes")
    # Sync Alice -> Bob
    node_a.share_with(node_b)
    print(f"Bob now knows: {len(node_b.knowledge)} facts")  # Should be 3
    # Sync Bob -> Carol (Bob has Alice's facts + his own)
    node_b.share_with(node_c)
    print(f"Carol now knows: {len(node_c.knowledge)} facts")  # Should be 3
    # Prove it propagated
    assert "Quantum entanglement" in str(node_c.knowledge)
    print("\n✅ P2P SIMULATION: PASSED — knowledge propagates across network!")
    # Trust demo: untrusted peer
    node_d = P2PNode("Dave")
    node_c.add_peer(node_d, trust=TrustLevel.UNTRUSTED)
    node_c.share_with(node_d)
    print(f"\nDave (untrusted) pending: {len(node_d.pending_inbox)} facts")
    assert len(node_d.knowledge) == 0  # blocked until approved
    node_d.approve_pending()
    print(f"Dave after approval: {len(node_d.knowledge)} facts")
    # Stats
    print(f"\nSync stats: {node_a.sync_stats()}")
    print(f"Sync stats: {node_b.sync_stats()}")
    print("\n✅ ALL TESTS PASSED")
