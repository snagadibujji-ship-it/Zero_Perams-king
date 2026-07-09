"""
Memory Engine — Wave 3
=======================
Makes events reference the past. Real workers constantly say:
- "same issue as last week"
- "third time this month"  
- "as discussed yesterday"
- "remember pump 7 explosion in 2019?"
- "still waiting for parts since Monday"

Also handles daily routine patterns (same readings at same time).
"""
import random
from typing import List, Optional


class MemoryEngine:
    """Tracks recent events and adds past references to messages."""
    
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.recent_events = []  # Last 50 events
        self.recurring_issues = []  # Problems that keep coming back
        self.daily_tasks_done = set()  # Track what's been done today
        self._last_shift = None  # Track shift changes for clearing daily tasks
    
    def on_shift_change(self, new_shift: str):
        """Clear daily task tracking when shift changes (prevents unbounded growth)."""
        if self._last_shift is not None and self._last_shift != new_shift:
            self.daily_tasks_done.clear()
        self._last_shift = new_shift
    
    def record_event(self, category: str, subtype: str, asset: str = ""):
        """Record an event for future reference."""
        self.recent_events.append({
            "category": category,
            "subtype": subtype,
            "asset": asset,
        })
        # Keep only last 100
        if len(self.recent_events) > 100:
            self.recent_events = self.recent_events[-100:]
        
        # Track daily tasks (capped to prevent unbounded growth)
        self.daily_tasks_done.add(subtype)
        if len(self.daily_tasks_done) > 50:
            # Evict oldest entries by clearing and keeping recent
            self.daily_tasks_done.clear()
        
        # Track recurring issues
        if category in ("maintenance", "mistakes_failures", "safety_accidents"):
            self.recurring_issues.append(subtype)
            if len(self.recurring_issues) > 20:
                self.recurring_issues = self.recurring_issues[-20:]
    
    def get_memory_prefix(self, category: str, asset: str = "") -> Optional[str]:
        """Get a memory-based prefix for a message (10% chance).
        
        Implements memory decay: recent events are recalled clearly,
        older events are vague or partially wrong.
        """
        if self.rng.random() > 0.12:  # 12% chance of memory reference
            return None
        
        # Check for recurring issues (strong memory — repetition reinforces)
        # 50% of the time use recurring, 50% use decay-based memory
        if self.recurring_issues and self.rng.random() < 0.5:
            issue = self.rng.choice(self.recurring_issues)
            prefixes = [
                f"same {issue.replace('_', ' ')} again... ",
                "third time this month. ",
                "this keeps happening. ",
                "told you so. same issue. ",
                "exactly what I said last week. ",
                "deja vu... same problem same place. ",
                "I predicted this would happen again. ",
            ]
            return self.rng.choice(prefixes)
        
        # ═══ MEMORY DECAY: older memories are vaguer ═══
        n_events = len(self.recent_events)
        if n_events == 0:
            return None
        
        # Pick a memory — bias toward recent but not overwhelmingly
        # Using sqrt decay so older memories still have a chance
        decay_weights = [(i + 1) ** 0.5 for i in range(n_events)]
        total = sum(decay_weights)
        decay_weights = [w / total for w in decay_weights]
        
        # Pick which memory to recall
        memory_idx = self.rng.choices(range(n_events), weights=decay_weights, k=1)[0]
        memory_age = n_events - memory_idx  # How many events ago
        
        # Fresh memory (< 10 events ago): clear and accurate
        if memory_age < 10:
            clear_memory = [
                "as discussed in morning meeting, ",
                "follow up from earlier: ",
                "update on what just happened: ",
                "like I said few minutes ago, ",
                "remember we just talked about this? ",
                "continuing from before, ",
            ]
            return self.rng.choice(clear_memory)
        
        # Medium memory (10-40 events ago): somewhat vague
        elif memory_age < 40:
            vague_memory = [
                "wasn't there something similar yesterday? ",
                "I think we discussed this recently... ",
                "if I remember correctly from last shift, ",
                "someone mentioned this before... ",
                "this reminds me of... what was it... ",
                "didn't we have this issue last week or something? ",
                "pretty sure this came up in the meeting... ",
            ]
            return self.rng.choice(vague_memory)
        
        # Old memory (40-100 events ago): distorted, possibly wrong details
        else:
            # 30% chance of slightly wrong detail (memory distortion)
            if self.rng.random() < 0.3:
                distorted_memory = [
                    "I think this happened before... maybe 2 months ago? or was it 3? ",
                    "similar thing happened in... was it night shift? no wait, morning. anyway, ",
                    "remember that time with the... what was it... the pump? no, the valve. anyway, ",
                    "last year also same thing... or was it the year before... ",
                    "someone told me about this... Ravi? or was it Kumar? anyway they said ",
                    "we had this exact issue before. fixed it by... hmm can't remember exactly. ",
                    "there was a memo about this. or was it an email. anyway the point is, ",
                ]
                return self.rng.choice(distorted_memory)
            else:
                old_memory = [
                    "since the last shutdown this keeps happening. ",
                    "after last audit they told us to fix this. ",
                    "supervisor mentioned this ages ago. ",
                    "finally addressing what we reported weeks ago. ",
                    "same thing happened in 2019 also. ",
                    "been saying this for months. ",
                    "old problem coming back. ",
                ]
                return self.rng.choice(old_memory)
    
    def add_memory_to_message(self, message: str, category: str, asset: str = "") -> str:
        """Potentially add memory reference to a message."""
        prefix = self.get_memory_prefix(category, asset)
        if prefix:
            return prefix + message
        
        # Sometimes add a suffix reference instead
        if self.rng.random() < 0.05:
            suffixes = [
                " (same as last time)",
                " — again!",
                " ...not surprised tbh",
                " 3rd time, need permanent fix",
                " mentioned this in last meeting also",
                " been saying this for weeks",
            ]
            return message + self.rng.choice(suffixes)
        
        return message


# Industry shift patterns
INDUSTRY_SCHEDULE = {
    # 24/7 continuous (never stops)
    "24x7": {
        "active_hours": list(range(24)),  # All hours active
        "peak_hours": [6, 7, 12, 14, 22],  # Shift changes + lunch
        "dead_hours": [1, 2, 3, 4],  # Very quiet but not zero
        "weekend_reduction": 0.9,  # Almost same on weekends
    },
    # 2-shift (6am-10pm, no night)
    "two_shift": {
        "active_hours": list(range(6, 22)),
        "peak_hours": [6, 7, 10, 12, 14, 17],
        "dead_hours": [22, 23, 0, 1, 2, 3, 4, 5],
        "weekend_reduction": 0.3,  # Much less on weekends
    },
    # Day only (9-6)
    "day_only": {
        "active_hours": list(range(8, 19)),
        "peak_hours": [9, 10, 12, 14, 17],
        "dead_hours": list(range(0, 8)) + list(range(19, 24)),
        "weekend_reduction": 0.0,  # No weekends
    },
    # Seasonal (depends on time of year)
    "seasonal": {
        "active_hours": list(range(5, 19)),  # Daylight hours
        "peak_hours": [6, 7, 11, 15],
        "dead_hours": list(range(0, 5)) + list(range(19, 24)),
        "weekend_reduction": 0.5,
    },
    # Gig/flexible (peaks at meal times)
    "gig_flex": {
        "active_hours": list(range(7, 23)),
        "peak_hours": [11, 12, 13, 18, 19, 20],  # Lunch + dinner
        "dead_hours": [0, 1, 2, 3, 4, 5, 6],
        "weekend_reduction": 1.2,  # MORE active weekends (food delivery!)
    },
}

# Map industries to their schedule type
# (This should ideally be in each IndustryConfig but for now use subsector mapping)
SUBSECTOR_SCHEDULE = {
    # 24/7 industries
    "power_generation": "24x7",
    "petrochemical": "24x7",
    "metallurgy": "24x7",
    "cement": "24x7",
    "chemical": "24x7",
    "oil_gas": "24x7",
    "gas": "24x7",
    "coal": "24x7",
    "storage": "24x7",
    "mining": "24x7",
    "healthcare": "24x7",
    "it_services": "24x7",
    "security": "24x7",
    "automobile": "24x7",
    
    # 2-shift industries
    "electronics": "two_shift",
    "pharmaceutical": "two_shift",
    "food_processing": "two_shift",
    "textile": "two_shift",
    "rubber": "two_shift",
    "plastic": "two_shift",
    "machinery": "two_shift",
    "electrical": "two_shift",
    "heavy_engineering": "two_shift",
    "paper_pulp": "two_shift",
    "precision": "two_shift",
    
    # Day only
    "education": "day_only",
    "consulting": "day_only",
    "banking": "day_only",
    "insurance": "day_only",
    "retail": "day_only",
    "services": "day_only",
    "tourism": "day_only",
    "media": "day_only",
    "software": "day_only",
    
    # Seasonal
    "agriculture": "seasonal",
    "horticulture": "seasonal",
    "fisheries": "seasonal",
    "forestry": "seasonal",
    "quarrying": "seasonal",
    "construction": "seasonal",
    "civil": "seasonal",
    
    # Gig/flexible
    "hospitality": "gig_flex",
    "entertainment": "gig_flex",
    "logistics": "gig_flex",
    "food_beverage": "gig_flex",
}


def get_industry_schedule(subsector: str) -> dict:
    """Get the schedule pattern for an industry."""
    schedule_type = SUBSECTOR_SCHEDULE.get(subsector, "two_shift")
    return INDUSTRY_SCHEDULE.get(schedule_type, INDUSTRY_SCHEDULE["two_shift"])


def is_active_hour(hour: int, subsector: str) -> bool:
    """Check if this hour is active for this industry type."""
    schedule = get_industry_schedule(subsector)
    return hour in schedule["active_hours"]
