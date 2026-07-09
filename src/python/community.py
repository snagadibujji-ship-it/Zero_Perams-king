#!/usr/bin/env python3
"""Community Intelligence — collective knowledge from multiple users."""
import json, os, time

COMMUNITY_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'community.json')

class CommunityKnowledge:
    def __init__(self):
        self.facts = []  # {fact, user_id, confidence, topic, timestamp, confirmations}
        self.experts = {}  # topic -> {user_id: count}
        self.load()
    
    def load(self):
        if os.path.isfile(COMMUNITY_FILE):
            try:
                with open(COMMUNITY_FILE) as f:
                    data = json.load(f)
                    self.facts = data.get('facts', [])
                    self.experts = data.get('experts', {})
            except: pass
    
    def save(self):
        os.makedirs(os.path.dirname(COMMUNITY_FILE), exist_ok=True)
        with open(COMMUNITY_FILE, 'w') as f:
            json.dump({'facts': self.facts, 'experts': self.experts}, f)
    
    def contribute(self, fact, user_id, confidence=0.8, topic='general'):
        # Check duplicate
        for f in self.facts:
            if f['fact'].lower() == fact.lower():
                f['confirmations'] = f.get('confirmations', 1) + 1
                f['confidence'] = min(0.99, f['confidence'] + 0.1)
                self.save()
                return 'confirmed'
        self.facts.append({
            'fact': fact, 'user_id': user_id, 'confidence': confidence,
            'topic': topic, 'timestamp': time.time(), 'confirmations': 1
        })
        # Track expertise
        if topic not in self.experts:
            self.experts[topic] = {}
        self.experts[topic][user_id] = self.experts[topic].get(user_id, 0) + 1
        self.save()
        return 'added'
    
    def query(self, topic):
        results = []
        for f in self.facts:
            if topic.lower() in f['fact'].lower() or f.get('topic','') == topic:
                results.append(f)
        return sorted(results, key=lambda x: x['confidence'], reverse=True)
    
    def get_expert(self, topic):
        if topic in self.experts:
            sorted_users = sorted(self.experts[topic].items(), key=lambda x: x[1], reverse=True)
            return sorted_users[0] if sorted_users else None
        return None
    
    def verify(self, fact):
        for f in self.facts:
            if f['fact'].lower() == fact.lower():
                return {'verified': f['confirmations'] >= 3, 'confirmations': f['confirmations'], 'confidence': f['confidence']}
        return {'verified': False, 'confirmations': 0, 'confidence': 0}
    
    def trending(self, limit=5):
        recent = sorted(self.facts, key=lambda x: x['timestamp'], reverse=True)
        return recent[:limit]
    
    def stats(self):
        users = set(f['user_id'] for f in self.facts)
        topics = {}
        for f in self.facts:
            t = f.get('topic', 'general')
            topics[t] = topics.get(t, 0) + 1
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
        return {'total_facts': len(self.facts), 'contributors': len(users), 'top_topics': top_topics}


if __name__ == '__main__':
    ck = CommunityKnowledge()
    ck.facts = []  # fresh start for test
    ck.experts = {}
    
    # Simulate 5 users
    ck.contribute("Python is a programming language", "alice", 0.9, "programming")
    ck.contribute("Dogs are loyal animals", "bob", 0.85, "animals")
    ck.contribute("Python is a programming language", "carol", 0.9, "programming")  # confirm
    ck.contribute("Python is a programming language", "dave", 0.9, "programming")  # confirm again
    ck.contribute("Quantum entanglement is spooky", "eve", 0.7, "physics")
    ck.contribute("Machine learning uses data", "alice", 0.85, "programming")
    ck.contribute("Cats are independent", "bob", 0.8, "animals")
    
    # Test verify (3 confirmations)
    v = ck.verify("Python is a programming language")
    assert v['verified'] == True and v['confirmations'] == 3
    print(f"✓ Verification: {v}")
    
    # Test expert
    expert = ck.get_expert("programming")
    assert expert[0] == "alice"
    print(f"✓ Expert in programming: {expert}")
    
    # Test query
    results = ck.query("python")
    assert len(results) >= 1
    print(f"✓ Query 'python': {len(results)} results")
    
    # Test stats
    s = ck.stats()
    print(f"✓ Stats: {s}")
    
    # Test trending
    t = ck.trending(3)
    print(f"✓ Trending: {len(t)} recent facts")
    
    print("\n✅ ALL COMMUNITY TESTS PASSED!")
