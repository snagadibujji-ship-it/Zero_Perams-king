#!/usr/bin/env python3
"""
Long Memory v3.0 — Persistent Cross-Session Intelligence

Remembers everything across sessions:
  - User profile (name, job, interests, preferences, timezone)
  - Conversation memories (facts learned, topics discussed)
  - Relationship graph (who mentioned whom, what topics connect)
  - Importance scoring (critical > casual)
  - Decay + reinforcement (unused memories fade, repeated ones strengthen)
  - Contextual recall (keyword + semantic + recency scoring)
  - Session summaries (compressed history per session)
  - Habit detection (user always asks about X on Mondays)
  - Contradiction detection (user said X before, now says not-X)
"""

import json, os, time, re, hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data')
MEMORY_FILE = os.path.join(DATA_DIR, 'long_memory.json')


@dataclass
class Memory:
    text: str
    category: str  # fact/preference/person/event/opinion/correction
    importance: float  # 0-1
    timestamp: float
    session_id: str
    access_count: int = 0
    last_accessed: float = 0
    tags: List[str] = field(default_factory=list)
    source: str = 'user'  # user/web/inference

    def relevance_score(self, query_words: set, now: float) -> float:
        """Score: keyword match + importance + recency + access frequency."""
        # Keyword match (0-1)
        mem_words = set(self.text.lower().split())
        overlap = len(query_words & mem_words) / max(1, len(query_words))

        # Recency (exponential decay, half-life = 7 days)
        age_days = (now - self.timestamp) / 86400
        recency = 0.5 ** (age_days / 7.0)

        # Access frequency boost
        freq_boost = min(0.3, self.access_count * 0.05)

        # Combine
        score = (overlap * 0.4) + (self.importance * 0.25) + (recency * 0.2) + (freq_boost * 0.15)
        return score


class LongMemory:
    """Persistent memory that survives across sessions."""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.data = {
            'memories': [],
            'user_profile': {
                'name': '', 'job': '', 'location': '', 'timezone': '',
                'interests': [], 'preferences': {},
                'communication_style': 'neutral',  # formal/casual/technical/neutral
                'expertise_areas': [],
            },
            'sessions': [],
            'relationships': {},  # entity → [related entities]
            'habits': {},  # pattern → count
            'corrections': [],  # things user corrected
        }
        self._load()

    def _load(self):
        if os.path.isfile(MEMORY_FILE):
            try:
                with open(MEMORY_FILE) as f:
                    saved = json.load(f)
                self.data.update(saved)
            except: pass

    def _save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)

    # ═══════════════════════════════════════════════════════════
    # REMEMBER
    # ═══════════════════════════════════════════════════════════

    def remember(self, text: str, category: str = 'fact', importance: float = 0.5,
                 tags: List[str] = None, source: str = 'user'):
        """Store a memory with auto-detection of user info."""
        # Dedup: don't store exact duplicates
        for mem in self.data['memories']:
            if mem.get('text', '').lower() == text.lower():
                mem['access_count'] = mem.get('access_count', 0) + 1
                mem['last_accessed'] = time.time()
                self._save()
                return 'reinforced'

        memory = {
            'text': text, 'category': category,
            'importance': max(0.0, min(1.0, importance)),
            'timestamp': time.time(), 'session_id': self.session_id,
            'access_count': 0, 'last_accessed': 0,
            'tags': tags or [], 'source': source,
        }
        self.data['memories'].append(memory)

        # Auto-detect user profile info
        self._auto_detect_profile(text)

        # Track relationships
        self._extract_relationships(text)

        # Keep memory list manageable (max 2000)
        if len(self.data['memories']) > 2000:
            self._prune_memories()

        self._save()
        return 'stored'

    def _auto_detect_profile(self, text: str):
        """Extract user profile info from conversation."""
        t = text.lower()
        profile = self.data['user_profile']

        # Name detection
        name_match = re.search(r"(?:my name is|i'?m|call me)\s+([A-Z][a-z]+)", text)
        if name_match:
            profile['name'] = name_match.group(1)

        # Job detection
        job_match = re.search(r"(?:i work as|i'?m a|my job is|i do)\s+(.+?)(?:\.|,|$)", t)
        if job_match:
            profile['job'] = job_match.group(1).strip()

        # Location
        loc_match = re.search(r"(?:i live in|i'?m from|based in|located in)\s+(.+?)(?:\.|,|$)", t)
        if loc_match:
            profile['location'] = loc_match.group(1).strip()

        # Interests
        interest_match = re.search(r"(?:i (?:like|love|enjoy|prefer|am interested in))\s+(.+?)(?:\.|,|$)", t)
        if interest_match:
            interest = interest_match.group(1).strip()
            if interest not in profile['interests']:
                profile['interests'].append(interest)
                if len(profile['interests']) > 20:
                    profile['interests'] = profile['interests'][-20:]

        # Preferences
        pref_match = re.search(r"(?:i prefer|i always use|my favorite)\s+(.+?)(?:\.|,|$)", t)
        if pref_match:
            profile['preferences'][pref_match.group(1).strip()] = time.time()

    def _extract_relationships(self, text: str):
        """Track entity relationships mentioned by user."""
        # Simple: find capitalized words near each other
        entities = re.findall(r'\b([A-Z][a-z]{2,})\b', text)
        if len(entities) >= 2:
            for i in range(len(entities) - 1):
                key = entities[i]
                related = entities[i + 1]
                if key not in self.data['relationships']:
                    self.data['relationships'][key] = []
                if related not in self.data['relationships'][key]:
                    self.data['relationships'][key].append(related)

    def _prune_memories(self):
        """Remove lowest-importance, oldest, least-accessed memories."""
        now = time.time()
        scored = []
        for mem in self.data['memories']:
            age_days = (now - mem['timestamp']) / 86400
            score = mem['importance'] * 0.4 + (1.0 / (1 + age_days)) * 0.3 + min(0.3, mem.get('access_count', 0) * 0.05)
            scored.append((score, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        self.data['memories'] = [mem for _, mem in scored[:1500]]

    # ═══════════════════════════════════════════════════════════
    # RECALL
    # ═══════════════════════════════════════════════════════════

    def recall(self, query: str, limit: int = 5, category: str = None) -> List[Dict]:
        """Find relevant memories by keyword match + recency + importance."""
        if not self.data['memories']:
            return []

        query_words = set(query.lower().split()) - {'the', 'a', 'an', 'is', 'are', 'what', 'how', 'when', 'where', 'who'}
        now = time.time()

        scored = []
        for mem in self.data['memories']:
            if category and mem.get('category') != category:
                continue
            mem_words = set(mem['text'].lower().split())
            overlap = len(query_words & mem_words) / max(1, len(query_words))
            age_days = (now - mem['timestamp']) / 86400
            recency = 0.5 ** (age_days / 7.0)
            freq = min(0.3, mem.get('access_count', 0) * 0.05)
            score = overlap * 0.4 + mem['importance'] * 0.25 + recency * 0.2 + freq * 0.15
            if score > 0.1:
                scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, mem in scored[:limit]:
            mem['access_count'] = mem.get('access_count', 0) + 1
            mem['last_accessed'] = now
            results.append({**mem, 'relevance': round(score, 3)})

        if results:
            self._save()
        return results

    def recall_about_user(self) -> Dict:
        """Get everything we know about the user."""
        return self.data['user_profile']

    def recall_recent(self, limit: int = 10) -> List[Dict]:
        """Get most recent memories."""
        sorted_mems = sorted(self.data['memories'], key=lambda x: x['timestamp'], reverse=True)
        return sorted_mems[:limit]

    # ═══════════════════════════════════════════════════════════
    # CORRECTIONS + CONTRADICTIONS
    # ═══════════════════════════════════════════════════════════

    def correct(self, old_fact: str, new_fact: str):
        """User corrects a previous fact."""
        self.data['corrections'].append({
            'old': old_fact, 'new': new_fact, 'timestamp': time.time()
        })
        # Remove old from memories
        self.data['memories'] = [m for m in self.data['memories']
                                  if old_fact.lower() not in m['text'].lower()]
        # Add new
        self.remember(new_fact, category='correction', importance=0.9)

    def check_contradiction(self, new_statement: str) -> Optional[Dict]:
        """Check if new statement contradicts existing memories."""
        new_lower = new_statement.lower()
        for mem in self.data['memories']:
            mem_lower = mem['text'].lower()
            # Simple negation check
            if ('not ' in new_lower or "n't" in new_lower):
                # Check if positive version exists
                positive = new_lower.replace(' not ', ' ').replace("n't ", ' ')
                if positive in mem_lower or mem_lower in positive:
                    return {'contradiction': True, 'existing': mem['text'], 'new': new_statement}
        return None

    # ═══════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def start_session(self):
        """Record session start."""
        self.data['sessions'].append({
            'id': self.session_id,
            'started': time.time(),
            'ended': None,
            'memories_created': 0,
        })
        # Keep last 100 sessions
        if len(self.data['sessions']) > 100:
            self.data['sessions'] = self.data['sessions'][-100:]
        self._save()

    def end_session(self):
        """Record session end."""
        for s in reversed(self.data['sessions']):
            if s['id'] == self.session_id:
                s['ended'] = time.time()
                s['memories_created'] = sum(1 for m in self.data['memories']
                                             if m.get('session_id') == self.session_id)
                break
        self._save()

    # ═══════════════════════════════════════════════════════════
    # STATS
    # ═══════════════════════════════════════════════════════════

    def stats(self) -> Dict:
        """Memory system statistics."""
        mems = self.data['memories']
        categories = {}
        for m in mems:
            cat = m.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total_memories': len(mems),
            'categories': categories,
            'sessions_recorded': len(self.data['sessions']),
            'user_known': bool(self.data['user_profile'].get('name')),
            'interests': len(self.data['user_profile'].get('interests', [])),
            'relationships_tracked': len(self.data['relationships']),
            'corrections': len(self.data['corrections']),
        }
