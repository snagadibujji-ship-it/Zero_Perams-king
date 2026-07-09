#!/usr/bin/env python3
"""
Hybrid AI - Full Intelligence Layer
Uses hybrid-ai core engines for world-class reasoning + response.
Runs alongside the C engine - C handles fast lookup, Python handles deep thinking.
"""
import sys, os, random, time, json

# Add paths
BORROWED = os.path.join(os.path.dirname(__file__), '..', 'engines')
CORPUS = '/root/hybrid-ai core'
sys.path.insert(0, BORROWED)
sys.path.insert(0, CORPUS)

# === Load ALL available engines ===
engines_loaded = []

# === Load ALL available engines (fault-tolerant) ===
engines_loaded = []

def try_import(code, name):
    try:
        exec(code, globals())
        engines_loaded.append(name)
    except Exception as e:
        pass  # silently skip unavailable engines

try_import("from memory_engine import MemoryEngine", "memory")
try_import("from story_engine import StoryEngine", "story")
try_import("from realism import PersonContinuityEngine, MoodEngine", "realism")
try_import("from frequency import INDUSTRY_EVENT_WEIGHTS", "frequency")
try_import("from seasonal import SEASONAL_PROFILES", "seasonal")
try_import("from drills import DRILL_PROFILES", "drills")
try_import("from industry_jargon import INDUSTRY_JARGON", "jargon")
try_import("from industry_messages import INDUSTRY_MESSAGES", "messages")
try_import("from worker_personality import PersonalityProfile", "personality")
try_import("from industry_behavior import IndustryBehavior", "behavior")
try_import("from digital_twin import StateTracker", "digital_twin")


class ConversationState:
    """Tracks conversation state across turns."""
    def __init__(self):
        self.turn = 0
        self.mood = "neutral"          # neutral, curious, frustrated, excited, confused
        self.mood_duration = 0
        self.topics = []               # topic history
        self.recurring = {}            # topic -> count
        self.last_intent = None
        self.confidence = 0.8
        self.session_start = time.time()


class HybridBrain:
    """Full AI brain with integrated reasoning engines."""
    
    def __init__(self, seed=None):
        self.rng = random.Random(seed or int(time.time()))
        self.state = ConversationState()
        
        # Core engines (init only what loaded)
        self.memory = MemoryEngine(self.rng) if "memory" in engines_loaded else None
        self.story = StoryEngine(self.rng) if "story" in engines_loaded else None
        self.mood_engine = MoodEngine(self.rng) if "realism" in engines_loaded else None
        
        # Knowledge from corpus (use what loaded)
        self.jargon = INDUSTRY_JARGON if "jargon" in engines_loaded else {}
        self.messages = INDUSTRY_MESSAGES if "messages" in engines_loaded else {}
        self.seasonal = SEASONAL_PROFILES if "seasonal" in engines_loaded else {}
        self.event_weights = INDUSTRY_EVENT_WEIGHTS if "frequency" in engines_loaded else {}
        
    def get_memory_context(self):
        """Get memory-aware context for response generation."""
        if not self.memory:
            return ""
        try:
            prefix = self.memory.get_memory_prefix("conversation")
            return prefix if prefix else ""
        except Exception:
            return ""
    
    def detect_mood(self, user_input):
        """Detect user mood from input signals."""
        inp = user_input.lower()
        # Frustration signals
        if any(w in inp for w in ['why', "can't", 'again', 'still', 'broken', '!!', 'ugh']):
            if self.state.mood != "frustrated":
                self.state.mood = "frustrated"
                self.state.mood_duration = 0
            return "frustrated"
        # Excitement
        if any(w in inp for w in ['awesome', 'great', 'amazing', 'wow', 'cool', '!!']):
            self.state.mood = "excited"
            return "excited"
        # Curiosity
        if any(w in inp for w in ['how', 'why', 'what if', 'tell me', 'explain']):
            self.state.mood = "curious"
            return "curious"
        # Confusion
        if any(w in inp for w in ["don't understand", 'confused', 'huh', 'what do you mean']):
            self.state.mood = "confused"
            return "confused"
        return "neutral"
    
    def track_recurrence(self, topic):
        """Track recurring topics (from memory_engine pattern)."""
        if topic in self.state.recurring:
            self.state.recurring[topic] += 1
        else:
            self.state.recurring[topic] = 1
        return self.state.recurring[topic]
    
    def should_add_memory_ref(self):
        """12% chance of adding memory reference (from memory_engine)."""
        return self.rng.random() < 0.12
    
    def get_mood_modifier(self):
        """Get response style modifier based on mood."""
        mods = {
            "neutral": {"prefix": "", "style": "balanced"},
            "frustrated": {"prefix": "I understand this is frustrating. ", "style": "patient"},
            "excited": {"prefix": "That's great! ", "style": "enthusiastic"},
            "curious": {"prefix": "", "style": "detailed"},
            "confused": {"prefix": "Let me explain more clearly. ", "style": "simple"},
        }
        return mods.get(self.state.mood, mods["neutral"])
    
    def process_turn(self, user_input, c_response=""):
        """
        Process a conversation turn. Takes user input + C engine response.
        Returns enhanced response with personality, mood, memory, and style.
        """
        self.state.turn += 1
        self.memory.record_event("conversation", "user_turn")
        
        # Detect mood
        mood = self.detect_mood(user_input)
        mood_mod = self.get_mood_modifier()
        
        # Track topic recurrence
        words = user_input.lower().split()
        topic = ' '.join(words[:3]) if len(words) >= 3 else user_input.lower()
        count = self.track_recurrence(topic)
        
        # Build enhanced response
        enhanced = c_response
        
        # Add mood prefix
        if mood_mod["prefix"] and self.state.turn > 1:
            enhanced = mood_mod["prefix"] + enhanced
        
        # Add memory reference (12% chance)
        if self.should_add_memory_ref() and self.state.turn > 3:
            mem = self.get_memory_context()
            if mem:
                enhanced = mem + " " + enhanced
        
        # Add recurrence awareness
        if count >= 3:
            enhanced += f" (I notice this has come up {count} times now.)"
        elif count == 2:
            enhanced += " (You asked about this before — let me add more detail.)"
        
        # Story engine: check if we should lock onto this topic
        self.story.check_triggers("conversation", topic, time.localtime().tm_hour)
        
        return {
            "response": enhanced,
            "mood": mood,
            "turn": self.state.turn,
            "confidence": self.state.confidence,
            "recurrence": count,
            "style": mood_mod["style"],
        }
    
    def status(self):
        return {
            "engines": engines_loaded,
            "turn": self.state.turn,
            "mood": self.state.mood,
            "topics_tracked": len(self.state.recurring),
            "uptime": int(time.time() - self.state.session_start),
        }


# === CLI Interface ===
if __name__ == "__main__":
    brain = HybridBrain()
    print(f"=== Hybrid AI Brain ===")
    print(f"Engines loaded: {len(engines_loaded)} ({', '.join(engines_loaded)})")
    print(f"Ready. Type 'status' for info, 'quit' to exit.\n")
    
    while True:
        try:
            user = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:
            continue
        if user == "quit":
            break
        if user == "status":
            print(json.dumps(brain.status(), indent=2))
            continue
        
        result = brain.process_turn(user, f"[C engine would answer: '{user}']")
        print(f"  {result['response']}")
        print(f"  [mood={result['mood']}, turn={result['turn']}, style={result['style']}]\n")
