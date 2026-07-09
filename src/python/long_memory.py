"""Infinite persistent memory that never forgets anything."""
import json, os, re, time


class LongMemory:
    def __init__(self, path="user_data/long_memory.json", session_id=None):
        self.path = path
        self.session_id = session_id or int(time.time())
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {"memories": [], "user_profile": {"name": "", "job": "", "interests": [], "preferences": {}}, "sessions": []}

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def remember(self, text, category="fact", importance=0.5):
        """Store a memory with timestamp and auto-detect user info."""
        self.data["memories"].append({
            "text": text, "category": category,
            "importance": max(0.0, min(1.0, importance)),
            "timestamp": time.time(), "session": self.session_id
        })
        self._auto_detect(text)
        self._save()

    def recall(self, query, limit=5):
        """Find relevant memories by keyword match + recency + importance."""
        if not self.data["memories"]:
            return []
        keywords = set(query.lower().split())
        now = time.time()
        timestamps = [m["timestamp"] for m in self.data["memories"]]
        time_range = max(now - min(timestamps), 1)
        scored = []
        for m in self.data["memories"]:
            words = set(m["text"].lower().split())
            overlap = len(keywords & words)
            keyword_score = overlap / max(len(keywords), 1)
            recency = 1.0 - (now - m["timestamp"]) / time_range if time_range > 0 else 1.0
            score = keyword_score * 0.6 + recency * 0.2 + m["importance"] * 0.2
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def get_user_profile(self):
        """Return accumulated user info."""
        return self.data["user_profile"]

    def update_user_profile(self, key, value):
        """Store a user attribute."""
        profile = self.data["user_profile"]
        if key == "interests" and isinstance(profile.get("interests"), list):
            if value not in profile["interests"]:
                profile["interests"].append(value)
        elif key == "preferences" and isinstance(value, dict):
            profile["preferences"].update(value)
        else:
            profile[key] = value
        self._save()

    def get_session_summary(self, n=5):
        """Summarize last N sessions."""
        return self.data["sessions"][-n:]

    def start_session(self, topics=None):
        """Register a new session."""
        self.data["sessions"].append({"start": time.time(), "topics": topics or [], "facts_learned": 0})
        self._save()

    def forget(self, query):
        """Remove memories matching query keywords."""
        keywords = set(query.lower().split())
        before = len(self.data["memories"])
        self.data["memories"] = [
            m for m in self.data["memories"]
            if not keywords.issubset(set(m["text"].lower().split()))
        ]
        removed = before - len(self.data["memories"])
        self._save()
        return removed

    def _auto_detect(self, text):
        """Auto-detect user info from conversation text."""
        lower = text.lower().strip()
        # Name detection
        match = re.search(r"my name is (\w+)", lower)
        if match:
            self.data["user_profile"]["name"] = match.group(1).capitalize()
        # Job detection
        match = re.search(r"i work at (.+?)(?:\.|$)", lower) or re.search(r"i'm an? (.+?)(?:\.|$)", lower)
        if match:
            self.data["user_profile"]["job"] = match.group(1).strip().title()
        # Interest detection
        match = re.search(r"i like (.+?)(?:\.|$)", lower)
        if match:
            interest = match.group(1).strip()
            if interest not in self.data["user_profile"]["interests"]:
                self.data["user_profile"]["interests"].append(interest)


# ─── Standalone Tests ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile, shutil

    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "test_memory.json")
    try:
        mem = LongMemory(path=path, session_id=1)

        # Test remember + recall
        mem.remember("Python is a great language", "fact", 0.9)
        mem.remember("I went to the park today", "event", 0.4)
        mem.remember("Machine learning uses neural networks", "fact", 0.8)
        results = mem.recall("Python language")
        assert len(results) > 0
        assert "Python" in results[0]["text"]
        print("✓ remember + recall works")

        # Test auto-detect name
        mem.remember("my name is Alice", "fact", 1.0)
        assert mem.get_user_profile()["name"] == "Alice"
        print("✓ auto-detect name works")

        # Test auto-detect job
        mem.remember("I work at Google", "fact", 0.9)
        assert "Google" in mem.get_user_profile()["job"]
        print("✓ auto-detect job works")

        # Test auto-detect interests
        mem.remember("I like hiking", "preference", 0.7)
        assert "hiking" in mem.get_user_profile()["interests"]
        print("✓ auto-detect interests works")

        # Test update_user_profile
        mem.update_user_profile("interests", "cooking")
        assert "cooking" in mem.get_user_profile()["interests"]
        mem.update_user_profile("preferences", {"theme": "dark"})
        assert mem.get_user_profile()["preferences"]["theme"] == "dark"
        print("✓ update_user_profile works")

        # Test session summary
        mem.start_session(topics=["intro"])
        mem.start_session(topics=["coding"])
        summaries = mem.get_session_summary(n=2)
        assert len(summaries) == 2
        assert summaries[-1]["topics"] == ["coding"]
        print("✓ session summary works")

        # Test forget
        mem.remember("delete this specific memory", "fact", 0.3)
        removed = mem.forget("delete this specific memory")
        assert removed == 1
        assert all("delete this specific" not in m["text"] for m in mem.data["memories"])
        print("✓ forget works")

        # Test persistence
        mem2 = LongMemory(path=path, session_id=2)
        assert mem2.get_user_profile()["name"] == "Alice"
        assert len(mem2.data["memories"]) > 0
        print("✓ persistence works")

        # Test scoring (recency + importance)
        mem3 = LongMemory(path=os.path.join(tmp, "score_test.json"), session_id=1)
        mem3.remember("old python fact", "fact", 0.3)
        time.sleep(0.01)
        mem3.remember("new python tutorial", "fact", 0.95)
        results = mem3.recall("python", limit=2)
        assert results[0]["importance"] >= results[1]["importance"] or "new" in results[0]["text"]
        print("✓ scoring (recency + importance) works")

        print("\n✅ All tests passed!")
    finally:
        shutil.rmtree(tmp)
